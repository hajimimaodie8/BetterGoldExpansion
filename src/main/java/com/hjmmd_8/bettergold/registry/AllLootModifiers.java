package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.common.loot.LootModifier;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

import java.util.List;

/**
 * 全局战利品修改器：
 * 金钱茄种子可在下界要塞（nether_bridge）与猪灵堡垒（bastion_*）箱子中开出：
 * - 普通箱子：6% 概率
 * - 堡垒藏宝室（bastion_treasure）藏宝堆：66% 概率
 */
public class AllLootModifiers {

    public static final DeferredRegister<MapCodec<? extends IGlobalLootModifier>> GLM =
            DeferredRegister.create(NeoForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, bettergold.MODID);

    /** 向指定箱子添加金钱茄种子的 modifier codec */
    public static final DeferredHolder<MapCodec<? extends IGlobalLootModifier>, MapCodec<AddEggplantSeedsModifier>> ADD_EGGPLANT_SEEDS =
            GLM.register("add_eggplant_seeds", AddEggplantSeedsModifier.CODEC::get);

    /** 通用：向指定箱子列表按概率添加物品（混沌金币串 6% 等） */
    public static final DeferredHolder<MapCodec<? extends IGlobalLootModifier>, MapCodec<AddChestItemModifier>> ADD_CHEST_ITEM =
            GLM.register("add_chest_item", AddChestItemModifier.CODEC::get);

    /** 通用：向指定箱子列表添加指定附魔的附魔书（取其金食 6% 等） */
    public static final DeferredHolder<MapCodec<? extends IGlobalLootModifier>, MapCodec<AddEnchantedBookModifier>> ADD_ENCHANTED_BOOK =
            GLM.register("add_enchanted_book", AddEnchantedBookModifier.CODEC::get);

    /** 箱子 loot table 列表（含藏宝室） */
    private static final List<String> CHEST_TABLES = List.of(
            "minecraft:chests/nether_bridge",
            "minecraft:chests/bastion_treasure",
            "minecraft:chests/bastion_bridge",
            "minecraft:chests/bastion_hoglin_stable",
            "minecraft:chests/bastion_other"
    );

    private AllLootModifiers() {
    }

    /**
     * 修改器实现：在指定箱子生成时，按概率添加金钱茄种子。
     * 概率由 JSON 传入（treasure 表用 0.66，其他用 0.06）。
     */
    public static class AddEggplantSeedsModifier extends LootModifier {

        public static final java.util.function.Supplier<MapCodec<AddEggplantSeedsModifier>> CODEC =
                () -> RecordCodecBuilder.mapCodec(inst -> inst.group(
                        IGlobalLootModifier.LOOT_CONDITIONS_CODEC.fieldOf("conditions").forGetter(l -> l.conditions),
                        net.minecraft.core.registries.BuiltInRegistries.ITEM
                                .byNameCodec().fieldOf("item").forGetter(l -> l.item),
                        net.minecraft.util.ExtraCodecs.POSITIVE_FLOAT.fieldOf("chance").forGetter(l -> l.chance)
                ).apply(inst, AddEggplantSeedsModifier::new));

        private final net.minecraft.world.item.Item item;
        private final float chance;

        public AddEggplantSeedsModifier(LootItemCondition[] conditions, net.minecraft.world.item.Item item, float chance) {
            super(conditions);
            this.item = item;
            this.chance = chance;
        }

        @Override
        protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
            // 只处理目标箱子
            ResourceLocation lootTableId = context.getQueriedLootTableId();
            if (lootTableId == null || !CHEST_TABLES.contains(lootTableId.toString())) {
                return generatedLoot;
            }
            // 判定概率：堡垒藏宝室 66%，其余 6%
            float effectiveChance = "minecraft:chests/bastion_treasure".equals(lootTableId.toString()) ? 0.66F : chance;
            if (context.getRandom().nextFloat() < effectiveChance) {
                generatedLoot.add(new ItemStack(item));
            }
            return generatedLoot;
        }

        @Override
        public MapCodec<? extends IGlobalLootModifier> codec() {
            return CODEC.get();
        }
    }

    /**
     * 通用箱子战利品修改器：在指定箱子列表中以给定概率添加单个物品。
     * JSON 形如 {"type":"bettergold:add_chest_item","item":"...","chance":0.06,"tables":["minecraft:chests/..."]}
     */
    public static class AddChestItemModifier extends LootModifier {

        public static final java.util.function.Supplier<MapCodec<AddChestItemModifier>> CODEC =
                () -> RecordCodecBuilder.mapCodec(inst -> inst.group(
                        IGlobalLootModifier.LOOT_CONDITIONS_CODEC.fieldOf("conditions").forGetter(l -> l.conditions),
                        net.minecraft.core.registries.BuiltInRegistries.ITEM
                                .byNameCodec().fieldOf("item").forGetter(l -> l.item),
                        net.minecraft.util.ExtraCodecs.POSITIVE_FLOAT.fieldOf("chance").forGetter(l -> l.chance),
                        com.mojang.serialization.Codec.STRING.listOf().fieldOf("tables").forGetter(l -> l.tables)
                ).apply(inst, AddChestItemModifier::new));

        private final net.minecraft.world.item.Item item;
        private final float chance;
        private final List<String> tables;

        public AddChestItemModifier(LootItemCondition[] conditions, net.minecraft.world.item.Item item,
                                    float chance, List<String> tables) {
            super(conditions);
            this.item = item;
            this.chance = chance;
            this.tables = tables;
        }

        @Override
        protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
            ResourceLocation lootTableId = context.getQueriedLootTableId();
            if (lootTableId == null || !tables.contains(lootTableId.toString())) {
                return generatedLoot;
            }
            if (context.getRandom().nextFloat() < chance) {
                generatedLoot.add(new ItemStack(item));
            }
            return generatedLoot;
        }

        @Override
        public MapCodec<? extends IGlobalLootModifier> codec() {
            return CODEC.get();
        }
    }

    /**
     * 通用"箱子中添加指定附魔的附魔书"修改器。
     * JSON 形如 {"type":"bettergold:add_enchanted_book","enchantment":"bettergold:take_gold_food",
     * "chance":0.06,"tables":["minecraft:chests/..."]}
     */
    public static class AddEnchantedBookModifier extends LootModifier {

        public static final java.util.function.Supplier<MapCodec<AddEnchantedBookModifier>> CODEC =
                () -> RecordCodecBuilder.mapCodec(inst -> inst.group(
                        IGlobalLootModifier.LOOT_CONDITIONS_CODEC.fieldOf("conditions").forGetter(l -> l.conditions),
                        net.minecraft.resources.ResourceLocation.CODEC.fieldOf("enchantment").forGetter(l -> l.enchantmentId),
                        net.minecraft.util.ExtraCodecs.POSITIVE_FLOAT.fieldOf("chance").forGetter(l -> l.chance),
                        com.mojang.serialization.Codec.STRING.listOf().fieldOf("tables").forGetter(l -> l.tables)
                ).apply(inst, AddEnchantedBookModifier::new));

        private final net.minecraft.resources.ResourceLocation enchantmentId;
        private final float chance;
        private final List<String> tables;

        public AddEnchantedBookModifier(LootItemCondition[] conditions, net.minecraft.resources.ResourceLocation enchantmentId,
                                        float chance, List<String> tables) {
            super(conditions);
            this.enchantmentId = enchantmentId;
            this.chance = chance;
            this.tables = tables;
        }

        @Override
        protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
            ResourceLocation lootTableId = context.getQueriedLootTableId();
            if (lootTableId == null || !tables.contains(lootTableId.toString())) {
                return generatedLoot;
            }
            if (context.getRandom().nextFloat() < chance) {
                var enchantLookup = context.getResolver().lookupOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT);
                var key = net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.ENCHANTMENT, enchantmentId);
                var holderOpt = enchantLookup.get(key);
                if (holderOpt.isPresent()) {
                    generatedLoot.add(net.minecraft.world.item.EnchantedBookItem.createForEnchantment(
                            new net.minecraft.world.item.enchantment.EnchantmentInstance(holderOpt.get(), 1)));
                }
            }
            return generatedLoot;
        }

        @Override
        public MapCodec<? extends IGlobalLootModifier> codec() {
            return CODEC.get();
        }
    }
}
