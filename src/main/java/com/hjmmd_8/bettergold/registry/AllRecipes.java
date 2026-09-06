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

    /** 万坚金原料配方（金钱贝版）：炼金燃油合成后返还玻璃瓶 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<RawSturdygoldRecipe>> RAW_STURDYGOLD_RECIPE =
            RECIPE_SERIALIZERS.register("raw_sturdygold",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new RawSturdygoldRecipe(cat, 0)));

    /** 万坚金原料配方（金钱茄版，易金台设定）：金钱贝换成金钱茄 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<RawSturdygoldRecipe>> RAW_STURDYGOLD_EGGPLANT_RECIPE =
            RECIPE_SERIALIZERS.register("raw_sturdygold_eggplant",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new RawSturdygoldRecipe(cat, 1)));

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
