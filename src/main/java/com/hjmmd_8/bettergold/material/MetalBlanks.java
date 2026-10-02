package com.hjmmd_8.bettergold.material;

import java.util.List;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 新约 1.5「金制武器扩展」的 <b>5 件「胚底」</b>（1.5 修正轮：作者的关键纠正）。
 *
 * <h2>它们是什么（作者原话）</h2>
 * <p>「那只是胚底，纯用于合成用的！！！……它没有实际用途，<b>根本就没有相应的金制器具</b>，
 * 只是用来给剩下的那些东西作为胚底，参与合成！……<b>没有金制系列工具！！！！</b>」</p>
 *
 * <p>所以这 5 件是<b>纯合成中间物</b>，一律用最普通的 {@link Item} 注册：</p>
 * <ul>
 *   <li><b>没有</b>攻击伤害 / 攻击速度属性修饰符（{@code ItemAttributeModifiers} 为空）；</li>
 *   <li><b>没有</b>耐久（不调用 {@code Properties#durability}，即最大堆叠 64）；</li>
 *   <li><b>不在</b> {@code #minecraft:enchantable/*} 的任何标签里（{@code isEnchantable} = false）；</li>
 *   <li><b>不属于</b>任何 {@link MetalFamily} ⇒ {@code MetalFamily.of(stack) == null}、
 *       {@code isWeapon} 恒为 false、进不了 {@link MetalEvents} 的任何派发链
 *       （重锤 ×1.2 / 三叉戟投掷 15 / 攻击附加 buff 全都不会触发）；</li>
 *   <li>模型就是最简单的 {@code minecraft:item/generated} 一层贴图，<b>没有任何 override 谓词</b>，
 *       也没有自定义渲染器 / 客户端扩展。</li>
 * </ul>
 *
 * <h2>它们在哪</h2>
 * <ol>
 *   <li>作者给的 5 条工作台配方产出这 5 件胚底
 *       （{@code data/bettergold/recipe/golden_<武器>_blank.json}）；</li>
 *   <li>30 条 {@code smithing_transform}（5 类 × 6 金属）的 {@code base} 就是对应的胚底：
 *       {@code <金属>_upgrade_template} + 胚底 + {@code <金属>_ingot} → {@code <金属>_<武器>}。</li>
 * </ol>
 * <p>创造页把它们放在「<b>材料</b>」分区（它们是合成材料，不是装备）。</p>
 *
 * <p>贴图沿用作者素材里的那 5 张 16×16「胚底」图
 * （{@code 黄制重锤胚底 / 金制弓箭胚底 / 金制弩胚底 / 金制三叉戟胚底 / 金制盾牌胚底}，
 * 其中「黄制」是笔误）。</p>
 */
public final class MetalBlanks {

    /** 胚底 id 的统一后缀（{@code golden_<武器>_blank}，blank = 胚底） */
    public static final String SUFFIX = "_blank";

    /** 五类武器后缀（与 {@link MetalWeapons#WEAPON_SUFFIXES} 一一对应） */
    public static final List<String> WEAPON_SUFFIXES = List.of("mace", "bow", "crossbow", "trident", "shield");

    /** 金制重锤胚底（作者配方第 1 条：1 金块 + 1 木棍竖排） */
    public static final DeferredItem<Item> GOLDEN_MACE_BLANK = register("mace");
    /** 金制弓箭胚底（作者配方第 2 条：原版弓配方把 3 根木棍换成 3 金锭） */
    public static final DeferredItem<Item> GOLDEN_BOW_BLANK = register("bow");
    /** 金制弩胚底（作者配方第 3 条） */
    public static final DeferredItem<Item> GOLDEN_CROSSBOW_BLANK = register("crossbow");
    /** 金制三叉戟胚底（作者配方第 4 条：1 木棍 + 4 金锭） */
    public static final DeferredItem<Item> GOLDEN_TRIDENT_BLANK = register("trident");
    /** 金制盾牌胚底（作者配方第 5 条：3×3 除左下、右下外全是金锭 = 7 个金锭） */
    public static final DeferredItem<Item> GOLDEN_SHIELD_BLANK = register("shield");

    /** 五件胚底的注册路径（创造页 / 配方生成 / 校验器共用一份清单） */
    public static final List<String> PATHS =
            WEAPON_SUFFIXES.stream().map(MetalBlanks::pathOf).toList();

    /** 五件胚底（顺序与 {@link #WEAPON_SUFFIXES} 一致） */
    public static final List<DeferredItem<Item>> ITEMS = List.of(
            GOLDEN_MACE_BLANK, GOLDEN_BOW_BLANK, GOLDEN_CROSSBOW_BLANK,
            GOLDEN_TRIDENT_BLANK, GOLDEN_SHIELD_BLANK);

    /** {@code mace} → {@code golden_mace_blank} */
    public static String pathOf(String weaponSuffix) {
        return "golden_" + weaponSuffix + SUFFIX;
    }

    /** 这个物品路径是不是五件胚底之一 */
    public static boolean isBlank(String path) {
        return PATHS.contains(path);
    }

    private static DeferredItem<Item> register(String weaponSuffix) {
        // 普通 Item + 空的 Properties：没有属性修饰符、没有耐久、没有附魔能力 —— 纯合成中间物
        return AllItems.ITEMS.registerSimpleItem(pathOf(weaponSuffix));
    }

    /** 触发静态初始化 */
    public static void bootstrap() {
    }

    private MetalBlanks() {
    }
}
