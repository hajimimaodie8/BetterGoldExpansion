package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.menu.SturdygoldAnvilMenu;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * <b>容器类型（{@code MenuType}）注册</b> —— 本仓第一次（1.7 {@code bg-n10} 轮8，万坚金砧）。
 *
 * <h2>1.21.1 / NeoForge 21.1 的事实（照源码，别照记忆）</h2>
 * <ul>
 *   <li><b>没有</b> Forge 时代的 {@code RegisterMenuTypes} 事件 —— 派单里点名的那个名字是<b>旧口径</b>：
 *       {@code MenuType} 就是普通注册表条目（{@code Registries.MENU}），用 {@code DeferredRegister} 注册，
 *       <b>双端</b>都走这一条（本类在 {@code bettergold} 主类里 register 到 mod 事件总线）。</li>
 *   <li>客户端 Screen 才需要单独注册：NeoForge 的事件是
 *       {@code net.neoforged.neoforge.client.event.RegisterMenuScreensEvent}
 *       （在 {@code bettergoldClient} 里挂），它写的是 {@code MenuScreens} 内部那张
 *       {@code Map<MenuType<?>, ScreenConstructor>}，最终被
 *       {@code ClientPacketListener#handleOpenScreen} → {@code MenuScreens#create} 读。</li>
 *   <li>工厂用 <b>2 参</b> {@code (int containerId, Inventory inv)}：服务端真正那份由方块给
 *       {@code SimpleMenuProvider} 带着 {@code ContainerLevelAccess} 造；客户端由本类造
 *       （access = {@code ContainerLevelAccess.NULL}）—— 与原版 {@code MenuType.ANVIL}
 *       （{@code MenuType.java:20} 就是 {@code register("anvil", AnvilMenu::new)}）逐字同构。</li>
 * </ul>
 */
public final class AllMenus {

    /** 容器类型注册表（{@code bettergold:sturdygold_anvil}） */
    public static final DeferredRegister<MenuType<?>> MENU_TYPES =
            DeferredRegister.create(Registries.MENU, bettergold.MODID);

    /**
     * 万坚金砧的容器。
     *
     * <p>⚠ {@code FeatureFlags.DEFAULT_FLAGS} ≡ NeoForge {@code IMenuTypeExtension#create} 用的那一档；
     * 原版内置用 {@code FeatureFlags.VANILLA_SET}，两者对"没有开关世界特性"的模组界面等价。</p>
     */
    public static final DeferredHolder<MenuType<?>, MenuType<SturdygoldAnvilMenu>> STURDYGOLD_ANVIL =
            MENU_TYPES.register("sturdygold_anvil",
                    () -> new MenuType<>(SturdygoldAnvilMenu::new, FeatureFlags.DEFAULT_FLAGS));

    private AllMenus() {
    }
}
