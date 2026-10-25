package com.hjmmd_8.bettergold.probe.bg18b;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.hjmmd_8.bettergold.material.MetalEvents;
import com.hjmmd_8.bettergold.registry.AllEffects;
import com.hjmmd_8.bettergold.recipe.GoldenCowrieMoldRecipe;
import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * bg18b（1.7 第七轮 A 级）临时服务端探针 —— <b>收尾整块删除</b>。
 *
 * <p>做四件事：</p>
 * <ol>
 *   <li>读加载后的 {@code RecipeManager}：金钱贝两条配方的 {@code catalyst} / {@code variant}
 *       （金锭 / 金钱茄），并从 {@code getIngredients()} 读 8 条九宫格原料配方；</li>
 *   <li>真 {@link CraftingMenu} + 真 {@code ContainerLevelAccess} + 两次真点击，把
 *       「2 条金钱贝 + 8 条九宫格」各合成 1 次（产物 count=2 记账、催化剂返还玻璃瓶）；</li>
 *   <li>音咆正负对照：施加者站在目标的 3×3×3 内 <b>不掉血</b>，别的实体照常掉血；
 *       另做一条反向对照（不记施加者 ⇒ 施加者会掉血，证明排除逻辑真的在起作用）；</li>
 *   <li>forceload 双向归零、{@code halt(false)} 只调一次。</li>
 * </ol>
 *
 * <p>开关文件 {@code run/bg18b-probe.enabled}。</p>
 */
@EventBusSubscriber(modid = "bettergold")
public final class Bg18bProbe {

    private static final String TAG = "[bg18b-s]";
    private static final Path SWITCH = Path.of("bg18b-probe.enabled");
    private static final Logger LOG = LoggerFactory.getLogger("Bg18bProbe");

    private static final int WAIT = 45;

    private static int passes;
    private static int fails;
    private static int phase;
    private static int tick;
    private static boolean done;

    private static ServerLevel level;
    private static ServerPlayer crafter;
    private static ServerPlayer caster;
    private static Zombie victimA;
    private static Zombie bystander;
    private static Zombie victimB;
    private static float casterHp;
    private static float victimAHp;
    private static float bystanderHp;
    private static int chunkX;
    private static int chunkZ;

    private Bg18bProbe() {
    }

    private static void check(String id, boolean ok, String detail) {
        if (ok) {
            passes++;
            LOG.info("{} PASS {} :: {}", TAG, id, detail);
        } else {
            fails++;
            LOG.error("{} FAIL {} :: {}", TAG, id, detail);
        }
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        if (done) {
            return;
        }
        MinecraftServer server = event.getServer();
        if (phase == 0) {
            if (!Files.isRegularFile(SWITCH)) {
                return;
            }
            try {
                setup(server);
                phase = 1;
                tick = 0;
            } catch (Throwable t) {
                LOG.error("{} setup threw", TAG, t);
                check("probe_setup", false, String.valueOf(t));
                finish(server);
            }
            return;
        }
        if (phase == 1) {
            tick++;
            // ⚠ 不能在 setup 那一 tick 就 spawn：chunk 刚 forceload、实体管理器还没就绪
            //   （实测 queries 看到 0 个实体，僵尸的 buff 也就从不 tick）⇒ 推迟到第 10 tick。
            if (tick == 10) {
                spawnA();
                return;
            }
            if (tick < WAIT + 10) {
                return;
            }
            evalA();
            spawnCaseB();
            phase = 2;
            tick = 0;
            return;
        }
        if (phase == 2) {
            if (++tick < WAIT) {
                return;
            }
            evalB();
            finish(server);
        }
    }

    // ==================== setup ====================

    private static void setup(MinecraftServer server) {
        level = server.overworld();
        recipes(server);
        echoRoarSetup(server);
    }

    private static void recipes(MinecraftServer server) {
        // ---- ① 金钱贝两条：加载后的实例上读 catalyst / variant ----
        Recipe<?> r0 = byKey(server, "bettergold:golden_cowrie_from_mold");
        Recipe<?> r1 = byKey(server, "bettergold:golden_cowrie_from_mold_money_eggplant");
        boolean type0 = r0 instanceof GoldenCowrieMoldRecipe;
        boolean type1 = r1 instanceof GoldenCowrieMoldRecipe;
        check("cowrie_two_instances", type0 && type1,
                "gold_ingot_recipe=" + cls(r0) + " money_eggplant_recipe=" + cls(r1));
        if (!type0 || !type1) {
            return;
        }
        GoldenCowrieMoldRecipe m0 = (GoldenCowrieMoldRecipe) r0;
        GoldenCowrieMoldRecipe m1 = (GoldenCowrieMoldRecipe) r1;
        String c0 = id(m0.catalyst());
        String c1 = id(m1.catalyst());
        check("cowrie_catalyst_gold_ingot", "minecraft:gold_ingot".equals(c0), "catalyst=" + c0);
        check("cowrie_catalyst_money_eggplant", "bettergold:golden_eggplant".equals(c1), "catalyst=" + c1);
        check("cowrie_variants", m0.variant() == 0 && m1.variant() == 1,
                "variant=" + m0.variant() + "/" + m1.variant());
        check("cowrie_serializers_differ", m0.getSerializer() != m1.getSerializer(),
                "serializer0=" + reg(m0.getSerializer()) + " serializer1=" + reg(m1.getSerializer()));
        // 真合成 2 条（各 1 次）
        craftCowrie("cowrie_craft_gold_ingot", "minecraft:gold_ingot", true);
        craftCowrie("cowrie_craft_money_eggplant", "bettergold:golden_eggplant", true);

        // ---- ② 8 条九宫格：从 RecipeManager 读实例 + 真合成 ----
        String[][] grid = {
                {"bettergold:mixed_crystal_pile", "minecraft:redstone", "minecraft:netherite_scrap"},
                {"minecraft:netherite_scrap", "minecraft:gold_ingot", "minecraft:gold_ingot"},
                {"bettergold:chaosgold_block", "bettergold:refined_alchemic_oil", null},
        };
        String[] families = {"echogold", "flamegold", "illusiongold", "indigoseagold",
                "sturdygold", "thornsgold", "thundergold", "voodoogold"};
        String[] exchanges = {"bettergold:bundled_echo_shard", "bettergold:blazing_rod",
                "bettergold:chorus_cherry_branch", "bettergold:indigo_ocean_heart",
                "bettergold:golden_cowrie", "bettergold:glittering_vine",
                "bettergold:amethyst_energy_dust", "bettergold:voodoo_feather"};
        int gridSeen = 0;
        for (int i = 0; i < families.length; i++) {
            String fam = families[i];
            String rid = "bettergold:raw_" + fam + "_chaosgold";
            Recipe<?> rr = byKey(server, rid);
            if (rr == null) {
                check("grid_recipe_" + fam, false, "missing " + rid);
                continue;
            }
            gridSeen++;
            grid[2][2] = exchanges[i];
            craftGrid("grid_craft_" + fam, grid, "bettergold:raw_" + fam, 2);
        }
        check("grid_recipes_eight", gridSeen == 8, "loaded=" + gridSeen + "/8");
    }

    private static void echoRoarSetup(MinecraftServer server) {
        BlockPos pos = new BlockPos(1000, 120, 1000);
        chunkX = pos.getX() >> 4;
        chunkZ = pos.getZ() >> 4;
        level.setChunkForced(chunkX, chunkZ, true);
        // 同步把 chunk 载到 FULL：只 setChunkForced 时实体管理器还没就绪，addFreshEntity 会"假成功"。
        level.getChunk(chunkX, chunkZ);
        // 遮光 + 地面（避免僵尸白天着火 / 掉下去，污染掉血读数）
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                level.setBlockAndUpdate(pos.offset(dx, -1, dz), Blocks.STONE.defaultBlockState());
                level.setBlockAndUpdate(pos.offset(dx, 2, dz), Blocks.STONE.defaultBlockState());
            }
        }
        // 施加者 = 真 ServerPlayer（进实体管理器，这样 AABB 查询能看见他 —— 作者那条 bug 的前提）
        caster = player(server, "bg18b_caster");
        caster.moveTo(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D, 0.0F, 0.0F);
        caster.setHealth(20.0F);
        level.addNewPlayer(caster);
        LOG.info("{} readout caster_added entities={}", TAG, queryCount(caster.blockPosition()));
    }

    private static void spawnA() {
        BlockPos pos = new BlockPos(1000, 120, 1000);
        victimA = zombie(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D);
        bystander = zombie(pos.getX() + 1.5D, pos.getY(), pos.getZ() + 0.5D);
        MetalEvents.markEchoRoarSource(victimA, caster);
        victimA.addEffect(new MobEffectInstance(AllEffects.ECHO_ROAR, 200, 0, false, false));

        casterHp = caster.getHealth();
        victimAHp = victimA.getHealth();
        bystanderHp = bystander.getHealth();
        int seen = queryCount(victimA.blockPosition());
        LOG.info("{} readout echoA caster={} victim={} bystander={} entities={}", TAG,
                casterHp, victimAHp, bystanderHp, seen);
        // ⚠ 同一 tick 内 addFreshEntity 后 query 恒 0（实体管理器在 tick 末才并入索引）——
        //   "看见没看见" 只能等到 evalA（tick 末之后）再判，否则是假阴性（本轮实测踩过）。
    }

    private static void spawnCaseB() {
        BlockPos pos = new BlockPos(1000, 120, 1000);
        victimB = zombie(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D);
        // 反向对照：**不**调 markEchoRoarSource ⇒ 施加者应被自己这一发声波打到
        victimB.addEffect(new MobEffectInstance(AllEffects.ECHO_ROAR, 200, 0, false, false));
        clearInvuln(caster);
        caster.setHealth(20.0F);
    }

    private static Zombie zombie(double x, double y, double z) {
        Zombie z0 = EntityType.ZOMBIE.create(level);
        if (z0 == null) {
            throw new IllegalStateException("cannot create zombie");
        }
        z0.moveTo(x, y, z, 0.0F, 0.0F);
        z0.setNoAi(true);
        z0.setPersistenceRequired();
        level.addFreshEntity(z0);
        z0.setHealth(20.0F);
        return z0;
    }

    private static int queryCount(BlockPos pos) {
        return level.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(pos).inflate(1.0D)).size();
    }

    // ==================== 读音 ====================

    private static void evalA() {
        float c = caster.getHealth();
        float v = victimA.getHealth();
        float b = bystander.getHealth();
        int seen = queryCount(victimA.blockPosition());
        LOG.info("{} readout evalA caster={} victimA={} bystander={} entities={}", TAG, c, v, b, seen);
        check("echo_entities_visible", seen >= 3,
                "entities_in_3x3x3=" + seen + " (caster + victimA + bystander)");
        check("echo_caster_unhurt", c == casterHp,
                "caster " + casterHp + " -> " + c + " (expected unchanged; source was recorded)");
        check("echo_victim_hurt", v < victimAHp, "victim " + victimAHp + " -> " + v);
        check("echo_bystander_hurt", b < bystanderHp, "bystander " + bystanderHp + " -> " + b);
    }

    private static void evalB() {
        float c = caster.getHealth();
        LOG.info("{} readout evalB caster={} (no source recorded -> must be hurt)", TAG, c);
        check("echo_control_without_mark_caster_hurt", c < 20.0F,
                "caster " + 20.0F + " -> " + c + " (expected hurt: negative control)");
    }

    private static void finish(MinecraftServer server) {
        if (done) {
            return;
        }
        done = true;
        try {
            level.setChunkForced(chunkX, chunkZ, false);
        } catch (Throwable t) {
            LOG.warn("{} unforce threw {}", TAG, String.valueOf(t));
        }
        int forced = level == null ? -1 : level.getForcedChunks().size();
        LOG.info("{} forcedNow={}", TAG, forced);
        check("forceload_zero", forced == 0, "forcedNow=" + forced);
        LOG.info("{} SUMMARY pass={} fail={} forcedNow={}", TAG, passes, fails, forced);
        server.halt(false);
    }

    // ==================== 真合成 ====================

    private static void craftCowrie(String tag, String catalystId, boolean expect) {
        String[] grid = {"bettergold:golden_cowrie_mold", catalystId, null, null, null, null,
                null, null, null};
        craft(tag, grid, "bettergold:golden_cowrie", 1, expect,
                Map.of(0, "damage", 1, "empty"));
    }

    private static void craftGrid(String tag, String[][] grid, String wantId, int wantCount) {
        String[] flat = new String[9];
        for (int r = 0; r < 3; r++) {
            for (int c = 0; c < 3; c++) {
                flat[r * 3 + c] = grid[r][c];
            }
        }
        craft(tag, flat, wantId, wantCount, true, Map.of(7, "bottle"));
    }

    /**
     * 真 {@link CraftingMenu} + 真 slotsChanged + 两次真点击。
     *
     * @param special slot -> "empty"（必须被消耗）/ "bottle"（变成玻璃瓶）/ "damage"（同物品、耐久 +1）
     */
    private static void craft(String tag, String[] grid, String wantId, int wantCount,
                              boolean expect, Map<Integer, String> special) {
        BlockPos pos = new BlockPos(400, 200, 380);
        level.setBlockAndUpdate(pos.below(), Blocks.STONE.defaultBlockState());
        if (crafter == null) {
            crafter = player(level.getServer(), "bg18b_crafter");
            crafter.moveTo(400.5D, 200.0D, 380.5D, 0.0F, 0.0F);
        }
        crafter.getInventory().clearContent();
        CraftingMenu menu = new CraftingMenu(0, crafter.getInventory(),
                ContainerLevelAccess.create(level, pos));
        crafter.containerMenu = menu;
        for (int i = 0; i < 9; i++) {
            ItemStack stack = grid[i] == null ? ItemStack.EMPTY : new ItemStack(item(grid[i]));
            menu.getSlot(1 + i).set(stack);
        }
        menu.slotsChanged(menu.getSlot(1).container);
        ItemStack result = menu.getSlot(0).getItem().copy();
        if (!expect) {
            check(tag + "_no_match", result.isEmpty(), "result=" + desc(result) + " (expected empty)");
            return;
        }
        String gotId = result.isEmpty() ? "<empty>" : id(result.getItem());
        check(tag + "_result", gotId.equals(wantId) && result.getCount() == wantCount,
                "result=" + desc(result) + " (expected " + wantCount + "x " + wantId + ")");
        if (result.isEmpty()) {
            return;
        }
        int[] before = new int[9];
        int[] dmgBefore = new int[9];
        for (int i = 0; i < 9; i++) {
            before[i] = menu.getSlot(1 + i).getItem().getCount();
            dmgBefore[i] = menu.getSlot(1 + i).getItem().getDamageValue();
        }
        int free = -1;
        for (int i = 10; i <= 45; i++) {
            if (menu.getSlot(i).getItem().isEmpty()) {
                free = i;
                break;
            }
        }
        menu.clicked(0, 0, ClickType.PICKUP, crafter);
        boolean resultCleared = menu.getSlot(0).getItem().isEmpty();
        menu.clicked(free, 0, ClickType.PICKUP, crafter);
        List<String> wrong = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            ItemStack now = menu.getSlot(1 + i).getItem();
            String sp = special.get(i);
            if (sp == null) {
                int want = grid[i] == null ? 0 : Math.max(0, before[i] - 1);
                if (now.getCount() != want) {
                    wrong.add("slot" + i + "=" + now.getCount() + " want " + want);
                }
            } else if ("empty".equals(sp)) {
                if (!now.isEmpty()) {
                    wrong.add("slot" + i + " not consumed: " + desc(now));
                }
            } else if ("bottle".equals(sp)) {
                if (!now.is(Items.GLASS_BOTTLE)) {
                    wrong.add("slot" + i + "=" + desc(now) + " want glass_bottle");
                }
            } else if ("damage".equals(sp)) {
                if (!now.is(item(grid[i])) || now.getDamageValue() != dmgBefore[i] + 1) {
                    wrong.add("slot" + i + "=" + desc(now) + " dmg=" + now.getDamageValue()
                            + " want dmg " + (dmgBefore[i] + 1));
                }
            }
        }
        check(tag + "_consumed", wrong.isEmpty(),
                wrong.isEmpty() ? "all slots consumed as expected; resultCleared=" + resultCleared
                        : String.valueOf(wrong));
        int landed = 0;
        for (int i = 0; i < crafter.getInventory().getContainerSize(); i++) {
            ItemStack s = crafter.getInventory().getItem(i);
            if (!s.isEmpty() && id(s.getItem()).equals(wantId)) {
                landed += s.getCount();
            }
        }
        check(tag + "_landed", landed == wantCount, "landed=" + landed + " (expected " + wantCount + ")");
    }

    // ==================== 小工具 ====================

    private static ServerPlayer player(MinecraftServer server, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(("bg18b:" + name).getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer p = new ServerPlayer(server, level, profile, ClientInformation.createDefault());
        try {
            p.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                    server,
                    new net.minecraft.network.Connection(
                            net.minecraft.network.protocol.PacketFlow.SERVERBOUND),
                    p,
                    net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        } catch (Throwable t) {
            LOG.warn("{} dummy connection failed for {}: {}", TAG, name, String.valueOf(t));
        }
        return p;
    }

    private static void clearInvuln(ServerPlayer p) {
        try {
            Field f = ServerPlayer.class.getDeclaredField("spawnInvulnerableTime");
            f.setAccessible(true);
            f.setInt(p, 0);
        } catch (Throwable ignored) {
            // ignore
        }
        try {
            Field f = net.minecraft.world.entity.Entity.class.getDeclaredField("invulnerableTime");
            f.setAccessible(true);
            f.setInt(p, 0);
        } catch (Throwable ignored) {
            // ignore
        }
    }

    private static Recipe<?> byKey(MinecraftServer server, String rid) {
        return server.getRecipeManager().byKey(ResourceLocation.parse(rid))
                .map(RecipeHolder::value).orElse(null);
    }

    private static String cls(Object o) {
        return o == null ? "null" : o.getClass().getSimpleName();
    }

    private static String id(Item item) {
        return BuiltInRegistries.ITEM.getKey(item).toString();
    }

    private static String reg(Object serializer) {
        return String.valueOf(
                BuiltInRegistries.RECIPE_SERIALIZER.getKey((net.minecraft.world.item.crafting
                        .RecipeSerializer<?>) serializer));
    }

    private static Item item(String id) {
        Item it = BuiltInRegistries.ITEM.get(ResourceLocation.parse(id));
        if (it == null || it == Items.AIR) {
            throw new IllegalStateException("missing item " + id);
        }
        return it;
    }

    private static String desc(ItemStack s) {
        return s == null || s.isEmpty() ? "<empty>" : s.getCount() + "x " + id(s.getItem());
    }
}
