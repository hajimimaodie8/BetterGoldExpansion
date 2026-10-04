package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 各套新金属的专属材料。
 *
 * <ul>
 *   <li>高燃烈焰棒（blazing_rod）：1 火药 + 8 烈焰棒合成，烈燃金原料的主材料。</li>
 *   <li>巫毒羽毛（voodoo_feather）：女巫 6% 掉落（受抢夺影响），
 *       1 羽毛 + 1 发酵蜘蛛眼 + 1 哭泣黑曜石 可复制出 2 个。</li>
 *   <li>聚紫能晶尘（amethyst_energy_dust）：4 紫水晶簇 + 4 红石粉 + 1 砂轮无序合成，
 *       合成后返还砂轮。</li>
 *   <li>靛蓝海洋之心（indigo_ocean_heart，1.5 靛海金）：中心 1 海洋之心 + 上下左右各 1 青金石块（共 4）。
 *       命名法对齐原版 {@code heart_of_the_sea}。</li>
 *   <li>紫颂樱花枝（chorus_cherry_branch，1.5 幻惑金）：1 紫颂花 + 8 樱花树苗。
 *       紫颂 = {@code chorus}（沿用原版 {@code chorus_flower}）、樱花 = {@code cherry}、枝 = {@code branch}。</li>
 * </ul>
 */
public final class MetalSpecialItems {

    public static final DeferredItem<Item> BLAZING_ROD = AllItems.ITEMS.registerSimpleItem("blazing_rod",
            new Item.Properties().fireResistant());

    public static final DeferredItem<Item> VOODOO_FEATHER = AllItems.ITEMS.registerSimpleItem("voodoo_feather",
            new Item.Properties());

    public static final DeferredItem<Item> AMETHYST_ENERGY_DUST = AllItems.ITEMS.registerSimpleItem(
            "amethyst_energy_dust", new Item.Properties());

    /** 靛蓝海洋之心：靛海金原料配方里的主材料（1.5） */
    public static final DeferredItem<Item> INDIGO_OCEAN_HEART = AllItems.ITEMS.registerSimpleItem(
            "indigo_ocean_heart", new Item.Properties());

    /** 紫颂樱花枝：幻惑金原料配方里的主材料（1.5） */
    public static final DeferredItem<Item> CHORUS_CHERRY_BRANCH = AllItems.ITEMS.registerSimpleItem(
            "chorus_cherry_branch", new Item.Properties());

    /**
     * 闪耀藤条：树棘金原料配方里的主材料（1.6）。
     *
     * <p><b>它是掉落物，不是合成物</b>：用本模组任意金属族的器具 / 五类武器破坏
     * {@code #minecraft:leaves} 或 {@code minecraft:vine} 时按概率掉落
     * （落点 = 全局战利品修改器 {@code bettergold:add_glittering_vine}，见
     * {@code AllLootModifiers.AddGlitteringVineModifier}；概率 {@code 0.06 + 0.06 × 时运等级}）。</p>
     *
     * <p>可堆肥（65% 加一层）走的是 NeoForge 的**数据地图**
     * {@code neoforge:compostables}（{@code data/neoforge/data_maps/item/compostables.json}）——
     * 1.21.1 的 {@code Item.Properties} 没有 {@code compostable(...)}，
     * 而 {@code ComposterBlock.COMPOSTABLES} 已被 Neo 标注为 deprecated 且被数据地图取代。</p>
     *
     * <p>⚠ <b>文件路径的命名空间就是数据地图 id 的一部分</b>：{@code data/<ns>/data_maps/<registry>/<path>.json}
     * ⇒ {@code <ns>:<path>}。读它的是 {@code ComposterBlock#getValue}，读的正是 **{@code neoforge:compostables}**
     * 这一张；写成 {@code data/bettergold/...} 会注册出一个从未注册过的 {@code bettergold:compostables}，
     * 整条被**静默丢弃**（不报错、不崩、`runData` 与静态关卡全绿，只是堆肥桶里那 65% 永远读不到）。
     * 本条由 bg-16 收口轮实机抓出并改正（{@code docs/bg16-证据/13}）。</p>
     */
    public static final DeferredItem<Item> GLITTERING_VINE = AllItems.ITEMS.registerSimpleItem(
            "glittering_vine", new Item.Properties());

    /**
     * 集束回响碎片：幽咆金原料配方里的主材料（1.6）。
     *
     * <p>3×3 有序合成：<b>中心 1 幽匿脉络（{@code minecraft:sculk_vein}）、外圈 8 回响碎片
     * （{@code minecraft:echo_shard}）</b> ⇒ 1 个（作者原话「1 幽匿脉络围上 8 回响碎片」）。</p>
     */
    public static final DeferredItem<Item> BUNDLED_ECHO_SHARD = AllItems.ITEMS.registerSimpleItem(
            "bundled_echo_shard", new Item.Properties());

    /** 触发静态初始化 */
    public static void bootstrap() {
    }

    private MetalSpecialItems() {
    }
}
