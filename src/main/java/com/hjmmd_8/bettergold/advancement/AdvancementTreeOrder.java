package com.hjmmd_8.bettergold.advancement;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import com.hjmmd_8.bettergold.material.CreativeSections;

import net.minecraft.advancements.AdvancementNode;
import net.minecraft.resources.ResourceLocation;

/**
 * <b>让「我们的 8 条金属线」在进度界面里的上下次序真正固定</b>（bgfix5，2026-10-08）。
 *
 * <h2>为什么不这样做就永远定不下来（源码级，1.21.1）</h2>
 * <ol>
 *   <li>{@code AdvancementNode#children()}（{@code AdvancementNode.java:50-52}）返回的
 *       {@code Iterable} 背后是一个 <b>{@code ReferenceOpenHashSet}</b>（同文件 {@code :12}）——
 *       <b>不是有序集合</b>，迭代序 = 对象身份哈希的槽位顺序 ⇒ <b>同一份数据每次 JVM 运行都不同</b>；</li>
 *   <li>{@code TreeNodePosition} 的构造器（{@code TreeNodePosition.java:37}）按
 *       {@code node.children()} 的<b>迭代顺序</b>把兄弟节点串成 {@code previousSibling} 链，
 *       {@code firstWalk} 里 {@code y = previousSibling.y + 1} ⇒ <b>纵向次序 = 那个哈希集合的槽位顺序</b>；</li>
 *   <li>位置只在<b>服务端</b>算一次（{@code ServerAdvancementManager.java:58-65} 的 {@code TreeNodePosition.run}），
 *       再经 {@code DisplayInfo.STREAM_CODEC}（{@code :127-128} 写、{@code :141} 读）同步给客户端
 *       ⇒ 改 JSON / 文件名 / 生成顺序<b>全都没用</b>；</li>
 *   <li>而且 <b>JSON 里根本没有排序位可用</b>：{@code DisplayInfo.CODEC}（{@code DisplayInfo.java:15-27}）
 *       只认 {@code icon / title / description / background / frame / show_toast / announce_to_chat / hidden}，
 *       {@code x} / {@code y} 是私有字段且只由 {@code setLocation} 写。
 *       ⇒ <b>要真固定只有注入原版这一条路</b>（见 {@code mixin/AdvancementNodeChildrenOrderMixin}）。</li>
 * </ol>
 *
 * <h2>范围（硬要求：不许动原版成就树，也不许动我们自己的其它兄弟组）</h2>
 * <p>排序<b>只在父节点恰好是</b> {@link #GUARDED_PARENT_ID}（{@code bettergold:treasure/any_core_material}，
 * 即 8 条金属线的共同父节点）时生效；其它任何父节点（原版、别的模组、以及本模组的
 * {@code bettergold:root} / {@code metal/sturdygold/weapon} / {@code agriculture/gold_infused_dirt}）
 * <b>原样返回同一个 {@code Iterable} 实例</b> ⇒ 那些树的迭代序一个字节都不变。</p>
 *
 * <h2>排序键：从唯一真源派生，<b>不新写第二份 8 族列表</b></h2>
 * <p>位次直接取 {@link CreativeSections#METAL_ORDER} 的下标。为了从"孩子节点"认出它是哪一族，
 * 这里沿数据本身走一步：8 条线的孩子是各族的<b>核心材料</b>节点（{@code bettergold:treasure/blazing_rod} 之类，
 * id 里不含族名），而它的孩子里有 {@code bettergold:metal/<族>/ingot}
 * （例如 {@code treasure/blazing_rod → metal/flamegold/ingot}）——族名从那里取。
 * ⇒ <b>族 ↔ 节点 的对应关系只存在于数据里</b>，本类与 mixin 里没有任何族名字面量。</p>
 * <p>非族节点（本仓实际存在的是 {@code bettergold:treasure/any_raw_metal}）取
 * {@code METAL_ORDER.size()} ⇒ 恒排在这 8 条线<b>之后</b>；同一位次再按 {@code ns:path} 字典序兜底
 * ⇒ 得到一个<b>全序</b>（与哈希迭代序无关，重复运行完全一致）。</p>
 *
 * <p>⚠ 本类不注册任何东西、不持有状态、只读入参；{@link #order} 在守卫不匹配时
 * <b>返回传入的那个对象本身</b>（不复制、不包装）。</p>
 */
public final class AdvancementTreeOrder {

    /**
     * 唯一被重排的父节点：8 条金属线的共同父节点
     * （{@code data/bettergold/advancement/treasure/any_core_material.json}，它的 9 个孩子 =
     * 8 族的核心材料节点 + {@code any_raw_metal}）。
     */
    public static final String GUARDED_PARENT_ID = "bettergold:treasure/any_core_material";

    private static final ResourceLocation GUARDED_PARENT = ResourceLocation.parse(GUARDED_PARENT_ID);
    private static final String NS = "bettergold";
    private static final String METAL_PATH_PREFIX = "metal/";
    private static final String INGOT_PATH_SUFFIX = "/ingot";

    private AdvancementTreeOrder() {
    }

    /** 这个父节点是不是唯一的白名单父节点（守卫的<b>全等</b>判定，不是命名空间前缀，也不是正则）。 */
    public static boolean isGuardedParent(ResourceLocation parentId) {
        return GUARDED_PARENT.equals(parentId);
    }

    /**
     * {@code AdvancementNode#children()} 的返回值经此转手：白名单父节点 ⇒ 返回按彩虹序排好的列表；
     * 其它一切父节点 ⇒ <b>原样返回同一个实例</b>。
     *
     * @param parentId 调用 {@code children()} 的那个节点的 id
     * @param original 原版返回值
     */
    public static Iterable<AdvancementNode> order(ResourceLocation parentId, Iterable<AdvancementNode> original) {
        if (!isGuardedParent(parentId)) {
            return original;
        }
        List<AdvancementNode> sorted = new ArrayList<>();
        for (AdvancementNode child : original) {
            sorted.add(child);
        }
        sorted.sort(Comparator.comparingInt(AdvancementTreeOrder::rankOf)
                .thenComparing(node -> node.holder().id().toString()));
        return sorted;
    }

    /**
     * 一个"线的起点"节点（= 白名单父节点的孩子）的位次。
     *
     * @return 族在 {@link CreativeSections#METAL_ORDER} 里的下标；
     *         认不出族（非族节点）时返回 {@code METAL_ORDER.size()}（恒排最后）
     */
    public static int rankOf(AdvancementNode node) {
        int best = Integer.MAX_VALUE;
        for (AdvancementNode child : node.children()) {
            ResourceLocation id = child.holder().id();
            if (!NS.equals(id.getNamespace())) {
                continue;
            }
            String path = id.getPath();
            if (path.startsWith(METAL_PATH_PREFIX) && path.endsWith(INGOT_PATH_SUFFIX)) {
                String family = path.substring(METAL_PATH_PREFIX.length(), path.length() - INGOT_PATH_SUFFIX.length());
                int index = CreativeSections.METAL_ORDER.indexOf(family);
                if (index >= 0 && index < best) {
                    best = index;
                }
            }
        }
        return best == Integer.MAX_VALUE ? CreativeSections.METAL_ORDER.size() : best;
    }
}
