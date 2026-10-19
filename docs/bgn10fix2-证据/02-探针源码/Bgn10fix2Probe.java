package com.hjmmd_8.bettergold.entity;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import com.hjmmd_8.bettergold.material.AllMetals;
import com.hjmmd_8.bettergold.material.ChaosRange;
import com.hjmmd_8.bettergold.material.ChaosWiring;
import com.hjmmd_8.bettergold.material.ImbalanceEffects;
import com.hjmmd_8.bettergold.registry.AllEffects;
import com.hjmmd_8.bettergold.registry.AllEntities;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * <b>临时探针</b>（`bg-n10fix2` A 级读数）—— 收尾整块删除，绝不进交付 jar。
 *
 * <p>开关：`run/bgn10fix2-probe.enabled` 存在才动作；跑完 `halt(false)` <b>只调一次</b>。</p>
 */
public final class Bgn10fix2Probe {

    private static int ticks;
    private static boolean started;
    private static final List<String> LINES = new ArrayList<>();
    private static int pass;
    private static int fail;

    private Bgn10fix2Probe() {
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
        Path flag = Path.of("bgn10fix2-probe.enabled");
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
                Files.write(Path.of("bgn10fix2-probe-result.txt"), LINES, StandardCharsets.UTF_8);
            } catch (Throwable ignored) {
                // 写不出就靠日志
            }
            for (String line : LINES) {
                System.out.println("[BGN10FIX2] " + line);
            }
            started = false;
            server.halt(false);
        }
    }

    private static void run(ServerLevel level) throws Exception {
        BlockPos base = new BlockPos(62 * 16 + 8, 100, 62 * 16 + 8);
        FakePlayer player = new FakePlayer(level, new GameProfile(
                UUID.nameUUIDFromBytes("bgn10fix2".getBytes(StandardCharsets.UTF_8)), "bgn10fix2"));
        player.setPos(base.getX(), base.getY(), base.getZ());
        player.getInventory().clearContent();
        var stale = level.getEntitiesOfClass(Entity.class,
                player.getBoundingBox().inflate(96.0D),
                e -> e instanceof ChaosCoinProjectile || e instanceof MoneyGremlin || e instanceof ItemEntity
                        || e instanceof ExperienceOrb);
        for (var e : stale) {
            e.discard();
        }
        LINES.add("cleanup-stale=" + stale.size());

        section1(level, player, base);
        section2(level, player, base);
        section3(level, base);
        section4(level);
    }

    // ==================== ① 金币穿过同类 ====================

    private static void section1(ServerLevel level, FakePlayer player, BlockPos base) {
        MoneyGremlin shooter = spawnGremlin(level, base.getX() + 2.0D, base.getY(), base.getZ());
        MoneyGremlin target = spawnGremlin(level, base.getX() + 7.0D, base.getY(), base.getZ());
        target.setHealth(30.0F);
        target.removeAllEffects();

        List<ChaosCoinProjectile> coins = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            ChaosCoinProjectile coin = new ChaosCoinProjectile(level, shooter);
            coin.setPos(shooter.getX(), shooter.getEyeY(), shooter.getZ());
            coins.add(coin);
            level.addFreshEntity(coin);
            coin.onHitEntity(new EntityHitResult(target));
        }
        long alive = coins.stream().filter(c -> !c.isRemoved()).count();
        check("01-pass-8-alive", alive == 8, "alive=" + alive + "/8");
        check("01-pass-no-damage", target.getHealth() == 30.0F, "hp=" + target.getHealth());
        check("01-pass-no-hunger", target.getEffect(MobEffects.HUNGER) == null,
                "hunger=" + target.getEffect(MobEffects.HUNGER));
        for (ChaosCoinProjectile c : coins) {
            c.discard();
        }

        // 玩家投掷的同一枚：按「全体同类穿透」口径，也不伤金钱妖
        ChaosCoinProjectile byPlayer = new ChaosCoinProjectile(level, player);
        byPlayer.setPos(shooter.getX(), shooter.getEyeY(), shooter.getZ());
        level.addFreshEntity(byPlayer);
        byPlayer.onHitEntity(new EntityHitResult(target));
        check("01-pass-player-coin", !byPlayer.isRemoved() && target.getHealth() == 30.0F,
                "removed=" + byPlayer.isRemoved() + " hp=" + target.getHealth()
                        + " playerThrown=" + byPlayer.isPlayerThrown());
        byPlayer.discard();

        // 真飞行：从 2 格外朝目标飞，穿过之后仍然 alive / 目标不掉血
        MoneyGremlin flyTarget = spawnGremlin(level, base.getX() + 7.0D, base.getY(), base.getZ() + 3.0D);
        flyTarget.setHealth(30.0F);
        List<ChaosCoinProjectile> flying = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            ChaosCoinProjectile c = new ChaosCoinProjectile(level, shooter);
            c.setPos(flyTarget.getX() - 3.0D, flyTarget.getY() + 1.0D, flyTarget.getZ());
            c.setDeltaMovement(1.0D, 0.0D, 0.0D);
            level.addFreshEntity(c);
            flying.add(c);
        }
        for (int t = 0; t < 12; t++) {
            for (ChaosCoinProjectile c : flying) {
                if (!c.isRemoved()) {
                    c.tick();
                }
            }
        }
        long flyAlive = flying.stream().filter(c -> !c.isRemoved()).count();
        check("01-flythrough", flyAlive == 3 && flyTarget.getHealth() == 30.0F
                        && flyTarget.getEffect(MobEffects.HUNGER) == null,
                "alive=" + flyAlive + "/3 hp=" + flyTarget.getHealth());
        for (ChaosCoinProjectile c : flying) {
            c.discard();
        }

        // 负向对照：同一发打僵尸 ⇒ 伤害 + 饥饿 + discard
        Zombie zombie = EntityType.ZOMBIE.create(level);
        zombie.setPos(base.getX() + 7.0D, base.getY(), base.getZ() + 6.0D);
        zombie.setNoAi(true);
        zombie.getAttribute(Attributes.ARMOR).setBaseValue(0.0D);
        level.addFreshEntity(zombie);
        zombie.setHealth(20.0F);
        ChaosCoinProjectile hitZombie = new ChaosCoinProjectile(level, shooter);
        hitZombie.setPos(zombie.getX(), zombie.getY() + 1.0D, zombie.getZ());
        level.addFreshEntity(hitZombie);
        hitZombie.onHitEntity(new EntityHitResult(zombie));
        MobEffectInstance hunger = zombie.getEffect(MobEffects.HUNGER);
        check("01-zombie-damage", zombie.getHealth() < 20.0F,
                "hp 20.0 -> " + zombie.getHealth() + " difficulty=" + level.getDifficulty());
        check("01-zombie-hunger", hunger != null && hunger.getAmplifier() == 0,
                "hunger=" + (hunger == null ? "null" : (hunger.getAmplifier() + " amp / " + hunger.getDuration())));
        check("01-zombie-discard", hitZombie.isRemoved(), "removed=" + hitZombie.isRemoved());

        shooter.discard();
        target.discard();
        flyTarget.discard();
        zombie.discard();
    }

    private static MoneyGremlin spawnGremlin(ServerLevel level, double x, double y, double z) {
        MoneyGremlin mob = AllEntities.MONEY_GREMLIN.get().create(level);
        mob.setPos(x, y, z);
        mob.setNoAi(true);
        level.addFreshEntity(mob);
        return mob;
    }

    // ==================== ② 金钱贝模具：只提升掉率、数量恒 1 ====================

    private static void section2(ServerLevel level, FakePlayer player, BlockPos base) throws Exception {
        Holder<Enchantment> looting = level.registryAccess().registryOrThrow(Registries.ENCHANTMENT)
                .getHolderOrThrow(Enchantments.LOOTING);
        DropSample l0 = killSample(level, player, base, null, 0, 300);
        DropSample l3 = killSample(level, player, base, looting, 3, 300);

        double rate0 = l0.molds / 300.0D;
        double rate3 = l3.molds / 300.0D;
        check("02-mold-chance-16", Math.abs(MoneyGremlin.cowrieMoldChance(0) - 0.16F) < 1e-6F,
                "chance(0)=" + MoneyGremlin.cowrieMoldChance(0));
        check("02-mold-chance-64", Math.abs(MoneyGremlin.cowrieMoldChance(3) - 0.64F) < 1e-6F,
                "chance(3)=" + MoneyGremlin.cowrieMoldChance(3));
        check("02-mold-rate-l0", rate0 >= 0.10D && rate0 <= 0.23D, "observed=" + rate0 + " n=300");
        check("02-mold-rate-l3", rate3 >= 0.56D && rate3 <= 0.72D, "observed=" + rate3 + " n=300");
        check("02-mold-count-1", l0.badMoldStacks == 0 && l3.badMoldStacks == 0,
                "l0 non-1 stacks=" + l0.badMoldStacks + " l3 non-1 stacks=" + l3.badMoldStacks);
        check("02-coinstring-l0", l0.coinCounts.stream().allMatch(c -> c == 1),
                "distinct=" + new HashSet<>(l0.coinCounts));
        check("02-coinstring-l3", l3.coinCounts.stream().anyMatch(c -> c > 1)
                        && l3.coinCounts.stream().allMatch(c -> c >= 1 && c <= 4)
                        && Math.abs(l3.meanCoins() - 2.5D) < 0.35D,
                "distinct=" + new HashSet<>(l3.coinCounts) + " mean=" + l3.meanCoins());
    }

    private static DropSample killSample(ServerLevel level, ServerPlayer player, BlockPos base,
            Holder<Enchantment> looting, int lootingLevel, int kills) {
        ItemStack sword = new ItemStack(Items.DIAMOND_SWORD);
        if (looting != null) {
            sword.enchant(looting, lootingLevel);
        }
        player.setItemInHand(InteractionHand.MAIN_HAND, sword);
        DamageSource source = level.damageSources().playerAttack(player);
        DropSample out = new DropSample();
        double x = base.getX() + 20.0D;
        double y = base.getY();
        double z = base.getZ();
        for (int i = 0; i < kills; i++) {
            MoneyGremlin mob = AllEntities.MONEY_GREMLIN.get().create(level);
            mob.setPos(x, y, z);
            level.addFreshEntity(mob);
            mob.invulnerableTime = 0;
            mob.setHealth(1.0F);
            mob.hurt(source, 100.0F);
            AABB box = new AABB(x - 8.0D, y - 4.0D, z - 8.0D, x + 8.0D, y + 4.0D, z + 8.0D);
            for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, box)) {
                ItemStack stack = item.getItem();
                if (stack.is(AllItems.GOLDEN_COWRIE_MOLD.get())) {
                    out.molds++;
                    if (stack.getCount() != 1) {
                        out.badMoldStacks++;
                    }
                } else if (stack.is(AllItems.CHAOS_COIN_STRING.get())) {
                    out.coinCounts.add(stack.getCount());
                }
                item.discard();
            }
            for (ExperienceOrb orb : level.getEntitiesOfClass(ExperienceOrb.class, box)) {
                orb.discard();
            }
            mob.discard();
        }
        return out;
    }

    private static final class DropSample {
        int molds;
        int badMoldStacks;
        final List<Integer> coinCounts = new ArrayList<>();

        double meanCoins() {
            return coinCounts.stream().mapToInt(Integer::intValue).average().orElse(-1.0D);
        }
    }

    // ==================== ③ 两个失衡：1%~50% 每次重取 ====================

    private static void section3(ServerLevel level, BlockPos base) {
        Zombie attacker = EntityType.ZOMBIE.create(level);
        attacker.setPos(base.getX() - 5.0D, base.getY(), base.getZ());
        attacker.setNoAi(true);
        level.addFreshEntity(attacker);
        Zombie victim = EntityType.ZOMBIE.create(level);
        victim.setPos(base.getX() - 5.0D, base.getY(), base.getZ() + 3.0D);
        victim.setNoAi(true);
        victim.getAttribute(Attributes.ARMOR).setBaseValue(0.0D);
        level.addFreshEntity(victim);

        attacker.addEffect(new MobEffectInstance(AllEffects.POWER_IMBALANCE.getDelegate(), 100000, 0));
        DamageSource source = level.damageSources().mobAttack(attacker);
        List<Float> power = new ArrayList<>();
        for (int i = 0; i < 2000; i++) {
            victim.setHealth(20.0F);
            victim.invulnerableTime = 0;
            victim.hurt(source, 1.0F);
            power.add(20.0F - victim.getHealth());
        }
        attacker.removeAllEffects();

        victim.addEffect(new MobEffectInstance(AllEffects.RESISTANCE_IMBALANCE.getDelegate(), 100000, 0));
        List<Float> resist = new ArrayList<>();
        for (int i = 0; i < 2000; i++) {
            victim.setHealth(20.0F);
            victim.invulnerableTime = 0;
            victim.hurt(source, 1.0F);
            resist.add(20.0F - victim.getHealth());
        }
        victim.removeAllEffects();

        stats("03-power", power, 0.50D, 0.99D, 0.745D);
        stats("03-resistance", resist, 1.01D, 1.50D, 1.255D);
        check("03-power-six", new HashSet<>(power.subList(0, 6)).size() >= 3,
                "six=" + power.subList(0, 6));
        check("03-resistance-six", new HashSet<>(resist.subList(0, 6)).size() >= 3,
                "six=" + resist.subList(0, 6));

        ImbalanceEffects.apply(victim, AllEffects.POWER_IMBALANCE.getDelegate());
        MobEffectInstance applied = victim.getEffect(AllEffects.POWER_IMBALANCE);
        check("03-amplifier-zero", applied != null && applied.getAmplifier() == 0,
                "amplifier=" + (applied == null ? "null" : applied.getAmplifier()));

        attacker.discard();
        victim.discard();
    }

    private static void stats(String name, List<Float> values, double min, double max, double mean) {
        float lo = values.stream().min(Float::compare).orElse(-1.0F);
        float hi = values.stream().max(Float::compare).orElse(-1.0F);
        double avg = values.stream().mapToDouble(Float::doubleValue).average().orElse(-1.0D);
        long distinct = values.stream().map(v -> Math.round(v * 100.0F)).distinct().count();
        check(name + "-range", lo >= min - 1e-4F && hi <= max + 1e-4F,
                "min=" + lo + " max=" + hi + " expected=[" + min + "," + max + "]");
        check(name + "-distinct", distinct >= 10, "distinct=" + distinct + "/2000");
        check(name + "-mean", Math.abs(avg - mean) < 0.02D, "mean=" + avg + " expected~" + mean);
    }

    // ==================== ④ 两把新刀的数值 ====================

    private static void section4(ServerLevel level) {
        RandomSource rng = RandomSource.create(20261019L);
        ItemStack chaosgoldKnife = knife("chaosgold");
        ItemStack chaosalloyKnife = knife("chaosalloy");
        check("04-final-flag", AllMetals.CHAOSGOLD.knifeValuesAreFinal
                        && AllMetals.CHAOSALLOY.knifeValuesAreFinal,
                "chaosgold=" + AllMetals.CHAOSGOLD.knifeValuesAreFinal
                        + " chaosalloy=" + AllMetals.CHAOSALLOY.knifeValuesAreFinal);

        KnifeSample cg = knifeSample(chaosgoldKnife, rng, 2000);
        KnifeSample ca = knifeSample(chaosalloyKnife, rng, 2000);
        check("04-chaosgold-damage", cg.min >= 2.5F - 1e-3F && cg.max <= 6.5F + 1e-3F
                        && Math.abs(cg.min - 2.5F) < 0.02F && Math.abs(cg.max - 6.5F) < 0.02F,
                "damage min=" + cg.min + " max=" + cg.max + " mean=" + cg.mean + " distinct=" + cg.distinct);
        check("04-chaosalloy-damage", ca.min >= 6.5F - 1e-3F && ca.max <= 13.0F + 1e-3F
                        && Math.abs(ca.min - 6.5F) < 0.02F && Math.abs(ca.max - 13.0F) < 0.02F,
                "damage min=" + ca.min + " max=" + ca.max + " mean=" + ca.mean + " distinct=" + ca.distinct);
        check("04-chaosgold-speed", Math.abs(cg.speed - 2.0D) < 1e-4D, "modifier=" + cg.modifierSpeed
                + " final=" + cg.speed);
        check("04-chaosalloy-speed", Math.abs(ca.speed - 2.0D) < 1e-4D, "modifier=" + ca.modifierSpeed
                + " final=" + ca.speed);
        check("04-no-10-15", ca.max < 15.0F && ca.min < 10.5F,
                "chaosalloy min/max=" + ca.min + "/" + ca.max + "（旧口径 10.0..15.5 已不再出现）");
        check("04-cg-no-10", cg.max < 10.0F, "chaosgold max=" + cg.max + "（旧口径最高 10.0 已不再出现）");

        // 既有 8 族：改前/改后都应恒为 6.5（物品属性；显示 7.5）/ 2.2
        List<String> eight = new ArrayList<>();
        boolean allEightOk = true;
        for (String id : List.of("flamegold", "voodoogold", "thundergold", "indigoseagold",
                "illusiongold", "thornsgold", "echogold", "sturdygold")) {
            ItemStack stack = knife(id);
            double damage = attackDamageOf(stack);
            double modifierSpeed = attackSpeedModifierOf(stack);
            eight.add(id + "=" + damage + "/" + (4.0D + modifierSpeed));
            if (Math.abs(damage - 6.5D) > 1e-3D || Math.abs(modifierSpeed + 1.8D) > 1e-3D) {
                allEightOk = false;
            }
        }
        check("04-eight-knives-unchanged", allEightOk, "eight=" + eight);

        // 剑的伤害仍高于刀（同一族对照）
        float cgSword = swordMax(AllMetals.CHAOSGOLD.sword.get(), rng);
        float caSword = swordMax(AllMetals.CHAOSALLOY.sword.get(), rng);
        check("04-sword-higher", cgSword > cg.max && caSword > ca.max,
                "chaosgold sword max=" + cgSword + " vs knife=" + cg.max
                        + "; chaosalloy sword max=" + caSword + " vs knife=" + ca.max);
    }

    private static ItemStack knife(String familyId) {
        Item item = BuiltInRegistries.ITEM.get(
                ResourceLocation.fromNamespaceAndPath("bettergold", familyId + "_knife"));
        return new ItemStack(item);
    }

    private static final class KnifeSample {
        float min;
        float max;
        double mean;
        long distinct;
        double modifierSpeed;
        double speed;
    }

    private static KnifeSample knifeSample(ItemStack stack, RandomSource rng, int n) {
        KnifeSample s = new KnifeSample();
        float lo = Float.MAX_VALUE;
        float hi = -Float.MAX_VALUE;
        double total = 0.0D;
        Set<Integer> distinct = new HashSet<>();
        for (int i = 0; i < n; i++) {
            ChaosRange.reroll(stack, ChaosRange.Channel.ATTACK, rng);
            float damage = (float) attackDamageOf(stack);
            lo = Math.min(lo, damage);
            hi = Math.max(hi, damage);
            total += damage;
            distinct.add(Math.round(damage * 100.0F));
        }
        s.min = lo;
        s.max = hi;
        s.mean = total / n;
        s.distinct = distinct.size();
        s.modifierSpeed = attackSpeedModifierOf(stack);
        s.speed = 4.0D + s.modifierSpeed;
        return s;
    }

    private static float swordMax(Item item, RandomSource rng) {
        ItemStack stack = new ItemStack(item);
        float max = -Float.MAX_VALUE;
        for (int i = 0; i < 2000; i++) {
            ChaosRange.reroll(stack, ChaosRange.Channel.ATTACK, rng);
            max = Math.max(max, (float) attackDamageOf(stack));
        }
        return max;
    }

    private static double attackDamageOf(ItemStack stack) {
        double total = 0.0D;
        for (var entry : stack.getAttributeModifiers().modifiers()) {
            if (entry.attribute().value() == Attributes.ATTACK_DAMAGE.value()) {
                total += entry.modifier().amount();
            }
        }
        return total;
    }

    private static double attackSpeedModifierOf(ItemStack stack) {
        double total = 0.0D;
        for (var entry : stack.getAttributeModifiers().modifiers()) {
            if (entry.attribute().value() == Attributes.ATTACK_SPEED.value()) {
                total += entry.modifier().amount();
            }
        }
        return total;
    }
}
