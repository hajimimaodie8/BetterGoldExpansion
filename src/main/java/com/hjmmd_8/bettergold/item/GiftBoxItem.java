package com.hjmmd_8.bettergold.item;

import com.hjmmd_8.bettergold.fd.FdModule;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * 礼品盒（新约 1.3）：右键开启，**没有物品冷却**。
 *
 * 四种盒子：
 * - TREASURE（万宝礼物盒）：开出 6 份来自掠夺者前哨站 / 林地府邸 / 丛林神庙 / 沉船 / 沙漠神殿 /
 *   远古城市 / 猪灵堡垒 / 下界要塞 / 主世界要塞 / 末地城 / 试炼大厅的箱子战利品；
 * - CURIO（珍品古董盒）：开出 1 个"没人要的老古董"，36% 概率替换为一件古董器具；
 * - IDOL（金雕礼品盒）：开出 1 个金雕摆件；
 * - GOURMET（金享珍味盒）：开出 3 份金食物（含农夫乐事联动食物），每份 6% 概率替换为万坚金食物。
 */
public class GiftBoxItem extends Item {

    public enum Kind {
        TREASURE, CURIO, IDOL, GOURMET
    }

    private static final ResourceKey<LootTable>[] TREASURE_TABLES = new ResourceKey[]{
            chest("pillager_outpost"), chest("woodland_mansion"), chest("jungle_temple"),
            chest("shipwreck_treasure"), chest("desert_pyramid"), chest("ancient_city"),
            chest("bastion_treasure"), chest("nether_bridge"), chest("stronghold_corridor"),
            chest("end_city_treasure"), chest("trial_chambers/reward")
    };

    private static final ResourceKey<LootTable> chest(String path) {
        return ResourceKey.create(Registries.LOOT_TABLE, ResourceLocation.withDefaultNamespace("chests/" + path));
    }

    private final Kind kind;

    public GiftBoxItem(Properties properties, Kind kind) {
        super(properties);
        this.kind = kind;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel serverLevel) {
            List<ItemStack> loot = new ArrayList<>();
            switch (this.kind) {
                case TREASURE -> rollTreasure(serverLevel, player, loot);
                case CURIO -> rollCurio(loot);
                case IDOL -> rollIdol(loot);
                case GOURMET -> rollGourmet(loot);
            }
            loot.forEach(gift -> {
                if (gift.isEmpty()) {
                    return;
                }
                if (!player.getInventory().add(gift)) {
                    player.drop(gift, false);
                }
            });
            if (!player.getAbilities().instabuild) {
                stack.shrink(1);
            }
        }
        // 无冷却：右键即开
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    /** 万宝礼物盒：抽取 6 份结构箱子战利品（每份从随机结构箱表里取一次掉落） */
    private void rollTreasure(ServerLevel level, Player player, List<ItemStack> loot) {
        var random = level.getRandom();
        Vec3 origin = player.position();
        for (int i = 0; i < 6; i++) {
            ResourceKey<LootTable> key = TREASURE_TABLES[random.nextInt(TREASURE_TABLES.length)];
            rollOne(level, key, origin, loot::add);
        }
    }

    /** 从指定箱子表取第一件掉落（避免一次开出整箱物品） */
    private void rollOne(ServerLevel level, ResourceKey<LootTable> key, Vec3 origin, Consumer<ItemStack> out) {
        LootTable table = level.getServer().reloadableRegistries().getLootTable(key);
        LootParams params = new LootParams.Builder(level)
                .withParameter(LootContextParams.ORIGIN, origin)
                .create(LootContextParamSets.CHEST);
        List<ItemStack> rolled = new ArrayList<>();
        table.getRandomItems(params, rolled::add);
        rolled.stream().filter(s -> !s.isEmpty()).findFirst().ifPresent(out);
    }

    /** 珍品古董盒：1 个没人要的老古董，36% 概率替换为古董器具 */
    private void rollCurio(List<ItemStack> loot) {
        var random = net.minecraft.util.RandomSource.create();
        random.setSeed(System.nanoTime());
        if (random.nextFloat() < 0.36F) {
            List<Item> tools = antiqueTools();
            loot.add(new ItemStack(tools.get(random.nextInt(tools.size()))));
        } else {
            loot.add(new ItemStack(AllItems.UNWANTED_ANTIQUE.get()));
        }
    }

    /** 金雕礼品盒：1 个金雕摆件 */
    private void rollIdol(List<ItemStack> loot) {
        Item[] idols = new Item[]{
                AllBlocks.GOLDEN_CAT_FIGURINE_ITEM.get(),
                AllBlocks.GOLDEN_TOAD_FIGURINE_ITEM.get(),
                AllBlocks.GOLDEN_ENDERMAN_FIGURINE_ITEM.get(),
                AllBlocks.GOLDEN_CREEPER_FIGURINE_ITEM.get()
        };
        loot.add(new ItemStack(idols[net.minecraft.util.RandomSource.create().nextInt(idols.length)]));
    }

    /** 金享珍味盒：3 份金食物，每份 6% 概率替换为万坚金食物 */
    private void rollGourmet(List<ItemStack> loot) {
        var random = net.minecraft.util.RandomSource.create();
        random.setSeed(System.nanoTime());
        List<Item> golden = goldenFoods();
        List<Item> sturdy = sturdygoldFoods();
        for (int i = 0; i < 3; i++) {
            boolean upgraded = random.nextFloat() < 0.06F;
            List<Item> pool = upgraded && !sturdy.isEmpty() ? sturdy : golden;
            loot.add(new ItemStack(pool.get(random.nextInt(pool.size()))));
        }
    }

    /** 古董器具（含农夫乐事联动的小刀） */
    private static List<Item> antiqueTools() {
        List<Item> tools = new ArrayList<>(List.of(
                AllItems.ANTIQUE_SWORD.get(), AllItems.ANTIQUE_AXE.get(), AllItems.ANTIQUE_PICKAXE.get(),
                AllItems.ANTIQUE_SHOVEL.get(), AllItems.ANTIQUE_HOE.get()));
        if (FdModule.isLoaded()) {
            tools.add(com.hjmmd_8.bettergold.fd.FdItems.ANTIQUE_KNIFE.get());
        }
        return tools;
    }

    /** 金食物池 */
    private static List<Item> goldenFoods() {
        List<Item> foods = new ArrayList<>(List.of(
                Items.GOLDEN_APPLE, Items.GOLDEN_CARROT,
                AllItems.GOLDEN_CHOCOLATE_BAR.get(), AllItems.GOLDEN_ICE_CREAM.get(),
                AllItems.GOLDEN_SUGAR_CANE_STICK.get(), AllItems.GOLDEN_EGGPLANT.get(),
                AllItems.GOLDEN_BREAD.get(), AllItems.GOLDEN_EGG_SANDWICH.get(),
                AllItems.GOLDEN_CHOCOLATE_COOKIE.get(), AllItems.GOLDEN_HONEY_COOKIE.get(),
                AllItems.FRIED_GOLDEN_EGG.get()));
        if (FdModule.isLoaded()) {
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.ALCHEMICAL_MEAT.get());
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.ALCHEMICAL_MEAT_SKEWER.get());
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.ALCHEMICAL_MEAT_SANDWICH.get());
        }
        return foods;
    }

    /** 万坚金食物池 */
    private static List<Item> sturdygoldFoods() {
        List<Item> foods = new ArrayList<>(List.of(
                AllItems.STURDYGOLD_APPLE.get(), AllItems.STURDYGOLD_CARROT.get(),
                AllItems.STURDYGOLD_CHOCOLATE_BAR.get(), AllItems.STURDYGOLD_ICE_CREAM.get(),
                AllItems.STURDYGOLD_SUGAR_CANE_STICK.get(), AllItems.STURDYGOLD_EGGPLANT.get(),
                AllItems.STURDYGOLD_BREAD.get(), AllItems.STURDYGOLD_EGG_SANDWICH.get(),
                AllItems.STURDYGOLD_CHOCOLATE_COOKIE.get(), AllItems.STURDYGOLD_HONEY_COOKIE.get(),
                AllItems.STURDYGOLD_FRIED_GOLDEN_EGG.get()));
        if (FdModule.isLoaded()) {
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.STURDYGOLD_ALCHEMICAL_MEAT.get());
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.STURDYGOLD_ALCHEMICAL_MEAT_SKEWER.get());
            foods.add(com.hjmmd_8.bettergold.fd.FdItems.STURDYGOLD_ALCHEMICAL_MEAT_SANDWICH.get());
        }
        return foods;
    }
}
