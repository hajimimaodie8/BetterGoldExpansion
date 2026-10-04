package com.hjmmd_8.bettergold.registry;

import java.util.function.BiConsumer;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 模组自定义状态效果。
 *
 * <ul>
 *   <li>抗寒性（cold_resistance）：免疫冰冻伤害，规避逻辑在伤害事件里。</li>
 *   <li>高燃（high_burn）：目标持续燃烧，等级每 +1 点燃烧伤害 +1 点，可无限叠加（新约 1.4 烈燃金）。</li>
 *   <li>巫毒（voodoo）：被对应器具攻击会叠加等级；窗口内目标受到的伤害按配置比例提取，
 *       效果<b>自然到期</b>时按 {@code 提取值 + 每级固定伤害 × 等级}
 *       （默认 = {@code 窗口内伤害总量 × 36% + buff 等级}）造成魔法伤害
 *       （提取与结算都在 {@code MetalEvents} + {@code material.VoodooAccumulator}）。</li>
 *   <li>颤栗（tremble）：每级 −1 点伤害、−0.1 攻速（新约 1.4 结雷金）。</li>
 *   <li>沉淀（sediment）：持续窒息伤害（等级 + 1 点 / 秒，伤害类型 {@code in_wall}）+ 每级 −1% 移速
 *       （{@code ADD_MULTIPLIED_TOTAL}）（新约 1.5 靛海金）。</li>
 *   <li>安抚（soothe）：目标暂时失去 AI；原始 NoAI / 目标由 {@code material.SootheState} 保存并还原，
 *       不叠加、时长取 max（新约 1.5 幻惑金）。</li>
 * </ul>
 */
public class AllEffects {

    public static final DeferredRegister<MobEffect> EFFECTS =
            DeferredRegister.create(Registries.MOB_EFFECT, bettergold.MODID);

    /** 抗寒性：免疫冰冻伤害 */
    public static final DeferredHolder<MobEffect, MobEffect> COLD_RESISTANCE =
            EFFECTS.register("cold_resistance", () -> new MobEffect(MobEffectCategory.BENEFICIAL, 0x55C8E8) {
                @Override
                public boolean applyEffectTick(LivingEntity entity, int amplifier) {
                    // 实际免伤在伤害事件里判断，这里不需要每 tick 逻辑
                    return true;
                }

                @Override
                public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
                    return duration % 20 == 0;
                }
            });

    /**
     * 高燃：持续燃烧。
     * 每秒直接结算 (amplifier + 2) 点火焰伤害（1 级 2 点、2 级 3 点，与规格一致），
     * 并维持 1 秒燃烧状态做视觉表现。
     * 注：实测「维持燃烧状态 + 我们自己结算」不会产生额外的原版燃烧伤害（hurt 会清掉燃烧计时），
     * 所以由本效果一次性结算全部伤害，数值可控。
     */
    public static final DeferredHolder<MobEffect, MobEffect> HIGH_BURN =
            EFFECTS.register("high_burn", () -> new MobEffect(MobEffectCategory.HARMFUL, 0xFF7A18) {
                @Override
                public boolean applyEffectTick(LivingEntity entity, int amplifier) {
                    if (entity.level() instanceof net.minecraft.server.level.ServerLevel serverLevel) {
                        entity.hurt(serverLevel.damageSources().onFire(), amplifier + 2);
                        entity.setRemainingFireTicks(20);
                    }
                    return true;
                }

                @Override
                public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
                    return duration % 20 == 0;
                }
            });

    /**
     * 巫毒：层数叠加；窗口内受到的伤害按比例累积，自然到期时一次性结算
     * （累积在 {@code VoodooAccumulator}，结算在 {@code MetalEvents#onVoodooExpired}）。
     */
    public static final DeferredHolder<MobEffect, MobEffect> VOODOO =
            EFFECTS.register("voodoo", () -> new MobEffect(MobEffectCategory.HARMFUL, 0x7B3FA0) {
                // 纯标记型效果：不掉血、不加属性，只在结束时按累积伤害结算
            });

    /**
     * 颤栗：每级 −1 伤害、−0.1 攻速。
     * 属性必须走 addAttributeModifier 注册进效果自身的模板表（覆写 createModifiers 只影响展示，
     * 不会作用到实体上 —— 这一点是实测踩出来的）。
     */
    public static final DeferredHolder<MobEffect, MobEffect> TREMBLE =
            EFFECTS.register("tremble", () -> new MobEffect(MobEffectCategory.HARMFUL, 0x9B59F6) {
                {
                    this.addAttributeModifier(Attributes.ATTACK_DAMAGE,
                            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "tremble_damage"),
                            AttributeModifier.Operation.ADD_VALUE,
                            amplifier -> -1.0D * (amplifier + 1));
                    this.addAttributeModifier(Attributes.ATTACK_SPEED,
                            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "tremble_speed"),
                            AttributeModifier.Operation.ADD_VALUE,
                            amplifier -> -0.1D * (amplifier + 1));
                }
            });

    /**
     * 沉淀（sediment，1.5 靛海金）：「持续受窒息伤害 + 每级降 1% 移动速度」。
     *
     * <ul>
     *   <li><b>伤害 = 等级 + 1</b>（1 级 2 点、2 级 3 点）。代码口径与 1.4 的
     *       {@link #HIGH_BURN 高燃} 逐字同构：每秒（{@code duration % 20 == 0}）结算
     *       {@code amplifier + 2} 点 —— {@code amplifier + 1} 是「等级」，再加 1 就是「等级 + 1」。</li>
     *   <li>伤害类型用 <b>{@code minecraft:in_wall}</b>（方块内窒息），与规格第七节第 3 条一致：
     *       {@code drown} 带 {@code DamageEffects.DROWNING}（会附溺水表现），{@code in_wall} 无附加效果，
     *       作持续掉血更干净；靛海金盔甲的「窒息 / 溺水抗性」正好覆盖它（第七节第 7 条：覆盖）。</li>
     *   <li>移速：<b>每级 1%</b>，必须用 {@link AttributeModifier.Operation#ADD_MULTIPLIED_TOTAL}
     *       （{@code -0.01 × (amplifier + 1)}）。玩家基础移速是 0.1，用 {@code ADD_VALUE} 加 −0.01
     *       实际是 −10%，差一个数量级。</li>
     *   <li>无等级上限：靛海金器具每次命中 +1 级（上限只受效果等级上限 255 限制）。</li>
     * </ul>
     */
    public static final DeferredHolder<MobEffect, MobEffect> SEDIMENT =
            EFFECTS.register("sediment", () -> new MobEffect(MobEffectCategory.HARMFUL, 0x4B0082) {
                {
                    this.addAttributeModifier(Attributes.MOVEMENT_SPEED,
                            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "sediment_speed"),
                            AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL,
                            amplifier -> -0.01D * (amplifier + 1));
                }

                @Override
                public boolean applyEffectTick(LivingEntity entity, int amplifier) {
                    if (entity.level() instanceof net.minecraft.server.level.ServerLevel serverLevel) {
                        entity.hurt(serverLevel.damageSources().inWall(), amplifier + 2);
                    }
                    return true;
                }

                @Override
                public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
                    return duration % 20 == 0;
                }
            });

    /**
     * 安抚（soothe，1.5 幻惑金）：目标<b>暂时失去 AI</b>，无法做出任何行动。
     *
     * <p>实现是 {@code Mob#setNoAi(true)} + {@code setTarget(null)}；<b>原始的 NoAI 与目标</b>由
     * {@link com.hjmmd_8.bettergold.material.SootheState} 保存，并在
     * 到期 / 提前移除 / 目标死亡 / 实体离开世界 / 读档时<b>还原</b> ——
     * 不还原就会把生物永久变傻（这是本效果唯一容易搞砸的地方，见那个类的注释）。</p>
     *
     * <p>重复施加<b>不叠加</b>：时长取 {@code max(剩余, 20)}（施加方在
     * {@code MetalEvents#applySoothe} 里算好再交过来），所以 1 秒安抚不会被无限续成永久控制。</p>
     *
     * <p>状态的登记在 {@link #onEffectStarted}：{@code LivingEntity#addEffect} 在「新挂上」与
     * 「升级/续时」两条路径的末尾都会调用它，而 {@code SootheState.begin} 对「已经在安抚中」的实体
     * 只保证 AI 仍是关的、<b>不覆盖</b>已保存的原始状态。</p>
     */
    public static final DeferredHolder<MobEffect, MobEffect> SOOTHE =
            EFFECTS.register("soothe", () -> new MobEffect(MobEffectCategory.HARMFUL, 0xC8A2E8) {
                @Override
                public void onEffectStarted(LivingEntity entity, int amplifier) {
                    com.hjmmd_8.bettergold.material.SootheState.begin(entity);
                }
            });

    /**
     * 寄生（parasite，1.6 树棘金）：目标持续受到「仙人掌同款」伤害。
     *
     * <ul>
     *   <li><b>伤害 = 等级</b>（1 级 1 点、2 级 2 点、3 级 3 点），类型 {@code minecraft:cactus}；
     *       每秒结算一次（{@code duration % 20 == 0}，与高燃 / 沉淀同节奏）。</li>
     *   <li>每次结算 <b>36% 概率</b>给<b>施加者</b>回「等级」点血（概率不随等级变；
     *       施加者 UUID 记在目标的持久数据里，见 {@code MetalEvents#markParasiteSource}）。</li>
     *   <li>叠加 = <b>提升等级、无上限</b>（{@code stackEffect} 每次命中 +1 级）。
     *       时长 16 秒（{@code MetalFamily.PARASITE_TICKS}，与沉淀同口径）。</li>
     * </ul>
     *
     * <p>结算逻辑写在 {@code MetalEvents#parasiteTick} —— 效果类只做"每秒调一次"的派发，
     * 与 {@link #HIGH_BURN} / {@link #SEDIMENT} 的分工一致。</p>
     */
    public static final DeferredHolder<MobEffect, MobEffect> PARASITE =
            EFFECTS.register("parasite", () -> new MobEffect(MobEffectCategory.HARMFUL, 0x5E8C31) {
                @Override
                public boolean applyEffectTick(LivingEntity entity, int amplifier) {
                    com.hjmmd_8.bettergold.material.MetalEvents.parasiteTick(entity, amplifier);
                    return true;
                }

                @Override
                public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
                    return duration % 20 == 0;
                }
            });

    /**
     * 幽咆（echo_roar，1.6 幽咆金）：目标中心爆发监守者声波。
     *
     * <ul>
     *   <li>每秒（{@code duration % 20 == 0}）以<b>目标所在方块坐标 ±1（3×3×3）</b>为中心，
     *       对范围内含目标自己的全部生物造成「等级」点 {@code minecraft:sonic_boom} 伤害，
     *       并在中心发 {@code SONIC_BOOM} 粒子。</li>
     *   <li>叠加 = <b>提升等级</b>（作者 2026-10-04 裁定：与寄生同口径）；时长 6 秒
     *       （{@code MetalFamily.ECHO_ROAR_TICKS}，与巫毒同口径）。</li>
     * </ul>
     *
     * <p>⚠ 中文名按作者裁定统一叫「<b>幽咆</b>」；作者素材的文件名是「音咆.png」，
     * 我们只取那张图（落盘为 {@code textures/mob_effect/echo_roar.png}），<b>不改文件名、不改贴图</b>。</p>
     */
    public static final DeferredHolder<MobEffect, MobEffect> ECHO_ROAR =
            EFFECTS.register("echo_roar", () -> new MobEffect(MobEffectCategory.HARMFUL, 0x1B6B7A) {
                @Override
                public boolean applyEffectTick(LivingEntity entity, int amplifier) {
                    com.hjmmd_8.bettergold.material.MetalEvents.echoRoarTick(entity, amplifier);
                    return true;
                }

                @Override
                public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
                    return duration % 20 == 0;
                }
            });

    private AllEffects() {
    }
}
