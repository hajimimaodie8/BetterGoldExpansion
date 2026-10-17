package com.hjmmd_8.bettergold.probe;

import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

import vazkii.patchouli.client.book.BookEntry;
import vazkii.patchouli.client.book.BookPage;
import vazkii.patchouli.client.book.ClientBookRegistry;
import vazkii.patchouli.client.book.gui.GuiBook;
import vazkii.patchouli.client.book.gui.GuiBookEntry;
import vazkii.patchouli.client.book.page.PageSpotlight;
import vazkii.patchouli.client.book.page.abstr.PageDoubleRecipe;
import vazkii.patchouli.client.book.page.abstr.PageWithText;
import vazkii.patchouli.common.book.Book;
import vazkii.patchouli.common.book.BookRegistry;

/**
 * <b>1.7 手册渲染验证轮（bgn10hv）的客户端探针</b> —— <b>收尾时整块删除，绝不进生产代码</b>。
 *
 * <p>开关文件 {@code run/bgn10hv-probe.enabled}；只在 {@link Dist#CLIENT} 注册。
 * 用 {@code --quickPlayPath logs/quickplay/bgn10hv.json --quickPlaySingleplayer bgn10hvcw}
 * 进到**本轮自己造的 ASCII 探针世界**（`run/bgn10hvgen` 的整目录副本）。</p>
 *
 * <p><b>读数分三段</b>：</p>
 * <ol>
 *   <li><b>进世界第一 tick 断言世界名</b>：整合服务端 {@code overworld().getLevelData()} 反射
 *       {@code getLevelName()} + 存档目录名；不是 {@code bgn10hvgen} / {@code bgn10hvcw} 就
 *       <b>立刻停手并退进程</b>（负向排除作者存档名 {@code 新的世界}）。</li>
 *   <li><b>内容树逐页读数</b>：4 条新章节 + 1 条既有章节（对照）的 {@code HVROW} / {@code HVPG} 行
 *       —— 每页的 {@code type} / 类名 / {@code PageDoubleRecipe.recipe1|recipe2} 是否 null /
 *       {@code PageSpotlight.stacks} 的栈数 / 文本页的文本键是否翻得出来。</li>
 *   <li><b>真开书（不点任何 UI）</b>：{@code ClientBookRegistry#displayBookGui} 逐条目打开
 *       {@code GuiBookEntry}，读 {@code bookLeft/bookTop}、左右两页的类、{@code BookTextRenderer.words}
 *       的排版结果（词数 / 缩放 / 下沿区间）—— 这是"页面真排出来了"的证据。</li>
 * </ol>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class Bgn10hvClientProbe {

    private static final String TAG = "BGN10HVCPROBE";
    private static final String SWITCH = "bgn10hv-probe.enabled";
    /** 探针世界：存档目录名 / level.dat 里的 LevelName（= 服务端 level-name） */
    private static final String WORLD_DIR = "bgn10hvcw";
    private static final String WORLD_NAME = "bgn10hvgen";
    private static final String BOOK_ID = "bettergold:alchemy_handbook";
    /** 进世界前最多等这么多 tick（约 3 分钟）还没进世界 ⇒ 判失败并退进程 */
    private static final int MAX_PRE_WORLD_TICKS = 3600;

    /** 4 条新章节 + 1 条既有章节（对照） */
    private static final String[] ENTRIES = {
            "bettergold:chaos_materials",
            "bettergold:chaos_feast",
            "bettergold:gear_chaosgold",
            "bettergold:gear_chaosalloy",
            "bettergold:gear_echogold",
    };

    private static int passes;
    private static int fails;
    private static boolean done;
    private static boolean inWorld;
    private static int preWorldTicks;
    private static int worldAttempts;
    private static int ticks;
    private static boolean dataDone;
    private static int guiIndex = -1;
    private static int guiWait;
    private static int wordPages;
    private static int wordTotal;

    private Bgn10hvClientProbe() {
    }

    private static void pass(String name, String detail) {
        passes++;
        bettergold.LOGGER.info("{} PASS {} :: {}", TAG, name, detail);
    }

    private static void fail(String name, String detail) {
        fails++;
        bettergold.LOGGER.error("{} FAIL {} :: {}", TAG, name, detail);
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            pass(name, detail);
        } else {
            fail(name, detail);
        }
    }

    private static void info(String msg) {
        bettergold.LOGGER.info("{} INFO {}", TAG, msg);
    }

    private static void row(String msg) {
        bettergold.LOGGER.info("{} {}", TAG, msg);
    }

    @SubscribeEvent
    public static void onClientTick(ClientTickEvent.Post event) {
        if (done || !Files.exists(Path.of(System.getProperty("user.dir"), SWITCH))) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.getSingleplayerServer() == null) {
            preWorldTicks++;
            if (preWorldTicks == MAX_PRE_WORLD_TICKS) {
                done = true;
                fail("c_world_entered", "等了 " + preWorldTicks + " tick 仍不在世界里（quickPlay 没生效？）");
                bettergold.LOGGER.info("{} SUMMARY pass={} fail={} (never-in-world)", TAG, passes, fails);
                Runtime.getRuntime().halt(3);
            }
            return;
        }
        // ① 进世界的第一 tick 就断言世界名（不做任何别的读写）
        if (!inWorld) {
            int gate = checkWorld(mc);
            if (gate < 0) {                       // 服务器还没就绪：下一 tick 再试（不误判）
                worldAttempts++;
                if (worldAttempts > 20) {
                    done = true;
                    bettergold.LOGGER.info("{} SUMMARY pass={} fail={} (world-gate-read-failed)", TAG, passes, fails);
                    Runtime.getRuntime().halt(2);
                }
                return;
            }
            if (gate == 0) {                      // 世界名不对 ⇒ 立刻停手
                done = true;
                bettergold.LOGGER.info("{} SUMMARY pass={} fail={} (world-gate)", TAG, passes, fails);
                Runtime.getRuntime().halt(2);
                return;
            }
            inWorld = true;
        }
        ticks++;
        if (!dataDone) {
            if (ticks < 60) {          // 进世界后再等 60 tick：配方同步 + Patchouli 建内容树
                return;
            }
            dataDone = true;
            try {
                readData(mc);
            } catch (Throwable t) {
                bettergold.LOGGER.error("{} data exception", TAG, t);
                fail("c_data_exception", String.valueOf(t));
            }
            guiIndex = 0;
            guiWait = 0;
            openGui(mc, ENTRIES[guiIndex]);
            return;
        }
        // ③ 逐条目开书取排版读数（每条目给 3 tick 初始化 + 真渲染）
        if (guiIndex >= 0 && guiIndex < ENTRIES.length) {
            guiWait++;
            if (guiWait < 3) {
                return;
            }
            sampleGui(mc, ENTRIES[guiIndex]);
            guiIndex++;
            guiWait = 0;
            if (guiIndex < ENTRIES.length) {
                openGui(mc, ENTRIES[guiIndex]);
                return;
            }
            mc.setScreen(null);
            finish();
        }
    }

    private static void finish() {
        done = true;
        row("HVLAYOUT pages=" + wordPages + " words=" + wordTotal);
        bettergold.LOGGER.info("{} SUMMARY pass={} fail={} ticks={}", TAG, passes, fails, ticks);
        bettergold.LOGGER.info("{} INFO exiting JVM（客户端没有「停服」；读数已落盘，探针直接退进程）", TAG);
        Runtime.getRuntime().halt(fails == 0 ? 0 : 1);
    }

    /** 世界闸门：LevelName（反射 {@code getLevelName}）+ 存档 id（{@code storageSource#getLevelId}）。
     *  1=对，0=错，-1=还没就绪。
     *
     *  <p>⚠ 实测坑：{@code getWorldPath(LevelResource.ROOT).getFileName()} 在本机 dev 整合服务端上返回
     *  {@code "."}（不是不许用的存档目录名，而是这条读数本身不成立）⇒ **世界身份以 level.dat 的
     *  {@code getLevelName()} 为准**，目录 id 走 {@code LevelStorageAccess#getLevelId()} 兜底。</p>
     */
    private static int checkWorld(Minecraft mc) {
        MinecraftServer server = mc.getSingleplayerServer();
        String levelName;
        String levelId;
        String root;
        try {
            Object data = server.overworld().getLevelData();
            levelName = String.valueOf(data.getClass().getMethod("getLevelName").invoke(data));
            root = server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT)
                    .toAbsolutePath().normalize().toString();
        } catch (Throwable t) {
            info("world-gate not ready yet: " + t);
            return -1;
        }
        levelId = readLevelId(server);
        row("HVWORLD levelName=" + levelName + " levelId=" + levelId + " root=" + root
                + " expectName=" + WORLD_NAME + " expectId=" + WORLD_DIR);
        check("c_world_levelname_is_probe", WORLD_NAME.equals(levelName), "LevelName=" + levelName);
        if (!levelId.startsWith("?")) {
            check("c_world_levelid_is_probe", WORLD_DIR.equals(levelId), "levelId=" + levelId);
        } else {
            info("levelId 读不到（" + levelId + "）⇒ 世界身份只以 LevelName 判定");
        }
        check("c_world_not_author_save",
                !"\u65b0\u7684\u4e16\u754c".equals(levelName) && !"\u65b0\u7684\u4e16\u754c".equals(levelId),
                "levelName=" + levelName + " levelId=" + levelId);
        return WORLD_NAME.equals(levelName) ? 1 : 0;
    }

    /** {@code MinecraftServer#storageSource} 是 protected ⇒ 反射取 {@code LevelStorageAccess#getLevelId()} */
    private static String readLevelId(MinecraftServer server) {
        try {
            Object storage = field(server, "storageSource");
            if (storage == null) {
                return "?null-storageSource";
            }
            return String.valueOf(storage.getClass().getMethod("getLevelId").invoke(storage));
        } catch (Throwable t) {
            return "?" + t;
        }
    }

    private static void readData(Minecraft mc) {
        Book book = BookRegistry.INSTANCE.books.get(ResourceLocation.parse(BOOK_ID));
        check("c_book_present", book != null, "book=" + (book == null ? "null" : book.id.toString()));
        if (book == null) {
            return;
        }
        var contents = book.getContents();
        check("c_book_contents_present", contents != null, "contents=" + contents);
        if (contents == null) {
            return;
        }
        check("c_book_not_errored", !contents.isErrored(),
                "errored=" + contents.isErrored() + " exception=" + contents.getException());
        int entries = contents.entries.size();
        int pages = 0;
        for (BookEntry e : contents.entries.values()) {
            pages += e.getPages().size();
        }
        row("HVBOOK entries=" + entries + " pages=" + pages
                + " categories=" + contents.categories.size()
                + " errored=" + contents.isErrored()
                + " overflowMode=" + book.overflowMode);
        row("HVGEOM fullW=" + GuiBook.FULL_WIDTH + " fullH=" + GuiBook.FULL_HEIGHT
                + " pageW=" + GuiBook.PAGE_WIDTH + " pageH=" + GuiBook.PAGE_HEIGHT
                + " topPad=" + GuiBook.TOP_PADDING + " leftX=" + GuiBook.LEFT_PAGE_X
                + " rightX=" + GuiBook.RIGHT_PAGE_X + " lineH=" + GuiBook.TEXT_LINE_HEIGHT);

        var lang = loadLang(mc, "zh_cn");
        row("HVLANG lang=zh_cn keys=" + lang.size());

        int totalKeyMissing = 0;
        int totalRecipeRefs = 0;
        int totalRecipeDead = 0;
        int totalSpotlights = 0;
        int totalSpotlightEmpty = 0;

        for (String entryId : ENTRIES) {
            BookEntry entry = contents.entries.get(ResourceLocation.parse(entryId));
            if (entry == null) {
                fail("c_entry_present_" + shortName(entryId), "条目不在内容树里：" + entryId);
                continue;
            }
            var list = entry.getPages();
            row("HVROW entry=" + entryId + " pages=" + list.size() + " icon=" + safeIcon(entry));
            for (int i = 0; i < list.size(); i++) {
                BookPage page = list.get(i);
                String type = String.valueOf(field(page, "type"));
                String cls = page.getClass().getSimpleName();
                String r1 = "-";
                String r2 = "-";
                String ok1 = "-";
                String ok2 = "-";
                String stacks = "-";
                String stackItems = "-";
                String textKey = "-";
                String textOk = "-";
                String textPrefix = "-";
                String err = "none";

                if (page instanceof PageDoubleRecipe<?>) {
                    Object id1 = field(page, "recipeId");
                    Object id2 = field(page, "recipe2Id");
                    Object o1 = field(page, "recipe1");
                    Object o2 = field(page, "recipe2");
                    if (id1 != null) {
                        totalRecipeRefs++;
                        r1 = String.valueOf(id1);
                        ok1 = String.valueOf(o1 != null);
                        if (o1 == null) {
                            totalRecipeDead++;
                            err = "recipe1";
                        }
                    }
                    if (id2 != null) {
                        totalRecipeRefs++;
                        r2 = String.valueOf(id2);
                        ok2 = String.valueOf(o2 != null);
                        if (o2 == null) {
                            totalRecipeDead++;
                            err = "none".equals(err) ? "recipe2" : err + "+recipe2";
                        }
                    }
                    if (id1 == null && id2 == null) {
                        err = "no-id";
                    }
                } else if (page instanceof PageSpotlight) {
                    Object raw = field(page, "stacks");
                    ItemStack[] arr = (ItemStack[]) raw;
                    totalSpotlights++;
                    int n = arr == null ? 0 : arr.length;
                    stacks = String.valueOf(n);
                    if (n == 0 || arr[0] == null || arr[0].isEmpty()) {
                        totalSpotlightEmpty++;
                        err = "spotlight-empty";
                    }
                    stackItems = firstItems(arr, 4);
                }
                if (page instanceof PageWithText) {
                    Object textVar = field(page, "text");
                    String raw;
                    if (textVar instanceof vazkii.patchouli.api.IVariable iv) {
                        raw = iv.asString();
                    } else if (textVar != null) {
                        raw = String.valueOf(textVar);
                    } else {
                        raw = "-";
                    }
                    textKey = shortKey(raw);
                    if (raw.startsWith("bettergold.")) {
                        String resolved = lang.get(raw);
                        boolean has = resolved != null;
                        textOk = String.valueOf(has);
                        textPrefix = has ? prefix(resolved) : "(MISSING)";
                        if (!has) {
                            totalKeyMissing++;
                            err = "none".equals(err) ? "text-key" : err + "+text-key";
                        }
                    } else {
                        textOk = "literal";
                        textPrefix = prefix(raw);
                    }
                }
                String title = field(page, "title") instanceof String t ? prefix(t) : "-";
                row("HVPG entry=" + entryId + " idx=" + i + " type=" + type + " cls=" + cls
                        + " err=" + err + " r1=" + r1 + " ok1=" + ok1 + " r2=" + r2 + " ok2=" + ok2
                        + " stacks=" + stacks + " items=" + stackItems
                        + " text=" + textKey + " textOk=" + textOk
                        + " body=" + textPrefix + " title=" + title);
            }
        }
        check("c_recipe_refs_all_resolved", totalRecipeDead == 0,
                "配方引用=" + totalRecipeRefs + " 死链=" + totalRecipeDead);
        check("c_spotlight_stacks_all_nonempty", totalSpotlightEmpty == 0,
                "spotlight 页=" + totalSpotlights + " 空栈=" + totalSpotlightEmpty);
        check("c_text_keys_all_translated", totalKeyMissing == 0,
                "文本键缺失=" + totalKeyMissing + "（lang keys=" + lang.size() + "）");

        // ---------- RecipeManager 一侧：这些配方 id 真在配方表里 ----------
        var rm = mc.level.getRecipeManager();
        int rmChecked = 0;
        int rmMissing = 0;
        for (String entryId : ENTRIES) {
            BookEntry entry = contents.entries.get(ResourceLocation.parse(entryId));
            if (entry == null) {
                continue;
            }
            for (BookPage page : entry.getPages()) {
                if (!(page instanceof PageDoubleRecipe<?>)) {
                    continue;
                }
                for (String slot : new String[]{"recipeId", "recipe2Id"}) {
                    Object idf = field(page, slot);
                    if (idf == null) {
                        continue;
                    }
                    rmChecked++;
                    ResourceLocation key = ResourceLocation.tryParse(String.valueOf(idf));
                    if (key == null) {
                        rmMissing++;
                        row("HVRM id=" + idf + " present=false parse=null");
                        continue;
                    }
                    var holder = rm.byKey(key);
                    if (holder.isEmpty()) {
                        rmMissing++;
                        row("HVRM id=" + idf + " present=false");
                    } else {
                        var recipe = holder.get().value();
                        ItemStack out = recipe.getResultItem(mc.level.registryAccess());
                        row("HVRM id=" + idf + " present=true type="
                                + BuiltInRegistries.RECIPE_TYPE.getKey(recipe.getType())
                                + " out=" + BuiltInRegistries.ITEM.getKey(out.getItem())
                                + " count=" + out.getCount());
                    }
                }
            }
        }
        check("c_recipe_manager_has_all_refs", rmMissing == 0,
                "RecipeManager 查了 " + rmChecked + " 条，缺 " + rmMissing);

        // ---------- JEI 一侧（装了才有；JEI 的配方来源就是 RecipeManager 这张表） ----------
        boolean jei = ModList.get().isLoaded("jei");
        row("HVJEI loaded=" + jei);
        if (jei) {
            int all = rm.getRecipes().size();
            int bg = 0;
            for (var h : rm.getRecipes()) {
                if (h.id().getNamespace().equals("bettergold")) {
                    bg++;
                }
            }
            row("HVJEI recipeManagerAll=" + all + " bettergoldRecipes=" + bg);
        }

        // ---------- 日志扫描（此刻为止的 latest.log） ----------
        Path log = Path.of(System.getProperty("user.dir")).resolve("logs").resolve("latest.log");
        int err = 0;
        int unable = 0;
        int patchouliErr = 0;
        var errSamples = new java.util.ArrayList<String>();
        try {
            if (Files.exists(log)) {
                for (String line : Files.readAllLines(log, java.nio.charset.StandardCharsets.UTF_8)) {
                    if (line.contains("/ERROR")) {
                        err++;
                        if (errSamples.size() < 5) {
                            errSamples.add(line.length() > 200 ? line.substring(0, 200) : line);
                        }
                    }
                    if (line.contains("Unable to ")) {
                        unable++;
                    }
                    if (line.contains("vazkii.patchouli") && line.contains("ERROR")) {
                        patchouliErr++;
                    }
                }
            }
        } catch (Exception e) {
            fail("c_log_scan_io", String.valueOf(e));
        }
        row("HVLOG errorLines=" + err + " unableToLines=" + unable
                + " patchouliErrorLines=" + patchouliErr + " samples=" + errSamples);
        check("c_log_no_patchouli_errors", patchouliErr == 0, "patchouli ERROR=" + patchouliErr);
    }

    private static String safeIcon(BookEntry entry) {
        try {
            return String.valueOf(entry.getIcon());
        } catch (Throwable t) {
            return "icon-exception:" + t;
        }
    }

    private static String firstItems(ItemStack[] arr, int max) {
        if (arr == null) {
            return "-";
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < Math.min(max, arr.length); i++) {
            if (i > 0) {
                sb.append('|');
            }
            sb.append(arr[i] == null ? "null" : BuiltInRegistries.ITEM.getKey(arr[i].getItem()));
        }
        return sb.toString();
    }

    private static String shortKey(String raw) {
        return raw.length() > 64 ? raw.substring(0, 64) + "..." : raw;
    }

    /** 正文前 40 字（空白换成 '~'，保证日志行仍是单 token；只为汇报里能看清"页上写了什么"） */
    private static String prefix(String s) {
        if (s == null) {
            return "-";
        }
        String one = s.replaceAll("[\\s\\u0000-\\u001f]+", "~");
        return one.length() > 40 ? one.substring(0, 40) + "..." : one;
    }

    private static String shortName(String id) {
        return id.replace("bettergold:", "").replace("/", "_");
    }

    /** 客户端语言文件（Patchouli 走 MC 的 I18n，所以我们查 zh_cn 这张表） */
    private static java.util.Map<String, String> loadLang(Minecraft mc, String code) {
        var out = new java.util.HashMap<String, String>();
        try {
            var res = mc.getResourceManager().getResource(
                    ResourceLocation.fromNamespaceAndPath("bettergold", "lang/" + code + ".json"));
            if (res.isEmpty()) {
                return out;
            }
            try (var in = res.get().openAsReader()) {
                JsonObject obj = JsonParser.parseReader(in).getAsJsonObject();
                for (var e : obj.entrySet()) {
                    if (e.getValue().isJsonPrimitive()) {
                        out.put(e.getKey(), e.getValue().getAsString());
                    }
                }
            }
        } catch (Throwable t) {
            info("lang load failed: " + t);
        }
        return out;
    }

    private static void openGui(Minecraft mc, String entryId) {
        try {
            ClientBookRegistry.INSTANCE.displayBookGui(ResourceLocation.parse(BOOK_ID),
                    ResourceLocation.parse(entryId), 0);
        } catch (Throwable t) {
            fail("c_gui_open_" + shortName(entryId), String.valueOf(t));
        }
    }

    /** 真开书之后读屏：部件尺寸 + 左右两页的排版结果（<b>只读，不点任何 UI</b>） */
    private static void sampleGui(Minecraft mc, String entryId) {
        try {
            Screen screen = mc.screen;
            String cls = screen == null ? "null" : screen.getClass().getSimpleName();
            int left = -1;
            int top = -1;
            int spread = -1;
            int maxSpreads = -1;
            String lpage = "null";
            String rpage = "null";
            int lwords = -1;
            int rwords = -1;
            int lh = -1;
            int rh = -1;
            String lspan = "-";
            String rspan = "-";
            float lscale = -1;
            float rscale = -1;
            if (screen instanceof GuiBook gb) {
                left = gb.bookLeft;
                top = gb.bookTop;
                spread = intField(gb, "spread");
                maxSpreads = intField(gb, "maxSpreads");
                if (gb instanceof GuiBookEntry ge) {
                    Object l = field(ge, "leftPage");
                    Object r = field(ge, "rightPage");
                    lpage = l == null ? "null" : l.getClass().getSimpleName();
                    rpage = r == null ? "null" : r.getClass().getSimpleName();
                    lwords = wordCount(l);
                    rwords = wordCount(r);
                    lscale = wordScale(l);
                    rscale = wordScale(r);
                    lspan = wordSpan(l);
                    rspan = wordSpan(r);
                    if (l instanceof PageWithText pwtL) {
                        lh = pwtL.getTextHeight();
                    }
                    if (r instanceof PageWithText pwtR) {
                        rh = pwtR.getTextHeight();
                    }
                    wordPages++;
                    wordTotal += Math.max(0, lwords) + Math.max(0, rwords);
                }
            }
            row("HVGUI entry=" + entryId + " screen=" + cls + " left=" + left + " top=" + top
                    + " spread=" + spread + "/" + maxSpreads
                    + " lpage=" + lpage + " lwords=" + lwords + " lscale=" + lscale + " lh=" + lh + " lspan=" + lspan
                    + " rpage=" + rpage + " rwords=" + rwords + " rscale=" + rscale + " rh=" + rh + " rspan=" + rspan);
            check("c_gui_opened_" + shortName(entryId), screen instanceof GuiBookEntry, "screen=" + cls);
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} gui exception {}", TAG, entryId, t);
            fail("c_gui_exception_" + shortName(entryId), String.valueOf(t));
        }
    }

    private static int intField(Object target, String name) {
        Object v = field(target, name);
        return v instanceof Integer i ? i : -1;
    }

    private static int wordCount(Object page) {
        Object tr = field(page, "textRender");
        if (tr == null) {
            return -1;
        }
        Object words = field(tr, "words");
        return words instanceof java.util.List<?> l ? l.size() : -1;
    }

    private static float wordScale(Object page) {
        Object tr = field(page, "textRender");
        if (tr == null) {
            return -1;
        }
        Object s = field(tr, "scale");
        return s instanceof Float f ? f : -1;
    }

    /** 排版结果的下沿区间（{@code Word.x/y/width/height} 都是 public final） */
    private static String wordSpan(Object page) {
        Object tr = field(page, "textRender");
        if (tr == null) {
            return "-";
        }
        Object words = field(tr, "words");
        if (!(words instanceof java.util.List<?> list) || list.isEmpty()) {
            return "-";
        }
        int minY = Integer.MAX_VALUE;
        int maxBottom = Integer.MIN_VALUE;
        int minX = Integer.MAX_VALUE;
        int maxRight = Integer.MIN_VALUE;
        for (Object w : list) {
            Object y = field(w, "y");
            Object h = field(w, "height");
            Object x = field(w, "x");
            Object wd = field(w, "width");
            if (y instanceof Integer yi && h instanceof Integer hi) {
                minY = Math.min(minY, yi);
                maxBottom = Math.max(maxBottom, yi + hi);
            }
            if (x instanceof Integer xi && wd instanceof Integer wi) {
                minX = Math.min(minX, xi);
                maxRight = Math.max(maxRight, xi + wi);
            }
        }
        return "y[" + minY + "," + maxBottom + "]x[" + minX + "," + maxRight + "]";
    }

    /** 读 Patchouli 页面/渲染器里的<b>私有</b>字段（探针专用；不进生产代码） */
    private static Object field(Object target, String name) {
        if (target == null) {
            return null;
        }
        Class<?> c = target.getClass();
        while (c != null) {
            try {
                var f = c.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(target);
            } catch (NoSuchFieldException e) {
                c = c.getSuperclass();
            } catch (Throwable t) {
                return null;
            }
        }
        return null;
    }
}
