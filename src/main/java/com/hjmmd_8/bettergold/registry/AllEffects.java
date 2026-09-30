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
 *   <li>巫毒（voodoo）：被对应器具攻击会叠加等级；窗口内目标受到的伤害按配置比例累积，
 *       效果<b>自然到期</b>时按 {@code 存储伤害 × (1 + 0.8 × 等级)} 造成魔法伤害
 *       （累积与结算都在 {@code MetalEvents} + {@code material.VoodooAccumulator}）。</li>
 *   <li>颤栗（tremble）：每级 −1 点伤害、−0.1 攻速（新约 1.4 结雷金）。</li>
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

    private AllEffects() {
    }
}
