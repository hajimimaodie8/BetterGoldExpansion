package com.hjmmd_8.bettergold.event;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.neoforged.neoforge.event.brewing.RegisterBrewingRecipesEvent;

/**
 * 酿造配方注册（NeoForge 支持任意物品作为酿造基底/材料）。
 *
 * 热可可酿造（万坚金食物本身直接提供强化效果，不再通过酿造升级药水）：
 * 1. 金酿热可可：玻璃瓶（基底） + 金钱巧克力棒（材料） → 金酿热可可
 * 2. 万坚金酿热可可：玻璃瓶（基底） + 万坚金巧克力棒（材料） → 万坚金酿热可可（16 分钟抗寒）
 *    —— 新约 1.2 起不再需要先用金酿热可可做基底，玻璃瓶直接酿。
 */
public class ModBrewing {

    public static void registerBrewingRecipes(RegisterBrewingRecipesEvent event) {
        var builder = event.getBuilder();

        // 1. 金酿热可可：玻璃瓶（基底） + 金钱巧克力棒（材料） → 金酿热可可
        builder.addRecipe(
                Ingredient.of(Items.GLASS_BOTTLE),
                Ingredient.of(AllItems.GOLDEN_CHOCOLATE_BAR.get()),
                new ItemStack(AllItems.BREWED_HOT_COCOA.get()));

        // 2. 万坚金酿热可可：玻璃瓶（基底） + 万坚金巧克力棒（材料） → 万坚金酿热可可
        builder.addRecipe(
                Ingredient.of(Items.GLASS_BOTTLE),
                Ingredient.of(AllItems.STURDYGOLD_CHOCOLATE_BAR.get()),
                new ItemStack(AllItems.STURDYGOLD_BREWED_HOT_COCOA.get()));
    }
}
