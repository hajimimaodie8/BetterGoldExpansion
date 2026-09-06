package com.hjmmd_8.bettergold.fd;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * FD（农夫乐事）联动分支的创造模式标签页。
 * 独立 DeferredRegister（namespace 仍是 bettergold，tab id = bettergold_fd_tab），
 * 由 {@link FdModule} 在农夫乐事加载时挂载；FD 未装则本 tab 不出现。
 * 只展示 {@link FdItems#ITEMS}（含 {@link FdBlocks} 注册进其物品表的派/蛋糕 BlockItem）。
 */
public class FdTabs {

    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, bettergold.MODID);

    /** 本标签页的注册名（本体主标签页以 withTabsBefore 引用它，保证本体 tab 在前） */
    public static final ResourceLocation TAB_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "bettergold_fd_tab");

    /** 农夫乐事联动标签页 */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> FD_TAB =
            CREATIVE_MODE_TABS.register("bettergold_fd_tab", () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.bettergold_fd"))
                    .withTabsBefore(CreativeModeTabs.COMBAT)
                    .icon(() -> FdItems.ALCHEMICAL_MEAT.get().getDefaultInstance())
                    .displayItems((parameters, output) -> {
                        FdItems.ITEMS.getEntries().forEach(holder -> output.accept(holder.get()));
                    }).build());

    private FdTabs() {
    }
}
