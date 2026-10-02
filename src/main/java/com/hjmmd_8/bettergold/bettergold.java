package com.hjmmd_8.bettergold;

import com.hjmmd_8.bettergold.config.Config;
import com.hjmmd_8.bettergold.event.ModBrewing;
import com.hjmmd_8.bettergold.event.ModEvents;
import com.hjmmd_8.bettergold.material.CreativePageSections;
import com.hjmmd_8.bettergold.material.SectionedCreativeTab;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllEffects;
import com.hjmmd_8.bettergold.registry.AllItems;
import com.hjmmd_8.bettergold.registry.AllLootModifiers;
import com.hjmmd_8.bettergold.registry.AllRecipes;

import org.slf4j.Logger;

import com.mojang.logging.LogUtils;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartingEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

// The value here should match an entry in the META-INF/neoforge.mods.toml file
@Mod(bettergold.MODID)
public class bettergold {
    // Define mod id in a common place for everything to reference
    public static final String MODID = "bettergold";
    // Directly reference a slf4j logger
    public static final Logger LOGGER = LogUtils.getLogger();
    // Create a Deferred Register to hold CreativeModeTabs which will all be registered under the "bettergold" namespace
    public static final DeferredRegister<CreativeModeTab> CREATIVE_MODE_TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    // ==================== 创造模式标签页：本体只有一个页（页内 5 条横幅分区） ====================
    // 作者定稿形态：本模组全部内容合并到「一个」创造页里，页内用 5 条横幅把内容分成 5 个分区
    // （材料 materials.png / 建筑 blocks.png / 食物 food.png / 装备 gear.png / 乐事 fd.png）。
    // 每个分区是<b>一个连续的物品列表</b>：分区内部的先后（例：材料 = 其他材料 → 交易金商人相关 → 金属）
    // 只是同一个列表里的次序，<b>不再各占一条横幅、也不插额外空行</b>。
    // 分区声明集中在 material.CreativePageSections / material.CreativeTabSections：
    // 金属出场顺序只在那两处维护，以后加金属不用改本文件。
    // 乐事分区由 FD 模块自己注入（fd.FdModule.register → fd.FdTabs.FD_SECTION），核心代码不引用 FdItems。

    /** 本模组唯一创造页（页内 5 个横幅分区：材料 / 建筑 / 食物 / 装备 / 乐事）：图标 = 万坚金锭 */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> BETTERGOLD_TAB =
            CREATIVE_MODE_TABS.register(CreativePageSections.PAGE_TAB_ID.getPath(), () ->
                    SectionedCreativeTab.builder()
                            .title(Component.translatable("itemGroup.bettergold"))
                            .icon(() -> AllItems.STURDYGOLD_INGOT.get().getDefaultInstance())
                            // 位置：所有普通原版页之后。语义提醒：withTabsBefore(X) = X 在本页之前。
                            // 只锚 CreativeModeTabs.SPAWN_EGGS —— 不要锚 HOTBAR/SEARCH/OP_BLOCKS/INVENTORY，
                            // 它们是 CreativeModeTabRegistry 里的 DEFAULT_TABS，被排除在排序图之外，
                            // 边会把它们重新拉回图里，把原版页挤乱。
                            .withTabsBefore(CreativeModeTabs.SPAWN_EGGS)
                            .build());

    // The constructor for the mod class is the first code that is run when your mod is loaded.
    // FML will recognize some parameter types like IEventBus or ModContainer and pass them in automatically.
    public bettergold(IEventBus modEventBus, ModContainer modContainer) {
        // Register the commonSetup method for modloading
        modEventBus.addListener(this::commonSetup);

        // Register the Deferred Register to the mod event bus so blocks get registered
        AllBlocks.BLOCKS.register(modEventBus);
        // Register the Deferred Register to the mod event bus so items get registered
        AllItems.ITEMS.register(modEventBus);
        // 新约 1.4：三套新金属（烈燃金 / 巫毒金 / 结雷金）通过 MetalFamily 一次性注册
        com.hjmmd_8.bettergold.material.AllMetals.bootstrap();
        // 新约 1.4：三套金属的专属材料（高燃烈焰棒 / 巫毒羽毛 / 聚紫能晶尘）
        com.hjmmd_8.bettergold.material.MetalSpecialItems.bootstrap();
        // 新约 1.5：5 件「胚底」（纯合成中间物，作者澄清：没有金制系列工具！
        // 它们只在合成链里：5 条工作台配方产出胚底 → 30 条锻造升级把胚底升级成六套金属武器）
        com.hjmmd_8.bettergold.material.MetalBlanks.bootstrap();
        // 新约 1.4：金属相关的全局事件（巫毒结束结算等）
        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.material.MetalEvents.class);
        // Register the Deferred Register to the mod event bus so creative tabs get registered
        CREATIVE_MODE_TABS.register(modEventBus);
        // Register custom recipe serializers
        AllRecipes.RECIPE_SERIALIZERS.register(modEventBus);
        // 新约 1.4：自定义网络通道（结雷金落雷音效 client_payload 档用）
        modEventBus.addListener(com.hjmmd_8.bettergold.network.BetterGoldNetwork::register);
        // Register custom mob effects
        AllEffects.EFFECTS.register(modEventBus);
        // Register global loot modifiers
        AllLootModifiers.GLM.register(modEventBus);
        // 新约 1.3：投掷物实体注册
        com.hjmmd_8.bettergold.registry.AllEntities.ENTITY_TYPES.register(modEventBus);
        // bg-15w：数据附件（掷出的三叉戟的金属 id，需要同步到客户端供实体渲染器取贴图）
        com.hjmmd_8.bettergold.registry.AllAttachments.ATTACHMENT_TYPES.register(modEventBus);
        // 新约 1.3：易金商人的工作站点（兴趣点）与村民职业
        com.hjmmd_8.bettergold.registry.AllVillagers.POI_TYPES.register(modEventBus);
        com.hjmmd_8.bettergold.registry.AllVillagers.PROFESSIONS.register(modEventBus);
        // Register brewing recipes on the game event bus (RegisterBrewingRecipesEvent is NOT an IModBusEvent)
        NeoForge.EVENT_BUS.addListener(ModBrewing::registerBrewingRecipes);

        // Register ourselves for server and other game events we are interested in.
        // Note that this is necessary if and only if we want *this* class (bettergold) to respond directly to events.
        // Do not add this line if there are no @SubscribeEvent-annotated functions in this class, like onServerStarting() below.
        NeoForge.EVENT_BUS.register(this);
        // Register the mod's business event handlers (tool loot drops, piglin neutrality, bartering boost, cowrie drops)
        NeoForge.EVENT_BUS.register(ModEvents.class);
        // 新约 1.3：易金商人交易列表
        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);

        // FD（农夫乐事）联动模块：仅在 FD 已加载时挂载（物品/方块/配方/标签页/事件整体装配）
        if (com.hjmmd_8.bettergold.fd.FdModule.isLoaded()) {
            com.hjmmd_8.bettergold.fd.FdModule.register(modEventBus);
        }

        // Register our mod's ModConfigSpec so that FML can create and load the config file for us
        modContainer.registerConfig(ModConfig.Type.COMMON, Config.SPEC);
        // 启动自证：配置加载时把「版本 + thunderSoundMode + 配置文件里有没有这个键」打进日志
        modEventBus.addListener(com.hjmmd_8.bettergold.config.StartupSelfCheck::onConfigLoading);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        // Some common setup code
        LOGGER.info("HELLO FROM COMMON SETUP");

        // 启动自证：打印「模组版本 + thunderSoundMode 实际取值 + 配置文件里有没有这个键」。
        // 作者排查「听不到落雷」时，第一件事就是看这行是不是新构建。
        event.enqueueWork(com.hjmmd_8.bettergold.config.StartupSelfCheck::log);

        if (Config.LOG_DIRT_BLOCK.getAsBoolean()) {
            LOGGER.info("DIRT BLOCK >> {}", BuiltInRegistries.BLOCK.getKey(Blocks.DIRT));
        }

        LOGGER.info("{}{}", Config.MAGIC_NUMBER_INTRODUCTION.get(), Config.MAGIC_NUMBER.getAsInt());

        Config.ITEM_STRINGS.get().forEach((item) -> LOGGER.info("ITEM >> {}", item));
    }

    // You can use SubscribeEvent and let the Event Bus discover methods to call
    @SubscribeEvent
    public void onServerStarting(ServerStartingEvent event) {
        // Do something when the server starts
        LOGGER.info("HELLO from server starting");
    }

}
