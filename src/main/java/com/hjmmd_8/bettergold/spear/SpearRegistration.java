package com.hjmmd_8.bettergold.spear;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.hjmmd_8.bettergold.material.AllMetals;
import com.hjmmd_8.bettergold.material.AllTiers;
import com.hjmmd_8.bettergold.material.ChaosRange;
import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.crafting.Ingredient;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import net.neoforged.neoforge.registries.DeferredItem;
import net.minecraft.spearcore.init.SpearStats;
import net.minecraft.spearcore.util.SpearCondition;

/**
 * <b>1.8 §G「新武器系统：长矛」的注册器 —— 全仓唯一引用 SpearCore 类型的地方。</b>
 *
 * <p>⚠ 这个类<b>只许在 {@link SpearModule#isLoaded()} 为 true 时被加载</b>
 * （原因与门面/注册器拆分的经过见 {@link SpearModule} 的类注释）。</p>
 *
 * <h2>依赖形态（作者已批准的范式）</h2>
 * <ul>
 *   <li>构建侧 = <b>{@code compileOnly} + {@code libs/} 里的真 jar</b>，故意没有
 *       {@code localRuntime}，真 jar 同时放 {@code run/mods}（与 Patchouli 同一套）；</li>
 *   <li>运行侧 = <b>没装就不注册</b>（paradigm B）。</li>
 * </ul>
 *
 * <h2>14 件矛（§G-28..32 + 素材实际 14 族）</h2>
 * <table>
 *   <caption>数值 = SpearCore {@code Stats} 的字段值</caption>
 *   <tr><th>id</th><th>伤害字段</th><th>attackDuration</th><th>突刺倍率</th><th>四段窗口</th></tr>
 *   <tr><td>{@code antique_spear} 古董长矛</td><td>4</td><td>1.05</td><td>1.05</td><td>同铁矛</td></tr>
 *   <tr><td>{@code yaksha_spear} 夜叉贯骸矛</td><td>6</td><td>0.87</td><td>1.3</td><td>同下界合金矛</td></tr>
 *   <tr><td>{@code <10 族>_spear} 贵金属矛</td><td>7</td><td>1.1</td><td>1.4</td><td>同下界合金矛</td></tr>
 *   <tr><td>{@code chaosgold_spear} 混沌金矛</td><td>3–7</td><td>1.05</td><td>1.075</td><td>同钻石矛</td></tr>
 *   <tr><td>{@code chaosalloy_spear} 崩乱合金矛</td><td>7–13</td><td>0.8</td><td>1.6</td>
 *       <td>0.3 / 2 / 2.5 / 3 秒、击落阈值 5</td></tr>
 * </table>
 *
 * <h2>★「伤害 / 攻速」的口径</h2>
 * <p>{@code Stats.attackDamageBonus} 是 {@code ATTACK_DAMAGE} 的<b>修饰值</b>
 * ⇒ 工具提示 = 字段 + 玩家基值 1.0；{@code Stats.attackDuration} 是「一击几秒」
 * ⇒ 工具提示的攻速 = {@code 1 / attackDuration}。§G 那张表给的是<b>字段值</b>：
 * §G-31 的 1.05 / 1.075 与库自带钻石矛（bonus 3.0 / 1.05 / 1.075）逐位相同。</p>
 */
final class SpearRegistration {

    static final String ANTIQUE_ID = "antique_spear";
    static final String YAKSHA_ID = "yaksha_spear";
    static final String CHAOSGOLD_ID = "chaosgold_spear";
    static final String CHAOSALLOY_ID = "chaosalloy_spear";

    // ---------- §G 的数值（唯一真源；关卡与 javadoc 都引用这里） ----------
    /** §G-28 古董长矛：4 伤害 / 1.05 / 1.05 */
    static final float ANTIQUE_DAMAGE = 4.0F;
    static final float ANTIQUE_DURATION = 1.05F;
    static final float ANTIQUE_MULTIPLIER = 1.05F;

    /** §G-29 夜叉贯骸矛：6 / 0.87 / 1.3；命中 6% 掉 1 个下界合金尘埃、受抢夺 */
    static final float YAKSHA_DAMAGE = 6.0F;
    static final float YAKSHA_DURATION = 0.87F;
    static final float YAKSHA_MULTIPLIER = 1.3F;
    static final float YAKSHA_DUST_CHANCE = 0.06F;

    /** §G-30 贵金属矛（10 族各一）：7 / 1.1 / 1.4 */
    static final float FAMILY_DAMAGE = 7.0F;
    static final float FAMILY_DURATION = 1.1F;
    static final float FAMILY_MULTIPLIER = 1.4F;

    /** §G-31 混沌金矛：3–7 / 1.05 / 1.075（同钻石矛的四段窗口） */
    static final float CHAOSGOLD_MIN = 3.0F;
    static final float CHAOSGOLD_MAX = 7.0F;
    static final float CHAOSGOLD_DURATION = 1.05F;
    static final float CHAOSGOLD_MULTIPLIER = 1.075F;

    /** §G-32 崩乱合金矛：7–13 / 0.8 / 1.6 / 5 击落阈值 / 0.3·2·2.5·3 秒 */
    static final float CHAOSALLOY_MIN = 7.0F;
    static final float CHAOSALLOY_MAX = 13.0F;
    static final float CHAOSALLOY_DURATION = 0.8F;
    static final float CHAOSALLOY_MULTIPLIER = 1.6F;
    /** 击落阈值（{@code SpearCondition#minSpeed}） */
    static final float CHAOSALLOY_DISMOUNT_SPEED = 5.0F;
    static final int CHAOSALLOY_DELAY_TICKS = 6;
    static final int CHAOSALLOY_DISMOUNT_TICK = 40;
    static final int CHAOSALLOY_KNOCKBACK_TICK = 50;
    static final int CHAOSALLOY_DAMAGE_TICK = 60;

    private static final Map<String, DeferredItem<Item>> BY_PATH = new LinkedHashMap<>();
    private static final Map<MetalFamily, DeferredItem<Item>> BY_FAMILY = new LinkedHashMap<>();
    private static final List<DeferredItem<Item>> ALL = new ArrayList<>();

    private SpearRegistration() {
    }

    /** 注册 14 件矛 + 一个 setup 监听（只由 {@link SpearModule#init} 在装了库时调用） */
    static void register(IEventBus modEventBus) {
        DeferredItem<Item> antique = reg(ANTIQUE_ID, null, null, false);
        reg(YAKSHA_ID, null, null, true);
        for (MetalFamily family : MetalFamily.all()) {
            if (family == AllMetals.CHAOSGOLD) {
                reg(CHAOSGOLD_ID, family, new ChaosRange.Range(CHAOSGOLD_MIN, CHAOSGOLD_MAX), false);
            } else if (family == AllMetals.CHAOSALLOY) {
                reg(CHAOSALLOY_ID, family, new ChaosRange.Range(CHAOSALLOY_MIN, CHAOSALLOY_MAX), false);
            } else {
                reg(family.id + "_" + SpearModule.SUFFIX, family, null, false);
            }
        }
        SpearModule.publish(antique, ALL);
        modEventBus.addListener((FMLCommonSetupEvent event) -> event.enqueueWork(SpearRegistration::afterRegistration));
    }

    /**
     * 注册完成后把「矛 → 家族」登记进各族（{@code MetalFamily#addExtraWeapon}）。
     *
     * <p>必须在物品<b>已经注册完</b>之后调用（{@code FMLCommonSetupEvent}）：那里
     * {@code DeferredItem#get()} 才安全，而 {@code MetalFamily#of(Item)} 与
     * {@code isWeapon(Item)} 从此认识这些矛 —— 贵金属矛的「戳击 + 突刺击都触发器具功能」
     * 就是靠这条（派发判据只有那一个）。</p>
     */
    private static void afterRegistration() {
        for (Map.Entry<MetalFamily, DeferredItem<Item>> entry : BY_FAMILY.entrySet()) {
            entry.getKey().addExtraWeapon(entry.getValue().get());
        }
    }

    private static DeferredItem<Item> reg(String path, MetalFamily family,
            ChaosRange.Range range, boolean nightshadeDust) {
        DeferredItem<Item> item = AllItems.ITEMS.register(path,
                () -> new MetalSpearItem(statsFor(path, family, range), family, range, nightshadeDust));
        BY_PATH.put(path, item);
        ALL.add(item);
        if (family != null) {
            BY_FAMILY.put(family, item);
        }
        return item;
    }

    /**
     * 一件矛的 {@code Stats}。{@code family == null} ⇒ 古董 / 夜叉这两件**不属于任何族**的。
     *
     * <p>⚠ 所有 {@code SpearStats.*} 的读取都发生在<b>物品供应商 lambda 内部</b>
     * （= 注册事件期间、声音事件已注册）—— 与 SpearCore 自己的物品完全同一时机。</p>
     */
    private static SpearStats.Stats statsFor(String path, MetalFamily family, ChaosRange.Range range) {
        if (family == null) {
            if (ANTIQUE_ID.equals(path)) {
                return copy(AllTiers.ANTIQUE.getUses(), ANTIQUE_DURATION, ANTIQUE_MULTIPLIER,
                        ANTIQUE_DAMAGE, AllTiers.ANTIQUE.getEnchantmentValue(), Rarity.COMMON,
                        Ingredient.of(AllItems.UNWANTED_ANTIQUE.get()), false, "antique",
                        SpearStats.IRON);
            }
            return copy(2031, YAKSHA_DURATION, YAKSHA_MULTIPLIER, YAKSHA_DAMAGE,
                    AllTiers.NETHERITE_ANTIQUE.getEnchantmentValue(), Rarity.COMMON,
                    Ingredient.of(Items.NETHERITE_INGOT), true, "yaksha", SpearStats.NETHERITE);
        }
        if (range != null) {
            if (AllMetals.CHAOSALLOY == family) {
                return chaosalloy(family, range);
            }
            return copy(family.tier.getUses(), CHAOSGOLD_DURATION, CHAOSGOLD_MULTIPLIER, range.min(),
                    family.gearEnchantmentValue, Rarity.COMMON,
                    Ingredient.of(family.ingot.get()), family.fireResistant, family.id,
                    SpearStats.DIAMOND);
        }
        return copy(family.tier.getUses(), FAMILY_DURATION, FAMILY_MULTIPLIER, FAMILY_DAMAGE,
                family.gearEnchantmentValue, Rarity.COMMON,
                Ingredient.of(family.ingot.get()), family.fireResistant, family.id,
                SpearStats.NETHERITE);
    }

    /**
     * 「只换自己那几项、其余四段窗口整组照抄某把原版矛」—— 规格里
     * 「阈值与阶段同铁矛 / 同下界合金矛 / 同钻石矛」就是这一句。
     */
    private static SpearStats.Stats copy(int durability, float attackDuration, float damageMultiplier,
            float damageBonus, int enchantmentValue, Rarity rarity, Ingredient repair,
            boolean fireResistant, String materialName, SpearStats.Stats windows) {
        return new SpearStats.Stats(durability, attackDuration, damageMultiplier, damageBonus,
                enchantmentValue, rarity, repair, fireResistant, materialName,
                windows.useSound(), windows.hitSound(), windows.attackSound(),
                windows.swingTimes(), windows.hitboxMargin(), windows.contactCooldownTicks(),
                windows.delayTicks(),
                windows.dismountConditions(), windows.knockbackConditions(), windows.damageConditions(),
                windows.forwardMovement(), windows.minRange(), windows.maxRange(),
                windows.minCreativeRange(), windows.maxCreativeRange(), windows.hitboxMargin2(),
                windows.mobFactor(), windows.dealsKnockback(), windows.dismounts());
    }

    /**
     * 崩乱合金矛：<b>四段窗口全部自定义</b>（§G-32 的 0.3 / 2 / 2.5 / 3 秒 + 5 击落阈值）。
     *
     * <p>库的 {@code spearOf(...)} 把击落阈值写死成 0.3，所以这一件必须直接构造 {@code Stats}：
     * 把「击落条件」换成 {@code ofAttackerSpeed(40, 5.0)} 并把 {@code dismounts} 置 true
     * （库自带的默认是 false ⇒ 其余矛一律不击落骑手）。</p>
     */
    private static SpearStats.Stats chaosalloy(MetalFamily family, ChaosRange.Range range) {
        SpearStats.Stats b = SpearStats.NETHERITE;
        return new SpearStats.Stats(family.tier.getUses(), CHAOSALLOY_DURATION, CHAOSALLOY_MULTIPLIER,
                range.min(), family.gearEnchantmentValue, Rarity.COMMON,
                Ingredient.of(family.ingot.get()), family.fireResistant, family.id,
                b.useSound(), b.hitSound(), b.attackSound(),
                b.swingTimes(), b.hitboxMargin(), b.contactCooldownTicks(),
                CHAOSALLOY_DELAY_TICKS,
                SpearCondition.ofAttackerSpeed(CHAOSALLOY_DISMOUNT_TICK, CHAOSALLOY_DISMOUNT_SPEED),
                SpearCondition.ofAttackerSpeed(CHAOSALLOY_KNOCKBACK_TICK, 5.1F),
                SpearCondition.ofRelativeSpeed(CHAOSALLOY_DAMAGE_TICK, 4.6F),
                b.forwardMovement(), b.minRange(), b.maxRange(),
                b.minCreativeRange(), b.maxCreativeRange(), b.hitboxMargin2(),
                b.mobFactor(), true, true);
    }
}
