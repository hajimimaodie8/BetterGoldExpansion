package com.hjmmd_8.bettergold.event;

import com.hjmmd_8.bettergold.material.MetalSpecialItems;
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
 * - 新手：6 绿宝石 → 1 金锭（5 经验）；45 金钱贝 → 1 礼品金票（20 经验）；
 *         6 巫毒羽毛 → 1 礼品金票（10 经验，1.4 新增）
 * - 学徒：3 礼品金票 → 万宝礼物盒；4 礼品金票 → 珍品古董盒
 * - 老手：5 礼品金票 → 金雕礼品盒；6 礼品金票 → 金享珍味盒
 *
 * <p><b>为什么 maxUses 取 {@link #MAX_USES}=999 就是"可选上限内的最大值"</b>：
 * {@code BasicItemListing.maxTrades}、{@code MerchantOffer.maxUses} 都是普通 {@code int}，
 * 没有任何游戏侧上限（{@code MerchantOffer.CODEC} 用 {@code Codec.INT}、
 * 网络用 {@code buffer.writeInt(getMaxUses())}，都能到 {@code Integer.MAX_VALUE}；
 * 源码见 {@code net.minecraft.world.item.trading.MerchantOffer} 第 19 / 154 / 237 行）。
 * 也就是说 999 不是引擎硬上限，而是<b>本项目可选范围内的最大值</b>：
 * 它是本文件既有的、也是全部 6 条交易共用的那个上限，已远大于任何玩家的实际交易次数；
 * 再往上写只会引入一个没有意义的更大魔数（并且会让 demand 折扣算得更极端），
 * 所以"能设多大就设多大"在这里 = 沿用本文件最大的既有值 999。</p>
 */
public class VillageTrades {

    /** 交易次数上限（作者要求尽量大；本文件全部交易的统一上限） */
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
        // 1.4 新增：6 巫毒羽毛 → 1 礼品金票（10 经验）
        trades.get(1).add(new BasicItemListing(new ItemStack(MetalSpecialItems.VOODOO_FEATHER.get(), 6),
                new ItemStack(AllItems.GIFT_GOLD_TICKET.get()), MAX_USES, 10, 0.05F));

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

        // ---- 专家（第 4 级）----
        // 1.6（bg-16 §4.2）：7 张礼品金票 + 20 经验 ⇒ 1 个炼金珍材盒。
        // ⚠ 两条与需求文档不一致、已按实际落档（详见 docs/1.6-规格.md §3.1）：
        //   ① 等级：作者说「专家售卖」⇒ 取第 4 级（Expert）—— 本文件此前最高只用到第 3 级（老手）；
        //      `computeIfAbsent` 是防御性的：自定义职业的等级表未必预先建了 4 号槽。
        //   ② 交易次数上限 = 999（沿用本文件其余 6 条的既有值）；需求 §7 #11 写的 99
        //      与它的理由"MC 交易上限"不成立 —— 见本文件类注释里的源码依据。
        trades.computeIfAbsent(4, k -> new java.util.ArrayList<>()).add(new BasicItemListing(
                new ItemStack(AllItems.GIFT_GOLD_TICKET.get(), 7),
                new ItemStack(AllItems.ALCHEMY_MATERIALS_BOX.get()), MAX_USES, 20, 0.05F));
    }

    private VillageTrades() {
    }
}
