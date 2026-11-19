package com.hjmmd_8.bettergold.recipe;

import com.hjmmd_8.bettergold.material.RingItems;
import com.hjmmd_8.bettergold.registry.AllRecipes;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

/**
 * 转化之戒的「合成表内转化」（1.8 阶段 3 段 C，§I-38 点金 / 冰霜 / 水压三条的「合成表里也能转」）。
 *
 * <h2>读法（本轮的判断点）</h2>
 * <p>作者原文是「<b>合成表里</b>也能转（<b>不消耗戒指</b>）」「水桶→冰块（<b>不消耗铁桶与戒指</b>）」
 * 「给玻璃瓶与铁桶灌水（<b>不消耗戒指</b>）」—— 主语是**工作台格子里的那枚戒指**，
 * 所以本配方 = <b>戒指 + 一件输入 → 一件产物</b>，戒指按"剩余物"原样退回（与金钱贝模具
 * 那套 {@code getRemainingItems} 同一写法）。它<b>不需要玩家戴着戒指</b>，也不查任何玩家状态
 * （{@code Recipe#matches} 拿不到玩家，这一点是源码级硬约束）。</p>
 *
 * <h2>六条配方</h2>
 * <ul>
 *   <li>点金：粗铜 / 粗铁 / 金粒 → <b>粗金</b>（3 条）；</li>
 *   <li>冰霜：水桶 → 冰块（铁桶按原版 craftRemainder 退回）；</li>
 *   <li>水压：玻璃瓶 → 水瓶、铁桶 → 水桶（玻璃瓶被消耗，与"灌水"一致）。</li>
 * </ul>
 *
 * <p>⚠ 与 {@code GoldenCowrieMoldRecipe}（{@code SimpleCraftingRecipeSerializer}）的区别：
 * 那个类的数据是<b>构造参数</b>、客户端按 category 重建（所以踩过 JEI 显示错材料的坑）；
 * 本类有 6 条<b>数据驱动</b>的配方 ⇒ 自带完整 {@code MapCodec} + {@code StreamCodec}，
 * 客户端重建出来的实例与服务器逐字段一致。</p>
 */
public class RingConversionRecipe extends CustomRecipe {

    /** 配方里的戒指（必须是转化之戒之一） */
    public final Item ring;
    /** 被转化 / 被灌水的那一件 */
    public final Ingredient ingredient;
    /** 产物 */
    public final ItemStack result;

    public RingConversionRecipe(CraftingBookCategory category, Item ring, Ingredient ingredient,
            ItemStack result) {
        super(category);
        this.ring = ring;
        this.ingredient = ingredient;
        this.result = result;
    }

    /**
     * ⭐ 1.21.1 的 {@code RecipeSerializer#codec()} 要的是 <b>{@code MapCodec<T>}</b>
     * （读源码：{@code RecipeSerializer.java} 的抽象方法是 {@code MapCodec<T> codec()}）⇒
     * 必须用 {@code RecordCodecBuilder.mapCodec(...)}；写成 {@code .create(...)} 会得到
     * {@code Codec<T>}，编译期「无法转换为 MapCodec」。
     */
    public static final MapCodec<RingConversionRecipe> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            CraftingBookCategory.CODEC.optionalFieldOf("category", CraftingBookCategory.MISC)
                    .forGetter(recipe -> recipe.category()),
            BuiltInRegistries.ITEM.byNameCodec().fieldOf("ring").forGetter(recipe -> recipe.ring),
            Ingredient.CODEC_NONEMPTY.fieldOf("ingredient").forGetter(recipe -> recipe.ingredient),
            ItemStack.CODEC.fieldOf("result").forGetter(recipe -> recipe.result))
            .apply(instance, RingConversionRecipe::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, RingConversionRecipe> STREAM_CODEC =
            StreamCodec.composite(
                    ItemStack.OPTIONAL_STREAM_CODEC, recipe -> new ItemStack(recipe.ring),
                    Ingredient.CONTENTS_STREAM_CODEC, recipe -> recipe.ingredient,
                    ItemStack.OPTIONAL_STREAM_CODEC, recipe -> recipe.result,
                    (ringStack, ingredient, result) -> new RingConversionRecipe(
                            CraftingBookCategory.MISC, ringStack.getItem(), ingredient, result));

    @Override
    public boolean matches(CraftingInput input, Level level) {
        boolean hasRing = false;
        boolean hasIngredient = false;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(this.ring) && !hasRing) {
                hasRing = true;
            } else if (this.ingredient.test(stack) && !hasIngredient) {
                hasIngredient = true;
            } else {
                return false;
            }
        }
        return hasRing && hasIngredient;
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 2;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return this.result.copy();
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return this.result.copy();
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY, Ingredient.of(this.ring), this.ingredient);
    }

    /** 戒指原样退回；输入那一件按原版 craftRemainder 退（水桶 → 空桶，玻璃瓶 → 无） */
    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.is(this.ring)) {
                remaining.set(i, stack.copy());            // ← 「不消耗戒指」
            } else if (stack.hasCraftingRemainingItem()) {
                remaining.set(i, stack.getCraftingRemainingItem());
            }
        }
        return remaining;
    }

    /** 允许在配方书里出现（默认 CustomRecipe 是特殊配方） */
    @Override
    public boolean isSpecial() {
        return false;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return AllRecipes.RING_CONVERSION.get();
    }

    /** 序列化器（唯一实现，注册在 {@code AllRecipes#RING_CONVERSION}） */
    public static final class Serializer implements RecipeSerializer<RingConversionRecipe> {

        @Override
        public MapCodec<RingConversionRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, RingConversionRecipe> streamCodec() {
            return STREAM_CODEC;
        }
    }

    /** 探针 / 关卡用：这枚物品是不是转化之戒（配方里的戒指一栏必须都是它） */
    public static boolean isRingItem(Item item) {
        return item == RingItems.BLANK.get() || RingItems.all().stream().anyMatch(r -> r.get() == item);
    }
}
