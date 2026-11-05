package com.hjmmd_8.bettergold.probe.bg21;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/**
 * bg21（创造模式物品栏 5 件顺序微调）临时客户端探针 —— <b>收尾整块删除</b>（含本包）。
 *
 * <p>读的是<b>真实创造页</b>：先按原版路径 {@code CreativeModeTab#buildContents(...)} 让
 * {@link com.hjmmd_8.bettergold.material.SectionedCreativeTab} 的 {@code displayItemsGenerator} 跑一遍，
 * 再读 {@code getDisplayItems()}（客户端创造界面读的就是它）。</p>
 *
 * <p>红线：进世界第 2 tick 先断言存档身份（目录名 = {@code bg21probe}、世界名 = {@code world}、
 * 且不含作者存档名），不对立刻 {@code mc.stop()} 停手；开关文件保护；不碰生产代码的 halt/stopServer。</p>
 */
@EventBusSubscriber(modid = "bettergold", value = Dist.CLIENT)
public final class Bg21CreativeOrderProbe {

    private static final String TAG = "[bg21-c]";
    private static final String WANT_WORLD_ID = "bg21probe";
    private static final String WANT_LEVEL_NAME = "world";
    /** 作者存档名（负向排除，U+65B0 U+7684 U+4E16 U+754C） */
    private static final String AUTHOR_WORLD = "\u65b0\u7684\u4e16\u754c";

    /** 本轮 5 条「紧邻」关系：{物品, 锚点, true = 物品在锚点之后} */
    private static final List<String[]> PAIRS = List.of(
            new String[] {"chaos_coin_string", "chaos_coin", "before"},
            new String[] {"money_gremlin_spawn_egg", "chaos_coin_string", "before"},
            new String[] {"refined_alchemic_oil", "alchemic_fuel", "after"},
            new String[] {"golden_bone_meal", "golden_shield_blank", "after"},
            new String[] {"sturdygold_anvil", "golden_creeper_figurine", "before"});

    /** 需要逐条打印位次与邻居的物品（5 件被移动的 + 5 个锚点） */
    private static final List<String> READOUT = List.of(
            "chaos_coin_string", "chaos_coin",
            "money_gremlin_spawn_egg",
            "refined_alchemic_oil", "alchemic_fuel",
            "golden_bone_meal", "golden_shield_blank",
            "sturdygold_anvil", "golden_creeper_figurine");

    private static boolean armed;
    private static int worldTick;
    private static int pass;
    private static int fail;
    private static boolean done;
    /** 同时落一份纯文本报告（run/bg21-report-<phase>.txt）：别的客户端也在用 run/logs/latest.log */
    private static final StringBuilder REPORT = new StringBuilder();

    private Bg21CreativeOrderProbe() {
    }

    private static Path gameDir() {
        return FMLPaths.GAMEDIR.get();
    }

    private static boolean enabled() {
        return Files.exists(gameDir().resolve("bg21-client-probe.enabled"));
    }

    private static String phase() {
        try {
            return Files.readString(gameDir().resolve("bg21-phase.txt"), StandardCharsets.UTF_8).trim();
        } catch (Throwable t) {
            return "unknown";
        }
    }

    private static void log(String msg) {
        bettergold.LOGGER.info("{} {}", TAG, msg);
        REPORT.append(msg).append('\n');
    }

    private static void flushReport() {
        try {
            Files.writeString(gameDir().resolve("bg21-report-" + phase() + ".txt"),
                    REPORT.toString(), StandardCharsets.UTF_8);
        } catch (Throwable t) {
            bettergold.LOGGER.warn("{} cannot write report: {}", TAG, t);
        }
    }

    private static void check(String id, boolean ok, String detail) {
        if (ok) {
            pass++;
        } else {
            fail++;
        }
        log("CHECK " + id + " " + (ok ? "PASS" : "FAIL") + " :: " + detail);
    }

    private static void readout(String id, String detail) {
        log("READOUT " + id + " :: " + detail);
    }

    @SubscribeEvent
    public static void onTick(ClientTickEvent.Post event) {
        if (done) {
            return;
        }
        if (!armed) {
            if (!enabled()) {
                return;
            }
            armed = true;
            log("armed=true gamedir=" + gameDir() + " phase=" + phase());
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.getSingleplayerServer() == null) {
            return;
        }
        worldTick++;
        if (worldTick == 2) {
            String name = readLevelName(mc);
            String id = readLevelId(mc);
            boolean ok = WANT_WORLD_ID.equals(id) && WANT_LEVEL_NAME.equals(name)
                    && !name.contains(AUTHOR_WORLD);
            log("readout levelId=" + id + " levelName=" + name + " worldTick=2");
            check("probe_world_guard", ok,
                    "levelId=" + id + " (expect " + WANT_WORLD_ID + ") / levelName=" + name
                            + " (expect " + WANT_LEVEL_NAME + ", must not be " + AUTHOR_WORLD + ")");
            if (!ok) {
                log("ABORT: wrong world, stopping probe");
                done = true;
                flushReport();
                mc.stop();
            }
            return;
        }
        if (worldTick < 60) {
            return;
        }
        try {
            run(mc);
        } catch (Throwable t) {
            log("FAIL run threw " + t);
            check("probe_run", false, String.valueOf(t));
        }
        done = true;
        log("SUMMARY pass=" + pass + " fail=" + fail + " worldTicks=" + worldTick + " phase=" + phase());
        flushReport();
        mc.stop();
    }

    private static String readLevelName(Minecraft mc) {
        try {
            Object data = mc.getSingleplayerServer().overworld().getLevelData();
            java.lang.reflect.Field f = data.getClass().getDeclaredField("levelName");
            f.setAccessible(true);
            return String.valueOf(f.get(data));
        } catch (Throwable t) {
            try {
                Object data = mc.getSingleplayerServer().overworld().getLevelData();
                java.lang.reflect.Method m = data.getClass().getMethod("getLevelName");
                return String.valueOf(m.invoke(data));
            } catch (Throwable t2) {
                log("WARN cannot read level name: " + t + " / " + t2);
                return "<unreadable>";
            }
        }
    }

    /** 存档目录名（= LevelStorageAccess#getLevelId）；读不到只记 WARN，不据此停手 */
    private static String readLevelId(Minecraft mc) {
        try {
            Object server = mc.getSingleplayerServer();
            java.lang.reflect.Field f = server.getClass().getSuperclass().getDeclaredField("storageSource");
            f.setAccessible(true);
            Object storage = f.get(server);
            java.lang.reflect.Method m = storage.getClass().getMethod("getLevelId");
            return String.valueOf(m.invoke(storage));
        } catch (Throwable t) {
            log("WARN cannot read level id: " + t);
            return "<unreadable>";
        }
    }

    private static void run(Minecraft mc) throws Exception {
        String ph = phase();
        CreativeModeTab tab = bettergold.BETTERGOLD_TAB.get();
        tab.buildContents(new CreativeModeTab.ItemDisplayParameters(
                mc.level.enabledFeatures(), true, mc.level.registryAccess()));
        Collection<ItemStack> items = tab.getDisplayItems();

        List<String> ids = new ArrayList<>();
        List<Integer> cells = new ArrayList<>();
        int cell = 0;
        for (ItemStack s : items) {
            cell++;
            if (s.isEmpty()) {
                continue;
            }
            String full = BuiltInRegistries.ITEM.getKey(s.getItem()).toString();
            ids.add(full);
            cells.add(cell);
        }

        // ---- 阳性对照：这一页真的读到了东西 ----
        check("creative_page_nonempty", !items.isEmpty() && !ids.isEmpty(),
                "getDisplayItems() 总格数=" + items.size() + " / 非空格数=" + ids.size()
                        + " / 第 1 格=" + (ids.isEmpty() ? "<empty>" : ids.get(0)));

        Map<String, Integer> itemIndex = new LinkedHashMap<>();
        for (int i = 0; i < ids.size(); i++) {
            itemIndex.putIfAbsent(ids.get(i), i);
        }

        // ---- 逐行打印全量顺序（一手读数） ----
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < ids.size(); i++) {
            sb.append('\n').append(TAG).append(" ORDER cell=").append(cells.get(i))
                    .append(" item=").append(i + 1).append(' ').append(ids.get(i));
        }
        log("ORDER-BEGIN totalCells=" + items.size() + " nonEmpty=" + ids.size() + " phase=" + ph + sb);
        log("ORDER-END");

        // ---- 全量顺序指纹（非空序列的 sha256） ----
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        for (String s : ids) {
            md.update(s.getBytes(StandardCharsets.UTF_8));
            md.update((byte) '\n');
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : md.digest()) {
            hex.append(String.format(Locale.ROOT, "%02x", b));
        }
        readout("order_fingerprint", "sha256(nonEmpty ids, LF-joined)=" + hex + " count=" + ids.size());

        // ---- 落盘一份全量顺序，供 before/after diff ----
        Path out = gameDir().resolve("bg21-order-" + ph + ".txt");
        StringBuilder file = new StringBuilder();
        for (int i = 0; i < ids.size(); i++) {
            file.append(i + 1).append(' ').append(ids.get(i)).append('\n');
        }
        Files.writeString(out, file.toString(), StandardCharsets.UTF_8);
        readout("order_dumped", out + " lines=" + ids.size());

        // ---- 这 9 个物品的位次与邻居 ----
        for (String path : READOUT) {
            String full = "bettergold:" + path;
            Integer idx = itemIndex.get(full);
            if (idx == null) {
                check("readout_present_" + path, false, full + " 不在创造页里");
                continue;
            }
            String prev = idx > 0 ? ids.get(idx - 1) : "<head>";
            String next = idx + 1 < ids.size() ? ids.get(idx + 1) : "<tail>";
            readout("neighbor_" + path, "cell=" + cells.get(idx) + " item=" + (idx + 1)
                    + " id=" + full + " prev=" + prev + " next=" + next);
        }

        // ---- 5 条紧邻关系 ----
        boolean expectAdjacent = "after".equals(ph);
        for (String[] pair : PAIRS) {
            String item = "bettergold:" + pair[0];
            String anchor = "bettergold:" + pair[1];
            String dir = pair[2];
            Integer a = itemIndex.get(item);
            Integer b = itemIndex.get(anchor);
            boolean adjacent = a != null && b != null
                    && ("before".equals(dir) ? a + 1 == b : b + 1 == a);
            String checkId = "adj_" + pair[0] + "_" + dir + "_" + pair[1];
            if (expectAdjacent) {
                check(checkId, adjacent, item + " " + dir + " " + anchor
                        + " actual itemIdx=" + a + "/" + b
                        + (a == null || b == null ? "" : " (gap=" + (b - a) + ")"));
            } else {
                // 改前基线：这 5 条关系**本就不成立**（作者说「太靠前 / 位置不对」）
                check("baseline_not_" + checkId, !adjacent,
                        "改前不应紧邻：" + item + " vs " + anchor
                                + " actual itemIdx=" + a + "/" + b
                                + (a == null || b == null ? "" : " (gap=" + (b - a) + ")"));
            }
        }

        // ---- 改后：其余物品相对顺序不许变（去掉这 5 件后逐项相等） ----
        if (expectAdjacent) {
            Path beforeFile = gameDir().resolve("bg21-order-before.txt");
            if (!Files.isRegularFile(beforeFile)) {
                check("other_items_relative_order_unchanged", false,
                        "缺基线文件 " + beforeFile + "（改前那一跑没落盘？）");
            } else {
                List<String> before = new ArrayList<>();
                for (String line : Files.readAllLines(beforeFile, StandardCharsets.UTF_8)) {
                    String s = line.trim();
                    if (s.isEmpty()) {
                        continue;
                    }
                    int sp = s.indexOf(' ');
                    before.add(sp >= 0 ? s.substring(sp + 1) : s);
                }
                List<String> moved = new ArrayList<>();
                for (String[] pair : PAIRS) {
                    moved.add("bettergold:" + pair[0]);
                }
                List<String> b2 = new ArrayList<>(before);
                List<String> a2 = new ArrayList<>(ids);
                b2.removeAll(moved);
                a2.removeAll(moved);
                check("other_items_relative_order_unchanged", b2.equals(a2),
                        "去掉了 " + moved + " 之后：before=" + b2.size() + " / after=" + a2.size()
                                + " / equal=" + b2.equals(a2)
                                + (b2.equals(a2) ? "" : " / firstDiff=" + firstDiff(b2, a2)));
                check("moved_items_still_present",
                        ids.containsAll(moved) && before.containsAll(moved),
                        "5 件都在：before=" + before.containsAll(moved)
                                + " after=" + ids.containsAll(moved));
            }
        }
    }

    private static String firstDiff(List<String> a, List<String> b) {
        int n = Math.min(a.size(), b.size());
        for (int i = 0; i < n; i++) {
            if (!a.get(i).equals(b.get(i))) {
                return "at " + (i + 1) + " before=" + a.get(i) + " after=" + b.get(i);
            }
        }
        return a.size() == b.size() ? "<same>" : "size " + a.size() + " vs " + b.size();
    }
}
