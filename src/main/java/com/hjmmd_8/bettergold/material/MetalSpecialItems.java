package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 三套新金属的专属材料（新约 1.4）。
 *
 * <ul>
 *   <li>高燃烈焰棒（blazing_rod）：1 火药 + 8 烈焰棒合成，烈燃金原料的主材料。</li>
 *   <li>巫毒羽毛（voodoo_feather）：女巫 6% 掉落（受抢夺影响），
 *       1 羽毛 + 1 发酵蜘蛛眼 + 1 哭泣黑曜石 可复制出 2 个。</li>
 *   <li>聚紫能晶尘（amethyst_energy_dust）：4 紫水晶簇 + 4 红石粉 + 1 砂轮无序合成，
 *       合成后返还砂轮。</li>
 * </ul>
 */
public final class MetalSpecialItems {

    public static final DeferredItem<Item> BLAZING_ROD = AllItems.ITEMS.registerSimpleItem("blazing_rod",
            new Item.Properties().fireResistant());

    public static final DeferredItem<Item> VOODOO_FEATHER = AllItems.ITEMS.registerSimpleItem("voodoo_feather",
            new Item.Properties());

    public static final DeferredItem<Item> AMETHYST_ENERGY_DUST = AllItems.ITEMS.registerSimpleItem(
            "amethyst_energy_dust", new Item.Properties());

    /** 触发静态初始化 */
    public static void bootstrap() {
    }

    private MetalSpecialItems() {
    }
}
