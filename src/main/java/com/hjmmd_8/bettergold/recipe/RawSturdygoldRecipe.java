package com.hjmmd_8.bettergold.recipe;

import java.util.Optional;
import java.util.function.Supplier;

import com.hjmmd_8.bettergold.registry.AllItems;
import com.hjmmd_8.bettergold.registry.AllRecipes;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingBookCategory;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

/**
 * 「原料」合成配方：2 混合晶石堆 + 2 红石粉 + 2 金块 + 1 下界合金锭 + 1 炼金燃油 + 1 兑换物 → 该金属的原料。
 * 炼金燃油（瓶子）在合成后返还玻璃瓶。
 *
 * <h2>1.5 修的就是这里（1.4 遗留 bug）</h2>
 *
 * <p>1.4 的实现把兑换物与产物<b>硬编码</b>成金钱贝 / {@code raw_sturdygold}（一个构造器里的 {@code int type}），
 * 于是 {@code raw_flamegold.json} / {@code raw_voodoogold.json} / {@code raw_thundergold.json}
 * 三份 JSON 虽然各有配方 id，读出来却<b>都是同一条配方</b>（序列化器字符串也一律是
 * {@code bettergold:raw_sturdygold}），三套新金属的原料<b>根本合成不出来</b>，合出来永远是万坚金原料。</p>
 *
 * <p>现在改成<b>数据驱动</b>：配方 JSON 可以带两个可选字段</p>
 *
 * <pre>{
 *   "type": "bettergold:raw_sturdygold",
 *   "exchange": "bettergold:blazing_rod",   // 兑换物（主材料），缺省 = 该序列化器的默认值
 *   "result":   "bettergold:raw_flamegold"  // 产物，缺省 = 万坚金原料
 * }</pre>
 *
 * <p><b>向后兼容</b>：两个字段都<b>可以缺省</b>，缺省时回落到该序列化器自己的默认值
 * （{@code bettergold:raw_sturdygold} → 金钱贝 / 万坚金原料；
 * {@code bettergold:raw_sturdygold_eggplant} → 金钱茄 / 万坚金原料），
 * 所以 1.4 写下的老 JSON 一字不改仍能正常加载、语义一字不变。</p>
 */
public class RawSturdygoldRecipe extends CustomRecipe {

    /** 兑换物（配方里最下面那一格的主材料） */
    private final Item exchange;
    /** 产物 */
    private final Item result;
    /** 来自哪个序列化器（0 = 金钱贝版，1 = 金钱茄版）；见 {@link #getSerializer()} */
    private final int variant;

    public RawSturdygoldRecipe(CraftingBookCategory category, Item exchange, Item result, int variant) {
        super(category);
        this.exchange = exchange;
        this.result = result;
        this.variant = variant;
    }

    /** 兑换物（探针 / 调试用） */
    public Item exchange() {
        return this.exchange;
    }

    /** 产物（探针 / 调试用） */
    public Item result() {
        return this.result;
    }

    public int variant() {
        return this.variant;
    }

    /** 允许在配方书中显示 */
    @Override
    public boolean isSpecial() {
        return false;
    }

    /** 提供输入物品列表，供 JEI/配方书展示 */
    @Override
    public NonNullList<Ingredient> getIngredients() {
        return NonNullList.of(Ingredient.EMPTY,
                Ingredient.of(AllItems.MIXED_CRYSTAL_PILE.get()),
                Ingredient.of(AllItems.MIXED_CRYSTAL_PILE.get()),
                Ingredient.of(Items.REDSTONE),
                Ingredient.of(Items.REDSTONE),
                Ingredient.of(Items.GOLD_BLOCK),
                Ingredient.of(Items.GOLD_BLOCK),
                Ingredient.of(Items.NETHERITE_INGOT),
                Ingredient.of(AllItems.ALCHEMIC_FUEL.get()),
                Ingredient.of(this.exchange)
        );
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 9;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        int crystal = 0, redstone = 0, goldBlock = 0, netherite = 0, fuel = 0, exchange = 0, other = 0;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(AllItems.MIXED_CRYSTAL_PILE.get())) crystal++;
            else if (stack.is(Items.REDSTONE)) redstone++;
            else if (stack.is(Items.GOLD_BLOCK)) goldBlock++;
            else if (stack.is(Items.NETHERITE_INGOT)) netherite++;
            else if (stack.is(AllItems.ALCHEMIC_FUEL.get())) fuel++;
            else if (stack.is(this.exchange)) exchange++;
            else other++;
        }
        return crystal == 2 && redstone == 2 && goldBlock == 2 && netherite == 1 && fuel == 1 && exchange == 1 && other == 0;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(this.result);
    }

    /** 提供输出物品，供 JEI/配方书展示（CustomRecipe 默认返回空） */
    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(this.result);
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.is(AllItems.ALCHEMIC_FUEL.get())) {
                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE)); // 返还玻璃瓶
            }
        }
        return remaining;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return this.variant == 1 ? AllRecipes.RAW_STURDYGOLD_EGGPLANT_RECIPE.get()
                : AllRecipes.RAW_STURDYGOLD_RECIPE.get();
    }

    /**
     * 本配方的序列化器：读 {@code category} / {@code exchange} / {@code result} 三个字段。
     *
     * <p>{@code exchange} 与 {@code result} 都是<b>可选</b>字段（一个物品 id 字符串），
     * 缺省时用构造器传进来的默认值兜底 —— 于是「金钱贝版」与「金钱茄版」各自拿到自己的默认值，
     * 而 1.4 的老 JSON（只有 {@code "type"}）继续按老语义工作。</p>
     *
     * <p>两个序列化器共用一个实现，靠 {@code variant}（0 / 1）区分：它同时进 Codec 与
     * StreamCodec，所以服务端→客户端同步后 {@link RawSturdygoldRecipe#getSerializer()}
     * 仍然指回正确的序列化器 id。</p>
     */
    public static final class Serializer implements RecipeSerializer<RawSturdygoldRecipe> {

        private final int variant;
        private final Supplier<Item> defaultExchange;
        private final Supplier<Item> defaultResult;
        private final MapCodec<RawSturdygoldRecipe> codec;
        private final StreamCodec<RegistryFriendlyByteBuf, RawSturdygoldRecipe> streamCodec;

        public Serializer(int variant, Supplier<Item> defaultExchange, Supplier<Item> defaultResult) {
            this.variant = variant;
            this.defaultExchange = defaultExchange;
            this.defaultResult = defaultResult;
            this.codec = RecordCodecBuilder.mapCodec(instance -> instance.group(
                    CraftingBookCategory.CODEC.optionalFieldOf("category", CraftingBookCategory.MISC)
                            .forGetter(CraftingRecipe::category),
                    BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("exchange")
                            .forGetter(r -> Optional.of(r.exchange)),
                    BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("result")
                            .forGetter(r -> Optional.of(r.result))
            ).apply(instance, (category, exchange, result) -> new RawSturdygoldRecipe(category,
                    exchange.orElseGet(this.defaultExchange),
                    result.orElseGet(this.defaultResult),
                    this.variant)));
            this.streamCodec = StreamCodec.composite(
                    CraftingBookCategory.STREAM_CODEC, CraftingRecipe::category,
                    ByteBufCodecs.registry(Registries.ITEM), RawSturdygoldRecipe::exchange,
                    ByteBufCodecs.registry(Registries.ITEM), RawSturdygoldRecipe::result,
                    ByteBufCodecs.VAR_INT, RawSturdygoldRecipe::variant,
                    RawSturdygoldRecipe::new);
        }

        @Override
        public MapCodec<RawSturdygoldRecipe> codec() {
            return this.codec;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, RawSturdygoldRecipe> streamCodec() {
            return this.streamCodec;
        }
    }
}
