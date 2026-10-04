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
        TREASURE, CURIO, IDOL, GOURMET,
        /** 1.6（bg-16）：炼金珍材盒 —— 开出任意一族的核心材料（见 {@link #rollAlchemy}） */
        ALCHEMY
    }

    private static final ResourceKey<LootTable>[] TREASURE_TABLES = new ResourceKey[]{
            chest("pillager_outpost"), chest("woodland_mansion"), chest("jungle_temple"),
            chest("shipwreck_treasure"), chest("desert_pyramid"), chest("ancient_city"),
            chest("bastion_treasure"), chest("nether_bridge"), chest("stronghold_corridor"),
            chest("end_city_treasure"), chest("trial_chambers/reward"),
            // 1.6（bg-16）：追加「埋藏宝藏」（作者原话"就是那个能开出海洋之心的战利品表"）。
            // ⚠ 需求文档 §4.3 写的是「现有 8 张 ⇒ 追加后 9 张」，**与实际不符**：
            //   本表实际是 11 张 ⇒ 追加后 = 12 张（关卡按 12 写，见 docs/1.6-规格.md §3.1）。
            chest("buried_treasure")
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
        // 开盒音效：箱子打开的声音
        level.playSound(null, player.getX(), player.getY() + 0.5D, player.getZ(),
                net.minecraft.sounds.SoundEvents.CHEST_OPEN,
                net.minecraft.sounds.SoundSource.PLAYERS,
                0.8F, 1.0F + (level.getRandom().nextFloat() - level.getRandom().nextFloat()) * 0.1F);
        if (level instanceof ServerLevel serverLevel) {
            List<ItemStack> loot = new ArrayList<>();
            switch (this.kind) {
                case TREASURE -> rollTreasure(serverLevel, player, loot);
                case CURIO -> rollCurio(loot);
                case IDOL -> rollIdol(loot);
                case GOURMET -> rollGourmet(loot);
                case ALCHEMY -> rollAlchemy(loot);
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

    /** 金雕礼品盒：1 个金雕摆件（金猫摆件模型待重做，暂时移出奖池） */
    private void rollIdol(List<ItemStack> loot) {
        Item[] idols = new Item[]{
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

    /**
     * 炼金珍材盒（1.6 · bg-16）：开出 <b>1 个</b>「任意一族的核心材料」，八族等概率。
     *
     * <p>池子 = {@link com.hjmmd_8.bettergold.material.MetalFamily#all()} 里所有**声明了
     * {@code coreItem} 的族**（炽焰棒 / 巫毒羽毛 / 紫紫能晶尘 / 靛蓝海洋之心 / 紫颂樱花枝 /
     * 金钱贝 / 闪耀藤条 / 集束回响碎片）= 8 个 —— 刻意**从家族表现算**而不是写死清单：
     * 以后再加一族金属，它自动进池子（写死清单就是 AGENTS 红线 2「生成器清单漏项」的同一种形态）。</p>
     *
     * <p>⚠ 需求 §7 #12 的推断值表写的是「全部族的 coreItem，等概率（含新两族）」，
     * 而作者原话是「任意一个<b>特殊金属</b>的核心材料」；按 §12.3 万坚金是"基础套装"、
     * 严格讲不算特殊金属，但文档的池子清单里**含**金钱贝 ⇒ 本轮按文档的 8 族池落档，
     * 并在 docs/1.6-规格.md 里标注"作者一句话可改"。</p>
     */
    private void rollAlchemy(List<ItemStack> loot) {
        List<Item> pool = coreMaterials();
        if (pool.isEmpty()) {
            return;
        }
        var random = net.minecraft.util.RandomSource.create();
        random.setSeed(System.nanoTime());
        loot.add(new ItemStack(pool.get(random.nextInt(pool.size()))));
    }

    /** 八族的核心材料（{@code coreItem} 为空的族跳过）—— 从家族表现算，不写死清单 */
    private static List<Item> coreMaterials() {
        List<Item> pool = new ArrayList<>();
        for (var family : com.hjmmd_8.bettergold.material.MetalFamily.all()) {
            if (family.coreItem != null) {
                pool.add(family.coreItem.get());
            }
        }
        return pool;
    }

    /** 古董器具（含农夫乐事联动的小刀） */
    private static List<Item> antiqueTools() {        List<Item> tools = new ArrayList<>(List.of(
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
