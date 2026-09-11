package com.hjmmd_8.bettergold.registry;

import com.google.common.collect.ImmutableSet;
import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 新约 1.3：易金商人村民职业与其工作站（易金柜台）。
 *
 * - {@link #GOLD_TRADER_POI}：工作站点兴趣类型，匹配"易金柜台"方块的全部状态；
 * - {@link #GOLD_TRADER}：易金商人职业，工作站点只认易金柜台，工作音效沿用制图师。
 * 交易列表见 {@link com.hjmmd_8.bettergold.event.VillageTrades}（VillagerTradesEvent）。
 */
public class AllVillagers {

    public static final DeferredRegister<PoiType> POI_TYPES =
            DeferredRegister.create(Registries.POINT_OF_INTEREST_TYPE, bettergold.MODID);

    public static final DeferredRegister<VillagerProfession> PROFESSIONS =
            DeferredRegister.create(Registries.VILLAGER_PROFESSION, bettergold.MODID);

    /** 易金柜台工作站 */
    public static final DeferredHolder<PoiType, PoiType> GOLD_TRADER_POI = POI_TYPES.register("gold_trader",
            () -> new PoiType(
                    ImmutableSet.copyOf(AllBlocks.GOLD_EXCHANGE_COUNTER.get().getStateDefinition().getPossibleStates()),
                    1, 1));

    /** 易金商人职业 */
    public static final DeferredHolder<VillagerProfession, VillagerProfession> GOLD_TRADER =
            PROFESSIONS.register("gold_trader", () -> new VillagerProfession(
                    "bettergold:gold_trader",
                    holder -> holder.is(GOLD_TRADER_POI.getKey()),
                    holder -> holder.is(GOLD_TRADER_POI.getKey()),
                    ImmutableSet.of(),
                    ImmutableSet.of(),
                    SoundEvents.VILLAGER_WORK_CARTOGRAPHER));

    private AllVillagers() {
    }
}
