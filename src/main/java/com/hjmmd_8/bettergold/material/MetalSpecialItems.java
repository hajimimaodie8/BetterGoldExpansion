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

    /** 触发静态初始化 */
    public static void bootstrap() {
    }

    private MetalSpecialItems() {
    }
}
