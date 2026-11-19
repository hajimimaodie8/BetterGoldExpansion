package com.hjmmd_8.bettergold.spear;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.material.ChaosRange;
import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.minecraft.spearcore.init.SpearStats;
import net.minecraft.spearcore.item.ConfiguredSpearItem;

/**
 * <b>本模组的长矛物品类（1.8 §G）</b>—— 直接继承外部库 SpearCore 的
 * {@link ConfiguredSpearItem}（它已经继承 {@code BaseSpearItem → SpearItem}），
 * 因此「戳刺 / 蓄力冲锋 / 四段判定窗口 / 第一与第三人称动作 / 附魔 / 怪物 AI / 命中音效」
 * <b>全部由库提供，本类一行都不重写</b>。
 *
 * <h2>为什么要一个子类，而不是直接 {@code new ConfiguredSpearItem(stats)}</h2>
 * <ol>
 *   <li><b>混沌金的伤害是区间</b>（§G-31「3–7」，两端值存在 {@code bettergold:chaos_range_flip}
 *       数据组件里）：库的属性表把 {@code ATTACK_DAMAGE} 直接烤成 {@code Stats.attackDamageBonus}，
 *       所以必须覆写 {@link #getDefaultAttributeModifiers(ItemStack)} 现读当前值
 *       （与既有 14 件套的 {@code ChaosWiring} 同一套区间机制，公式仍只有 {@link ChaosRange} 一处）。</li>
 *   <li><b>夜叉贯骸矛的「6% 掉下界合金尘埃」</b>（§G-29，受抢夺）：最省事、且两条命中路径都会
 *       经过的落点是 {@link #hurtEnemy}（库的 {@code attack} 与 {@code stabAttack} 都调
 *       {@code ItemStack#hurtEnemy}，见 3.2.1 的字节码；两者 = 戳击 STAB 与冲锋 CHARGE）。</li>
 *   <li><b>贵金属矛的「戳击与突刺击都触发贵金属器具功能」</b>：<b>不在本类做</b> ——
 *       那条功能的派发判据是 {@code MetalFamily#isWeapon(Item)}（见
 *       {@code MetalFamily#addExtraWeapon}），本类只要被家族认识就自动生效。</li>
 * </ol>
 *
 * <h2>「伤害 / 攻速」两个数的口径（★ 与 §G 的原文逐条对应）</h2>
 * <p>库的 {@code Stats} 里：</p>
 * <ul>
 *   <li>{@code attackDamageBonus} 是 {@code ATTACK_DAMAGE} 的<b>修饰值</b>（玩家基值 1.0 由引擎加），
 *       所以工具提示显示 = 本值 + 1；</li>
 *   <li>{@code attackDuration} 是「一击几秒」，最终攻速 = {@code 1 / attackDuration}
 *       （{@code Stats#getAttackSpeedModifier() = 1/attackDuration − 4.0}，3.2.1 字节码）。</li>
 * </ul>
 * <p>§G 那张表给的是<b>库的字段值</b>（例：§G-31 的 1.05 / 1.075 与库自带的钻石矛
 * {@code DIAMOND} 逐位相同），所以本模组的实现照字段写，A 级读数同时打印「字段值 / 显示值」两列。</p>
 */
public class MetalSpearItem extends ConfiguredSpearItem implements SpearGear {

    /** 本矛属于哪一族；古董长矛与夜叉贯骸矛<b>不属于任何族</b>（null） */
    private final @Nullable MetalFamily family;

    /**
     * 混沌金 / 崩乱合金的伤害区间（§G-31 的 3–7、§G-32 的 7–13）；其余矛为 null。
     *
     * <p>当前值存在物品栈的数据组件里（{@link ChaosRange#VALUE}），每次命中后
     * {@link ChaosRange#reroll} 重掷一次 —— 与既有 14 件混沌金器具「命中即重掷」同构
     * （本次命中用重掷前的值）。</p>
     */
    private final @Nullable ChaosRange.Range attackRange;

    /** 夜叉贯骸矛：命中后 6%、受抢夺，掉 1 个下界合金尘埃（§G-29） */
    private final boolean nightshadeDust;

    public MetalSpearItem(SpearStats.Stats stats, @Nullable MetalFamily family,
            @Nullable ChaosRange.Range attackRange, boolean nightshadeDust) {
        super(stats);
        this.family = family;
        this.attackRange = attackRange;
        this.nightshadeDust = nightshadeDust;
    }

    /** 本矛属于哪一族（古董 / 夜叉为 null） */
    public @Nullable MetalFamily family() {
        return this.family;
    }

    /** 是否是「伤害走区间」的矛（混沌金 / 崩乱合金） */
    public boolean hasAttackRange() {
        return this.attackRange != null;
    }

    /**
     * 属性表：区间矛<b>现读当前值</b>，其余直接交回库的实现。
     *
     * <p>三条修饰符与库的 {@code BaseSpearItem#buildAttributeModifiers} 逐项同形
     * （伤害 / 攻速 / 交互距离 +1.5），唯一差别是伤害那个数从区间组件读。</p>
     */
    @Override
    public ItemAttributeModifiers getDefaultAttributeModifiers(ItemStack stack) {
        if (this.attackRange == null) {
            return super.getDefaultAttributeModifiers(stack);
        }
        float damage = ChaosRange.current(stack, ChaosRange.Channel.ATTACK, this.attackRange);
        float speed = SpearStats.get(this).getAttackSpeedModifier();
        return ItemAttributeModifiers.builder()
                .add(Attributes.ATTACK_DAMAGE,
                        new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID, damage,
                                AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .add(Attributes.ATTACK_SPEED,
                        new AttributeModifier(Item.BASE_ATTACK_SPEED_ID, speed,
                                AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .add(Attributes.ENTITY_INTERACTION_RANGE,
                        new AttributeModifier(
                                ResourceLocation.fromNamespaceAndPath("spearcore", "spear_range"), 1.5D,
                                AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .build();
    }

    /**
     * 命中之后：① 区间矛重掷伤害（本次已用旧值）② 夜叉贯骸矛掷 6%（每级抢夺 +6%）掉尘埃。
     *
     * <p>服务端才有意义（客户端不会有 {@code Player} 的命中判定）；这里显式早退，
     * 保证客户端一个随机数都不消耗。</p>
     */
    @Override
    public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        boolean result = super.hurtEnemy(stack, target, attacker);
        if (this.attackRange != null) {
            ChaosRange.reroll(stack, ChaosRange.Channel.ATTACK, this.attackRange, attacker.getRandom());
        }
        if (this.nightshadeDust && attacker instanceof Player player && !player.level().isClientSide()) {
            Level level = player.level();
            int looting = stack.getEnchantmentLevel(
                    level.registryAccess().holderOrThrow(Enchantments.LOOTING));
            // 「6%，受抢夺」= 每级 +6%（与 §F-23 寒烁冰晶「0.06 × (1+时运)」同一套口径）。
            float chance = 0.06F * (1 + looting);
            if (player.getRandom().nextFloat() < chance) {
                Containers.dropItemStack(level, target.getX(), target.getY(0.5D), target.getZ(),
                        new ItemStack(AllItems.NETHERITE_DUST.get()));
            }
        }
        return result;
    }
}
