package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.SimpleCraftingRecipeSerializer;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * FD（农夫乐事）联动分支的"配方序列化器"注册表。
 * 只注册联动配方（馅饼酥皮合成、桶装热可可分装），对应 data/bettergold/recipe 里
 * type = bettergold:golden_pie_crust / bettergold:*_bucket_to_bottle 的配方 json
 * （这些 json 均带 neoforge:conditions 的 mod_loaded(farmersdelight) 守卫，无 FD 时不加载）。
 */
public class FdRecipes {

    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS =
            DeferredRegister.create(Registries.RECIPE_SERIALIZER, bettergold.MODID);

    /** 金馅饼酥皮配方：中心奶瓶+左右下三金麦，返还玻璃瓶 */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<PieCrustRecipe>> GOLDEN_PIE_CRUST_RECIPE =
            RECIPE_SERIALIZERS.register("golden_pie_crust",
                    () -> new SimpleCraftingRecipeSerializer<>(PieCrustRecipe::new));

    /** 桶装金酿热可可 → 3 瓶金酿热可可（返还铁桶） */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<BucketToBottleRecipe>> BREWED_HOT_COCOA_BUCKET_TO_BOTTLE_RECIPE =
            RECIPE_SERIALIZERS.register("brewed_hot_cocoa_bucket_to_bottle",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new BucketToBottleRecipe(cat, 0)));

    /** 桶装万坚金酿热可可 → 3 瓶万坚金酿热可可（返还铁桶） */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<BucketToBottleRecipe>> STURDYGOLD_BREWED_HOT_COCOA_BUCKET_TO_BOTTLE_RECIPE =
            RECIPE_SERIALIZERS.register("sturdygold_brewed_hot_cocoa_bucket_to_bottle",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new BucketToBottleRecipe(cat, 1)));

    /** 炼金贝肉串：2 木棍 + 金胡萝卜 + 金钱茄 + 炼金贝肉 → 2 串（返还金钱贝） */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<AlchemicalMeatRecipe>> ALCHEMICAL_MEAT_SKEWER_RECIPE =
            RECIPE_SERIALIZERS.register("alchemical_meat_skewer",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new AlchemicalMeatRecipe(cat, 0)));

    /** 炼金贝肉三明治：金砖面包 + 炼金贝肉 → 1 个（返还金钱贝） */
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<AlchemicalMeatRecipe>> ALCHEMICAL_MEAT_SANDWICH_RECIPE =
            RECIPE_SERIALIZERS.register("alchemical_meat_sandwich",
                    () -> new SimpleCraftingRecipeSerializer<>(cat -> new AlchemicalMeatRecipe(cat, 1)));

    private FdRecipes() {
    }
}
