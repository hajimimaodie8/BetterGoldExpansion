package com.hjmmd_8.bettergold.material;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;

/**
 * 本模组<b>唯一</b>创造页（{@link #PAGE_TAB_ID}）的「分区」注册表。
 *
 * <h2>最终形态（作者定稿）</h2>
 * <pre>
 * 页（1 个，{@link #PAGE_TAB_ID}）
 *   └─ 分区（5 个，每个分区<b>一条横幅</b> + 一个<b>连续的物品列表</b>）
 *        材料 materials.png / 建筑 blocks.png / 食物 food.png / 装备 gear.png / 乐事 fd.png
 * </pre>
 *
 * <p>分区内部的先后（例：材料 = 其他材料 → 交易金商人相关 → 金属）由 {@link Section#rules()}
 * 表达：这些规则只负责「下一段拿哪些物品、怎么排」，<b>不各自产生横幅、也不插空行</b>，
 * 整段首尾相接成该分区唯一的连续列表（排布规则见 {@link CreativeSections#layout}）。</p>
 *
 * <h2>谁注册什么（架构红线）</h2>
 * <ul>
 *   <li>内置 4 个分区（材料 / 建筑 / 食物 / 装备）由本类在 {@link #ensureCoreSections()} 里登记，
 *       物品全部来自 {@link CreativeTabSections}，<b>不依赖任何可选模组</b>。</li>
 *   <li>乐事分区（{@code fd}）由 <b>FD 模块自己</b>在 {@code fd.FdModule.register} 里登记
 *       （{@code fd.FdTabs.FD_SECTION}，物品是 {@code FdItems.ITEMS}）。
 *       核心代码只认这里的 {@link Section} 抽象，从不引用 {@code FdItems}/{@code FdTabs}，
 *       所以「没装农夫乐事」时本页自然只有 4 个分区。</li>
 * </ul>
 *
 * <p>分区分桶是<b>各自独立</b>的（{@link #buckets()}）：每个分区的规则只看本分区候选物品，
 * 分区之间不会互相抢物品。</p>
 */
public final class CreativePageSections {

    /** 本模组唯一创造页的注册名：注册（{@code bettergold.java}）与渲染（客户端）共用这一处，改名不会失配 */
    public static final ResourceLocation PAGE_TAB_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "bettergold_tab");

    /** 横幅贴图目录：{@code assets/bettergold/textures/gui/creative_sections/*.png}（162×18） */
    private static final String BANNER_DIR = "textures/gui/creative_sections/";

    /**
     * 内置分区数量，同时也是「非内置分区」该用的 order：
     * 外部模块（FD 联动）用自己的 order 排在全部内置分区<b>之后</b>，即页尾。
     */
    public static final int CORE_SECTION_COUNT = 4;

    /**
     * 一个分区：<b>一条横幅</b> + <b>一个连续的物品列表</b>。
     *
     * @param key        分区 key（页内唯一；= {@link CreativeSections#SECTION_ROWS} 的键 = 横幅贴图名）
     * @param order      页内显示顺序（升序；相同则按注册顺序）
     * @param label      横幅释词（材料 / 建筑 / 食物 / 装备 / 乐事）
     * @param banner     横幅贴图（162×18，一整行）
     * @param rules      分区内物品排列规则（顺序 = 先后，见 {@link CreativeTabSections.Slot}）；
     *                   只决定次序，<b>不产生额外横幅与空行</b>
     * @param candidates 该分区候选物品（每次调用都重新取，生成器里现取现用）
     */
    public record Section(String key, int order, String label, ResourceLocation banner,
            List<CreativeTabSections.Slot> rules, Supplier<List<ItemStack>> candidates) {
    }

    /** 已登记的分区（key -> 分区），按注册顺序迭代 */
    private static final Map<String, Section> SECTIONS = new LinkedHashMap<>();

    private static boolean coreRegistered;

    /** 分区横幅贴图：{@code bettergold:textures/gui/creative_sections/<name>.png} */
    public static ResourceLocation bannerTexture(String name) {
        return ResourceLocation.fromNamespaceAndPath(bettergold.MODID, BANNER_DIR + name + ".png");
    }

    /**
     * 登记一个分区。key 重复是编程错误（会直接抛，避免两个分区悄悄抢同一个 {@code SECTION_ROWS} 键）。
     * 内置分区由 {@link #ensureCoreSections()} 首访时登记，外部模块（FD）在自己的初始化里登记。
     */
    public static void register(Section section) {
        Section previous = SECTIONS.putIfAbsent(section.key(), section);
        if (previous != null) {
            throw new IllegalStateException("duplicate creative section key: " + section.key());
        }
    }

    /** 全部分区（按 order 升序；同 order 保持注册顺序）——页内显示顺序就是它 */
    public static List<Section> all() {
        ensureCoreSections();
        List<Section> out = new ArrayList<>(SECTIONS.values());
        out.sort(Comparator.comparingInt(Section::order));
        return List.copyOf(out);
    }

    /** 按分区 key 取分区；没登记过返回 null（渲染端拿不到横幅就不画，绝不崩） */
    public static @Nullable Section byKey(String key) {
        ensureCoreSections();
        return SECTIONS.get(key);
    }

    /** 整页的候选物品 = 各分区候选按分区顺序拼接（本模组全部物品，含 FD 模块自己那部分） */
    public static List<ItemStack> allCandidates() {
        List<ItemStack> out = new ArrayList<>();
        for (Section section : all()) {
            out.addAll(section.candidates().get());
        }
        return out;
    }

    /**
     * 整页的分桶结果：<b>每个分区恰好一个桶</b>（key + 释词 + 该分区排好序的连续物品列表）。
     * 分区内部的多段规则由 {@link CreativeTabSections#ordered} 首尾相接成一条列表。
     */
    public static List<CreativeSections.Bucket> buckets() {
        List<CreativeSections.Bucket> out = new ArrayList<>();
        for (Section section : all()) {
            out.add(new CreativeSections.Bucket(section.key(), section.label(),
                    CreativeTabSections.ordered(section.rules(), section.candidates().get())));
        }
        return out;
    }

    /**
     * 登记内置 4 个分区（首访时一次）。顺序即作者定稿的页内顺序：
     * 材料（materials.png）→ 建筑（blocks.png）→ 食物（food.png）→ 装备（gear.png）；
     * 乐事分区（fd.png）由 FD 模块以 {@link #CORE_SECTION_COUNT} 排在这 4 个之后。
     */
    private static void ensureCoreSections() {
        if (coreRegistered) {
            return;
        }
        coreRegistered = true;
        register(new Section("materials", 0, "材料", bannerTexture("materials"),
                CreativeTabSections.MATERIALS, CreativeTabSections::materialsCandidates));
        register(new Section("blocks", 1, "建筑", bannerTexture("blocks"),
                CreativeTabSections.BLOCKS, CreativeTabSections::blockCandidates));
        register(new Section("food", 2, "食物", bannerTexture("food"),
                CreativeTabSections.FOOD, CreativeTabSections::foodCandidates));
        register(new Section("gear", 3, "装备", bannerTexture("gear"),
                CreativeTabSections.GEAR, CreativeTabSections::gearCandidates));
    }

    private CreativePageSections() {
    }
}
