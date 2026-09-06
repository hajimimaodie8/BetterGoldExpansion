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
 * 金馅饼酥皮：3x3 有序——中心奶瓶、左右下各 1 金麦（共 3 金麦）。
 * 奶瓶（farmersdelight:milk_bottle 或原版奶桶均视为奶源）用完后返还 1 玻璃瓶。
 * 属于 FD 联动分支（酥皮是 FD 物品 {@link FdItems#GOLDEN_PIE_CRUST}）。
 */
public class PieCrustRecipe extends CustomRecipe {

    public PieCrustRecipe(CraftingBookCategory category) {
        super(category);
    }

    @Override
    public boolean isSpecial() {
        return false;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(net.minecraft.tags.ItemTags.create(
                        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("bettergold", "drinks/milk"))),
                Ingredient.of(AllItems.GOLDEN_WHEAT.get()));
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width >= 3 && height >= 3;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        // 只支持 3x3 网格
        if (input.width() != 3 || input.height() != 3) {
            return false;
        }
        // 中心(1,1)=奶；左(0,1)右(2,1)下(1,2)=金麦；其余必须为空
        int[] milk = {1, 1};
        int[][] wheats = {{0, 1}, {2, 1}, {1, 2}};
        if (!isMilk(input.getItem(1 * 3 + 1))) {
            return false;
        }
        for (int[] w : wheats) {
            if (!input.getItem(w[1] * 3 + w[0]).is(AllItems.GOLDEN_WHEAT.get())) {
                return false;
            }
        }
        // 其余 5 格必须为空
        for (int y = 0; y < 3; y++) {
            for (int x = 0; x < 3; x++) {
                boolean isMilkCell = x == 1 && y == 1;
                boolean isWheatCell = (x == 0 && y == 1) || (x == 2 && y == 1) || (x == 1 && y == 2);
                if (!isMilkCell && !isWheatCell && !input.getItem(y * 3 + x).isEmpty()) {
                    return false;
                }
            }
        }
        return true;
    }

    private static boolean isMilk(ItemStack stack) {
        return stack.is(net.minecraft.tags.ItemTags.create(
                net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("bettergold", "drinks/milk")));
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(FdItems.GOLDEN_PIE_CRUST.get());
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(FdItems.GOLDEN_PIE_CRUST.get());
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            // 奶源（奶瓶/奶桶）用完后给回玻璃瓶
            if (isMilk(stack)) {
                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE));
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return FdRecipes.GOLDEN_PIE_CRUST_RECIPE.get();
    }
}
