package com.hjmmd_8.bettergold.recipe;

import com.hjmmd_8.bettergold.registry.AllItems;
import com.hjmmd_8.bettergold.registry.AllRecipes;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

/**
 * 金蜂蜜曲奇：1 蜂蜜瓶 + 2 金麦 无序 → 8 金蜂蜜曲奇，返还 1 玻璃瓶。
 * 1.21.1 的 Ingredient 不支持 remainder，蜂蜜瓶（craftRemainder 为空）必须用自定义配方返还空瓶。
 */
public class GoldenHoneyCookieRecipe extends CustomRecipe {

    public GoldenHoneyCookieRecipe(CraftingBookCategory category) {
        super(category);
    }

    @Override
    public boolean isSpecial() {
        return false;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(Items.HONEY_BOTTLE),
                Ingredient.of(AllItems.GOLDEN_WHEAT.get()),
                Ingredient.of(AllItems.GOLDEN_WHEAT.get()));
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 2;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        boolean hasHoney = false;
        int wheatCount = 0;
        boolean hasOther = false;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(Items.HONEY_BOTTLE)) {
                hasHoney = true;
            } else if (stack.is(AllItems.GOLDEN_WHEAT.get())) {
                wheatCount++;
            } else {
                hasOther = true;
            }
        }
        return hasHoney && wheatCount == 2 && !hasOther;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(AllItems.GOLDEN_HONEY_COOKIE.get(), 8);
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(AllItems.GOLDEN_HONEY_COOKIE.get(), 8);
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            // 蜂蜜瓶 → 空玻璃瓶返还
            if (input.getItem(i).is(Items.HONEY_BOTTLE)) {
                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE));
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return AllRecipes.GOLDEN_HONEY_COOKIE_RECIPE.get();
    }
}
