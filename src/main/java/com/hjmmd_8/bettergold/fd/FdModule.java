package com.hjmmd_8.bettergold.fd;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.common.NeoForge;

/**
 * FD（农夫乐事）联动模块的装配入口。
 *
 * 主类 {@code bettergold} 在农夫乐事已加载时调用 {@link #register(IEventBus)}，
 * 一次性把本模块的物品 / 方块 / 配方 / 标签页 / 事件全部挂到对应事件总线上；
 * FD 未加载时本模块整体不挂载，所有内容都不出现（无需逐条条件注册）。
 */
public final class FdModule {

    private FdModule() {
    }

    /** 农夫乐事是否已加载 */
    public static boolean isLoaded() {
        return ModList.get().isLoaded("farmersdelight");
    }

    /** 挂载 FD 模块的全部内容（仅在 {@link #isLoaded()} 为 true 时由主类调用） */
    public static void register(IEventBus modEventBus) {
        FdItems.ITEMS.register(modEventBus);
        FdBlocks.BLOCKS.register(modEventBus);
        FdRecipes.RECIPE_SERIALIZERS.register(modEventBus);
        FdTabs.CREATIVE_MODE_TABS.register(modEventBus);
        // FD 物品吃完后的效果（滋养）走游戏事件总线
        NeoForge.EVENT_BUS.register(FdEvents.class);
    }
}
