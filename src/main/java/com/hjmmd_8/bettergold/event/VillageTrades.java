package com.hjmmd_8.bettergold.event;

import com.hjmmd_8.bettergold.registry.AllItems;
import com.hjmmd_8.bettergold.registry.AllVillagers;

import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import net.minecraft.world.entity.npc.VillagerTrades;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.BasicItemListing;
import net.neoforged.neoforge.event.village.VillagerTradesEvent;

import java.util.List;

/**
 * 新约 1.3：易金商人交易列表。
 *
 * 等级：新手 1 / 学徒 2 / 老手 3。交易次数上限按作者要求"能拉多大拉多大"（999）。
 * - 新手：6 绿宝石 → 1 金锭（5 经验）；45 金钱贝 → 1 礼品金票（20 经验）
 * - 学徒：3 礼品金票 → 万宝礼物盒；4 礼品金票 → 珍品古董盒
 * - 老手：5 礼品金票 → 金雕礼品盒；6 礼品金票 → 金享珍味盒
 */
public class VillageTrades {

    /** 交易次数上限（作者要求尽量大） */
    private static final int MAX_USES = 999;

    @SubscribeEvent
    public static void onVillagerTrades(VillagerTradesEvent event) {
        if (event.getType() != AllVillagers.GOLD_TRADER.get()) {
            return;
        }
        Int2ObjectMap<List<VillagerTrades.ItemListing>> trades = event.getTrades();

        // ---- 新手 ----
        trades.get(1).add(new BasicItemListing(new ItemStack(Items.EMERALD, 6),
                new ItemStack(Items.GOLD_INGOT), MAX_USES, 5, 0.05F));
        trades.get(1).add(new BasicItemListing(new ItemStack(AllItems.GOLDEN_COWRIE.get(), 45),
                new ItemStack(AllItems.GIFT_GOLD_TICKET.get()), MAX_USES, 20, 0.05F));

        // ---- 学徒 ----
        trades.get(2).add(new BasicItemListing(new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), 3),
                new ItemStack(AllItems.TREASURE_GIFT_BOX.get()), MAX_USES, 20, 0.05F));
        trades.get(2).add(new BasicItemListing(new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), 4),
                new ItemStack(AllItems.CURIO_BOX.get()), MAX_USES, 20, 0.05F));

        // ---- 老手 ----
        trades.get(3).add(new BasicItemListing(new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), 5),
                new ItemStack(AllItems.IDOL_GIFT_BOX.get()), MAX_USES, 20, 0.05F));
        trades.get(3).add(new BasicItemListing(new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), 6),
                new ItemStack(AllItems.GOURMET_BOX.get()), MAX_USES, 20, 0.05F));
    }

    private VillageTrades() {
    }
}
