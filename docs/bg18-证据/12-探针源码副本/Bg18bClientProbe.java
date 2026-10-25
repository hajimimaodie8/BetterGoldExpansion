package com.hjmmd_8.bettergold.probe.bg18b;

import java.lang.reflect.Field;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.google.gson.JsonObject;

import net.minecraft.client.Minecraft;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ClientTickEvent;

import vazkii.patchouli.client.book.BookContents;
import vazkii.patchouli.client.book.BookEntry;
import vazkii.patchouli.client.book.BookPage;
import vazkii.patchouli.common.book.Book;
import vazkii.patchouli.common.book.BookRegistry;

/**
 * bg18b（1.7 第七轮 A 级）临时客户端探针 —— <b>收尾整块删除</b>。
 *
 * <p>读 Patchouli 真正加载出来的 {@code BookContents}（必须进世界才有内容树），并做
 * {@code I18n} 的实机渲染读数。红线：进世界第 2 tick 断言世界名；名字不对立刻停手。</p>
 */
@EventBusSubscriber(modid = "bettergold", value = Dist.CLIENT)
public final class Bg18bClientProbe {

    private static final String TAG = "[bg18b-c]";
    private static final String BOOK_ID = "bettergold:alchemy_handbook";
    private static final String P = "patchouli:";
    private static final String WANT_WORLD = "bg18probe";

    /** 8 条含 `%%` 的手册正文键（P2-b） */
    private static final String[] PCT_KEYS = {
            "bettergold.handbook.page.gear_indigoseagold_1_left",
            "bettergold.handbook.page.gear_indigoseagold_2_left",
            "bettergold.handbook.page.gear_voodoogold_1_left",
            "bettergold.handbook.page.gear_illusiongold_1_left",
            "bettergold.handbook.page.gear_illusiongold_1_right",
            "bettergold.handbook.page.gear_illusiongold_2_left",
            "bettergold.handbook.page.prison_chaosalloy_2_left",
            "bettergold.handbook.page.prison_chaosalloy_2_right",
    };

    private static boolean armed;
    private static int tick;
    private static int worldTick;
    private static int pass;
    private static int fail;
    private static boolean done;

    private Bg18bClientProbe() {
    }

    private static boolean enabled() {
        return Files.exists(FMLPaths.GAMEDIR.get().resolve("bg18b-client-probe.enabled"));
    }

    private static void log(String msg) {
        System.out.println(TAG + " " + msg);
    }

    private static void check(String id, boolean ok, String detail) {
        if (ok) {
            pass++;
        } else {
            fail++;
        }
        log("CHECK " + id + " " + (ok ? "PASS" : "FAIL") + " :: " + detail);
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
            log("armed=true gamedir=" + FMLPaths.GAMEDIR.get());
        }
        tick++;
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.getSingleplayerServer() == null) {
            return;
        }
        // ⚠ tick 从 arm 起算 ⇒ 世界加载完时早已 >2；世界名闸门必须用「进世界之后的第几 tick」。
        //   （第一次跑就是踩了这条：tick==2 时 level 还是 null，闸门整段被跳过、一条都不打。）
        worldTick++;
        if (worldTick == 2) {
            String name = readLevelName(mc);
            boolean ok = WANT_WORLD.equals(name) && !name.contains("\u65b0\u7684\u4e16\u754c");
            log("readout levelName=" + name + " worldTick=2");
            check("probe_world_guard", ok, "levelName=" + name + " (expected " + WANT_WORLD + ")");
            if (!ok) {
                log("ABORT: wrong world, stopping probe");
                done = true;
                mc.stop();
            }
            return;
        }
        if (worldTick < 40) {
            return;
        }
        try {
            run(mc);
        } catch (Throwable t) {
            log("FAIL run threw " + t);
            check("probe_run", false, String.valueOf(t));
        }
        done = true;
        mc.stop();
    }

    private static String readLevelName(Minecraft mc) {
        try {
            // 整合服务端：LevelData 没有 public 名字访问器 ⇒ 反射 getLevelName()（本仓历轮口径）
            Object data = mc.getSingleplayerServer().overworld().getLevelData();
            Field f = data.getClass().getDeclaredField("levelName");
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

    private static void run(Minecraft mc) {
        // ---------- ① 手册内容树 ----------
        Map<ResourceLocation, Book> books = BookRegistry.INSTANCE.books;
        Book book = books.get(ResourceLocation.parse(BOOK_ID));
        check("book_registered", book != null, "books=" + books.size());
        if (book == null) {
            summary();
            return;
        }
        BookContents c = book.getContents();
        check("book_contents_no_error", c != null && !c.isErrored(),
                "errored=" + (c == null ? "null" : c.isErrored() + " / " + c.getException()));
        if (c == null) {
            summary();
            return;
        }
        int pages = 0;
        for (BookEntry e : c.entries.values()) {
            pages += e.getPages().size();
        }
        log("readout entries=" + c.entries.size() + " pages=" + pages
                + " categories=" + c.categories.size());
        check("book_entries_27", c.entries.size() == 27, "entries=" + c.entries.size());
        check("book_pages_233", pages == 233, "pages=" + pages);

        // ---------- ② 新章节：4 页页型 ----------
        BookEntry ne = c.entries.get(ResourceLocation.parse("bettergold:refined_extraction"));
        check("new_entry_present", ne != null, "bettergold:refined_extraction");
        if (ne != null) {
            List<BookPage> pgs = ne.getPages();
            List<String> types = new ArrayList<>();
            for (BookPage p : pgs) {
                JsonObject so = p.sourceObject;
                types.add(so != null && so.has("type") ? so.get("type").getAsString() : "?");
            }
            log("readout new_entry pages=" + pgs.size() + " types=" + types);
            check("new_entry_4_pages", pgs.size() == 4, "pages=" + pgs.size());
            check("new_entry_types", types.equals(List.of(P + "text", P + "crafting",
                    P + "text", P + "crafting")), "types=" + types);
            boolean textOnRecipes = pgs.size() == 4
                    && pgs.get(1).sourceObject != null && pgs.get(1).sourceObject.has("text")
                    && pgs.get(3).sourceObject != null && pgs.get(3).sourceObject.has("text");
            check("new_entry_recipe_pages_have_text", textOnRecipes,
                    "page1.text=" + hasText(pgs, 1) + " page3.text=" + hasText(pgs, 3));
            check("new_entry_recipes", pgs.size() == 4
                            && recipeOf(pgs.get(1)).equals("bettergold:raw_sturdygold_doubled")
                            && recipeOf(pgs.get(3)).equals("bettergold:raw_sturdygold_chaosgold"),
                    "recipe1=" + (pgs.size() > 1 ? recipeOf(pgs.get(1)) : "?")
                            + " recipe2=" + (pgs.size() > 3 ? recipeOf(pgs.get(3)) : "?"));
        }

        // ---------- ③ P2-a 同屏：熔炉页 / 工作台页的**真实下标** ----------
        BookEntry cg = c.entries.get(ResourceLocation.parse("bettergold:prison_chaosgold_main"));
        if (cg == null) {
            check("p2a_entry_present", false, "missing prison_chaosgold_main");
        } else {
            List<BookPage> pgs = cg.getPages();
            int sm = -1;
            int cr = -1;
            for (int i = 0; i < pgs.size(); i++) {
                if (recipeOf(pgs.get(i)).equals("bettergold:chaos_coin_smelting")) {
                    sm = i;
                }
                if (recipeOf(pgs.get(i)).equals("bettergold:chaosgold_ingot_from_nugget")) {
                    cr = i;
                }
            }
            log("readout p2a smelting_index=" + sm + " crafting_index=" + cr
                    + " spread=" + (sm / 2) + "/" + (cr / 2));
            check("p2a_same_spread", sm >= 0 && cr == sm + 1 && sm % 2 == 0,
                    "smelting=" + sm + " crafting=" + cr + " (need adjacent, first even)");
            check("p2a_pages_smelting_crafting",
                    sm >= 0 && P.concat("smelting").equals(typeOf(pgs.get(sm)))
                            && cr >= 0 && P.concat("crafting").equals(typeOf(pgs.get(cr))),
                    "types=" + (sm >= 0 ? typeOf(pgs.get(sm)) : "?") + "/"
                            + (cr >= 0 ? typeOf(pgs.get(cr)) : "?"));
        }

        // ---------- ④ P2-b：8 条 `%%` 键的页面渲染 + I18n ----------
        Set<String> found = new LinkedHashSet<>();
        String chaosPage = null;
        String chaosKey = "bettergold.handbook.page.prison_chaosalloy_2_left";
        for (BookEntry e : c.entries.values()) {
            for (BookPage p : e.getPages()) {
                JsonObject so = p.sourceObject;
                if (so == null || !so.has("text") || !so.get("text").isJsonPrimitive()) {
                    continue;
                }
                String key = so.get("text").getAsString();
                for (String k : PCT_KEYS) {
                    if (!k.equals(key)) {
                        continue;
                    }
                    found.add(k);
                    String raw = Language.getInstance().getOrDefault(k);
                    String rendered;
                    try {
                        rendered = p.i18n(k);
                    } catch (Throwable t) {
                        rendered = "THREW " + t;
                    }
                    boolean noErr = !rendered.startsWith("Format error") && !rendered.contains("Format error");
                    boolean onePct = rendered.contains("%") && !rendered.contains("%%");
                    boolean rawNoBare = !raw.replace("%%", "").contains("%");
                    if (!noErr || !onePct || !rawNoBare) {
                        check("p2b_page_" + k.substring(k.lastIndexOf('.') + 1), false,
                                "rendered=" + sample(rendered) + " raw=" + sample(raw));
                    }
                    if (chaosKey.equals(k)) {
                        chaosPage = rendered;
                    }
                }
            }
        }
        log("readout p2b_keys_found=" + found.size() + "/8 " + found);
        check("p2b_all_eight_pages_rendered", found.size() == 8, "found=" + found.size());
        check("p2b_chaos_page_no_format_error",
                chaosPage != null && !chaosPage.contains("Format error")
                        && chaosPage.contains("50%") && !chaosPage.contains("%%"),
                "rendered=" + sample(chaosPage));
        log("readout p2b_chaos_page=" + sample(chaosPage));

        int i18nOk = 0;
        List<String> bad = new ArrayList<>();
        for (String k : PCT_KEYS) {
            try {
                String s = Component.translatable(k).getString();
                if (s != null && !s.isEmpty() && s.contains("%") && !s.contains("Format error")) {
                    i18nOk++;
                } else {
                    bad.add(k + " -> " + sample(s));
                }
            } catch (Throwable t) {
                bad.add(k + " THREW " + t);
            }
        }
        check("i18n_translatable_eight", i18nOk == 8, "ok=" + i18nOk + "/8 bad=" + bad);
        log("readout i18n_sample=" + sample(Component.translatable(PCT_KEYS[6]).getString()));

        summary();
    }

    private static String sample(String s) {
        if (s == null) {
            return "null";
        }
        String t = s.length() > 90 ? s.substring(0, 90) + "..." : s;
        return t.replace("\n", "\\n");
    }

    private static boolean hasText(List<BookPage> pgs, int i) {
        return pgs.size() > i && pgs.get(i).sourceObject != null
                && pgs.get(i).sourceObject.has("text");
    }

    private static String recipeOf(BookPage p) {
        JsonObject so = p.sourceObject;
        if (so == null) {
            return "";
        }
        for (String k : new String[]{"recipe", "recipe2"}) {
            if (so.has(k) && so.get(k).isJsonPrimitive()) {
                String v = so.get(k).getAsString();
                if (v != null) {
                    return v;
                }
            }
        }
        return "";
    }

    private static String typeOf(BookPage p) {
        JsonObject so = p.sourceObject;
        return so != null && so.has("type") ? so.get("type").getAsString() : "?";
    }

    private static void summary() {
        log("SUMMARY pass=" + pass + " fail=" + fail + " ticks=" + tick);
    }
}
