package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;

import java.util.function.Supplier;

/**
 * 工具材料。
 * - STURDYGOLD：万坚金，耐久 6144 / 速度 10 / 攻击加成 4.5 / 附魔 30，修复用万坚金锭，下界合金级挖掘。
 * - ANTIQUE（新约 1.3 古董器具）：耐久 200 / 速度 8 / 附魔 12，修复用"没人要的老古董"，铁级挖掘。
 * - NETHERITE_ANTIQUE（新约 1.3 下界合金古董器具）：耐久 2031 / 速度 11 / 附魔 15，
 *   修复用下界合金锭，下界合金级挖掘（可挖远古残骸）。
 *
 * 挖掘等级由 incorrectBlocks 决定：INCORRECT_FOR_IRON_TOOL = #needs_diamond_tool（铁级），
 * INCORRECT_FOR_NETHERITE_TOOL = 空集（下界合金级，可挖一切）。
 */
public enum AllTiers implements Tier {

    STURDYGOLD(6144, 10.0F, 4.5F, 30,
            BlockTags.INCORRECT_FOR_NETHERITE_TOOL,
            () -> Ingredient.of(AllItems.STURDYGOLD_INGOT.get())),

    ANTIQUE(200, 8.0F, 0.0F, 12,
            BlockTags.INCORRECT_FOR_IRON_TOOL,
            () -> Ingredient.of(AllItems.UNWANTED_ANTIQUE.get())),

    NETHERITE_ANTIQUE(2031, 11.0F, 0.0F, 15,
            BlockTags.INCORRECT_FOR_NETHERITE_TOOL,
            () -> Ingredient.of(net.minecraft.world.item.Items.NETHERITE_INGOT));

    private final int uses;
    private final float speed;
    private final float attackDamage;
    private final int enchantmentValue;
    private final TagKey<Block> incorrectBlocks;
    private final Supplier<Ingredient> repairIngredient;

    AllTiers(int uses, float speed, float attackDamage, int enchantmentValue,
             TagKey<Block> incorrectBlocks, Supplier<Ingredient> repairIngredient) {
        this.uses = uses;
        this.speed = speed;
        this.attackDamage = attackDamage;
        this.enchantmentValue = enchantmentValue;
        this.incorrectBlocks = incorrectBlocks;
        this.repairIngredient = repairIngredient;
    }

    @Override
    public int getUses() {
        return this.uses;
    }

    @Override
    public float getSpeed() {
        return this.speed;
    }

    @Override
    public float getAttackDamageBonus() {
        return this.attackDamage;
    }

    @Override
    public TagKey<Block> getIncorrectBlocksForDrops() {
        return this.incorrectBlocks;
    }

    @Override
    public int getEnchantmentValue() {
        return this.enchantmentValue;
    }

    @Override
    public Ingredient getRepairIngredient() {
        return this.repairIngredient.get();
    }
}
