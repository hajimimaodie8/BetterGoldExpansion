package com.hjmmd_8.bettergold.probe.bg19;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.UUID;

import com.hjmmd_8.bettergold.material.AllMetals;
import com.hjmmd_8.bettergold.material.ChaosRange;
import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.registry.AllEffects;
import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * bg19（1.7 第八轮 A 级）临时服务端探针 —— <b>收尾整块删除</b>。
 *
 * <p>五件事（对应 R1 / R2 / R3 / R5 / R6）：</p>
 * <ol>
 *   <li><b>R1 牛奶免疫</b>：真 {@link ServerPlayer} 逐个挂上本模组 10 个效果 + 原版 {@code speed}，
 *       然后走<b>真的</b> {@code Items.MILK_BUCKET.finishUsingItem(...)}（= 客户端喝完 32 tick 后
 *       {@code LivingEntity#updateUsingItem} 调的那一句）⇒ 我们 10 个仍在、原版 speed 被清。</li>
 *   <li><b>R2 甜浆果丛</b>：放一个真的 {@code minecraft:sweet_berry_bush}（AGE=3），调它的
 *       {@code BlockState#entityInside}（= {@code Entity#checkInsideBlocks} 里那一句）⇒
 *       用两个探针监听器（HIGHEST 记"我们改之前"、LOWEST 记"改之后"）读倍数，0/1/2/3/4 件。</li>
 *   <li><b>R3 区间核对</b>：真物品栈上反复 {@code ChaosRange.reroll} 采样，逐件读
 *       {@code ChaosRange.current} 的最小/最大值，再把四件之和的最小/最大算出来。</li>
 *   <li><b>R5 耐久</b>：混沌金四件 {@code getMaxDamage()}。</li>
 *   <li><b>R6 音波击退</b>：真 {@link Warden} + 真 {@code SonicBoom} 行为（反射调它 protected 的
 *       {@code tick}，which 是原版 {@code hurt} + {@code push} 的唯一入口）⇒ 读受击者的
 *       {@code getDeltaMovement()} 水平位移，0/1/2/3/4 件。</li>
 * </ol>
 *
 * <p>开关文件 {@code run/bg19-probe.enabled}。forceload 双向归零、{@code halt(false)} 只调一次。</p>
 */
@EventBusSubscriber(modid = "bettergold")
public final class Bg19Probe {

    private static final String TAG = "[bg19-s]";
    private static final Path SWITCH = Path.of("bg19-probe.enabled");
    private static final Logger LOG = LoggerFactory.getLogger("Bg19Probe");

    private static int passes;
    private static int fails;
    private static int phase;
    private static int tick;
    private static boolean done;

    private static ServerLevel level;
    private static ServerPlayer milkMan;
    private static ServerPlayer berryMan;
    private static ServerPlayer sonicMan;
    private static Warden warden;

    private static final BlockPos BASE = new BlockPos(2000, 120, 2000);
    private static final BlockPos BUSH = new BlockPos(2000, 120, 2000);
    private static final int[] FORCED_X = {2000 >> 4, 2001 >> 4, 2002 >> 4};

    /** R2 用：HIGHEST 记"我们改之前"、LOWEST 记"改之后"。 */
    private static float berryBefore = -1.0F;
    private static float berryAfter = -1.0F;

    private Bg19Probe() {
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

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void berryBeforeListener(LivingDamageEvent.Pre event) {
        if (event.getSource().is(net.minecraft.world.damagesource.DamageTypes.SWEET_BERRY_BUSH)) {
            berryBefore = event.getNewDamage();
        }
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void berryAfterListener(LivingDamageEvent.Pre event) {
        if (event.getSource().is(net.minecraft.world.damagesource.DamageTypes.SWEET_BERRY_BUSH)) {
            berryAfter = event.getNewDamage();
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
            // 等 chunk 到 FULL / 实体管理器就绪（bg18b 踩过的假阴性：同一 tick 看不到实体）
            if (tick < 10) {
                return;
            }
            try {
                runR1();
                runR5();
                runR3();
                runR2();
                runR6();
                runR7();
            } catch (Throwable t) {
                LOG.error("{} measure threw", TAG, t);
                check("probe_measure", false, String.valueOf(t));
            }
            phase = 2;
            tick = 0;
            return;
        }
        if (phase == 2) {
            // 至少过完一个完整 tick：R6 的瞬态修饰符必须已经被 ServerTickEvent.Post 摘干净
            if (++tick < 3) {
                return;
            }
            try {
                var inst = sonicMan.getAttribute(Attributes.KNOCKBACK_RESISTANCE);
                boolean left = inst != null && inst.hasModifier(SONIC_ID());
                check("sonic_knockback_cleared", !left,
                        "leftover_modifier=" + left + " (tick-end cleanup)");
            } catch (Throwable t) {
                check("sonic_knockback_cleared", false, String.valueOf(t));
            }
            finish(server);
        }
    }

    // ==================== setup ====================

    private static void setup(MinecraftServer server) {
        level = server.overworld();
        for (int cx : FORCED_X) {
            level.setChunkForced(cx, BASE.getZ() >> 4, true);
            level.getChunk(cx, BASE.getZ() >> 4);
            // 地面：避免掉进洞里 / 光照问题
            for (int dx = 0; dx < 16; dx++) {
                for (int dz = 0; dz < 16; dz++) {
                    level.setBlockAndUpdate(new BlockPos((cx << 4) + dx, BASE.getY() - 1, (BASE.getZ() >> 4 << 4) + dz),
                            Blocks.STONE.defaultBlockState());
                    level.setBlockAndUpdate(new BlockPos((cx << 4) + dx, BASE.getY() + 3, (BASE.getZ() >> 4 << 4) + dz),
                            Blocks.STONE.defaultBlockState());
                }
            }
        }
        level.setBlockAndUpdate(BUSH, Blocks.SWEET_BERRY_BUSH.defaultBlockState()
                .setValue(SweetBerryBushBlock.AGE, Integer.valueOf(3)));

        milkMan = player(server, "bg19_milk");
        milkMan.moveTo(BASE.getX() + 0.5D, BASE.getY(), BASE.getZ() + 4.5D, 0.0F, 0.0F);
        milkMan.setHealth(20.0F);
        level.addNewPlayer(milkMan);

        berryMan = player(server, "bg19_berry");
        berryMan.moveTo(BUSH.getX() + 0.5D, BUSH.getY(), BUSH.getZ() + 0.5D, 0.0F, 0.0F);
        berryMan.setHealth(20.0F);
        level.addNewPlayer(berryMan);

        // ⚠ 距离必须 **≤ 15**：`SonicBoom#tick` 的 filter 是 `owner.closerThan(target, 15.0, 20.0)`
        //   （第一个数是 XZ 距离上限，不是"最小距离" —— 17 格时整段 ifPresent 直接不进，读数恒 0）。
        sonicMan = player(server, "bg19_sonic");
        sonicMan.moveTo(BASE.getX() + 10.5D, BASE.getY(), BASE.getZ() + 8.5D, 0.0F, 0.0F);
        sonicMan.setHealth(20.0F);
        level.addNewPlayer(sonicMan);

        warden = EntityType.WARDEN.create(level);
        if (warden == null) {
            throw new IllegalStateException("cannot create warden");
        }
        warden.moveTo(BASE.getX() + 0.5D, BASE.getY(), BASE.getZ() + 8.5D, 0.0F, 0.0F);
        warden.setPersistenceRequired();
        level.addFreshEntity(warden);

        LOG.info("{} readout setup levelName={} forced={} warden={} playerDist={}", TAG,
                levelName(server), level.getForcedChunks().size(),
                warden.blockPosition().toShortString(),
                String.format("%.3f", warden.distanceTo(sonicMan)));
    }

    private static String levelName(MinecraftServer server) {
        try {
            Object data = server.overworld().getLevelData();
            Method m = data.getClass().getMethod("getLevelName");
            return String.valueOf(m.invoke(data));
        } catch (Throwable t) {
            return "<unreadable:" + t.getClass().getSimpleName() + ">";
        }
    }

    // ==================== R1：牛奶免疫 ====================

    private static void runR1() {
        List<Holder<MobEffect>> ours = List.of(
                AllEffects.COLD_RESISTANCE, AllEffects.HIGH_BURN, AllEffects.VOODOO,
                AllEffects.TREMBLE, AllEffects.SEDIMENT, AllEffects.SOOTHE,
                AllEffects.PARASITE, AllEffects.ECHO_ROAR,
                AllEffects.POWER_IMBALANCE, AllEffects.RESISTANCE_IMBALANCE);
        for (Holder<MobEffect> h : ours) {
            milkMan.addEffect(new MobEffectInstance(h, 600, 0, false, true));
        }
        milkMan.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 600, 0, false, true));
        int before = milkMan.getActiveEffects().size();
        String cures = String.valueOf(milkMan.getEffect(AllEffects.PARASITE).getCures());
        LOG.info("{} readout r1_before active={} parasiteCures={}", TAG, before, cures);
        check("r1_cures_exclude_milk", !milkMan.getEffect(AllEffects.PARASITE).getCures()
                .contains(net.neoforged.neoforge.common.EffectCures.MILK), "cures=" + cures);

        // 真牛奶：客户端喝完 32 tick 后 LivingEntity#updateUsingItem 调的就是这一句
        Items.MILK_BUCKET.finishUsingItem(new ItemStack(Items.MILK_BUCKET), level, milkMan);

        int kept = 0;
        for (Holder<MobEffect> h : ours) {
            boolean still = milkMan.hasEffect(h);
            if (still) {
                kept++;
            }
            check("r1_kept_" + h.unwrapKey().map(k -> k.location().getPath()).orElse("?"),
                    still, "duration=" + (still ? milkMan.getEffect(h).getDuration() : -1));
        }
        check("r1_all_ten_kept", kept == ours.size(), "kept=" + kept + "/" + ours.size());
        // 负向对照：原版 speed 必须**被清掉**
        check("r1_vanilla_speed_cleared", !milkMan.hasEffect(MobEffects.MOVEMENT_SPEED),
                "speed_present=" + milkMan.hasEffect(MobEffects.MOVEMENT_SPEED));
    }

    // ==================== R5：混沌金耐久 ====================

    private static void runR5() {
        MetalFamily cg = AllMetals.CHAOSGOLD;
        int helm = new ItemStack(cg.helmet.get()).getMaxDamage();
        int chest = new ItemStack(cg.chestplate.get()).getMaxDamage();
        int legs = new ItemStack(cg.leggings.get()).getMaxDamage();
        int boots = new ItemStack(cg.boots.get()).getMaxDamage();
        LOG.info("{} readout r5_durability helmet={} chest={} legs={} boots={}", TAG, helm, chest, legs, boots);
        check("r5_durability", helm == 200 && chest == 264 && legs == 246 && boots == 220,
                "helmet=" + helm + " chest=" + chest + " legs=" + legs + " boots=" + boots
                        + " (expected 200/264/246/220)");
    }

    // ==================== R3：区间核对 ====================

    private static void runR3() {
        sampleRanges(AllMetals.CHAOSGOLD, "chaosgold", 0.0F, 6.0F, 0.0F, 24.0F);
        sampleRanges(AllMetals.CHAOSALLOY, "chaosalloy", 4.0F, 10.0F, 16.0F, 40.0F);
    }

    private static void sampleRanges(MetalFamily family, String tag, float wantMin, float wantMax,
                                     float wantSetMin, float wantSetMax) {
        Item[] pieces = {family.helmet.get(), family.chestplate.get(), family.leggings.get(), family.boots.get()};
        MetalFamily.Form[] forms = {MetalFamily.Form.HELMET, MetalFamily.Form.CHESTPLATE,
                MetalFamily.Form.LEGGINGS, MetalFamily.Form.BOOTS};
        float[] mins = new float[4];
        float[] maxs = new float[4];
        float setMin = Float.MAX_VALUE;
        float setMax = -Float.MAX_VALUE;
        for (int i = 0; i < 4; i++) {
            mins[i] = Float.MAX_VALUE;
            maxs[i] = -Float.MAX_VALUE;
        }
        ItemStack[] stacks = new ItemStack[4];
        for (int i = 0; i < 4; i++) {
            stacks[i] = new ItemStack(pieces[i]);
        }
        for (int it = 0; it < 4000; it++) {
            float sum = 0.0F;
            boolean all = true;
            for (int i = 0; i < 4; i++) {
                ChaosRange.reroll(stacks[i], ChaosRange.Channel.ARMOR, level.getRandom());
                Float v = ChaosRange.current(stacks[i], family, forms[i], ChaosRange.Channel.ARMOR);
                if (v == null) {
                    all = false;
                    continue;
                }
                mins[i] = Math.min(mins[i], v);
                maxs[i] = Math.max(maxs[i], v);
                sum += v;
            }
            if (all) {
                setMin = Math.min(setMin, sum);
                setMax = Math.max(setMax, sum);
            }
        }
        boolean perPiece = true;
        for (int i = 0; i < 4; i++) {
            if (Math.abs(mins[i] - wantMin) > 0.001F || Math.abs(maxs[i] - wantMax) > 0.001F) {
                perPiece = false;
            }
        }
        LOG.info("{} readout r3_{} perPiece={} set={} .. {}", TAG, tag,
                String.format("[%.3f..%.3f]", mins[0], maxs[0]),
                String.format("%.3f", setMin), String.format("%.3f", setMax));
        LOG.info("{} readout r3_{}_pieces helm={} chest={} legs={} boots={}", TAG, tag,
                fmt(mins[0], maxs[0]), fmt(mins[1], maxs[1]), fmt(mins[2], maxs[2]), fmt(mins[3], maxs[3]));
        check("r3_" + tag + "_per_piece", perPiece,
                "each piece in [" + wantMin + ".." + wantMax + "]: helm=" + fmt(mins[0], maxs[0])
                        + " chest=" + fmt(mins[1], maxs[1]) + " legs=" + fmt(mins[2], maxs[2])
                        + " boots=" + fmt(mins[3], maxs[3]));
        check("r3_" + tag + "_full_set",
                setMin >= wantSetMin - 0.001F && setMax <= wantSetMax + 0.001F
                        && setMin <= wantSetMin + 2.0F && setMax >= wantSetMax - 2.0F,
                "full set observed [" + setMin + ".." + setMax + "] expected [" + wantSetMin + ".."
                        + wantSetMax + "] (bounds strictly inside; ends within 2.0 by sampling)");
    }

    private static String fmt(float a, float b) {
        return String.format("%.3f..%.3f", a, b);
    }

    // ==================== R2：甜浆果丛 ====================

    private static void runR2() {
        var bush = level.getBlockState(BUSH);
        for (int n = 0; n <= 4; n++) {
            wear(berryMan, AllMetals.THORNSGOLD, n);
            berryMan.setHealth(20.0F);
            clearInvuln(berryMan);
            berryMan.invulnerableTime = 0;
            berryMan.xOld = berryMan.getX() - 0.1D;      // entityInside 的移动判定门槛
            berryMan.zOld = berryMan.getZ();
            berryBefore = -1.0F;
            berryAfter = -1.0F;
            // 真方块的真判定：Entity#checkInsideBlocks 里就是这一句
            bush.entityInside(level, BUSH, berryMan);
            float want = 1.0F - 0.25F * n;
            float ratio = berryBefore > 0.0F ? berryAfter / berryBefore : -1.0F;
            LOG.info("{} readout r2_pieces_{} before={} after={} ratio={} want={}", TAG, n,
                    berryBefore, berryAfter, ratio, want);
            check("r2_pieces_" + n + "_damage_ratio",
                    berryBefore > 0.0F && Math.abs(ratio - want) < 1.0E-5F,
                    "n=" + n + " before=" + berryBefore + " after=" + berryAfter
                            + " ratio=" + ratio + " want=" + want);
            if (n == 4) {
                check("r2_pieces_4_zero", berryAfter == 0.0F, "after=" + berryAfter);
            }
        }
        wear(berryMan, AllMetals.THORNSGOLD, 0);
    }

    // ==================== R6：音波击退 ====================

    private static final double[] sonicHoriz = new double[5];

    private static void runR6() throws Exception {
        Class<?> boomClass = Class.forName("net.minecraft.world.entity.ai.behavior.warden.SonicBoom");
        Object boom = boomClass.getConstructor().newInstance();
        Method tickMethod = boomClass.getDeclaredMethod("tick", ServerLevel.class, Warden.class, long.class);
        tickMethod.setAccessible(true);
        for (int n = 0; n <= 4; n++) {
            wear(sonicMan, AllMetals.ECHOGOLD, n);
            sonicMan.setHealth(20.0F);
            clearInvuln(sonicMan);
            sonicMan.invulnerableTime = 0;
            sonicMan.setDeltaMovement(Vec3.ZERO);
            // 真 Warden 的 brain 记忆：有目标、没有冷却
            warden.getBrain().setMemory(MemoryModuleType.ATTACK_TARGET, sonicMan);
            warden.getBrain().eraseMemory(MemoryModuleType.SONIC_BOOM_COOLDOWN);
            warden.getBrain().eraseMemory(MemoryModuleType.SONIC_BOOM_SOUND_COOLDOWN);
            warden.getBrain().eraseMemory(MemoryModuleType.SONIC_BOOM_SOUND_DELAY);
            warden.getLookControl().setLookAt(sonicMan);
            double hpBefore = sonicMan.getHealth();
            tickMethod.invoke(boom, level, warden, level.getGameTime());
            Vec3 d = sonicMan.getDeltaMovement();
            sonicHoriz[n] = Math.sqrt(d.x * d.x + d.z * d.z);
            LOG.info("{} readout r6_pieces_{} hp={} -> {} delta=({},{},{}) horiz={}", TAG, n,
                    hpBefore, sonicMan.getHealth(),
                    String.format("%.4f", d.x), String.format("%.4f", d.y), String.format("%.4f", d.z),
                    String.format("%.6f", sonicHoriz[n]));
            if (n > 0) {
                double want = 1.0D - 0.25D * n;
                double ratio = sonicHoriz[0] > 0.0D ? sonicHoriz[n] / sonicHoriz[0] : -1.0D;
                check("r6_pieces_" + n + "_knockback_ratio", Math.abs(ratio - want) < 0.005D,
                        "n=" + n + " horiz=" + sonicHoriz[n] + " base=" + sonicHoriz[0]
                                + " ratio=" + ratio + " want=" + want);
            }
        }
        check("r6_base_nonzero", sonicHoriz[0] > 0.01D, "base_horiz=" + sonicHoriz[0]);
        check("r6_pieces_4_zero", sonicHoriz[4] < 1.0E-4D, "n=4 horiz=" + sonicHoriz[4]);
        wear(sonicMan, AllMetals.ECHOGOLD, 0);
    }

    private static ResourceLocation SONIC_ID() {
        return ResourceLocation.fromNamespaceAndPath("bettergold", "sonic_boom_knockback");
    }

    // ==================== R7-a：金工细作不许被 doubled 变体误触发 ====================

    private static final String CRAFT_ADV = "bettergold:metal/chaosgold/craft";

    private static void runR7() {
        BlockPos pos = new BlockPos(BASE.getX() + 2, BASE.getY() + 40, BASE.getZ() + 2);
        level.setBlockAndUpdate(pos.below(), Blocks.STONE.defaultBlockState());
        ServerPlayer p1 = player(level.getServer(), "bg19_r7a");
        p1.moveTo(pos.getX() + 0.5D, pos.getY(), pos.getZ() + 0.5D, 0.0F, 0.0F);
        level.addNewPlayer(p1);
        ServerPlayer p2 = player(level.getServer(), "bg19_r7b");
        p2.moveTo(pos.getX() + 1.5D, pos.getY(), pos.getZ() + 0.5D, 0.0F, 0.0F);
        level.addNewPlayer(p2);

        // ① 只有高精度油、**没有混沌金块** ⇒ 不该弹成就
        String[] doubled = {
                "bettergold:mixed_crystal_pile", "bettergold:mixed_crystal_pile",
                "minecraft:redstone", "minecraft:redstone",
                "minecraft:gold_block", "minecraft:gold_block",
                "minecraft:netherite_ingot", "bettergold:refined_alchemic_oil",
                "bettergold:blazing_rod"};
        boolean ok1 = craft(pos, p1, doubled, "bettergold:raw_flamegold", 2, "r7_doubled_result");
        check("r7_doubled_no_advancement", ok1 && !hasCraftAdv(p1),
                "crafted=" + ok1 + " advancement_done=" + hasCraftAdv(p1) + " (must be false)");

        // ② 含混沌金块 ⇒ 必须弹成就（同一个玩家，前置已满足）
        String[] chaos = {
                "bettergold:mixed_crystal_pile", "minecraft:redstone",
                "minecraft:netherite_scrap", "minecraft:netherite_scrap",
                "minecraft:gold_ingot", "minecraft:gold_ingot",
                "bettergold:chaosgold_block", "bettergold:refined_alchemic_oil",
                "bettergold:blazing_rod"};
        boolean ok2 = craft(pos, p1, chaos, "bettergold:raw_flamegold", 2, "r7_chaosgold_result");
        check("r7_chaosgold_advancement", ok2 && hasCraftAdv(p1),
                "crafted=" + ok2 + " advancement_done=" + hasCraftAdv(p1) + " (must be true)");

        // ③ 偷梁换柱那条（无形状铜块 + 混沌金币）⇒ 必须弹成就（换一个干净玩家）
        String[] copper = {
                "minecraft:copper_ingot", "minecraft:copper_ingot", "minecraft:copper_ingot",
                "minecraft:copper_ingot", "bettergold:chaos_coin", null, null, null, null};
        boolean ok3 = craft(pos, p2, copper, "minecraft:copper_block", 1, "r7_copper_result");
        check("r7_copper_advancement", ok3 && hasCraftAdv(p2),
                "crafted=" + ok3 + " advancement_done=" + hasCraftAdv(p2) + " (must be true)");
    }

    private static boolean hasCraftAdv(ServerPlayer player) {
        var holder = level.getServer().getAdvancements()
                .get(ResourceLocation.parse(CRAFT_ADV));
        return holder != null && player.getAdvancements().getOrStartProgress(holder).isDone();
    }

    /** 真 {@link net.minecraft.world.inventory.CraftingMenu} + 真玩家点击（与 bg18b 同一套路径）。 */
    private static boolean craft(BlockPos pos, ServerPlayer crafter, String[] grid, String wantId,
                                 int wantCount, String tag) {
        crafter.getInventory().clearContent();
        net.minecraft.world.inventory.CraftingMenu menu =
                new net.minecraft.world.inventory.CraftingMenu(
                        0, crafter.getInventory(),
                        net.minecraft.world.inventory.ContainerLevelAccess.create(level, pos));
        crafter.containerMenu = menu;
        for (int i = 0; i < 9; i++) {
            ItemStack stack = grid[i] == null ? ItemStack.EMPTY
                    : new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM
                            .get(ResourceLocation.parse(grid[i])));
            menu.getSlot(1 + i).set(stack);
        }
        menu.slotsChanged(menu.getSlot(1).container);
        ItemStack result = menu.getSlot(0).getItem().copy();
        boolean match = !result.isEmpty()
                && wantId.equals(String.valueOf(net.minecraft.core.registries.BuiltInRegistries.ITEM
                        .getKey(result.getItem())))
                && result.getCount() == wantCount;
        check(tag, match, "result=" + (result.isEmpty() ? "<empty>"
                : result.getCount() + "x " + result.getItem()) + " want " + wantCount + "x " + wantId);
        if (result.isEmpty()) {
            return false;
        }
        int free = -1;
        for (int i = 10; i <= 45; i++) {
            if (menu.getSlot(i).getItem().isEmpty()) {
                free = i;
                break;
            }
        }
        menu.clicked(0, 0, net.minecraft.world.inventory.ClickType.PICKUP, crafter);
        if (free > 0) {
            menu.clicked(free, 0, net.minecraft.world.inventory.ClickType.PICKUP, crafter);
        }
        return true;
    }

    // ==================== 小工具 ====================

    /** 给实体穿 n 件该族盔甲（头 / 胸 / 腿 / 靴 依次），其余槽位清空。 */
    private static void wear(LivingEntity entity, MetalFamily family, int n) {
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
        Item[] pieces = {family.helmet.get(), family.chestplate.get(), family.leggings.get(), family.boots.get()};
        for (int i = 0; i < 4; i++) {
            entity.setItemSlot(slots[i], i < n ? new ItemStack(pieces[i]) : ItemStack.EMPTY);
        }
    }

    /** 关掉 ServerPlayer 的出生无敌（否则 hurt 恒 false ⇒ 甜浆果丛 / 音波都测不出东西）。 */
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

    private static ServerPlayer player(MinecraftServer server, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(("bg19:" + name).getBytes(StandardCharsets.UTF_8)), name);
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

    private static void finish(MinecraftServer server) {
        if (done) {
            return;
        }
        done = true;
        try {
            for (int cx : FORCED_X) {
                level.setChunkForced(cx, BASE.getZ() >> 4, false);
            }
        } catch (Throwable t) {
            LOG.warn("{} unforce threw {}", TAG, String.valueOf(t));
        }
        int forced = level == null ? -1 : level.getForcedChunks().size();
        LOG.info("{} forcedNow={}", TAG, forced);
        check("forceload_zero", forced == 0, "forcedNow=" + forced);
        LOG.info("{} SUMMARY pass={} fail={} forcedNow={}", TAG, passes, fails, forced);
        server.halt(false);
    }
}
