package com.hjmmd_8.bettergold.event;

import com.hjmmd_8.bettergold.block.GoldInfusedFarmlandBlock;
import com.hjmmd_8.bettergold.config.Config;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllEffects;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.piglin.Piglin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.BlockPos;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.ItemAbilities;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.living.LivingEntityUseItemEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.level.BlockEvent;

import java.util.List;

/**
 * 模组业务事件处理器。
 *
 * 1. 手持万坚金工具攻击生物 → 100% 触发掉落金系物品（附魔金苹果仅 1% 权重）。
 * 2. 万坚金盔甲（任意一件）：
 *    - 猪灵中立由 AllItems.SturdygoldArmorItem 覆写 makesPiglinsNeutral 实现（单件生效），无需事件；
 *    - 猪灵以物易物产出物品数量翻倍（任意一件盔甲即可）。
 * 3. 金钱贝战利品掉落：猪灵蛮兵 50% / 猪灵 15% / 僵尸猪灵 5%。
 * 4. 猪灵以物易物时 6% 概率额外掉落金钱贝。
 * 5. 抗寒性：免疫冰冻伤害（细雪冻伤）。
 * 6. 锄头点击金染土 → 金染耕地。
 * 7. 金骨粉催熟金作物。
 * 8. 食用金淇淋去除燃烧状态。
 * 9. 食用金酿热可可/万坚金酿热可可清除全部负面状态。
 *
 * 注意：1.21.1 的 NeoForge 没有 LivingHurtEvent（已拆分为 LivingIncomingDamageEvent / LivingDamageEvent），
 * 也没有 PiglinBarterEvent，因此用等价事件实现。
 */
public class ModEvents {

    /** 附魔金苹果的掉落权重：1% */
    private static final double ENCHANTED_GOLDEN_APPLE_WEIGHT = 0.01;

    /**
     * 白板万坚金工具（无"取其金食"附魔）爆金掉落池：金钱贝 / 金锭 / 金粒 / 粗金。
     */
    private static final List<Item> BASE_GOLD_LOOT_POOL = List.of(
            AllItems.GOLDEN_COWRIE.get(),   // 金钱贝
            Items.GOLD_INGOT,               // 金锭
            Items.GOLD_NUGGET,              // 金粒
            Items.RAW_GOLD                  // 粗金
    );

    /**
     * 附魔"取其金食"追加的金食物掉落池：
     * 金苹果 / 金萝卜 / 金蛋 / 金麦种子 / 金麦 / 金钱茄种子 / 金钱茄 / 金钱巧克力棒 / 金甘蔗棒
     * （附魔金苹果按 1% 单独判定）
     */
    private static final List<Item> GOLD_FOOD_LOOT_POOL = List.of(
            Items.GOLDEN_APPLE,                    // 金苹果
            Items.GOLDEN_CARROT,                   // 金萝卜
            AllItems.GOLDEN_EGG.get(),             // 金蛋
            AllItems.GOLDEN_WHEAT_SEEDS.get(),     // 金麦种子
            AllItems.GOLDEN_WHEAT.get(),           // 金麦
            AllItems.GOLDEN_EGGPLANT_SEEDS.get(),  // 金钱茄种子
            AllItems.GOLDEN_EGGPLANT.get(),        // 金钱茄
            AllItems.GOLDEN_CHOCOLATE_BAR.get(),   // 金钱巧克力棒
            AllItems.GOLDEN_SUGAR_CANE_STICK.get() // 金甘蔗棒
    );

    /** 取其金食附魔 id */
    private static final net.minecraft.resources.ResourceKey<net.minecraft.world.item.enchantment.Enchantment>
            TAKE_GOLD_FOOD_KEY = net.minecraft.resources.ResourceKey.create(
            net.minecraft.core.registries.Registries.ENCHANTMENT,
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("bettergold", "take_gold_food"));

    // ==================== 猪灵以物易物：产出翻倍 + 6% 金钱贝 ====================

    @SubscribeEvent
    public static void onEntityJoinLevel(EntityJoinLevelEvent event) {
        Level level = event.getLevel();
        if (level.isClientSide) {
            return;
        }
        if (!(event.getEntity() instanceof ItemEntity itemEntity)) {
            return;
        }
        // 识别猪灵 barter 抛出的物品：投掷者（owner）是猪灵
        Entity owner = itemEntity.getOwner();
        if (!(owner instanceof Piglin)) {
            return;
        }
        // 任意万坚金盔甲玩家在场时：产出翻倍（金钱贝除外——金钱贝不受翻倍影响）
        boolean anyArmorPlayer = level.players().stream()
                .anyMatch(ModEvents::wearingAnySturdygoldArmor);
        if (anyArmorPlayer && !itemEntity.getItem().is(AllItems.GOLDEN_COWRIE.get())) {
            ItemStack stack = itemEntity.getItem();
            stack.grow(stack.getCount());
            itemEntity.setItem(stack);
        }
        // 6% 概率额外掉落金钱贝（猪灵交易获得）
        if (level.random.nextFloat() < 0.06F) {
            ItemEntity cowrie = new ItemEntity(level,
                    itemEntity.getX(), itemEntity.getY(), itemEntity.getZ(),
                    new ItemStack(AllItems.GOLDEN_COWRIE.get()));
            cowrie.setDefaultPickUpDelay();
            level.addFreshEntity(cowrie);
        }
        // 6% 概率额外掉落混沌金币串（猪灵交易获得，独立判定可与金钱贝同时出）
        // 万坚金甲在场时同样享受翻倍（与上面 barter 主产物翻倍一致）
        if (level.random.nextFloat() < 0.06F) {
            int count = anyArmorPlayer ? 2 : 1;
            ItemEntity coinString = new ItemEntity(level,
                    itemEntity.getX(), itemEntity.getY(), itemEntity.getZ(),
                    new ItemStack(AllItems.CHAOS_COIN_STRING.get(), count));
            coinString.setDefaultPickUpDelay();
            level.addFreshEntity(coinString);
        }
        // 6% 概率额外掉落"取其金食"附魔书（宝藏附魔，猪灵交易获得）
        if (level.random.nextFloat() < 0.06F) {
            try {
                var enchantLookup = level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT);
                var key = net.minecraft.resources.ResourceKey.create(
                        net.minecraft.core.registries.Registries.ENCHANTMENT,
                        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("bettergold", "take_gold_food"));
                var holderOpt = enchantLookup.get(key);
                if (holderOpt.isPresent()) {
                    ItemStack book = net.minecraft.world.item.EnchantedBookItem.createForEnchantment(
                            new net.minecraft.world.item.enchantment.EnchantmentInstance(holderOpt.get(), 1));
                    ItemEntity bookEntity = new ItemEntity(level,
                            itemEntity.getX(), itemEntity.getY(), itemEntity.getZ(), book);
                    bookEntity.setDefaultPickUpDelay();
                    level.addFreshEntity(bookEntity);
                }
            } catch (Exception ignored) {
                // 注册表未就绪时静默跳过
            }
        }
        // 6% 概率额外掉落礼品金票（新约 1.3）：同样受万坚金甲翻倍，并向附近玩家提示"奢华"
        if (level.random.nextFloat() < 0.06F) {
            int ticketCount = anyArmorPlayer ? 2 : 1;
            ItemEntity ticket = new ItemEntity(level,
                    itemEntity.getX(), itemEntity.getY(), itemEntity.getZ(),
                    new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), ticketCount));
            ticket.setDefaultPickUpDelay();
            level.addFreshEntity(ticket);
            showLuxuriousMessage(level, itemEntity.position());
        }
    }

    /** 向附近玩家在物品栏上方（屏幕中下方）显示"奢华"提示 */
    private static void showLuxuriousMessage(Level level, net.minecraft.world.phys.Vec3 pos) {
        var message = net.minecraft.network.chat.Component.translatable("message.bettergold.luxurious");
        for (Player nearby : level.players()) {
            if (nearby.distanceToSqr(pos) <= 256.0D) {
                nearby.displayClientMessage(message, true);
            }
        }
    }

    // ==================== 万坚金工具攻击：100% 触发掉落金系物品 ====================

    @SubscribeEvent
    public static void onLivingIncomingDamage(LivingIncomingDamageEvent event) {
        if (event.getEntity().level().isClientSide) {
            return;
        }
        // 校验攻击者：必须是玩家
        Entity attacker = event.getSource().getEntity();
        if (!(attacker instanceof Player player)) {
            return;
        }
        ItemStack held = player.getMainHandItem();

        // ---- 新约 1.3：下界合金古董剑/斧/刀攻击时 6% 掉落下界合金尘埃（受抢夺影响） ----
        if (isDustOnAttackTool(held)) {
            int looting = enchantLevel(held, player.level(),
                    net.minecraft.world.item.enchantment.Enchantments.LOOTING);
            float chance = 0.06F + 0.06F * looting;
            if (player.getRandom().nextFloat() < chance) {
                LivingEntity victim = event.getEntity();
                int count = 1 + looting / 2;
                dropItem(victim.level(), victim.getX(), victim.getY() + 0.5D, victim.getZ(),
                        new ItemStack(AllItems.NETHERITE_DUST.get(), count));
            }
        }

        // 校验手持物品：必须是万坚金工具
        if (!isSturdygoldTool(held)) {
            return;
        }
        // 功能 100% 触发：必定掉落一件金系物品（白板掉基础四件；有"取其金食"附魔才掉金食物）
        Item loot = rollGoldLoot(player, held);
        LivingEntity victim = event.getEntity();
        Level level = victim.level();
        if (level instanceof ServerLevel serverLevel) {
            ItemEntity drop = new ItemEntity(serverLevel,
                    victim.getX(), victim.getY() + 0.5D, victim.getZ(),
                    new ItemStack(loot));
            drop.setDefaultPickUpDelay();
            serverLevel.addFreshEntity(drop);
        }
    }

    // ==================== 新约 1.3：下界合金古董器具的挖掘效果 ====================

    /**
     * 挖掘掉落处理（斧/镐/锹/锄，均为下界合金古董器具时）：
     * - 镐挖远古残骸：直接掉落 1~3 个下界合金碎片（受时运影响）；
     * - 其余：6% 概率（受时运影响）把该方块的掉落物替换为 1 个下界合金尘埃。
     */
    @SubscribeEvent
    public static void onBlockDrops(net.neoforged.neoforge.event.level.BlockDropsEvent event) {
        ItemStack tool = event.getTool();
        if (!(tool.getItem() instanceof net.minecraft.world.item.TieredItem tiered)
                || tiered.getTier() != com.hjmmd_8.bettergold.material.AllTiers.NETHERITE_ANTIQUE) {
            return;
        }
        ServerLevel level = event.getLevel();
        var random = level.getRandom();
        int fortune = enchantLevel(tool, level, net.minecraft.world.item.enchantment.Enchantments.FORTUNE);

        // 镐 + 远古残骸：1~3 个下界合金碎片（时运每级 +1）
        if (tool.getItem() instanceof net.minecraft.world.item.PickaxeItem
                && event.getState().is(net.minecraft.world.level.block.Blocks.ANCIENT_DEBRIS)) {
            int count = 1 + random.nextInt(3) + fortune;
            event.getDrops().clear();
            event.setDroppedExperience(0);
            dropItem(level, event.getPos().getX() + 0.5D, event.getPos().getY() + 0.5D, event.getPos().getZ() + 0.5D,
                    new ItemStack(Items.NETHERITE_SCRAP, count));
            return;
        }

        // 斧/镐/锹/锄：6%（+时运）概率把掉落物替换成下界合金尘埃
        if (!isDustOnMineTool(tool)) {
            return;
        }
        float chance = 0.06F + 0.06F * fortune;
        if (random.nextFloat() < chance && !event.getDrops().isEmpty()) {
            int count = 1 + fortune / 2;
            event.getDrops().clear();
            event.setDroppedExperience(0);
            dropItem(level, event.getPos().getX() + 0.5D, event.getPos().getY() + 0.5D, event.getPos().getZ() + 0.5D,
                    new ItemStack(AllItems.NETHERITE_DUST.get(), count));
        }
    }

    /** 攻击型：下界合金古董的剑/斧/刀（非镐/锹/锄即视为剑斧刀，含农夫乐事小刀） */
    private static boolean isDustOnAttackTool(ItemStack stack) {
        if (!(stack.getItem() instanceof net.minecraft.world.item.TieredItem tiered)
                || tiered.getTier() != com.hjmmd_8.bettergold.material.AllTiers.NETHERITE_ANTIQUE) {
            return false;
        }
        Item item = stack.getItem();
        return !(item instanceof net.minecraft.world.item.PickaxeItem)
                && !(item instanceof net.minecraft.world.item.ShovelItem)
                && !(item instanceof net.minecraft.world.item.HoeItem);
    }

    /** 挖掘型：下界合金古董的斧/镐/锹/锄 */
    private static boolean isDustOnMineTool(ItemStack stack) {
        Item item = stack.getItem();
        return item instanceof net.minecraft.world.item.PickaxeItem
                || item instanceof net.minecraft.world.item.AxeItem
                || item instanceof net.minecraft.world.item.ShovelItem
                || item instanceof net.minecraft.world.item.HoeItem;
    }

    /** 读取物品上某附魔的等级（注册表缺失时返回 0） */
    private static int enchantLevel(ItemStack stack, Level level,
                                    net.minecraft.resources.ResourceKey<net.minecraft.world.item.enchantment.Enchantment> key) {
        try {
            var lookup = level.registryAccess().lookupOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT);
            return lookup.get(key).map(stack::getEnchantmentLevel).orElse(0);
        } catch (Exception ignored) {
            return 0;
        }
    }

    /** 在指定位置生成一个物品实体 */
    private static void dropItem(Level level, double x, double y, double z, ItemStack stack) {
        if (level instanceof ServerLevel serverLevel) {
            ItemEntity drop = new ItemEntity(serverLevel, x, y, z, stack);
            drop.setDefaultPickUpDelay();
            serverLevel.addFreshEntity(drop);
        }
    }

    // ==================== 金钱贝战利品掉落 ====================

    @SubscribeEvent
    public static void onLivingDrops(LivingDropsEvent event) {
        Entity entity = event.getEntity();
        Level level = entity.level();
        if (level.isClientSide) {
            return;
        }
        float chance = 0.0F;
        if (entity.getType() == EntityType.PIGLIN_BRUTE) {
            chance = 0.50F; // 猪灵蛮兵 50%
        } else if (entity.getType() == EntityType.PIGLIN) {
            chance = 0.15F; // 普通猪灵 15%
        } else if (entity.getType() == EntityType.ZOMBIFIED_PIGLIN) {
            chance = 0.05F; // 僵尸猪灵 5%
        }
        if (chance <= 0.0F) {
            return;
        }
        if (level.random.nextFloat() < chance) {
            event.getDrops().add(new ItemEntity(level, entity.getX(), entity.getY(), entity.getZ(),
                    new ItemStack(AllItems.GOLDEN_COWRIE.get())));
        }
    }

    // ==================== 工具方法 ====================

    /**
     * 按权重掷出金系掉落：
     * - 白板（无附魔）：从基础池（金钱贝/金锭/金粒/粗金）随机；
     * - 有"取其金食"附魔：基础池 + 金食物池，附魔金苹果单独 1%。
     * 均受配置黑/白名单过滤。
     */
    private static Item rollGoldLoot(Player player, ItemStack held) {
        var random = player.getRandom();
        boolean hasFoodEnchant = hasTakeGoldFood(held);
        // 附魔金苹果 1% 特判（仅附魔后才有）
        if (hasFoodEnchant && random.nextDouble() < ENCHANTED_GOLDEN_APPLE_WEIGHT
                && isAllowedByConfig(Items.ENCHANTED_GOLDEN_APPLE)) {
            return Items.ENCHANTED_GOLDEN_APPLE;
        }
        // 构建按配置过滤后的掉落池
        List<Item> pool = new java.util.ArrayList<>(BASE_GOLD_LOOT_POOL.stream()
                .filter(ModEvents::isAllowedByConfig).toList());
        if (hasFoodEnchant) {
            pool.addAll(GOLD_FOOD_LOOT_POOL.stream()
                    .filter(ModEvents::isAllowedByConfig).toList());
        }
        if (pool.isEmpty()) {
            return Items.GOLD_NUGGET; // 兜底：全被过滤时掉金粒
        }
        return pool.get(random.nextInt(pool.size()));
    }

    /** 手持物品是否带有"取其金食"附魔 */
    private static boolean hasTakeGoldFood(ItemStack stack) {
        if (stack == null || stack.isEmpty()) {
            return false;
        }
        for (net.minecraft.core.Holder<net.minecraft.world.item.enchantment.Enchantment> holder
                : stack.getEnchantments().keySet()) {
            if (holder.is(TAKE_GOLD_FOOD_KEY)) {
                return true;
            }
        }
        return false;
    }

    /** 按配置黑/白名单判断物品是否允许掉落 */
    private static boolean isAllowedByConfig(Item item) {
        String mode = Config.GOLD_LOOT_MODE.get();
        List<? extends String> configured = Config.GOLD_LOOT_ITEMS.get();
        if (configured == null || configured.isEmpty()) {
            return true; // 空列表 = 不限制
        }
        String itemName = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(item).toString();
        boolean listed = configured.contains(itemName);
        if ("whitelist".equalsIgnoreCase(mode)) {
            return listed;
        }
        // blacklist（默认）
        return !listed;
    }

    /** 玩家是否穿戴任意一件万坚金盔甲（单件即可，无需全套） */
    public static boolean wearingAnySturdygoldArmor(Player player) {
        return player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.HEAD).is(AllItems.STURDYGOLD_HELMET.get())
                || player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST).is(AllItems.STURDYGOLD_CHESTPLATE.get())
                || player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.LEGS).is(AllItems.STURDYGOLD_LEGGINGS.get())
                || player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.FEET).is(AllItems.STURDYGOLD_BOOTS.get());
    }

    /** 校验物品是否为万坚金工具：材质 tier 为 STURDYGOLD 的任何 TieredItem（剑/镐/斧/锹/锄，含 FD 联动小刀） */
    private static boolean isSturdygoldTool(ItemStack stack) {
        return stack.getItem() instanceof net.minecraft.world.item.TieredItem tiered
                && tiered.getTier() == com.hjmmd_8.bettergold.material.AllTiers.STURDYGOLD;
    }

    // ==================== 抗寒性：免疫冰冻伤害 ====================

    @SubscribeEvent
    public static void onLivingIncomingDamageCold(LivingIncomingDamageEvent event) {
        LivingEntity entity = event.getEntity();
        // 免疫冰冻伤害（细雪冻伤 FREEZE）
        if (event.getSource().is(DamageTypes.FREEZE)
                && entity.hasEffect(AllEffects.COLD_RESISTANCE)) {
            event.setCanceled(true);
        }
    }

    // ==================== 锄头点击金染土 → 金染耕地 ====================

    @SubscribeEvent
    public static void onBlockToolModification(BlockEvent.BlockToolModificationEvent event) {
        if (event.isSimulated()) {
            return;
        }
        if (!ItemAbilities.HOE_TILL.equals(event.getItemAbility())) {
            return;
        }
        BlockState state = event.getState();
        if (state.is(AllBlocks.GOLD_INFUSED_DIRT.get())) {
            event.setFinalState(AllBlocks.GOLD_INFUSED_FARMLAND.get().defaultBlockState());
        }
    }

    // ==================== 食用金食物特殊效果 ====================

    @SubscribeEvent
    public static void onItemUseFinish(LivingEntityUseItemEvent.Finish event) {
        LivingEntity entity = event.getEntity();
        if (entity.level().isClientSide) {
            return;
        }
        ItemStack stack = event.getItem();
        Item item = stack.getItem();

        // 金冰淇淋：立即去除燃烧状态（并返还木碗由 craftRemainder 处理）
        if (item == AllItems.GOLDEN_ICE_CREAM.get() || item == AllItems.STURDYGOLD_ICE_CREAM.get()) {
            entity.clearFire();
        }

        // 金酿热可可 / 万坚金酿热可可：只清除负面效果，保留正面效果（如夜视/力量等增益）
        if (item == AllItems.BREWED_HOT_COCOA.get() || item == AllItems.STURDYGOLD_BREWED_HOT_COCOA.get()) {
            clearHarmfulEffects(entity);
            // 抗寒性由 FoodProperties 效果提供（保留不重复添加）
        }

        // ---- 新约 1.2：曲奇 / 面包 / 三明治 清除状态 ----
        if (item == AllItems.GOLDEN_CHOCOLATE_COOKIE.get()) {
            // 金巧克力曲奇：去饥饿
            entity.removeEffect(net.minecraft.world.effect.MobEffects.HUNGER);
        } else if (item == AllItems.STURDYGOLD_CHOCOLATE_COOKIE.get()) {
            // 万坚金巧克力曲奇：去饥饿 + 虚弱
            entity.removeEffect(net.minecraft.world.effect.MobEffects.HUNGER);
            entity.removeEffect(net.minecraft.world.effect.MobEffects.WEAKNESS);
        } else if (item == AllItems.GOLDEN_HONEY_COOKIE.get()) {
            // 金蜂蜜曲奇：去中毒
            entity.removeEffect(net.minecraft.world.effect.MobEffects.POISON);
        } else if (item == AllItems.STURDYGOLD_HONEY_COOKIE.get()) {
            // 万坚金蜂蜜曲奇：去中毒 + 凋零
            entity.removeEffect(net.minecraft.world.effect.MobEffects.POISON);
            entity.removeEffect(net.minecraft.world.effect.MobEffects.WITHER);
        } else if (item == AllItems.GOLDEN_BREAD.get()) {
            // 金砖面包：去饥饿 + 反胃
            entity.removeEffect(net.minecraft.world.effect.MobEffects.HUNGER);
            entity.removeEffect(net.minecraft.world.effect.MobEffects.CONFUSION);
        } else if (item == AllItems.STURDYGOLD_BREAD.get()) {
            // 万坚金砖面包：清除全部负面状态
            clearHarmfulEffects(entity);
        } else if (item == AllItems.GOLDEN_EGG_SANDWICH.get()) {
            // 金蛋三明治：去饥饿 + 反胃
            entity.removeEffect(net.minecraft.world.effect.MobEffects.HUNGER);
            entity.removeEffect(net.minecraft.world.effect.MobEffects.CONFUSION);
        } else if (item == AllItems.STURDYGOLD_EGG_SANDWICH.get()) {
            // 万坚金蛋三明治：清除全部负面状态
            clearHarmfulEffects(entity);
        }
    }

    /** 只清除实体身上的负面状态效果（保留正面效果） */
    private static void clearHarmfulEffects(LivingEntity entity) {
        java.util.Set<net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect>> effects =
                java.util.Set.copyOf(entity.getActiveEffectsMap().keySet());
        for (net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> effect : effects) {
            // 只移除负面（HARMFUL）效果
            if (effect.value().getCategory() == net.minecraft.world.effect.MobEffectCategory.HARMFUL) {
                entity.removeEffect(effect);
            }
        }
    }

    // ==================== 金钥匙：打开铁门/铁活板门/万坚金门/万坚金活板门 ====================

    @SubscribeEvent
    public static void onRightClickBlock(net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock event) {
        if (event.getLevel().isClientSide) {
            return;
        }
        Player player = event.getEntity();
        ItemStack held = event.getItemStack();
        if (!held.is(AllItems.GOLDEN_KEY.get())) {
            return;
        }
        Level level = event.getLevel();
        BlockPos pos = event.getPos();
        BlockState state = level.getBlockState(pos);
        net.minecraft.world.level.block.Block block = state.getBlock();
        boolean opened = false;

        if (block instanceof net.minecraft.world.level.block.DoorBlock door) {
            // 铁门 / 万坚金门
            if (block == net.minecraft.world.level.block.Blocks.IRON_DOOR || block == AllBlocks.STURDYGOLD_DOOR.get()) {
                boolean open = !door.isOpen(state);
                door.setOpen(player, level, state, pos, open);
                level.levelEvent(player, open ? 1005 : 1011, pos, 0); // 门开/关音效
                opened = true;
            }
        } else if (block instanceof net.minecraft.world.level.block.TrapDoorBlock) {
            // 铁活板门 / 万坚金活板门
            if (block == net.minecraft.world.level.block.Blocks.IRON_TRAPDOOR || block == AllBlocks.STURDYGOLD_TRAPDOOR.get()) {
                boolean open = !state.getValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.OPEN);
                level.setBlock(pos, state.setValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.OPEN, open), 2);
                level.levelEvent(player, open ? 1007 : 1008, pos, 0); // 活板门开/关音效
                opened = true;
            }
        }

        if (opened) {
            // 金钥匙使用音效（金属解锁声）
            level.playSound(null, pos, net.minecraft.sounds.SoundEvents.IRON_DOOR_OPEN,
                    net.minecraft.sounds.SoundSource.BLOCKS, 1.0F, 1.0F);
            // 消耗钥匙耐久（每次使用扣 1 点，64 耐久）
            if (!player.getAbilities().instabuild) {
                held.hurtAndBreak(1, player, event.getHand() == net.minecraft.world.InteractionHand.MAIN_HAND
                        ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND);
            }
            event.setCanceled(true);
        }
    }

    // ==================== 原版金胡萝卜本尊可直接种到金染耕地 ====================

    @SubscribeEvent
    public static void onRightClickGoldenCarrot(net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock event) {
        if (event.getLevel().isClientSide) {
            return;
        }
        Player player = event.getEntity();
        ItemStack held = event.getItemStack();
        // 手持原版金胡萝卜
        if (!held.is(Items.GOLDEN_CARROT)) {
            return;
        }
        Level level = event.getLevel();
        BlockPos pos = event.getPos();
        BlockState clickedState = level.getBlockState(pos);
        // 点击金染耕地
        if (!(clickedState.getBlock() instanceof GoldInfusedFarmlandBlock)) {
            return;
        }
        BlockPos plantPos = pos.above();
        BlockState plantState = level.getBlockState(plantPos);
        if (plantState.isAir() || plantState.canBeReplaced()) {
            BlockState cropState = AllBlocks.GOLDEN_CARROT_CROP.get().defaultBlockState();
            if (cropState.canSurvive(level, plantPos)) {
                level.setBlock(plantPos, cropState, 3);
                // 种植音效（原版种子种植音效）
                level.playSound(null, plantPos, net.minecraft.sounds.SoundEvents.CROP_PLANTED,
                        net.minecraft.sounds.SoundSource.BLOCKS, 1.0F, 1.0F);
                if (!player.getAbilities().instabuild) {
                    held.shrink(1);
                }
                event.setCanceled(true);
            }
        }
    }

    // ==================== 新约 1.2：金麦块免疫摔落 ====================

    @SubscribeEvent
    public static void onLivingFall(net.neoforged.neoforge.event.entity.living.LivingFallEvent event) {
        LivingEntity entity = event.getEntity();
        if (entity.level().isClientSide) {
            return;
        }
        // 落在金麦块上（落地位置下方的方块）完全免疫摔落伤害
        BlockPos below = entity.getOnPos();
        if (entity.level().getBlockState(below).is(AllBlocks.GOLDEN_WHEAT_BLOCK.get())) {
            event.setCanceled(true);
        }
    }

    // ==================== 新约 1.2：喂食互动（马食 / 金蛋） ====================

    @SubscribeEvent
    public static void onEntityInteract(net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract event) {
        if (event.getLevel().isClientSide) {
            return;
        }
        Player player = event.getEntity();
        ItemStack held = event.getItemStack();
        net.minecraft.world.entity.Entity target = event.getTarget();
        if (!(target instanceof LivingEntity living)) {
            return;
        }

        // --- 全金马食 / 万坚金马食：喂马/驴/骡/羊驼/行商羊驼 ---
        boolean isFeed = held.is(AllItems.GOLDEN_HORSE_FEED.get()) || held.is(AllItems.STURDYGOLD_HORSE_FEED.get());
        boolean isTameableHorse = target.getType() == EntityType.HORSE
                || target.getType() == EntityType.DONKEY
                || target.getType() == EntityType.MULE
                || target.getType() == EntityType.LLAMA
                || target.getType() == EntityType.TRADER_LLAMA;
        if (isFeed && isTameableHorse) {
            // 回满血
            living.heal(living.getMaxHealth());
            boolean sturdy = held.is(AllItems.STURDYGOLD_HORSE_FEED.get());
            if (sturdy) {
                // 万坚金马食：16 分钟迅捷4(amplifier3) + 跳跃提升3(amplifier2)
                living.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 19200, 3));
                living.addEffect(new MobEffectInstance(MobEffects.JUMP, 19200, 2));
            } else {
                // 全金马食：6 分钟迅捷3(amplifier2) + 跳跃提升2(amplifier1)
                living.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 7200, 2));
                living.addEffect(new MobEffectInstance(MobEffects.JUMP, 7200, 1));
            }
            if (!player.getAbilities().instabuild) {
                held.shrink(1);
            }
            event.setCanceled(true);
            return;
        }

        // --- 金蛋：用金麦种子或金钱茄种子喂鸡，36% 概率获得 ---
        boolean isSeed = held.is(AllItems.GOLDEN_WHEAT_SEEDS.get()) || held.is(AllItems.GOLDEN_EGGPLANT_SEEDS.get());
        if (isSeed && target.getType() == EntityType.CHICKEN) {
            if (!player.getAbilities().instabuild) {
                held.shrink(1);
            }
            // 喂食音效
            event.getLevel().playSound(null, target.blockPosition(), net.minecraft.sounds.SoundEvents.GENERIC_EAT,
                    net.minecraft.sounds.SoundSource.NEUTRAL, 1.0F, 1.0F);
            // 36% 概率产下金蛋实体（模拟原版鸡下蛋：掉落物）
            if (event.getLevel().random.nextFloat() < 0.36F) {
                ItemEntity egg = new ItemEntity(event.getLevel(),
                        target.getX(), target.getY(), target.getZ(),
                        new ItemStack(AllItems.GOLDEN_EGG.get()));
                egg.setDefaultPickUpDelay();
                event.getLevel().addFreshEntity(egg);
            }
            event.setCanceled(true);
        }
    }
}
