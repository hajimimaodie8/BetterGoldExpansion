package com.hjmmd_8.bettergold.entity;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import com.hjmmd_8.bettergold.material.AllMetals;
import com.hjmmd_8.bettergold.material.ChaosItems;
import com.hjmmd_8.bettergold.material.ChaosRange;
import com.hjmmd_8.bettergold.material.ChaosWiring;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllEntities;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.SuspiciousStewEffects;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.phys.EntityHitResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * <b>临时探针</b>（`bg-n10fix` A 级读数）—— 收尾整块删除，绝不进交付 jar。
 *
 * <p>开关：`run/bgn10fix-probe.enabled` 存在才动作；跑完 `halt(false)` **只调一次**。</p>
 */
public final class Bgn10fixProbe {

    private static int ticks;
    private static boolean started;
    private static final List<String> LINES = new ArrayList<>();
    private static int pass;
    private static int fail;

    private Bgn10fixProbe() {
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            pass++;
            LINES.add("PASS " + name + " | " + detail);
        } else {
            fail++;
            LINES.add("FAIL " + name + " | " + detail);
        }
    }

    @SubscribeEvent
    public static void onStarted(ServerStartedEvent event) {
        Path flag = Path.of("bgn10fix-probe.enabled");
        started = Files.isRegularFile(flag);
        if (started) {
            LINES.add("probe-start " + event.getServer().getWorldData().getLevelName());
        }
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        if (!started) {
            return;
        }
        ticks++;
        MinecraftServer server = event.getServer();
        ServerLevel level = server.overworld();
        int cx = 62;
        int cz = 62;
        // 两阶段：先 forceload、**等 60 tick**（让区块到 ENTITY_TICKING），再做 AABB 查询 ——
        // 文档 §三.5 的假阴性陷阱（上一版就是 0 tick 后立刻查询 ⇒ 弹射物数成 0）。
        if (ticks == 60) {
            level.setChunkForced(cx, cz, true);
            return;
        }
        if (ticks != 140) {
            return;
        }
        try {
            run(level);
        } catch (Throwable t) {
            fail++;
            LINES.add("FAIL probe-crash | " + t);
            t.printStackTrace();
        } finally {
            level.setChunkForced(cx, cz, false);
            LINES.add("forcedNow=" + level.getForcedChunks().size());
            LINES.add("SUMMARY pass=" + pass + " fail=" + fail);
            try {
                Files.write(Path.of("bgn10fix-probe-result.txt"), LINES, StandardCharsets.UTF_8);
            } catch (Throwable ignored) {
                // 写不出就靠日志
            }
            for (String line : LINES) {
                System.out.println("[BGN10FIX] " + line);
            }
            started = false;
            server.halt(false);
        }
    }

    private static void run(ServerLevel level) throws Exception {
        BlockPos base = new BlockPos(62 * 16 + 8, 100, 62 * 16 + 8);
        FakePlayer player = new FakePlayer(level, new GameProfile(
                UUID.nameUUIDFromBytes("bgn10fix".getBytes(StandardCharsets.UTF_8)), "bgn10fix"));
        player.setPos(base.getX(), base.getY(), base.getZ());
        player.getInventory().clearContent();
        // ⚠ 上一轮跑测留下的实体（弹射物 / 金钱妖）会污染 AABB 计数 —— 先清场再测。
        var stale = level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class,
                player.getBoundingBox().inflate(96.0D),
                e -> e instanceof ChaosCoinProjectile || e instanceof MoneyGremlin);
        for (var e : stale) {
            e.discard();
        }
        LINES.add("cleanup-stale=" + stale.size());

        // ---------- ③ 迷之炖菜（真 CraftingInput + 真配方 assemble + 真 finishUsingItem）----------
        CraftingInput stewInput = CraftingInput.of(2, 2, List.of(
                new ItemStack(AllBlocks.GOLDEN_TORCHFLOWER.get().asItem()),
                new ItemStack(Items.BROWN_MUSHROOM),
                new ItemStack(Items.RED_MUSHROOM),
                new ItemStack(Items.BOWL)));
        SuspiciousStewRecipeProbe stew = stew(level, stewInput);
        check("03-stew-recipe-matches", stew.matched, "matched=" + stew.matched);
        check("03-stew-flower-effect", stew.duration == 320,
                "stewEffects=" + stew.story + " duration=" + stew.duration);
        if (stew.stack != null) {
            player.removeEffect(MobEffects.ABSORPTION);
            // ⚠ 真路径 = `LivingEntity#completeUsingItem`，它会走 `EventHooks.onItemUseFinish`
            //   ⇒ 探针必须走同一个入口，直接 `finishUsingItem` 不会发 `LivingEntityUseItemEvent.Finish`
            //   （上一版就是这样把「III 级补丁」测成没生效 —— 测量方法错，不是模组坏）。
            net.neoforged.neoforge.event.EventHooks.onItemUseFinish(player, stew.stack.copy(),
                    stew.stack.getUseDuration(player), stew.stack.finishUsingItem(level, player));
            MobEffectInstance absorption = player.getEffect(MobEffects.ABSORPTION);
            check("03-stew-absorption-III", absorption != null && absorption.getAmplifier() == 2
                            && absorption.getDuration() >= 318 && absorption.getDuration() <= 320,
                    "effect=" + (absorption == null ? "null"
                            : (absorption.getAmplifier() + " amp / " + absorption.getDuration() + " tick")));
            player.removeEffect(MobEffects.ABSORPTION);
        }

        // ---------- ④ 附魔书 ----------
        ItemStack book = new ItemStack(ChaosItems.CHAOSGOLD_ENCHANTING_BOOK.get(), 16);
        check("04-book-stack-16", book.getMaxStackSize() == 16, "maxStack=" + book.getMaxStackSize());
        ItemStack sword = new ItemStack(Items.DIAMOND_SWORD);
        player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
        player.setItemInHand(InteractionHand.MAIN_HAND, book);
        player.setItemInHand(InteractionHand.OFF_HAND, sword);
        player.experienceLevel = 30;
        int levelBefore = player.experienceLevel;
        InteractionResult bookUse = book.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        boolean enchanted = !sword.getOrDefault(DataComponents.ENCHANTMENTS,
                net.minecraft.world.item.enchantment.ItemEnchantments.EMPTY).isEmpty();
        check("04-book-main-hand-enchants", bookUse.consumesAction() && enchanted,
                "result=" + bookUse + " enchanted=" + enchanted
                        + " level=" + levelBefore + "->" + player.experienceLevel + " count=" + book.getCount());
        check("04-book-xp-cost", player.experienceLevel < levelBefore,
                "experienceLevel " + levelBefore + " -> " + player.experienceLevel);
        // 负向：副手空 ⇒ 不生效
        ItemStack book2 = new ItemStack(ChaosItems.CHAOSGOLD_ENCHANTING_BOOK.get(), 2);
        player.setItemInHand(InteractionHand.MAIN_HAND, book2);
        player.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
        int count2 = book2.getCount();
        InteractionResult emptyOff = book2.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        check("04-book-empty-offhand-noop", !emptyOff.consumesAction() && book2.getCount() == count2,
                "result=" + emptyOff + " count " + count2 + "->" + book2.getCount());
        // 创造：0 级也能用，且经验一分不扣（`Player#isCreative` 读的是 GameType ⇒ 必须真换模式）
        ItemStack book3 = new ItemStack(ChaosItems.CHAOSGOLD_ENCHANTING_BOOK.get(), 1);
        ItemStack sword3 = new ItemStack(Items.DIAMOND_SWORD);
        player.setItemInHand(InteractionHand.MAIN_HAND, book3);
        player.setItemInHand(InteractionHand.OFF_HAND, sword3);
        player.setGameMode(net.minecraft.world.level.GameType.CREATIVE);
        player.experienceLevel = 0;
        player.totalExperience = 0;
        InteractionResult creativeUse = book3.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        boolean creativeEnchanted = !sword3.getOrDefault(DataComponents.ENCHANTMENTS,
                net.minecraft.world.item.enchantment.ItemEnchantments.EMPTY).isEmpty();
        check("04-book-creative-free", creativeUse.consumesAction() && creativeEnchanted
                        && player.totalExperience == 0 && player.experienceLevel == 0,
                "creative=" + player.isCreative() + " result=" + creativeUse
                        + " enchanted=" + creativeEnchanted + " level=" + player.experienceLevel
                        + " xp=" + player.totalExperience);
        player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);

        // ---------- ⑥ 禁果：饥饿满格也能吃 ----------
        ItemStack fruit = new ItemStack(ChaosItems.CHAOSGOLD_FORBIDDEN_FRUIT.get());
        // 负向对照用**普通食物**（熟牛肉）：原版金苹果自己就是 alwaysEdible ⇒ 当不了对照
        ItemStack plainFood = new ItemStack(Items.COOKED_BEEF);
        player.getFoodData().setFoodLevel(20);
        player.getFoodData().setSaturation(20.0F);
        player.setItemInHand(InteractionHand.MAIN_HAND, fruit);
        InteractionResult fruitUse = fruit.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        player.getFoodData().setFoodLevel(20);
        player.getFoodData().setSaturation(20.0F);
        player.setItemInHand(InteractionHand.MAIN_HAND, plainFood);
        InteractionResult plainUse = plainFood.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        check("06-fruit-always-edible", fruitUse == InteractionResult.CONSUME,
                "chaosgold_fruit=" + fruitUse);
        check("06-plain-food-negative", plainUse == InteractionResult.FAIL,
                "cooked_beef=" + plainUse);

        // ---------- ⑤ 建材硬度 / 铁级 ----------
        var blockState = AllMetals.CHAOSGOLD.block.get().defaultBlockState();
        float hardness = blockState.getDestroySpeed(level, base);
        check("05-hardness-two-thirds", Math.abs(hardness - 55.0F * 2.0F / 3.0F) < 0.001F,
                "destroyTime=" + hardness + " expect=" + (55.0F * 2.0F / 3.0F));
        check("05-iron-tool-tag", blockState.is(BlockTags.NEEDS_IRON_TOOL)
                        && !blockState.is(BlockTags.NEEDS_DIAMOND_TOOL),
                "needs_iron=" + blockState.is(BlockTags.NEEDS_IRON_TOOL)
                        + " needs_diamond=" + blockState.is(BlockTags.NEEDS_DIAMOND_TOOL));
        check("05-wood-cannot-iron-can",
                !new ItemStack(Items.WOODEN_PICKAXE).isCorrectToolForDrops(blockState)
                        && new ItemStack(Items.IRON_PICKAXE).isCorrectToolForDrops(blockState),
                "wood=" + new ItemStack(Items.WOODEN_PICKAXE).isCorrectToolForDrops(blockState)
                        + " iron=" + new ItemStack(Items.IRON_PICKAXE).isCorrectToolForDrops(blockState));

        // ---------- ⑩ 区间随机（2000 采样 + 连续 6 次）----------
        ItemStack chaosSword = new ItemStack(AllMetals.CHAOSGOLD.sword.get());
        RandomSource rng = RandomSource.create(20261018L);
        List<Integer> samples = new ArrayList<>();
        for (int i = 0; i < 2000; i++) {
            ChaosRange.reroll(chaosSword, ChaosRange.Channel.ATTACK, rng);
            samples.add((int) Math.round(ChaosWiring.attackDamageOf(chaosSword)));
        }
        int min = samples.stream().mapToInt(Integer::intValue).min().orElse(-1);
        int max = samples.stream().mapToInt(Integer::intValue).max().orElse(-1);
        double mean = samples.stream().mapToInt(Integer::intValue).average().orElse(-1);
        check("10-range-4..8", min == 4 && max == 8, "min=" + min + " max=" + max + " mean=" + mean);
        check("10-range-intermediate", samples.contains(5) && samples.contains(6) && samples.contains(7),
                "distinct=" + samples.stream().distinct().sorted().toList());
        List<Integer> six = new ArrayList<>();
        for (int i = 0; i < 6; i++) {
            ChaosRange.reroll(chaosSword, ChaosRange.Channel.ATTACK, rng);
            six.add((int) Math.round(ChaosWiring.attackDamageOf(chaosSword)));
        }
        boolean alternating = six.get(0) == 4 && six.get(1) == 8 && six.get(2) == 4;
        boolean hasMiddle = six.stream().anyMatch(v -> v > 4 && v < 8);
        check("10-six-attacks", !alternating && hasMiddle, "six=" + six);
        RandomSource rng2 = RandomSource.create(7L);
        ChaosRange.rerollFor(chaosSword, ChaosRange.Channel.MINING, rng2);
        int m1 = ChaosRange.fractionOf(chaosSword, ChaosRange.Channel.MINING);
        ChaosRange.rerollFor(chaosSword, ChaosRange.Channel.MINING, rng2);
        int m2 = ChaosRange.fractionOf(chaosSword, ChaosRange.Channel.MINING);
        check("10-held-change-rerolls", m1 != m2, "miningFraction " + m1 + " -> " + m2);

        // ---------- ⑧ 弹幕：2.5 格不射 / 5 格射 ----------
        MoneyGremlin near = spawnGremlin(level, player, 2.5D);
        int nearShots = tickAndCount(level, near, player, 130);
        check("08-barrage-2.5m-silent", nearShots == 0, "shots=" + nearShots);
        near.discard();
        MoneyGremlin far = spawnGremlin(level, player, 5.0D);
        int farShots = tickAndCount(level, far, player, 130);
        check("08-barrage-5m-fires", farShots >= 8, "shots=" + farShots);
        far.discard();

        // ---------- ⑨ 混沌金币投掷 ----------
        ItemStack coins = new ItemStack(AllItems.CHAOS_COIN.get(), 2);
        player.setItemInHand(InteractionHand.MAIN_HAND, coins);
        player.getCooldowns().removeCooldown(AllItems.CHAOS_COIN.get());
        InteractionResult coinUse = coins.getItem().use(level, player, InteractionHand.MAIN_HAND).getResult();
        List<ChaosCoinProjectile> thrown = level.getEntitiesOfClass(ChaosCoinProjectile.class,
                player.getBoundingBox().inflate(4.0D));
        check("09-coin-throws-projectile", coinUse.consumesAction() && !thrown.isEmpty(),
                "result=" + coinUse + " projectiles=" + thrown.size());
        check("09-coin-consumes-one", coins.getCount() == 1, "count=" + coins.getCount());
        if (!thrown.isEmpty()) {
            ChaosCoinProjectile coin = thrown.stream().filter(ChaosCoinProjectile::isPlayerThrown)
                    .findFirst().orElse(thrown.get(0));
            Zombie zombie = EntityType.ZOMBIE.create(level);
            zombie.setPos(base.getX() + 1.0D, base.getY(), base.getZ());
            zombie.setNoAi(true);
            // 僵尸自带 2 点护甲 ⇒ 3 点会被折算成 2.76；这里把护甲清零，直接读「裸 3 点」
            zombie.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.ARMOR).setBaseValue(0.0D);
            level.addFreshEntity(zombie);
            zombie.setHealth(20.0F);
            float before = zombie.getHealth();
            coin.onHitEntity(new EntityHitResult(zombie));
            float after = zombie.getHealth();
            MobEffectInstance hunger = zombie.getEffect(MobEffects.HUNGER);
            check("09-coin-3-damage", Math.abs((before - after) - 3.0F) < 0.001F,
                    "health " + before + " -> " + after + " playerThrown=" + coin.isPlayerThrown());
            check("09-coin-hunger-16s", hunger != null && hunger.getDuration() >= 319
                            && hunger.getDuration() <= 320 && hunger.getAmplifier() == 0,
                    "hunger=" + (hunger == null ? "null"
                            : (hunger.getAmplifier() + " amp / " + hunger.getDuration() + " tick")));
            zombie.discard();
        }

        // ---------- ⑦ 悬浮偏移（客户端类不在这里读 —— 那只在客户端探针 / 关卡里验）----------
        check("07-hover-offset", Math.abs(MoneyGremlin.HOVER_OFFSET - 0.4D) < 1e-9,
                "HOVER_OFFSET=" + MoneyGremlin.HOVER_OFFSET);
    }

    private record SuspiciousStewRecipeProbe(boolean matched, int duration, String story, ItemStack stack) {
    }

    private static SuspiciousStewRecipeProbe stew(ServerLevel level, CraftingInput input) {
        for (var holder : level.getRecipeManager().getAllRecipesFor(RecipeType.CRAFTING)) {
            if (holder.value() instanceof net.minecraft.world.item.crafting.SuspiciousStewRecipe recipe) {
                if (!recipe.matches(input, level)) {
                    continue;
                }
                ItemStack out = recipe.assemble(input, level.registryAccess());
                SuspiciousStewEffects effects = out.getOrDefault(DataComponents.SUSPICIOUS_STEW_EFFECTS,
                        SuspiciousStewEffects.EMPTY);
                int duration = effects.effects().isEmpty() ? -1 : effects.effects().get(0).duration();
                String story = effects.effects().stream()
                        .map(e -> net.minecraft.core.registries.BuiltInRegistries.MOB_EFFECT
                                .getKey(e.effect().value()) + "/" + e.duration())
                        .toList().toString();
                return new SuspiciousStewRecipeProbe(true, duration, story, out);
            }
        }
        return new SuspiciousStewRecipeProbe(false, -1, "no-recipe", null);
    }

    private static MoneyGremlin spawnGremlin(ServerLevel level, ServerPlayer target, double distance) {
        MoneyGremlin mob = AllEntities.MONEY_GREMLIN.get().create(level);
        mob.setPos(target.getX() + distance, target.getY(), target.getZ());
        level.addFreshEntity(mob);
        mob.setTarget(target);
        return mob;
    }

    private static int tickAndCount(ServerLevel level, MoneyGremlin mob, ServerPlayer target, int ticks)
            throws Exception {
        Field cooldown = MoneyGremlin.class.getDeclaredField("barrageCooldown");
        cooldown.setAccessible(true);
        cooldown.setInt(mob, 0);
        for (int i = 0; i < ticks; i++) {
            mob.setTarget(target);
            mob.customServerAiStep();
            if (i % 40 == 0) {
                mob.setPos(target.getX() + (mob.getX() - target.getX()), mob.getY(),
                        target.getZ() + (mob.getZ() - target.getZ()));
            }
        }
        return level.getEntitiesOfClass(ChaosCoinProjectile.class, mob.getBoundingBox().inflate(8.0D)).size();
    }
}
