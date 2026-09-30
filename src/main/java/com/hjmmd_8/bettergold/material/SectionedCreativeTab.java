package com.hjmmd_8.bettergold.material;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;

/**
 * 会补上「分区空行」的创造模式标签页（本模组唯一创造页用它建，见 {@link CreativePageSections#PAGE_TAB_ID}）。
 *
 * <p><b>为什么空行不能在 displayItems 里 accept？</b>（实测结论，别改回去）
 * NeoForge 在 {@code EventHooks.onCreativeModeTabBuildContents} 里会把生成器产出的每个
 * {@link ItemStack} 先收进两个集合，收的时候有
 * {@code if (stack.getCount() != 1) throw new IllegalArgumentException("The stack count must be 1");}；
 * 原版 {@code CreativeModeTab.ItemDisplayBuilder#accept} 也有同样的 count == 1 检查。
 * 而 {@code ItemStack.EMPTY.getCount()} 是 0，所以 {@code output.accept(ItemStack.EMPTY)}
 * 不是"被过滤掉"而是<b>直接抛异常</b>，会把整个标签页的构建打断。
 * 参考实现（航空学）能塞空格子是因为它用 Mixin 整个接管了 {@code buildContents}、
 * 直接把私有字段 {@code displayItems} 换成自己的 LinkedList；我们不引 Mixin，所以换个等价的干净做法。</p>
 *
 * <p><b>做法：</b>生成器照常把物品按 {@link CreativeSections#layout} 的顺序 accept 给原版
 * （只 accept 非空格子），同时把每个分区的物品数记下来；渲染用的
 * {@link #getDisplayItems()} 再把空格子按同样的分区长度插回去。
 * 创造界面的物品列表本来就走 {@code getDisplayItems()}
 * （{@code CreativeModeInventoryScreen#selectTab} / {@code #refreshCurrentTabContents}，
 * 客户端确实会自己重建本页内容，见该文件第 133/144/178 行），
 * 而且原版自己也往这个列表里放 {@code ItemStack.EMPTY}（快捷栏页的占位格），
 * 所以"列表里有空格子"是原版支持的形态。</p>
 *
 * <p>本页只有<b>一个</b>，内容是 {@link CreativePageSections} 里登记的全部分区
 * （内置 4 个：材料/建筑/食物/装备，+ FD 模块自己注入的乐事分区）；
 * 每个分区恰好一条横幅、一个连续物品列表，分区之间不互相抢物品。</p>
 *
 * <p>标签页实例通过 NeoForge 官方扩展点 {@code CreativeModeTab.Builder#withTabFactory} 创建，
 * 不需要 Mixin / AccessTransformer / 反射。</p>
 */
public final class SectionedCreativeTab extends CreativeModeTab {

    private final Layout layout;

    private SectionedCreativeTab(CreativeModeTab.Builder builder, Layout layout) {
        super(builder);
        this.layout = layout;
    }

    /**
     * 建本模组唯一创造页的构建器（内容 = {@link CreativePageSections#all()} 的全部分区，按分区顺序排布）。
     *
     * <p>不需要传分区表 / 候选物品：分区注册表本身就是唯一的真相来源，
     * 生成器在真正构建时才去取（那时 FD 模块早已把自己的分区登记进来了）。</p>
     */
    public static CreativeModeTab.Builder builder() {
        Layout layout = new Layout();
        return CreativeModeTab.builder()
                .displayItems((parameters, output) -> layout.build(output))
                .withTabFactory(builder -> new SectionedCreativeTab(builder, layout));
    }

    /** 对外暴露的排布结果（带分区空行）；原版创造界面就是从这里取物品列表的 */
    @Override
    public Collection<ItemStack> getDisplayItems() {
        return this.layout.padded(super.getDisplayItems());
    }

    /** 生成器与渲染之间的桥梁：记住分区长度，渲染时把空行插回去 */
    private static final class Layout {

        /** 最近一次构建的分区结果（分区 key + 释词 + 每区物品数） */
        private volatile List<CreativeSections.Bucket> buckets = List.of();

        /**
         * 生成器本体：按分区取"排好序的连续列表" → 排布（记录 {@link CreativeSections#SECTION_ROWS}）
         * → 把非空格子交给原版。空格子一律不 accept（会被 NeoForge 的 count == 1 检查打断），
         * 只由 {@link #padded} 补。
         */
        void build(CreativeModeTab.Output output) {
            List<CreativeSections.Bucket> grouped = CreativePageSections.buckets();
            // 这次调用负责记录本页各分区的起始行号（横幅渲染要用）
            List<ItemStack> laidOut = CreativeSections.layout(grouped);
            for (ItemStack stack : laidOut) {
                if (!stack.isEmpty()) {
                    output.accept(stack);
                }
            }
            this.buckets = grouped;
        }

        /** 按记录下来的分区长度，把空行插回物品列表 */
        Collection<ItemStack> padded(Collection<ItemStack> source) {
            List<CreativeSections.Bucket> grouped = this.buckets;
            if (grouped.isEmpty()) {
                return source;
            }
            List<ItemStack> flat = List.copyOf(source);
            int expected = 0;
            for (CreativeSections.Bucket bucket : grouped) {
                expected += bucket.items().size();
            }
            if (expected != flat.size()) {
                // 实际物品数与生成时不一致（例如别的模组往本页插了物品）：宁可不画横幅也不能错位
                return flat;
            }
            // 只按长度切，物品本身以原版集合（= 真实内容）为准，顺序与生成时一致
            List<CreativeSections.Bucket> rebuilt = new ArrayList<>(grouped.size());
            int index = 0;
            for (CreativeSections.Bucket bucket : grouped) {
                int size = bucket.items().size();
                rebuilt.add(new CreativeSections.Bucket(bucket.key(), bucket.label(),
                        List.copyOf(flat.subList(index, index + size))));
                index += size;
            }
            // 补空行的规则只在 CreativeSections.layout 一处维护
            return CreativeSections.layout(rebuilt);
        }
    }
}
