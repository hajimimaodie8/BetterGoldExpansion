package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.material.CreativePageSections;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.common.NeoForge;

/**
 * FD（农夫乐事）联动模块的装配入口。
 *
 * 主类 {@code bettergold} 在农夫乐事已加载时调用 {@link #register(IEventBus)}，
 * 一次性把本模块的物品 / 方块 / 配方 / 事件 / 创造页内容全部挂到对应事件总线上；
 * FD 未加载时本模块整体不挂载，所有内容都不出现（无需逐条条件注册）。
 *
 * <p>本模组只有一个创造页（{@link CreativePageSections#PAGE_TAB_ID}），页内共 5 个横幅分区。
 * 乐事分区由本模块在这里<b>自己注入</b>：注册 {@link FdTabs#FD_SECTION}
 * （横幅 fd.png + 分区内部排列规则 + {@link FdItems} 的全部物品）。
 * 核心代码不认识 {@link FdItems}，所以没装 FD 时那一页自然只有 4 个分区。</p>
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
        // 把「乐事分区」注入本模组唯一的创造页（不再单独注册创造标签页）
        CreativePageSections.register(FdTabs.FD_SECTION);
        // FD 物品吃完后的效果（滋养）走游戏事件总线
        NeoForge.EVENT_BUS.register(FdEvents.class);
    }
}
