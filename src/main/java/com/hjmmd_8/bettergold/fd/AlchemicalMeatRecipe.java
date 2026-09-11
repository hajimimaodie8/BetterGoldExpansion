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
 * 炼金贝肉加工配方（炼金贝肉串 / 炼金贝肉三明治）。
 *
 * 炼金贝肉是"包着金钱贝"的食物（食用时返还金钱贝）；用它合成时同样必须返还金钱贝，
 * 否则贝肉里那颗金钱贝会被合成吞掉。因此本配方用自定义实现，在 getRemainingItems 里
 * 把炼金贝肉所在格子替换为 1 个金钱贝。
 *
 * type 0 = 炼金贝肉串：2 木棍 + 金胡萝卜 + 金钱茄 + 炼金贝肉 → 2 串
 * type 1 = 炼金贝肉三明治：金砖面包 + 炼金贝肉 → 1 个
 */
public class AlchemicalMeatRecipe extends CustomRecipe {

    private final int type;

    public AlchemicalMeatRecipe(CraftingBookCategory category) {
        this(category, 0);
    }

    public AlchemicalMeatRecipe(CraftingBookCategory category, int type) {
        super(category);
        this.type = type;
    }

    @Override
    public boolean isSpecial() {
        return false;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        if (type == 0) {
            return NonNullList.of(Ingredient.EMPTY,
                    Ingredient.of(Items.STICK),
                    Ingredient.of(Items.STICK),
                    Ingredient.of(Items.GOLDEN_CARROT),
                    Ingredient.of(AllItems.GOLDEN_EGGPLANT.get()),
                    Ingredient.of(FdItems.ALCHEMICAL_MEAT.get()));
        }
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(AllItems.GOLDEN_BREAD.get()),
                Ingredient.of(FdItems.ALCHEMICAL_MEAT.get()));
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= (type == 0 ? 5 : 2);
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        int sticks = 0;
        int carrots = 0;
        int eggplants = 0;
        int breads = 0;
        int meats = 0;
        int others = 0;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(FdItems.ALCHEMICAL_MEAT.get())) {
                meats++;
            } else if (type == 0 && stack.is(Items.STICK)) {
                sticks++;
            } else if (type == 0 && stack.is(Items.GOLDEN_CARROT)) {
                carrots++;
            } else if (type == 0 && stack.is(AllItems.GOLDEN_EGGPLANT.get())) {
                eggplants++;
            } else if (type == 1 && stack.is(AllItems.GOLDEN_BREAD.get())) {
                breads++;
            } else {
                others++;
            }
        }
        if (others > 0 || meats != 1) {
            return false;
        }
        return type == 0 ? (sticks == 2 && carrots == 1 && eggplants == 1) : (breads == 1);
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(resultItem(), type == 0 ? 2 : 1);
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(resultItem(), type == 0 ? 2 : 1);
    }

    private net.minecraft.world.item.Item resultItem() {
        return type == 0 ? FdItems.ALCHEMICAL_MEAT_SKEWER.get() : FdItems.ALCHEMICAL_MEAT_SANDWICH.get();
    }

    /** 关键：把炼金贝肉所在的格子返还为金钱贝（不吞掉里面的贝） */
    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            if (input.getItem(i).is(FdItems.ALCHEMICAL_MEAT.get())) {
                remaining.set(i, new ItemStack(AllItems.GOLDEN_COWRIE.get()));
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return type == 0
                ? FdRecipes.ALCHEMICAL_MEAT_SKEWER_RECIPE.get()
                : FdRecipes.ALCHEMICAL_MEAT_SANDWICH_RECIPE.get();
    }
}
