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
 * 临时服务端探针（bg-n10anvil：GUI 重做后的回归 + 改名链路）—— 收尾整块删除。
 *
 * <p>开关文件 {@code run/bgn10anvil-probe.enabled}；假玩家 = {@code new ServerPlayer(...)}
 * （与轮5/轮8/轮9 同一套，不写 playerdata）；不 forceload、不碰作者存档；{@code halt(false)} 只调一次。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID)
public final class BgN10anvilServerProbe {

    private static final String TAG = "BGN10ANVILSERVER";
    private static final String SWITCH = "bgn10anvil-probe.enabled";

    private static int passes;
    private static int fails;
    private static boolean done;

    private BgN10anvilServerProbe() {
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
        server.halt(false); // 只调一次
    }

    private static void run(MinecraftServer server, ServerLevel level) {
        ServerPlayer dummy = new ServerPlayer(server, level,
                new GameProfile(UUID.randomUUID(), "bgn10anvildummy"), ClientInformation.createDefault());
        Connection conn = new Connection(PacketFlow.SERVERBOUND);
        try {
            // Neoforge 的 hasChannel() 会直接 channel().attr(...) ⇒ 没有 channel 会 NPE（轮8 同一个坑）
            java.lang.reflect.Field chf = Connection.class.getDeclaredField("channel");
            chf.setAccessible(true);
            chf.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} channel setup failed", TAG, t);
        }
        dummy.connection = new ServerGamePacketListenerImpl(server, conn, dummy,
                CommonListenerCookie.createInitial(new GameProfile(UUID.randomUUID(), "bgn10anvilprobe"), false));
        dummy.moveTo(1008.5D, 120.0D, 1008.5D, 0.0F, 0.0F);

        BlockPos pos = new BlockPos(1010, 120, 1008);
        level.setBlockAndUpdate(pos, AllBlocks.STURDYGOLD_ANVIL.get().defaultBlockState());
        BlockState state = level.getBlockState(pos);
        check("block_state", state.is(AllBlocks.STURDYGOLD_ANVIL.get()),
                "state=" + state + " pos=" + pos);

        // ① 菜单仍能开（走方块自己的 MenuProvider，与 useWithoutItem 那条路同源）
        MenuProvider provider = state.getMenuProvider(level, pos);
        check("provider_present", provider != null, "provider=" + provider);
        dummy.openMenu(provider);
        AbstractContainerMenu m = dummy.containerMenu;
        SturdygoldAnvilMenu menu = (SturdygoldAnvilMenu) m;
        check("menu_class", m instanceof SturdygoldAnvilMenu,
                "containerMenu=" + m.getClass().getName());
        check("menu_type", BuiltInRegistries.MENU.getKey(m.getType()).toString()
                        .equals("bettergold:sturdygold_anvil"),
                "type=" + BuiltInRegistries.MENU.getKey(m.getType()));
        check("menu_slots_39", m.slots.size() == 39,
                "slots=" + m.slots.size() + "（2 输入 + 1 输出 + 36 玩家）");
        check("menu_title_container_repair",
                provider != null && provider.getDisplayName().equals(Component.translatable("container.repair")),
                "title=" + (provider == null ? "null" : provider.getDisplayName()));
        check("menu_still_valid", m.stillValid(dummy), "near=true");

        dummy.giveExperienceLevels(30 - dummy.experienceLevel);

        // ② 金币串修复回归（上一轮 onTake 重入 bug 的防线）
        ItemStack sword = new ItemStack(Items.DIAMOND_SWORD);
        sword.setDamageValue(1000);
        m.getSlot(0).set(sword);
        m.getSlot(1).set(new ItemStack(AllItems.CHAOS_COIN_STRING.get(), 5));
        ItemStack out = m.getSlot(2).getItem();
        check("repair_result_damage", out.is(Items.DIAMOND_SWORD) && out.getDamageValue() == 0,
                "out=" + out + " damage=" + out.getDamageValue());
        check("repair_cost_3", menu.getCost() == 3, "cost=" + menu.getCost());
        check("repair_coin_path", menu.isCoinRepair() && menu.getCoinCount() == 3,
                "coinRepair=" + menu.isCoinRepair() + " used=" + menu.getCoinCount());
        check("repair_may_pickup", m.getSlot(2).mayPickup(dummy),
                "levels=" + dummy.experienceLevel + " cost=" + menu.getCost());
        int levelsBefore = dummy.experienceLevel;
        ItemStack taken = out.copy();
        m.getSlot(2).onTake(dummy, taken);
        ItemStack coinsLeft = m.getSlot(1).getItem();
        check("repair_take_levels", dummy.experienceLevel == levelsBefore - 3,
                "levels " + levelsBefore + " -> " + dummy.experienceLevel);
        check("repair_take_coins", coinsLeft.getCount() == 2, "coinsLeft=" + coinsLeft.getCount());
        check("repair_take_input0_empty", m.getSlot(0).getItem().isEmpty(),
                "input0=" + m.getSlot(0).getItem());

        // ③ 改名链路（原版 EditBox -> setItemName -> 结果带名字，且 +1 级；旧强制同步已删）
        m.getSlot(0).set(sword.copy());
        m.getSlot(1).set(new ItemStack(AllItems.CHAOS_COIN_STRING.get(), 5));
        boolean nameChanged = menu.setItemName("BGN Anvil Probe");
        ItemStack renamed = m.getSlot(2).getItem();
        check("rename_changed", nameChanged, "setItemName returned " + nameChanged);
        check("rename_applied", "BGN Anvil Probe".equals(renamed.getHoverName().getString()),
                "resultName=" + renamed.getHoverName().getString());
        check("rename_cost_plus_1", menu.getCost() == 4,
                "cost=" + menu.getCost() + "（修理 3 + 改名 1）");

        // ④ 花费为 0：两个输入都空 ⇒ cost=0、输出空
        m.getSlot(0).set(ItemStack.EMPTY);
        m.getSlot(1).set(ItemStack.EMPTY);
        check("empty_cost_zero", menu.getCost() == 0 && m.getSlot(2).getItem().isEmpty(),
                "cost=" + menu.getCost() + " out=" + m.getSlot(2).getItem());

        check("forceload_none", level.getForcedChunks().size() == 0,
                "forcedNow=" + level.getForcedChunks().size());
    }
}
