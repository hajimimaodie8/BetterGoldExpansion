package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.recipe.GoldenCowrieMoldRecipe;
import com.hjmmd_8.bettergold.recipe.GoldenFoodRecipe;
import com.hjmmd_8.bettergold.recipe.GoldenHoneyCookieRecipe;
import com.hjmmd_8.bettergold.recipe.RawSturdygoldRecipe;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.SimpleCraftingRecipeSerializer;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 自定义配方注册（本体部分）。
 * FD 联动配方（馅饼酥皮、桶装热可可分装）见 {@link com.hjmmd_8.bettergold.fd.FdRecipes}。
 */
public class AllRecipes {

    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS =
            DeferredRegister.create(Registries.RECIPE_SERIALIZER, bettergold.MODID);

    /** 金钱贝模具配方：模具 + 金锭 → 金钱贝（模具耐久 -1） */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<GoldenCowrieMoldRecipe>> GOLDEN_COWRIE_MOLD_RECIPE =
            RECIPE_SERIALIZERS.register("golden_cowrie_mold",
                    () -> new SimpleCraftingRecipeSerializer<>(GoldenCowrieMoldRecipe::new));

    /**
     * 金钱贝模具配方（<b>金钱茄</b>版，1.7 作者 2026-10-24 第 ③ 条）：模具 + 金钱茄 → 1 金钱贝，模具耐久 -1。
     *
     * <p>与上面那条<b>同一个配方类</b>，只换「兑换物」这一件 ⇒ 消耗语义（模具 −1 耐久、耗尽消失、
     * 金钱茄被消耗 1 个、产物恒 1）逐字复用，没有第二份实现。</p>
     *
     * <p>⚠ 归属说明（本轮唯一的判断点）：派单原话把它写成「{@code chaos_eggplant}（金钱茄）」，
     * 但全仓<b>没有</b> {@code chaos_eggplant} 这个物品（grep = 0）；本项目的「金钱茄」是
     * <b>{@code bettergold:golden_eggplant}</b>（{@code AllItems#GOLDEN_EGGPLANT} 的注释就叫「金钱茄」，
     * 而且被替换掉的旧配方 {@code raw_sturdygold_eggplant} 用的兑换物正是它）⇒ 按<b>中文名</b>取
     * {@code golden_eggplant}。见 {@code docs/1.7-...md} §29 ③。</p>
     */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<GoldenCowrieMoldRecipe>> GOLDEN_COWRIE_MOLD_MONEY_EGGPLANT_RECIPE =
            RECIPE_SERIALIZERS.register("golden_cowrie_mold_money_eggplant",
                    () -> new SimpleCraftingRecipeSerializer<>(
                            cat -> new GoldenCowrieMoldRecipe(cat, AllItems.GOLDEN_EGGPLANT.get())));

    /**
     * 原料配方（金钱贝版，{@code variant = 0}）：炼金燃油合成后返还玻璃瓶。
     *
     * <p>1.5 起兑换物与产物都是<b>数据驱动</b>的：JSON 可以写 {@code "exchange"} / {@code "result"}
     * 两个可选字段，缺省时回落到这里的默认值（金钱贝 / 万坚金原料）。
     * 三套 1.4 新金属（烈燃金 / 巫毒金 / 结雷金）与 1.5 两套新金属的原料配方都复用这一个序列化器，
     * 各自在 JSON 里声明自己的兑换物与产物 —— 1.4 那个「四条配方产物全是万坚金原料」的 bug
     * 就是在这里修掉的（详见 {@link RawSturdygoldRecipe}）。</p>
     */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<RawSturdygoldRecipe>> RAW_STURDYGOLD_RECIPE =
            RECIPE_SERIALIZERS.register("raw_sturdygold",
                    () -> new RawSturdygoldRecipe.Serializer(0,
                            () -> AllItems.GOLDEN_COWRIE.get(), () -> AllItems.RAW_STURDYGOLD.get()));

    /** 原料配方（金钱茄版，易金台设定，{@code variant = 1}）：缺省兑换物是金钱茄、产物仍是万坚金原料 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<RawSturdygoldRecipe>> RAW_STURDYGOLD_EGGPLANT_RECIPE =
            RECIPE_SERIALIZERS.register("raw_sturdygold_eggplant",
                    () -> new RawSturdygoldRecipe.Serializer(1,
                            () -> AllItems.GOLDEN_EGGPLANT.get(), () -> AllItems.RAW_STURDYGOLD.get()));

    /** 金钱巧克力棒配方：返还铁桶 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<GoldenFoodRecipe>> GOLDEN_CHOCOLATE_BAR_RECIPE =
            RECIPE_SERIALIZERS.register("golden_chocolate_bar",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new GoldenFoodRecipe(cat, 0)));

    /** 金冰淇淋配方：返还铁桶 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<GoldenFoodRecipe>> GOLDEN_ICE_CREAM_RECIPE =
            RECIPE_SERIALIZERS.register("golden_ice_cream",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new GoldenFoodRecipe(cat, 1)));

    /** 金蜂蜜曲奇配方：返还玻璃瓶 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<GoldenHoneyCookieRecipe>> GOLDEN_HONEY_COOKIE_RECIPE =
            RECIPE_SERIALIZERS.register("golden_honey_cookie",
                    () -> new SimpleCraftingRecipeSerializer<>(GoldenHoneyCookieRecipe::new));

    private AllRecipes() {
    }
}
