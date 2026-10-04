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

    /**
     * 1.6（bg-16）：<b>闪耀藤条</b>——用本模组金属器具 / 五类武器破坏树叶或藤蔓时按概率掉落。
     *
     * <p>为什么不用"往每个树叶 loot table 里塞一个 GLM + 物品标签"：判据里有两条 vanilla 表达不了的东西 ——
     * ①「工具属于本模组<b>任意一族</b>的器具或五类武器」是**代码判据**（{@code MetalFamily.of(tool)}）；
     * ② 时运曲线要跟着本仓既有口径走（{@code 0.06 + 0.06 × 等级}）。
     * 所以落成自定义 GLM（与 {@code AddChestItemModifier} 同一种形态），JSON 只留条件。</p>
     */
    public static final DeferredHolder<MapCodec<? extends IGlobalLootModifier>, MapCodec<AddGlitteringVineModifier>> ADD_GLITTERING_VINE =
            GLM.register("add_glittering_vine", AddGlitteringVineModifier.CODEC::get);

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

    /**
     * 1.6（bg-16）闪耀藤条：<b>用本模组金属器具 / 五类武器</b>破坏
     * {@code #minecraft:leaves} 或 {@code minecraft:vine} 时按概率掉 1 个。
     *
     * <h2>口径（需求 §3.1 + §7 #2 / #4）</h2>
     * <ul>
     *   <li>基础 <b>6%</b>、<b>受时运提升</b>：{@code p = 0.06 + 0.06 × 时运等级}
     *       （0/1/2/3 级 ⇒ 6% / 12% / 18% / 24%）。</li>
     *   <li>「任意金武器工具」= <b>本模组全部金属族的器具（剑/斧/镐/锹/锄/小刀）
     *       + 1.5 五类武器（重锤/弓/弩/三叉戟/盾牌）</b> —— 判据是 {@code MetalFamily.of(tool)}
     *       且该物品属于该族的 {@code isTool}/{@code isWeapon}。</li>
     *   <li><b>反例</b>：用别的模组的工具、或挖的不是树叶 / 藤蔓 ⇒ 不掉（两个判据都不满足）。</li>
     *   <li>概率与目标方块都写在 Java 里（vanilla 的物品标签表达不了"任意一族"），JSON 只提供 conditions。</li>
     * </ul>
     */
    public static class AddGlitteringVineModifier extends LootModifier {

        /** 基础概率 6% */
        public static final float BASE_CHANCE = 0.06F;
        /** 每级时运 +6%（概率口径：0/1/2/3 级 ⇒ 6%/12%/18%/24%） */
        public static final float CHANCE_PER_FORTUNE = 0.06F;

        public static final java.util.function.Supplier<MapCodec<AddGlitteringVineModifier>> CODEC =
                () -> RecordCodecBuilder.mapCodec(inst -> inst.group(
                        IGlobalLootModifier.LOOT_CONDITIONS_CODEC.fieldOf("conditions")
                                .forGetter(l -> l.conditions)
                ).apply(inst, AddGlitteringVineModifier::new));

        public AddGlitteringVineModifier(LootItemCondition[] conditions) {
            super(conditions);
        }

        @Override
        protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
            var state = context.getParamOrNull(net.minecraft.world.level.storage.loot.parameters.LootContextParams.BLOCK_STATE);
            if (state == null || !isTarget(state)) {
                return generatedLoot;
            }
            var tool = context.getParamOrNull(net.minecraft.world.level.storage.loot.parameters.LootContextParams.TOOL);
            if (tool == null || !isOurTool(tool)) {
                return generatedLoot;
            }
            float chance = BASE_CHANCE + CHANCE_PER_FORTUNE * fortuneLevel(context, tool);
            if (context.getRandom().nextFloat() < chance) {
                generatedLoot.add(new ItemStack(
                        com.hjmmd_8.bettergold.material.MetalSpecialItems.GLITTERING_VINE.get()));
            }
            return generatedLoot;
        }

        /** 目标方块：{@code #minecraft:leaves} 或 {@code minecraft:vine} */
        private static boolean isTarget(net.minecraft.world.level.block.state.BlockState state) {
            return state.is(net.minecraft.tags.BlockTags.LEAVES)
                    || state.is(net.minecraft.world.level.block.Blocks.VINE);
        }

        /** 工具：本模组任意金属族的器具（含乐事小刀）或五类武器 */
        private static boolean isOurTool(ItemStack tool) {
            var family = com.hjmmd_8.bettergold.material.MetalFamily.of(tool);
            return family != null && (family.isTool(tool.getItem()) || family.isWeapon(tool.getItem()));
        }

        /** 工具上的时运等级（0 = 没有 / 拿不到附魔注册表时也按 0 算） */
        private static int fortuneLevel(LootContext context, ItemStack tool) {
            return context.getLevel().registryAccess()
                    .lookupOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT)
                    .get(net.minecraft.world.item.enchantment.Enchantments.FORTUNE)
                    .map(holder -> net.minecraft.world.item.enchantment.EnchantmentHelper
                            .getItemEnchantmentLevel(holder, tool))
                    .orElse(0);
        }

        @Override
        public MapCodec<? extends IGlobalLootModifier> codec() {
            return CODEC.get();
        }
    }
}
