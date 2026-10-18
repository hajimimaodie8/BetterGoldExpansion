package com.hjmmd_8.bettergold.probe;

import java.util.UUID;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.menu.SturdygoldAnvilMenu;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllItems;
import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.state.BlockState;

import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * 临时服务端探针（bg-n10err：GUI 改动后的回归 +「无法锻造」那一刻的菜单状态）—— 收尾整块删除。
 *
 * <p>开关文件 {@code run/bgn10err-probe.enabled}；假玩家 = {@code new ServerPlayer(...)}（不写 playerdata）；
 * 不 forceload、不碰作者存档；{@code halt(false)} 只调一次。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID)
public final class BgN10errServerProbe {

    private static final String TAG = "BGN10ERRSERVER";
    private static final String SWITCH = "bgn10err-probe.enabled";

    private static int passes;
    private static int fails;
    private static boolean done;

    private BgN10errServerProbe() {
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            passes++;
            bettergold.LOGGER.info("{} PASS {} :: {}", TAG, name, detail);
        } else {
            fails++;
            bettergold.LOGGER.error("{} FAIL {} :: {}", TAG, name, detail);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (done || !java.nio.file.Files.exists(
                java.nio.file.Path.of(System.getProperty("user.dir"), SWITCH))) {
            return;
        }
        done = true;
        MinecraftServer server = event.getServer();
        ServerLevel level = server.overworld();
        try {
            run(server, level);
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} EXCEPTION", TAG, t);
            fails++;
        }
        bettergold.LOGGER.info("{} SUMMARY pass={} fail={} forcedNow={}",
                TAG, passes, fails, level.getForcedChunks().size());
        server.halt(false);
    }

    private static void run(MinecraftServer server, ServerLevel level) {
        ServerPlayer dummy = new ServerPlayer(server, level,
                new GameProfile(UUID.randomUUID(), "bgn10errdummy"), ClientInformation.createDefault());
        Connection conn = new Connection(PacketFlow.SERVERBOUND);
        try {
            java.lang.reflect.Field chf = Connection.class.getDeclaredField("channel");
            chf.setAccessible(true);
            chf.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} channel setup failed", TAG, t);
        }
        dummy.connection = new ServerGamePacketListenerImpl(server, conn, dummy,
                CommonListenerCookie.createInitial(new GameProfile(UUID.randomUUID(), "bgn10errprobe"), false));
        dummy.moveTo(1008.5D, 120.0D, 1008.5D, 0.0F, 0.0F);

        BlockPos pos = new BlockPos(1010, 120, 1008);
        level.setBlockAndUpdate(pos, AllBlocks.STURDYGOLD_ANVIL.get().defaultBlockState());
        BlockState state = level.getBlockState(pos);
        check("block_state", state.is(AllBlocks.STURDYGOLD_ANVIL.get()), "state=" + state + " pos=" + pos);

        MenuProvider provider = state.getMenuProvider(level, pos);
        check("provider_present", provider != null, "provider=" + provider);
        dummy.openMenu(provider);
        AbstractContainerMenu m = dummy.containerMenu;
        SturdygoldAnvilMenu menu = (SturdygoldAnvilMenu) m;
        check("menu_class", m instanceof SturdygoldAnvilMenu, "containerMenu=" + m.getClass().getName());
        check("menu_type", BuiltInRegistries.MENU.getKey(m.getType()).toString()
                        .equals("bettergold:sturdygold_anvil"),
                "type=" + BuiltInRegistries.MENU.getKey(m.getType()));
        check("menu_slots_39", m.slots.size() == 39, "slots=" + m.slots.size() + "（2 输入 + 1 输出 + 36 玩家）");
        check("menu_title_container_repair",
                provider != null && provider.getDisplayName().equals(Component.translatable("container.repair")),
                "title=" + (provider == null ? "null" : provider.getDisplayName()));
        check("menu_still_valid", m.stillValid(dummy), "near=true");

        // ① 「无法锻造」那一刻：输入有东西、输出空、花费 0 —— 客户端 renderErrorIcon 的判据正是
        //    (slot0.hasItem() || slot1.hasItem()) && !slot2.hasItem()
        m.getSlot(0).set(new ItemStack(Items.DIAMOND_SWORD));
        m.getSlot(1).set(new ItemStack(Items.STICK, 3));
        boolean hasInput = m.getSlot(0).hasItem() || m.getSlot(1).hasItem();
        boolean outEmpty = m.getSlot(2).getItem().isEmpty();
        check("cannot_forge_result_empty", outEmpty, "out=" + m.getSlot(2).getItem());
        check("cannot_forge_input_present", hasInput, "input0=" + m.getSlot(0).getItem());
        check("cannot_forge_error_icon_condition", hasInput && outEmpty,
                "errorIconCondition=" + (hasInput && outEmpty) + "（客户端据此画叉号）");
        check("cannot_forge_cost_zero", menu.getCost() == 0, "cost=" + menu.getCost());
        check("cannot_forge_may_not_pickup", !m.getSlot(2).mayPickup(dummy), "mayPickup=false");
        check("cannot_forge_menu_type_ok", BuiltInRegistries.MENU.getKey(m.getType()).toString()
                        .equals("bettergold:sturdygold_anvil"),
                "type=" + BuiltInRegistries.MENU.getKey(m.getType()) + " slots=" + m.slots.size());

        // ② 金币串修复回归（证明这次改动没碰菜单/配方那条路）
        ItemStack sword = new ItemStack(Items.DIAMOND_SWORD);
        sword.setDamageValue(1000);
        m.getSlot(0).set(sword);
        m.getSlot(1).set(new ItemStack(AllItems.CHAOS_COIN_STRING.get(), 5));
        ItemStack out = m.getSlot(2).getItem();
        check("repair_result_damage", out.is(Items.DIAMOND_SWORD) && out.getDamageValue() == 0,
                "out=" + out + " damage=" + out.getDamageValue());
        check("repair_cost_3", menu.getCost() == 3, "cost=" + menu.getCost());

        // ③ 花费为 0：两个输入都空 ⇒ cost=0、输出空
        m.getSlot(0).set(ItemStack.EMPTY);
        m.getSlot(1).set(ItemStack.EMPTY);
        check("empty_cost_zero", menu.getCost() == 0 && m.getSlot(2).getItem().isEmpty(),
                "cost=" + menu.getCost() + " out=" + m.getSlot(2).getItem());

        check("forceload_none", level.getForcedChunks().size() == 0,
                "forcedNow=" + level.getForcedChunks().size());
    }
}
