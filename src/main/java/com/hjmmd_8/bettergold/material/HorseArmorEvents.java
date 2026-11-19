package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.config.Config;
import com.hjmmd_8.bettergold.registry.AllEffects;

import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.horse.AbstractHorse;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * <b>1.8 §H 马铠的运行时效果（第 33–35 条）。</b>
 *
 * <p>马只穿一件（没有"每件 / 全套"）⇒ 所有判据都是"这一件"，与玩家盔甲那套
 * {@code wornPieces} 无关。挂在 {@link EntityTickEvent.Post} 上而不是全局扫描：
 * 只有马会走这里，其余实体第一句早退。</p>
 *
 * <h2>三种"每 20 tick 一次"</h2>
 * <ul>
 *   <li><b>10 贵金属</b>：以马为中心 3×3×3 内的<b>敌对生物</b>挂并叠该族专属状态
 *       （雷族挂的是<b>颤栗</b>，不是落雷 —— 状态表见 {@link #applyPreciousStatus}）；</li>
 *   <li><b>幻惑金</b>（例外）：3×3×3 内的<b>玩家 / 友善生物 / 马自己</b>换成
 *       <b>不可叠加的 6 秒生命恢复 I</b>（等级恒 0，重复施加只刷新时长）；</li>
 *   <li><b>万坚金</b>（例外）：每 <b>16 秒 +1 颗黄心</b>（2 点吸收），上限 <b>10 颗</b>（20 点）。</li>
 * </ul>
 *
 * <h2>伤害面</h2>
 * <ul>
 *   <li><b>免疫特定伤害</b>（逐族映射见 {@link #immune}）：9 族有对应伤害类型；万坚 / 幻惑<b>不免疫</b>；</li>
 *   <li><b>混沌金 / 崩乱合金</b>：区间减伤（0–16% / 16–40%，与玩家盔甲共用 {@link ChaosRange} 组件）；</li>
 *   <li><b>崩乱合金</b>：受到攻击时按器具概率（{@code Config.weaponBuffChance("chaosalloy")}，默认 0.5）
 *       对攻击者挂<b>双失衡</b>（力量 + 抗性各一个）；</li>
 *   <li><b>幻惑金</b>：仍 16% 概率对攻击者挂 1 秒安抚（与玩家盔甲同一条 {@code applySoothe}）。</li>
 * </ul>
 *
 * <p>⚠ 「对带风斩的目标每次 −1 tick」：3×3×3 每次施加时，若目标身上已有
 * {@code bettergold:wind_slash}，本次时长 <b>−1 tick</b>（作者 §H-33 的字面值；
 * 与风斩"无上限叠加"不冲突 —— 等级照叠，只是这一次的时长少 1 tick）。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID)
public final class HorseArmorEvents {

    /** 3×3×3 的状态施加周期（作者 §H-33：每 20 tick 一次） */
    public static final int STATUS_INTERVAL = 20;
    /** 万坚金：每 16 秒 +1 颗黄心 */
    public static final int STURDY_HEART_INTERVAL = 16 * 20;
    /** 万坚金黄心上限：10 颗 = 20 点吸收 */
    public static final float STURDY_HEART_CAP = 10.0F * 2.0F;
    /** 一颗黄心 = 2 点吸收 */
    public static final float STURDY_HEART_PER_GRANT = 2.0F;
    /** 凛冰金马铠自带的冰霜行者规格等级（§H-34：4 级，不是附魔） */
    public static final int FROST_WALKER_SPEC_LEVEL = 4;
    /** 幻惑金马铠给友善方的生命恢复时长（6 秒，等级恒 0 = 不可叠加） */
    public static final int ILLUSION_REGEN_TICKS = 6 * 20;
    /** 幻惑金马铠对攻击者的安抚概率（§H-34：仍 16%） */
    public static final float ILLUSION_SOOTHE_CHANCE = 0.16F;

    /** 万坚金马铠吸收上限的属性修饰符 id（一个实体只有一个，与玩家盔甲同构） */
    private static final net.minecraft.resources.ResourceLocation STURDY_ABSORPTION_CAP_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(bettergold.MODID,
                    "horse_armor_absorption_cap");

    private HorseArmorEvents() {
    }

    /** 这一匹马穿的马铠属于哪一族（没穿 / 不是本模组 / 未解析 ⇒ null） */
    public static MetalFamily armorFamily(AbstractHorse horse) {
        if (!horse.isWearingBodyArmor()) {
            return null;
        }
        ItemStack stack = horse.getBodyArmorItem();
        return MetalHorseArmor.familyOf(stack);
    }

    @SubscribeEvent
    public static void onEntityTick(EntityTickEvent.Post event) {
        if (!(event.getEntity() instanceof AbstractHorse horse)) {
            return;
        }
        if (horse.level().isClientSide()) {
            return;
        }
        MetalFamily family = armorFamily(horse);
        if (family == null) {
            return;
        }
        // ---------- 每 20 tick：3×3×3 状态 ----------
        if (horse.tickCount % STATUS_INTERVAL == 0) {
            if (family == AllMetals.ILLUSIONGOLD) {
                illusionField(horse);
            } else if (family != AllMetals.STURDYGOLD) {
                applyPreciousStatus(horse, family);
            }
        }
        // ---------- 万坚金：每 16 秒 +1 颗黄心（上限 10） ----------
        if (family == AllMetals.STURDYGOLD && horse.tickCount % STURDY_HEART_INTERVAL == 0) {
            sturdyHeart(horse);
        }
        // ---------- 凛冰金：自带 4 级冰霜行者规格 ----------
        if (family == AllMetals.FROSTGOLD && horse.onGround()) {
            MetalEvents.freezeAround(horse, FROST_WALKER_SPEC_LEVEL);
        }
    }

    /** 以马为中心 3×3×3 的 AABB（方块中心，含马自己） */
    private static net.minecraft.world.phys.AABB cube(AbstractHorse horse) {
        var center = horse.blockPosition();
        return new net.minecraft.world.phys.AABB(
                center.getX() - 0.5D, center.getY() - 0.5D, center.getZ() - 0.5D,
                center.getX() + 1.5D, center.getY() + 1.5D, center.getZ() + 1.5D);
    }

    /**
     * 10 贵金属的专属状态（与 {@link MetalEvents#applyFamilyWeaponEffect} 的<b>状态段</b>同表；
     * 唯一差别：结雷金挂的是<b>颤栗</b>而不是落雷 —— 马铠每 20 tick 落一次雷显然不是作者要的）。
     */
    private static void applyPreciousStatus(AbstractHorse horse, MetalFamily family) {
        var targets = horse.level().getEntitiesOfClass(LivingEntity.class, cube(horse),
                entity -> entity instanceof Enemy && entity.isAlive() && entity != horse);
        for (LivingEntity target : targets) {
            int ticks = statusTicks(family);
            // §H-33 最后一句：对带风斩的目标每次 −1 tick
            if (target.hasEffect(AllEffects.WIND_SLASH)) {
                ticks = Math.max(1, ticks - 1);
            }
            applyOne(family, horse, target, ticks);
        }
    }

    private static int statusTicks(MetalFamily family) {
        if (family == AllMetals.ECHOGOLD) {
            return MetalFamily.ECHO_ROAR_TICKS;
        }
        if (family == AllMetals.VOODOOGOLD) {
            return MetalEvents.VOODOO_TICKS;
        }
        return MetalFamily.HIGH_BURN_TICKS;
    }

    private static void applyOne(MetalFamily family, AbstractHorse horse, LivingEntity target, int ticks) {
        if (family == AllMetals.FLAMEGOLD) {
            MetalEvents.stackEffect(target, AllEffects.HIGH_BURN, ticks);
        } else if (family == AllMetals.VOODOOGOLD) {
            MetalEvents.stackVoodoo(target, horse);
        } else if (family == AllMetals.THUNDERGOLD) {
            MetalEvents.stackEffect(target, AllEffects.TREMBLE, ticks);
        } else if (family == AllMetals.INDIGOSEAGOLD) {
            MetalEvents.stackEffect(target, AllEffects.SEDIMENT, ticks);
        } else if (family == AllMetals.THORNSGOLD) {
            MetalEvents.stackEffect(target, AllEffects.PARASITE, ticks);
            MetalEvents.markParasiteSource(target, horse);
        } else if (family == AllMetals.ECHOGOLD) {
            MetalEvents.stackEffect(target, AllEffects.ECHO_ROAR, ticks);
            MetalEvents.markEchoRoarSource(target, horse);
        } else if (family == AllMetals.WINDGOLD) {
            MetalEvents.stackEffect(target, AllEffects.WIND_SLASH, ticks);
        } else if (family == AllMetals.FROSTGOLD) {
            MetalEvents.stackEffect(target, AllEffects.FROST_SEEP, ticks);
        }
        // 万坚金 / 幻惑金 / 混沌金 / 崩乱合金：不在状态表里（各有自己的例外机制）
    }

    /**
     * 幻惑金马铠：3×3×3 内的玩家 / 友善生物 / 马自己 ⇒ <b>不可叠加的 6 秒生命恢复 I</b>。
     *
     * <p>"不可叠加"的落地：等级恒为 0（原版只在 {@code amplifier > 0} 时显示等级），
     * 重复施加只刷新时长，不会变成 II / III。</p>
     */
    private static void illusionField(AbstractHorse horse) {
        var targets = horse.level().getEntitiesOfClass(LivingEntity.class, cube(horse),
                entity -> entity.isAlive() && !(entity instanceof Enemy));
        for (LivingEntity target : targets) {
            target.addEffect(new MobEffectInstance(MobEffects.REGENERATION, ILLUSION_REGEN_TICKS, 0,
                    false, true, true));
        }
    }

    /** 万坚金马铠：每 16 秒 +1 颗黄心，上限 10 颗 */
    private static void sturdyHeart(AbstractHorse horse) {
        // ⚠ 原版 `setAbsorptionAmount` 会被 `MAX_ABSORPTION` 属性夹住（默认 0）——
        //   与玩家盔甲那条（MetalEvents#onAbsorptionTick）同一条坑：必须自己挂上限修饰符，
        //   否则 `setAbsorptionAmount(2)` 静默写成 0。
        var max = horse.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_ABSORPTION);
        if (max != null) {
            max.removeModifier(STURDY_ABSORPTION_CAP_ID);
            max.addOrUpdateTransientModifier(
                    new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                            STURDY_ABSORPTION_CAP_ID, STURDY_HEART_CAP,
                            net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE));
        }
        float current = horse.getAbsorptionAmount();
        if (current < STURDY_HEART_CAP) {
            horse.setAbsorptionAmount(Math.min(STURDY_HEART_CAP, current + STURDY_HEART_PER_GRANT));
        }
    }

    // ==================== 伤害面 ====================

    @SubscribeEvent
    public static void onDamagePre(LivingDamageEvent.Pre event) {
        if (!(event.getEntity() instanceof AbstractHorse horse) || horse.level().isClientSide()) {
            return;
        }
        MetalFamily family = armorFamily(horse);
        if (family == null) {
            return;
        }
        DamageSource source = event.getSource();
        // ---------- 免疫特定伤害（逐族映射；万坚 / 幻惑不免疫） ----------
        if (immune(family, source)) {
            event.setNewDamage(0.0F);
            return;
        }
        // ---------- 混沌金 / 崩乱合金：区间减伤 ----------
        ChaosRange.Range range = MetalHorseArmor.reductionOf(family);
        if (range != null) {
            ItemStack stack = horse.getBodyArmorItem();
            float percent = ChaosRange.current(stack, ChaosRange.Channel.ARMOR, range);
            event.setNewDamage(event.getNewDamage() * (1.0F - percent / 100.0F));
            // 触发点 = 受到伤害（与玩家盔甲同构：先用当前值结算，再重掷）
            ChaosRange.reroll(stack, ChaosRange.Channel.ARMOR, range, horse.getRandom());
        }
    }

    /**
     * 「免疫特定伤害」的逐族映射（父代理 2026-11-19 批准的工作值 = 沿用各族既有抗性判据）。
     *
     * <p>⚠ 万坚金 / 幻惑金<b>不在这张表里</b>（它们没有对应的既有抗性；万坚只保留黄心、
     * 幻惑只保留安抚/恢复）。混沌 / 崩乱走减伤区间，也不在表里。</p>
     */
    public static boolean immune(MetalFamily family, DamageSource source) {
        if (family == AllMetals.FLAMEGOLD) {
            return MetalEvents.isFire(source);
        }
        if (family == AllMetals.VOODOOGOLD) {
            return MetalEvents.isMagic(source);
        }
        if (family == AllMetals.THUNDERGOLD) {
            return source.is(DamageTypes.LIGHTNING_BOLT);
        }
        if (family == AllMetals.INDIGOSEAGOLD) {
            return MetalEvents.isSuffocation(source);
        }
        if (family == AllMetals.THORNSGOLD) {
            return MetalEvents.isCactus(source) || MetalEvents.isSweetBerryBush(source);
        }
        if (family == AllMetals.ECHOGOLD) {
            return MetalEvents.isSonicBoom(source);
        }
        if (family == AllMetals.WINDGOLD) {
            return MetalEvents.isWindCharge(source);
        }
        if (family == AllMetals.FROSTGOLD) {
            return MetalEvents.isFreeze(source);
        }
        return false;
    }

    @SubscribeEvent
    public static void onDamagePost(LivingDamageEvent.Post event) {
        if (!(event.getEntity() instanceof AbstractHorse horse) || horse.level().isClientSide()) {
            return;
        }
        if (!(event.getSource().getEntity() instanceof LivingEntity attacker) || attacker == horse) {
            return;
        }
        MetalFamily family = armorFamily(horse);
        if (family == null) {
            return;
        }
        if (family == AllMetals.ILLUSIONGOLD) {
            // §H-34：仍 16% 概率对攻击者挂 1 秒安抚
            if (horse.getRandom().nextFloat() < ILLUSION_SOOTHE_CHANCE) {
                MetalEvents.applySoothe(attacker, MetalFamily.SOOTHE_TICKS);
            }
        } else if (family == AllMetals.CHAOSALLOY) {
            // §H-35：「同样对攻击者挂双失衡（概率同器具）」⇒ 概率闸门 = 器具那条配置（默认 0.5）
            float chance = Config.weaponBuffChance(AllMetals.CHAOSALLOY.id);
            if (chance > 0.0F && horse.getRandom().nextFloat() < chance) {
                ImbalanceEffects.apply(attacker, AllEffects.POWER_IMBALANCE.getDelegate());
                ImbalanceEffects.apply(attacker, AllEffects.RESISTANCE_IMBALANCE.getDelegate());
            }
        }
    }

    /** 供 A 级探针直接驱动"每 20 tick"那一段（生产路径不调用） */
    public static void tickStatusForProbe(AbstractHorse horse, MetalFamily family) {
        if (family == AllMetals.ILLUSIONGOLD) {
            illusionField(horse);
        } else {
            applyPreciousStatus(horse, family);
        }
    }

    /** 供 A 级探针读取"这次施加会持续多久" */
    static int statusTicksForProbe(MetalFamily family) {
        return statusTicks(family);
    }

    /** 供 A 级探针检查"马是不是被当成穿戴者" */
    static boolean wearsArmor(Mob mob) {
        return mob.isWearingBodyArmor() && MetalHorseArmor.familyOf(mob.getBodyArmorItem()) != null;
    }
}
