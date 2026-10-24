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
 * 金钱贝模具配方：模具（未损坏）+ 1 个「兑换物」 → 1 金钱贝，模具耐久 -1。
 * 模具耐久耗尽（64）后消失。
 *
 * <p><b>兑换物</b>：默认 = <b>金锭</b>（1.4 起的既有口径，{@code golden_cowrie_from_mold.json} 一字不改）；
 * 1.7 作者 2026-10-24 第 ③ 条起多一条 <b>金钱茄</b>版
 * （{@code golden_cowrie_from_mold_money_eggplant.json}，注册在
 * {@code AllRecipes#GOLDEN_COWRIE_MOLD_MONEY_EGGPLANT_RECIPE}）—— 两条配方<b>同一个类、不同构造参数</b>，
 * 所以「模具每合一次 −1 耐久 / 耗尽消失 / 产物恒 1 个金钱贝」的语义只有一份实现。</p>
 */
public class GoldenCowrieMoldRecipe extends CustomRecipe {

    /** 兑换物（与模具搭配的那一件）：默认金锭；金钱茄版 = {@code bettergold:golden_eggplant} */
    private final net.minecraft.world.item.Item catalyst;

    public GoldenCowrieMoldRecipe(CraftingBookCategory category) {
        this(category, Items.GOLD_INGOT);
    }

    public GoldenCowrieMoldRecipe(CraftingBookCategory category, net.minecraft.world.item.Item catalyst) {
        super(category);
        this.catalyst = catalyst;
    }

    /** 兑换物（探针 / 调试用） */
    public net.minecraft.world.item.Item catalyst() {
        return this.catalyst;
    }

    /** 允许在配方书中显示（默认 CustomRecipe 是特殊配方，不出现在配方书） */
    @Override
    public boolean isSpecial() {
        return false;
    }

    /** 提供输入物品列表，供 JEI/配方书展示 */
    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(AllItems.GOLDEN_COWRIE_MOLD.get()), // 金钱贝模具
                Ingredient.of(this.catalyst)                      // 金锭（默认）/ 金钱茄（1.7 第 ③ 条）
        );
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 2;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        boolean hasMold = false;
        boolean hasCatalyst = false;
        boolean hasOther = false;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(AllItems.GOLDEN_COWRIE_MOLD.get()) && stack.getDamageValue() < stack.getMaxDamage()) {
                hasMold = true;
            } else if (stack.is(this.catalyst)) {
                hasCatalyst = true;
            } else {
                hasOther = true;
            }
        }
        return hasMold && hasCatalyst && !hasOther;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(AllItems.GOLDEN_COWRIE.get());
    }

    /** 提供输出物品，供 JEI/配方书展示（CustomRecipe 默认返回空） */
    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(AllItems.GOLDEN_COWRIE.get());
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.is(AllItems.GOLDEN_COWRIE_MOLD.get())) {
                ItemStack worn = stack.copy();
                worn.setDamageValue(worn.getDamageValue() + 1);
                if (worn.getDamageValue() >= worn.getMaxDamage()) {
                    remaining.set(i, ItemStack.EMPTY); // 模具耐久耗尽
                } else {
                    remaining.set(i, worn);            // 模具耐久 -1 后返还
                }
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return AllRecipes.GOLDEN_COWRIE_MOLD_RECIPE.get();
    }
}
