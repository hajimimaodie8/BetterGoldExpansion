package com.hjmmd_8.bettergold.api;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;

/**
 * 公开给外部模组 / 附属数据包使用的标签接口。
 *
 * <h2>为什么要用标签而不是写死物品</h2>
 * 本模组后续会加入 16 种新的建材（及其门、砖块等）。如果每种材料的"锭 / 粒 / 块"都要
 * 一个个手写进原版和通用标签，工作量会爆炸。这里的做法是：
 * <b>本模组先定义自己的"材料家族"标签，再由它们桥接进原版 / 通用标签</b>——
 * 于是"加入一个标签 = 同时加入其他所有相关标签"。
 *
 * <pre>
 * 把物品加进 #bettergold:ingots  →  自动成为
 *     #c:ingots                       （NeoForge 通用标签）
 *     #minecraft:beacon_payment_items （可给信标付款）
 * 把方块加进 #bettergold:storage_blocks  →  自动成为
 *     #c:storage_blocks（物品 + 方块）
 *     #minecraft:mineable/pickaxe
 * </pre>
 *
 * 其它模组想让自己的物品被本模组当作"锭"来用时，只要在自己的数据包里
 * <pre>{@code
 * { "replace": false, "values": [ "你的模组:某锭" ] }
 * }</pre>
 * 写进 {@code data/bettergold/tags/item/ingots.json} 即可，不需要改本模组的代码。
 *
 * <h2>装备类要注意</h2>
 * 1.21 的附魔台只提供"物品所在标签允许"的附魔（{@code #minecraft:enchantable/*} 由
 * {@code #minecraft:swords}、{@code #minecraft:pickaxes} 等类别标签拼出来）。
 * 所以新工具必须加进对应的类别标签，否则<b>没法附魔</b>；盔甲则要加进
 * {@code head/chest/leg/foot_armor}（同时也是盔甲纹饰的前提）。
 */
public final class BetterGoldTags {

    // ==================== 材料家族（本模组自己的标签） ====================

    /** 本模组所有"锭" */
    public static final TagKey<Item> INGOTS = item("ingots");
    /** 本模组所有"粒" */
    public static final TagKey<Item> NUGGETS = item("nuggets");
    /** 本模组所有"原材料"（粗矿之类） */
    public static final TagKey<Item> RAW_MATERIALS = item("raw_materials");
    /** 本模组所有"材料块"（物品形式） */
    public static final TagKey<Item> STORAGE_BLOCKS = item("storage_blocks");
    /** 本模组所有"材料块"（方块形式） */
    public static final TagKey<Block> STORAGE_BLOCKS_BLOCK = block("storage_blocks");

    // ==================== 便捷判定（外部模组可直接调用） ====================

    public static boolean isIngot(ItemStack stack) {
        return stack.is(INGOTS);
    }

    public static boolean isNugget(ItemStack stack) {
        return stack.is(NUGGETS);
    }

    public static boolean isRawMaterial(ItemStack stack) {
        return stack.is(RAW_MATERIALS);
    }

    public static boolean isStorageBlock(ItemStack stack) {
        return stack.is(STORAGE_BLOCKS);
    }

    public static boolean isStorageBlock(Block block) {
        return block.builtInRegistryHolder().is(STORAGE_BLOCKS_BLOCK);
    }

    private static TagKey<Item> item(String path) {
        return TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("bettergold", path));
    }

    private static TagKey<Block> block(String path) {
        return TagKey.create(Registries.BLOCK, ResourceLocation.fromNamespaceAndPath("bettergold", path));
    }

    private BetterGoldTags() {
    }
}
