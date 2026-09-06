package com.hjmmd_8.bettergold;

import com.hjmmd_8.bettergold.config.Config;
import com.hjmmd_8.bettergold.event.ModBrewing;
import com.hjmmd_8.bettergold.event.ModEvents;
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
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.ItemStack;
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

    // ==================== 创造模式标签页：本体三个相邻 tab（方块材料 / 食物饮品 / 装备工具） ====================
    // 仿照航空学 / Create 的"顶部相邻 tab 长带"：本体内容分类成三个 tab 图标紧挨排列，
    // 装了农夫乐事时 FD 联动 tab（fd.FdTabs）紧随其后，形成 本体→本体→本体→FD 的连续长带。
    // 分类判定集中见 {@link AllItems#tabCategoryOf}，增删物品时只需在集合里加/删注册名。

    /** 本体 tab 1（方块与材料）：图标 = 万坚金块 */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> BETTERGOLD_BLOCKS_TAB = CREATIVE_MODE_TABS.register("bettergold_tab", () -> {
        CreativeModeTab.Builder builder = CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.bettergold_blocks"))
                .icon(() -> AllBlocks.STURDYGOLD_BLOCK_ITEM.get().getDefaultInstance())
                .displayItems((parameters, output) -> {
                    AllItems.ITEMS.getEntries().forEach(holder -> {
                        ItemStack stack = holder.get().getDefaultInstance();
                        // 方块与材料：既不是食物也不是装备的，都归本页（方块 BlockItem + 锭/粒/原料/金钱贝/模具等）
                        if (!AllItems.isFoodTab(holder.getId(), stack) && !AllItems.isGearTab(holder.getId(), stack)) {
                            output.accept(holder.get());
                        }
                    });
                });
        // 位置链：方块材料 tab → 食物 tab
        builder.withTabsBefore(ResourceLocation.fromNamespaceAndPath(MODID, "bettergold_food_tab"));
        return builder.build();
    });

    /** 本体 tab 2（食物与饮品）：图标 = 万坚金苹果 */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> BETTERGOLD_FOOD_TAB = CREATIVE_MODE_TABS.register("bettergold_food_tab", () -> {
        CreativeModeTab.Builder builder = CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.bettergold_food"))
                .icon(() -> AllItems.STURDYGOLD_APPLE.get().getDefaultInstance())
                .displayItems((parameters, output) -> {
                    AllItems.ITEMS.getEntries().forEach(holder -> {
                        ItemStack stack = holder.get().getDefaultInstance();
                        if (AllItems.isFoodTab(holder.getId(), stack)) {
                            output.accept(holder.get());
                        }
                    });
                });
        builder.withTabsBefore(ResourceLocation.fromNamespaceAndPath(MODID, "bettergold_gear_tab"));
        return builder.build();
    });

    /** 本体 tab 3（装备工具）：图标 = 万坚金剑 */
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> BETTERGOLD_GEAR_TAB = CREATIVE_MODE_TABS.register("bettergold_gear_tab", () -> {
        CreativeModeTab.Builder builder = CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.bettergold_gear"))
                .icon(() -> AllItems.STURDYGOLD_SWORD.get().getDefaultInstance())
                .displayItems((parameters, output) -> {
                    AllItems.ITEMS.getEntries().forEach(holder -> {
                        ItemStack stack = holder.get().getDefaultInstance();
                        if (AllItems.isGearTab(holder.getId(), stack)) {
                            output.accept(holder.get());
                        }
                    });
                });
        // 位置链：装备 tab → (FD tab | 战斗页)
        if (com.hjmmd_8.bettergold.fd.FdModule.isLoaded()) {
            builder.withTabsBefore(com.hjmmd_8.bettergold.fd.FdTabs.TAB_ID);
        } else {
            builder.withTabsBefore(CreativeModeTabs.COMBAT);
        }
        return builder.build();
    });

    // The constructor for the mod class is the first code that is run when your mod is loaded.
    // FML will recognize some parameter types like IEventBus or ModContainer and pass them in automatically.
    public bettergold(IEventBus modEventBus, ModContainer modContainer) {
        // Register the commonSetup method for modloading
        modEventBus.addListener(this::commonSetup);

        // Register the Deferred Register to the mod event bus so blocks get registered
        AllBlocks.BLOCKS.register(modEventBus);
        // Register the Deferred Register to the mod event bus so items get registered
        AllItems.ITEMS.register(modEventBus);
        // Register the Deferred Register to the mod event bus so creative tabs get registered
        CREATIVE_MODE_TABS.register(modEventBus);
        // Register custom recipe serializers
        AllRecipes.RECIPE_SERIALIZERS.register(modEventBus);
        // Register custom mob effects
        AllEffects.EFFECTS.register(modEventBus);
        // Register global loot modifiers
        AllLootModifiers.GLM.register(modEventBus);
        // Register brewing recipes on the game event bus (RegisterBrewingRecipesEvent is NOT an IModBusEvent)
        NeoForge.EVENT_BUS.addListener(ModBrewing::registerBrewingRecipes);

        // Register ourselves for server and other game events we are interested in.
        // Note that this is necessary if and only if we want *this* class (bettergold) to respond directly to events.
        // Do not add this line if there are no @SubscribeEvent-annotated functions in this class, like onServerStarting() below.
        NeoForge.EVENT_BUS.register(this);
        // Register the mod's business event handlers (tool loot drops, piglin neutrality, bartering boost, cowrie drops)
        NeoForge.EVENT_BUS.register(ModEvents.class);

        // FD（农夫乐事）联动模块：仅在 FD 已加载时挂载（物品/方块/配方/标签页/事件整体装配）
        if (com.hjmmd_8.bettergold.fd.FdModule.isLoaded()) {
            com.hjmmd_8.bettergold.fd.FdModule.register(modEventBus);
        }

        // Register our mod's ModConfigSpec so that FML can create and load the config file for us
        modContainer.registerConfig(ModConfig.Type.COMMON, Config.SPEC);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        // Some common setup code
        LOGGER.info("HELLO FROM COMMON SETUP");

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
