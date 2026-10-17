package com.hjmmd_8.bettergold.event;

import com.hjmmd_8.bettergold.registry.AllBlocks;
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

        // 3. 高精度炼金油（1.7 轮5，bg-n10r5）：炼金燃油（基底） + 金火把花（引子） → 高精度炼金油
        // 作者原话：「在酿造台上以炼金燃油为基、以金火把花为引即可酿制成高精度炼金油」。
        // 依据（为什么不另造一条 Potion）：
        //   ① 作者点名的就是**酿造台**（立档 §4 ⑩a 裁定走酿造台）；
        //   ② `alchemic_fuel` 在本仓是**物品**、不是药水；而 NeoForge 的酿造接口
        //      （`IBrewingRecipe` / `RegisterBrewingRecipesEvent#getBuilder`）**允许任意物品当基底**——
        //      本类上面两条热可可就是「玻璃瓶（基底）+ 材料」，同一条路。
        //   ③ 所以「以燃油为基」= 基底槽放 1 个炼金燃油，**不需要**为它再定义一种 Potion；
        //      立档 ⑩a 里担心的"必须有一条药水"只在原版 `PotionBrewing` 上成立，NeoForge 已放开。
        builder.addRecipe(
                Ingredient.of(AllItems.ALCHEMIC_FUEL.get()),
                Ingredient.of(AllBlocks.GOLDEN_TORCHFLOWER.get().asItem()),
                new ItemStack(AllItems.REFINED_ALCHEMIC_OIL.get()));
    }
}
