package com.hjmmd_8.bettergold.material;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.function.Predicate;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;

/**
 * 各创造页「分区内部排列规则」的声明。
 *
 * <p>这里是<b>唯一</b>描述"某个分区里物品按什么先后排"的地方：规则顺序 = 段先后，
 * 段内的金属物品自动按 {@link CreativeSections} 的规则排序（金属顺序 → 段内位次），
 * 非金属物品默认保持投放顺序；需要「套件按类型排」的段（建筑的「其他建筑方块」）
 * 给 {@link Slot#order} 传 {@link CreativeSections#SUITE_ORDER} 即可，类型表仍然只有一张。
 * 以后新增金属不需要改这个文件。</p>
 *
 * <p><b>注意（1.4 定稿）</b>：这些规则<b>不再各自画横幅、也不再插空行</b> ——
 * 它们只是同一个分区里物品的<b>先后次序</b>（例：材料 = 其他材料 → 交易金商人相关 → 金属），
 * 由 {@link #ordered} 首尾相接成该分区唯一的连续列表。横幅只有「分区」这一级
 * （材料 / 建筑 / 食物 / 装备 / 乐事，见 {@link CreativePageSections}）。</p>
 *
 * <p>内置 4 个分区（材料 / 建筑 / 食物 / 装备）的规则在本类；
 * 乐事分区的规则归 FD 模块自己（{@code fd.FdTabs.RULES}），核心代码不引用它。</p>
 */
public final class CreativeTabSections {

    /**
     * 分区内的一段排列规则：标签 + 归属判定 +（可选的）段内排序。
     *
     * @param title 这一段的标签（<b>只用于日志/自检，不再画到横幅上</b>；横幅释词在
     *              {@link CreativePageSections.Section#label()}）
     * @param test  归属判定
     * @param order 段内排序；{@code null}（绝大多数段）＝沿用默认规则：能分类的金属物品按
     *              {@link CreativeSections#classify} 的排序键排、其余保持投放顺序，且后者在前。
     *              传 {@link CreativeSections#SUITE_ORDER} 则整段按建材类型位次排、杂项排最后。
     */
    public record Slot(String title, Predicate<ItemStack> test, @Nullable Comparator<ItemStack> order) {

        /** 不带自定义段内排序的规则（默认规则） */
        public Slot(String title, Predicate<ItemStack> test) {
            this(title, test, null);
        }
    }

    /**
     * 按规则顺序把<b>本分区</b>物品排成<b>一条连续列表</b>（先到先得：每件物品只进第一个命中的段）。
     *
     * <p>段内顺序与旧实现完全一致：声明了 {@link Slot#order} 的段整段用那个比较器排
     * （建材类型 → 物品 id），其余段是「非金属按投放顺序在前、能分类的金属按排序键在后」。
     * 金属那部分的排序键是
     * (分区, 金属位次, 类型位次, 物品 id) —— 前三位来自 {@link CreativeSections.Placement#sortKey()}，
     * 最后一位是 {@link CreativeSections#itemIdOf} 兜底，因此同一金属的各类型严格连排、
     * 同键时也与注册 / 投放顺序无关。段与段之间<b>不加任何空行</b>。</p>
     *
     * <p>兜底：万一某件物品没有被任何规则命中（规则漏写），它会被追加在末尾而不是被丢掉 ——
     * 「物品一个都不能丢」优先于顺序；真出现这种情况，自检里的逐元素比对会暴露出来。</p>
     */
    public static List<ItemStack> ordered(List<Slot> slots, List<ItemStack> items) {
        List<ItemStack> out = new ArrayList<>();
        boolean[] taken = new boolean[items.size()];
        for (Slot slot : slots) {
            List<ItemStack> plain = new ArrayList<>();
            List<Long> keys = new ArrayList<>();
            List<ItemStack> metals = new ArrayList<>();
            for (int i = 0; i < items.size(); i++) {
                if (taken[i]) {
                    continue;
                }
                ItemStack stack = items.get(i);
                if (!slot.test().test(stack)) {
                    continue;
                }
                taken[i] = true;
                if (slot.order() != null) {
                    // 自定义排序的段：整段一起排，不区分"金属 / 非金属"
                    plain.add(stack);
                    continue;
                }
                String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
                CreativeSections.Placement place = CreativeSections.classify(path);
                if (place == null) {
                    plain.add(stack);
                } else {
                    keys.add(place.sortKey());
                    metals.add(stack);
                }
            }
            if (slot.order() != null) {
                plain.sort(slot.order());
                out.addAll(plain);
                continue;
            }
            // 排序键 = (分区, 金属位次, 类型位次) 后按物品 id 兜底；下标排序以保留原始下标备用
            List<Integer> order = new ArrayList<>(keys.size());
            for (int i = 0; i < keys.size(); i++) {
                order.add(i);
            }
            order.sort(Comparator.comparingLong((Integer i) -> keys.get(i))
                    .thenComparing(i -> CreativeSections.itemIdOf(metals.get(i))));
            out.addAll(plain);
            for (int i : order) {
                out.add(metals.get(i));
            }
        }
        for (int i = 0; i < items.size(); i++) {
            if (!taken[i]) {
                out.add(items.get(i));
            }
        }
        return out;
    }

    /** 由物品 id / 路径判定的小工具 */
    private static boolean pathIs(ItemStack stack, String... paths) {
        String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
        for (String candidate : paths) {
            if (path.equals(candidate)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 是不是「金属装备」：{@link CreativeSections#classify} 认得出来的金属物品
     * （剑斧镐锹锄 + 四件盔甲 + 1.5 的五类武器，见 {@link CreativeSections} 的 {@code GEAR_SLOT}）。
     *
     * <p>1.5 修正轮：五件「胚底」不是装备（作者澄清它们是纯合成材料），
     * 因此这里不再有「金制基础武器」的特例；胚底由材料分区的兜底段接住，落在「材料」分区。</p>
     */
    private static boolean isMetalGear(ItemStack stack) {
        return kindOf(stack) == CreativeSections.Kind.METAL_GEAR;
    }

    /** 物品 id 后缀判定（公开：FD 模块自己的分区规则要用，见 {@code fd.FdTabs.RULES}） */
    public static boolean pathEndsWith(ItemStack stack, String... suffixes) {
        String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
        for (String suffix : suffixes) {
            if (path.endsWith(suffix)) {
                return true;
            }
        }
        return false;
    }

    // ==================== 内置 4 个分区的内部规则（分区 key / 横幅 / 释词见 CreativePageSections） ====================

    /**
     * 材料分区内部顺序：<b>炼金术学员手册 → 其他材料 → 交易金商人相关 → 金属</b>
     * （作者定稿原话：其他材料排最前、交易金商人相关物排中、特殊金属排后）。
     *
     * <p>注意：规则是"先到先得"（每件物品只进第一个命中的段），所以「其他材料」排在第一位时
     * 不能再写成 {@code stack -> true} 的兜底判定 —— 那会把整个分区都吃进第一段。
     * 这里改成正面判定"既不是交易金商人相关物、也不是金属物品"，四段合起来仍然恰好覆盖全部物品，
     * 一件都不会丢。</p>
     *
     * <p><b>bg-book（1.6）：手册为什么是"材料位第一"</b> —— 需求要「新生代炼金术学员手册排在材料位第一」，
     * 两种做法见需求 §6#5，本轮取的是<b>②「在材料分区的段列表里把它单列成第一段」</b>：</p>
     * <ul>
     *   <li>① 给它一个 {@link CreativeSections#MATERIAL_SLOT} 的最靠前新位次 —— <b>做不到/不该做</b>：
     *       那张表是「**金属 id 后缀 → 位次**」（ingot / nugget / upgrade_template），
     *       查它之前必须先通过 {@code metalOf(path)} 认出金属前缀；手册不是金属物品，
     *       塞进去只会破坏 8 族金属的金属位次语义，而且根本走不到那张表。</li>
     *   <li>② 本段 = 材料分区的第一段 ⇒ 手册就是整个材料分区的**第一个物品**（干净、不动机制）。</li>
     * </ul>
     * <p>⚠ 手册物品只在装了 Patchouli 时才注册；没装时本段的判定恒为 false（段为空、无副作用）。</p>
     */
    public static final List<Slot> MATERIALS = List.of(
            new Slot("炼金术学员手册", CreativeTabSections::isHandbook),
            new Slot("其他材料", stack -> !isTraderRelated(stack) && !isMetal(stack)),
            new Slot("交易金商人相关", CreativeTabSections::isTraderRelated),
            new Slot("金属", CreativeTabSections::isMetal));

    /**
     * 新生代炼金术学员手册（bg-book，1.6）：材料分区的第一段就它一件。
     *
     * <p>判据用物品类而不是 id 字符串 —— 类比较不会因为 id 写错而静默失效，
     * 而且没装 Patchouli 时根本没有实例，判定自然恒为 false。</p>
     */
    private static boolean isHandbook(ItemStack stack) {
        return stack.getItem() instanceof com.hjmmd_8.bettergold.item.HandbookItem;
    }

    /**
     * 建筑分区内部顺序：金属建材（金属块 + 那套建材）→ 其他建筑方块。
     *
     * <p><b>金属块不是独立的一段</b>（作者 1.4 定稿）：它是这套金属建材的
     * {@link CreativeSections#BUILDING_SLOT 类型位次 0}，所以这一段的排序键是
     * (金属位次, 类型位次) = 每种金属的 11 件严格连排、且以自己的 {@code <金属>_block} 开头，
     * 金属之间按 {@link CreativeSections#METAL_ORDER}：
     * 块 → 砖 → 柱 → 砖楼梯 → 砖台阶 → 砖墙 → 门 → 活板门 → 栏杆 → 链 → 灯笼。
     * 以前这里分两段（先 4 个金属块、再每种金属 10 件）是错的，别再拆开。</p>
     *
     * <p>「其他建筑方块」是兜底段，装的是「不是金属物品」的方块：普通金那一套建材
     * （金砖块 / 金柱 / …… / 金灯笼）加上金染土、筐装物、易金柜台、金雕这类杂项。</p>
     *
     * <p>它复用 {@link CreativeSections#SUITE_ORDER}：整段先按<b>同一张</b>建材类型表排
     * （块 → 砖块 → 柱 → 楼梯 → 台阶 → 墙 → 门 → 活板门 → 栏杆 → 链 → 灯笼，与「金属建材」一致），
     * 同类型按物品 id 稳定排序；不属于任何套件的杂项排在全部套件之后，并按
     * {@link CreativeSections} 里的那张杂项有序表排：<b>金染土 → 金麦块 → 筐装方块（一整组，
     * 组内按物品 id）→ 易金柜台 → 金雕（苦力怕 → 末影人 → 青蛙）</b>，
     * 之后再是没命中该表的其它杂项（仍按物品 id）。</p>
     */
    public static final List<Slot> BLOCKS = List.of(
            new Slot("金属建材", stack -> kindOf(stack) == CreativeSections.Kind.METAL_BUILDING),
            new Slot("其他建筑方块", stack -> true, CreativeSections.SUITE_ORDER));

    /** 装备分区内部顺序：金属装备 → 其他工具 */
    public static final List<Slot> GEAR = List.of(
            new Slot("金属装备", CreativeTabSections::isMetalGear),
            new Slot("其他工具", stack -> true));

    /** 食物分区内部顺序：种子 → 普通金食物 → 万坚金食物 */
    public static final List<Slot> FOOD = List.of(
            new Slot("种子", stack -> pathEndsWith(stack, "_seeds")),
            new Slot("普通金食物", stack -> !isSturdygold(stack)),
            new Slot("万坚金食物", stack -> true));

    private static CreativeSections.Kind kindOf(ItemStack stack) {
        String path = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
        CreativeSections.Placement place = CreativeSections.classify(path);
        return place == null ? null : place.kind();
    }

    /** 供调用方快速判断：这个物品是不是方块（材料分区要排除方块，建筑分区只要方块） */
    public static boolean isBlockItem(ItemStack stack) {
        return stack.getItem() instanceof BlockItem;
    }

    /** 物品注册路径（如 {@code flamegold_ingot}） */
    private static String pathOf(ItemStack stack) {
        return BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
    }

    /** 交易金商人相关物：礼品金票 + 四种礼盒（材料分区的判定，与段标签一一对应） */
    private static boolean isTraderRelated(ItemStack stack) {
        return pathEndsWith(stack, "_gift_box") || pathIs(stack, "curio_box", "gourmet_box", "gift_gold_ticket");
    }

    /** 金属物品：规则引擎（{@link CreativeSections#classify}）认得出来的那些（核心材料/原料/锭/粒/模板/建材/器具/盔甲） */
    private static boolean isMetal(ItemStack stack) {
        return CreativeSections.classify(pathOf(stack)) != null;
    }

    /** 是不是万坚金系物品（按 id 前缀判定，非枚举；公开：FD 模块的分区规则要用） */
    public static boolean isSturdygold(ItemStack stack) {
        return pathOf(stack).startsWith("sturdygold_");
    }

    /** 本体物品里是不是"食物链"那一类的（判定沿用 {@link AllItems#isFoodTab}） */
    private static boolean isFood(ItemStack stack) {
        return AllItems.isFoodTab(BuiltInRegistries.ITEM.getKey(stack.getItem()), stack);
    }

    /** 本体物品里是不是"装备工具"那一类的（判定沿用 {@link AllItems#isGearTab}） */
    private static boolean isGear(ItemStack stack) {
        return AllItems.isGearTab(BuiltInRegistries.ITEM.getKey(stack.getItem()), stack);
    }

    /** 收集本体注册表里满足条件的物品（每个注册项一份默认 ItemStack，保持注册顺序） */
    private static List<ItemStack> ownItems(Predicate<ItemStack> filter) {
        List<ItemStack> out = new ArrayList<>();
        for (var holder : AllItems.ITEMS.getEntries()) {
            ItemStack stack = holder.get().getDefaultInstance();
            if (filter.test(stack)) {
                out.add(stack);
            }
        }
        return out;
    }

    /**
     * 材料分区候选：本体物品里既不是食物、也不是装备、并且不是方块的（方块归建筑分区）。
     *
     * <p><b>bg-15w 第 8 项 + 续工轮 §3.8 的口径改正</b>：五件「胚底」（{@code golden_<武器>_blank}）
     * <b>只在检测到装了 `mut`（MoreUpgradeTemplate，更多锻造模板重生）时才排除</b>。</p>
     *
     * <p>作者原话：「我是让你检测有没有装更多锻造模板重生才自动隐藏胚底，而不是直接进游戏就直接把胚底隐藏」。
     * ⇒ <b>没装 mut 时一切照旧</b>：五件胚底可见、可用工作台配方合成、可以当 30 条锻造升级的基底；
     * 装了 mut 时它们让位给 MUT 自带的五件金武器（30 条以 {@code mut:golden_*} 为 base 的条件配方）。</p>
     *
     * <p>物品注册 / lang / 模型<b>两种情况都保留</b>（老存档里已有的胚底不会变成未知物品）。</p>
     */
    public static List<ItemStack> materialsCandidates() {
        // 装没装 mut 是**运行期**才知道的事实，所以这里每次进来判一次（创造页重建时求值）
        boolean hideBlanks = net.neoforged.fml.ModList.get().isLoaded("mut");
        List<ItemStack> out = ownItems(stack -> !isFood(stack) && !isGear(stack) && !isBlockItem(stack)
                && !(hideBlanks && MetalBlanks.isBlank(pathOf(stack))));
        // 分区内顺序（作者确认）：礼品金票 + 四种礼盒 → 把金票提到最前，其余保持注册顺序
        for (int i = 0; i < out.size(); i++) {
            if (pathOf(out.get(i)).equals("gift_gold_ticket")) {
                out.add(0, out.remove(i));
                break;
            }
        }
        return out;
    }

    /** 建筑分区候选：本体物品里的方块（种子那类"食物方块"不会落进来） */
    public static List<ItemStack> blockCandidates() {
        return ownItems(stack -> isBlockItem(stack) && !isFood(stack) && !isGear(stack));
    }

    /** 装备分区候选 */
    public static List<ItemStack> gearCandidates() {
        return ownItems(CreativeTabSections::isGear);
    }

    /** 食物分区候选 */
    public static List<ItemStack> foodCandidates() {
        return ownItems(CreativeTabSections::isFood);
    }

    private CreativeTabSections() {
    }
}
