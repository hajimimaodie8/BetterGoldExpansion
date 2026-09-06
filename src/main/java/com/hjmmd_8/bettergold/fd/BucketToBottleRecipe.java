package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.registry.AllItems;

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
 * 桶装热可可分装：1 桶装金酿热可可（万坚金桶装）+ 3 玻璃瓶 → 3 瓶装热可可，返还 1 铁桶。
 * type 0 = 金桶装→金瓶（瓶装属本体物品 AllItems.BREWED_HOT_COCOA）；
 * type 1 = 万坚金桶装→万坚金瓶（瓶装本体 AllItems.STURDYGOLD_BREWED_HOT_COCOA）。
 * 1.21.1 无 Ingredient remainder，铁桶返还需自定义配方。
 * 桶装是 FD 物品（FdItems），故本配方属于 FD 联动分支。
 */
public class BucketToBottleRecipe extends CustomRecipe {

    private final int type;

    public BucketToBottleRecipe(CraftingBookCategory category) {
        this(category, 0);
    }

    public BucketToBottleRecipe(CraftingBookCategory category, int type) {
        super(category);
        this.type = type;
    }

    @Override
    public boolean isSpecial() {
        return false;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(type == 0
                        ? FdItems.BREWED_HOT_COCOA_BUCKET.get()
                        : FdItems.STURDYGOLD_BREWED_HOT_COCOA_BUCKET.get()),
                Ingredient.of(Items.GLASS_BOTTLE));
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 3;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        boolean hasBucket = false;
        int bottles = 0;
        boolean hasOther = false;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            ItemStack bucketItem = new ItemStack(type == 0
                    ? FdItems.BREWED_HOT_COCOA_BUCKET.get()
                    : FdItems.STURDYGOLD_BREWED_HOT_COCOA_BUCKET.get());
            if (stack.is(bucketItem.getItem())) {
                hasBucket = true;
            } else if (stack.is(Items.GLASS_BOTTLE)) {
                bottles++;
            } else {
                hasOther = true;
            }
        }
        return hasBucket && bottles == 3 && !hasOther;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(type == 0 ? AllItems.BREWED_HOT_COCOA.get() : AllItems.STURDYGOLD_BREWED_HOT_COCOA.get(), 3);
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(type == 0 ? AllItems.BREWED_HOT_COCOA.get() : AllItems.STURDYGOLD_BREWED_HOT_COCOA.get(), 3);
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            // 桶装（消耗一个）→ 返还铁桶
            ItemStack bucketItem = new ItemStack(type == 0
                    ? FdItems.BREWED_HOT_COCOA_BUCKET.get()
                    : FdItems.STURDYGOLD_BREWED_HOT_COCOA_BUCKET.get());
            if (stack.is(bucketItem.getItem())) {
                remaining.set(i, new ItemStack(Items.BUCKET));
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return type == 0 ? FdRecipes.BREWED_HOT_COCOA_BUCKET_TO_BOTTLE_RECIPE.get()
                : FdRecipes.STURDYGOLD_BREWED_HOT_COCOA_BUCKET_TO_BOTTLE_RECIPE.get();
    }
}
