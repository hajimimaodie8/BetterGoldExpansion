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
 *
 * <h2>1.7（bg-n10rg）：「双倍贵金原料」= 同一套形状，换催化剂 + 改数量</h2>
 *
 * <p>作者 2026-10-17 原话：「"贵金"原料<b>双倍合成</b>就是<b>直接把炼金燃油的位置换成高阶炼金油</b>，
 * 然后<b>原料的合成量改为 2</b>，<b>记得返还玻璃瓶</b>」。</p>
 *
 * <p>于是本类再加<b>两个可选字段</b>（同样缺省回落，老 JSON 一字不改）：</p>
 *
 * <pre>{
 *   "type": "bettergold:raw_sturdygold",
 *   "exchange": "bettergold:bundled_echo_shard",
 *   "result":   "bettergold:raw_echogold",
 *   "catalyst": "bettergold:refined_alchemic_oil",   // 缺省 = 炼金燃油（alchemic_fuel）
 *   "count":    2                                    // 缺省 = 1
 * }</pre>
 *
 * <p><b>为什么玻璃瓶 remainder 写在这里、而不是给物品挂 {@code craftRemainder}</b>：
 * 1.21.1 的「合成后返还」机制<b>不是数据组件</b>（{@code DataComponents} 里<b>没有</b>
 * {@code crafting_remaining_item} 这种东西，全仓 grep = 0 命中），而是
 * {@code Item.Properties#craftRemainder}（{@code Item.java:463}）→
 * {@code Item#getCraftingRemainingItem}（{@code Item.java:285-291}），
 * 由 {@code Recipe#getRemainingItems} 的<b>默认实现</b>（{@code Recipe.java:33-39}）
 * 逐格取用。给 {@code refined_alchemic_oil} 挂上物品级 remainder 会
 * <b>顺带改掉别的配方</b>（例如 {@code chaosalloy_ingot.json} 也吃这瓶油 ⇒ 那条会凭空开始返瓶），
 * 而本轮作者只要求「原料双倍」这一条返还玻璃瓶 ⇒ 沿用<b>本类既有的</b>做法
 * （{@link #getRemainingItems} 在<b>催化剂那一格</b>放玻璃瓶，`alchemic_fuel` 从 1.5 起就是这么做的），
 * 影响范围精确锁死在"用本类的那几条配方"。</p>
 */
public class RawSturdygoldRecipe extends CustomRecipe {

    /** 兑换物（配方里最下面那一格的主材料） */
    private final Item exchange;
    /** 产物 */
    private final Item result;
    /** 催化剂（瓶装那一格）：缺省 = 炼金燃油；双倍版 = 高阶炼金油 */
    private final Item catalyst;
    /** 来自哪个序列化器（0 = 金钱贝版，1 = 金钱茄版）；见 {@link #getSerializer()} */
    private final int variant;
    /** 产物数量（缺省 1；「双倍贵金原料」= 2） */
    private final int count;

    public RawSturdygoldRecipe(CraftingBookCategory category, Item exchange, Item result, Item catalyst,
                               int variant, int count) {
        super(category);
        this.exchange = exchange;
        this.result = result;
        this.catalyst = catalyst;
        this.variant = variant;
        this.count = count;
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

    /** 催化剂（探针 / 调试用）：炼金燃油 或 高阶炼金油 */
    public Item catalyst() {
        return this.catalyst;
    }

    /** 产物数量（探针 / 调试用）：1 = 普通原料，2 = 双倍贵金原料 */
    public int count() {
        return this.count;
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
                Ingredient.of(this.catalyst),
                Ingredient.of(this.exchange));
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 9;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        int crystal = 0, redstone = 0, goldBlock = 0, netherite = 0, catalyst = 0, exchange = 0, other = 0;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            if (stack.is(AllItems.MIXED_CRYSTAL_PILE.get())) crystal++;
            else if (stack.is(Items.REDSTONE)) redstone++;
            else if (stack.is(Items.GOLD_BLOCK)) goldBlock++;
            else if (stack.is(Items.NETHERITE_INGOT)) netherite++;
            else if (stack.is(this.catalyst)) catalyst++;
            else if (stack.is(this.exchange)) exchange++;
            else other++;
        }
        return crystal == 2 && redstone == 2 && goldBlock == 2 && netherite == 1 && catalyst == 1
                && exchange == 1 && other == 0;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return new ItemStack(this.result, this.count);
    }

    /** 提供输出物品，供 JEI/配方书展示（CustomRecipe 默认返回空） */
    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return new ItemStack(this.result, this.count);
    }

    @Override
    public NonNullList<ItemStack> getRemainingItems(CraftingInput input) {
        NonNullList<ItemStack> remaining = NonNullList.withSize(input.size(), ItemStack.EMPTY);
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.is(this.catalyst)) {
                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE)); // 返还玻璃瓶（燃油 / 高阶炼金油都是瓶装）
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
     * 本配方的序列化器：读 {@code category} / {@code exchange} / {@code result} 三个字段
     * （1.7 bg-n10rg 起再加两个可选的 {@code catalyst} / {@code count}）。
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
        /** 催化剂的缺省值：两种 variant 都是「炼金燃油」（lazy supplier，注册顺序无关） */
        private final Supplier<Item> defaultCatalyst = () -> AllItems.ALCHEMIC_FUEL.get();
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
                            .forGetter(r -> Optional.of(r.result)),
                    BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("catalyst")
                            .forGetter(r -> Optional.of(r.catalyst)),
                    net.minecraft.util.ExtraCodecs.NON_NEGATIVE_INT.optionalFieldOf("count", 1)
                            .forGetter(RawSturdygoldRecipe::count)
            ).apply(instance, (category, exchange, result, catalyst, count) -> new RawSturdygoldRecipe(category,
                    exchange.orElseGet(this.defaultExchange),
                    result.orElseGet(this.defaultResult),
                    catalyst.orElseGet(this.defaultCatalyst),
                    this.variant,
                    count)));
            this.streamCodec = StreamCodec.composite(
                    CraftingBookCategory.STREAM_CODEC, CraftingRecipe::category,
                    ByteBufCodecs.registry(Registries.ITEM), RawSturdygoldRecipe::exchange,
                    ByteBufCodecs.registry(Registries.ITEM), RawSturdygoldRecipe::result,
                    ByteBufCodecs.registry(Registries.ITEM), RawSturdygoldRecipe::catalyst,
                    ByteBufCodecs.VAR_INT, RawSturdygoldRecipe::variant,
                    ByteBufCodecs.VAR_INT, RawSturdygoldRecipe::count,
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
