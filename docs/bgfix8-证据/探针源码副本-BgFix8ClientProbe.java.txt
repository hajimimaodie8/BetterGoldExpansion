package com.hjmmd_8.bettergold.probe.bgfix8;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.electronwill.nightconfig.core.UnmodifiableConfig;
import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.config.Config;
import com.google.gson.JsonObject;

import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.language.I18n;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.ModConfigSpec;

import vazkii.patchouli.client.book.BookContents;
import vazkii.patchouli.client.book.BookEntry;
import vazkii.patchouli.client.book.BookPage;
import vazkii.patchouli.common.book.Book;
import vazkii.patchouli.common.book.BookRegistry;

/**
 * bgfix8 A 级客户端探针（**只读验证，不参与任何玩法**；收尾整块删除）。
 *
 * <p>会话隔离：整包 {@code com.hjmmd_8.bettergold.probe.bgfix8}（收尾只删这个子目录）。
 * 开关文件 {@code <gameDir>/bgfix8c-probe.enabled}（按 {@link FMLPaths#GAMEDIR} 算）。</p>
 *
 * <p>红线 5：进世界后**第一 tick** 从整合服务端反射读 {@code getLevelName()}，
 * 必须是本轮自己造的 ASCII 探针世界 {@code bgfix8probe}，并**负向排除作者存档名**；
 * 不等 ⇒ ABORT（**不调 halt**、不调 stop 之外的动作）。</p>
 *
 * <h2>本轮要证的两件事</h2>
 * <ol>
 *   <li><b>配置界面显示文案</b>：读**已加载的 config spec** —— {@code Config.SPEC.getSpec()} 里
 *       那 16 个 {@code ModConfigSpec.ValueSpec} 的 {@code getComment()}（= 提示行）
 *       与 {@code getTranslationKey()} 经 {@code I18n.get(...)} 解析出来的**条目名**；
 *       另外读 {@code getDefault()} 与 {@code getRange()} 证明默认值/范围没动。</li>
 *   <li><b>手册章3 第 1 页右页</b>：读 **Patchouli 真加载后的内容树** ——
 *       该页 {@code title} 的**实际解析值**（并按 {@code PageSpotlight.render} 的同一分支算出
 *       "中上边字幕实际会画什么"）、{@code text} 的键与解析值（逐字 == 冻结快照 §6.3 第 1 行右格）。</li>
 * </ol>
 * <p>期望值：手册那两段逐字取自**仓库内冻结快照**（仓库根从 {@code GAMEDIR}（= {@code <repo>/run}）
 * 的 parent 反推 —— {@code ex/03 §3.18} 陷阱②）；14 条配置字面**直接写死在本探针里**
 * （那是作者给的需求字面，不是从实现里读出来的）。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class BgFix8ClientProbe {

    private static final String TAG = "BGFIX8C-PROBE";
    private static final String PROBE_WORLD = "bgfix8probe";
    private static final String AUTHOR_WORLD = "\u65b0\u7684\u4e16\u754c";   // 新的世界
    private static final String BOOK_ID = "bettergold:alchemy_handbook";
    private static final String ENTRY_ID = "bettergold:golden_knowledge";
    private static final String SNAPSHOT =
            "tools/asset-generator/bgappend-requirements-snapshot/bg-book-6.1-6.3.md";

    /** 作者 2026-10-09 给的**两条字面**（逐族展开；万坚金**不在表里**）。 */
    private static final String[][] FAMS = {
            {"flamegold", "\u70c8\u71c3\u91d1", "Flamegold"},
            {"voodoogold", "\u5deb\u6bd2\u91d1", "Voodoogold"},
            {"thundergold", "\u7ed3\u96f7\u91d1", "Thundergold"},
            {"indigoseagold", "\u975b\u6d77\u91d1", "Indigoseagold"},
            {"illusiongold", "\u5e7b\u60d1\u91d1", "Illusiongold"},
            {"thornsgold", "\u6811\u68d8\u91d1", "Thornsgold"},
            {"echogold", "\u5e7d\u5486\u91d1", "Echogold"},
    };

    /** 万坚金两条：**必须逐字不动**的原措辞（改前 = 现行）。 */
    private static final String[][] STURDY_KEYS = {
            {"sturdygoldWeaponAbilityChance",
             "\u4e07\u575a\u91d1\u3010\u6b66\u5668\u5de5\u5177\u3011\u89e6\u53d1\u80fd\u529b"
                     + "\uff08\u7206\u91d1\uff1a\u547d\u4e2d\u5fc5\u5b9a\u6389\u843d\u4e00\u4ef6"
                     + "\u91d1\u7cfb\u7269\u54c1\uff09\u7684\u6982\u7387\u3002"},
            {"sturdygoldArmorAbilityIntervalMultiplier",
             "\u4e07\u575a\u91d1\u3010\u76d4\u7532\u76fe\u724c\u3011\u89e6\u53d1\u80fd\u529b"
                     + "\uff08\u6bcf 16 \u79d2 1 \u4efd\u4f24\u5bb3\u5438\u6536\uff09\u7684"
                     + "\u95f4\u9694\u4e58\u6cd5\u7cfb\u6570\u3002"},
    };

    private static boolean armed;
    private static boolean worldOk;
    private static boolean done;
    private static int bootTick;
    private static int worldTick;
    private static int pass;
    private static int fail;
    private static int skip;
    private static String levelName = "?";
    private static final List<String> problems = new ArrayList<>();
    private static final List<String> readouts = new ArrayList<>();

    private BgFix8ClientProbe() {
    }

    private static void report(String rawId, boolean ok, String detail) {
        String key = rawId.replace('/', '_');
        if (ok) {
            pass++;
            bettergold.LOGGER.info("{} {} :: PASS {}", TAG, key, detail);
        } else {
            fail++;
            problems.add(key + " :: " + detail);
            bettergold.LOGGER.error("{} {} :: FAIL {}", TAG, key, detail);
        }
    }

    private static void skipped(String rawId, String detail) {
        skip++;
        bettergold.LOGGER.warn("{} {} :: SKIP {}", TAG, rawId.replace('/', '_'), detail);
    }

    private static void readout(String rawId, String detail) {
        readouts.add(rawId.replace('/', '_'));
        bettergold.LOGGER.info("{} {} :: READOUT {}", TAG, rawId.replace('/', '_'), detail);
    }

    @SubscribeEvent
    public static void onClientTick(ClientTickEvent.Post event) {
        if (done) {
            return;
        }
        if (!armed) {
            Path flag = FMLPaths.GAMEDIR.get().resolve("bgfix8c-probe.enabled");
            if (!Files.isRegularFile(flag)) {
                return;
            }
            armed = true;
            bettergold.LOGGER.info("{} armed=true gamedir={} flag={} cwd={} userDir={}",
                    TAG, FMLPaths.GAMEDIR.get(), flag, Path.of("").toAbsolutePath(),
                    System.getProperty("user.dir"));
        }
        Minecraft mc = Minecraft.getInstance();
        // ⚠ tick 计数**在"进入目标状态之后"才起算**（ex/03 §3.12 陷阱②）
        if (!worldOk) {
            bootTick++;
            if (mc.level == null || mc.getSingleplayerServer() == null) {
                return;
            }
            guardWorld(mc);
            if (!worldOk) {
                return;     // ABORT：不动任何东西
            }
        }
        worldTick++;
        try {
            if (worldTick == 60) {
                probeBook();
                probeConfigSpec();
            } else if (worldTick == 100) {
                summary();
            }
        } catch (Throwable t) {
            fail++;
            problems.add("worldTick=" + worldTick + " 抛异常：" + t);
            bettergold.LOGGER.error("{} worldTick={} 抛异常", TAG, worldTick, t);
        }
    }

    private static void guardWorld(Minecraft mc) {
        String name = "?";
        try {
            Object integrated = mc.getSingleplayerServer();
            Object lvl = integrated.getClass().getMethod("overworld").invoke(integrated);
            Object data = lvl.getClass().getMethod("getLevelData").invoke(lvl);
            name = String.valueOf(data.getClass().getMethod("getLevelName").invoke(data));
        } catch (Throwable t) {
            name = "<反射失败:" + t.getClass().getSimpleName() + ">";
        }
        levelName = name;
        boolean ok = PROBE_WORLD.equals(name) && !name.contains(AUTHOR_WORLD);
        report("probe_world_guard", ok, "levelName=" + name + " expect=" + PROBE_WORLD
                + " authorWorld=" + AUTHOR_WORLD);
        if (!ok) {
            bettergold.LOGGER.error("{} ABORT 世界名不对（不是本轮自己的 ASCII 探针世界）—— "
                    + "停止一切动作；**不调 halt / stop**，避免把当前世界存盘", TAG);
            done = true;
            return;
        }
        worldOk = true;
        readout("boot_ticks_before_world", "进入世界用了 bootTick=" + bootTick);
    }

    // ==================== 仓库根 / 冻结快照 ====================

    private static Path repoRoot() {
        Path gamedir = FMLPaths.GAMEDIR.get();
        List<Path> candidates = new ArrayList<>();
        if (gamedir.getParent() != null) {
            candidates.add(gamedir.getParent());
        }
        candidates.add(Path.of("").toAbsolutePath());
        if (Path.of("").toAbsolutePath().getParent() != null) {
            candidates.add(Path.of("").toAbsolutePath().getParent());
        }
        for (Path c : candidates) {
            if (Files.isRegularFile(c.resolve(SNAPSHOT))) {
                readout("repo_root", "GAMEDIR=" + gamedir + " cwd=" + Path.of("").toAbsolutePath()
                        + " userDir=" + System.getProperty("user.dir") + " => repoRoot=" + c);
                return c;
            }
        }
        readout("repo_root_not_found", "GAMEDIR=" + gamedir + " cwd=" + Path.of("").toAbsolutePath()
                + " userDir=" + System.getProperty("user.dir") + " candidates=" + candidates
                + "（三处都找不到 " + SNAPSHOT + "）");
        return null;
    }

    /** 冻结快照 §6.3 第 1 行：返回 {左标题, 右标题, 左正文, 右正文}（读不到给 null）。 */
    private static String[] snapshotK3Row1() {
        Path root = repoRoot();
        if (root == null) {
            return null;
        }
        try {
            List<String> lines = Files.readAllLines(root.resolve(SNAPSHOT), StandardCharsets.UTF_8);
            boolean active = false;
            for (String ln : lines) {
                if (ln.startsWith("### 6.3")) {
                    active = true;
                    continue;
                }
                if (active && ln.startsWith("---")) {
                    break;
                }
                if (!active || !ln.startsWith("|") || ln.contains("|---")) {
                    continue;
                }
                String[] cells = ln.split("\\|");
                if (cells.length < 4) {
                    continue;
                }
                String num = cells[1].trim().replace("*", "");
                if (!num.equals("1")) {
                    continue;
                }
                String left = cells[2].trim();
                String right = cells[3].trim();
                return new String[] {
                        titleOf(left), titleOf(right), bodyOf(left), bodyOf(right)};
            }
        } catch (Throwable t) {
            problems.add("读冻结快照失败：" + t);
        }
        return null;
    }

    /** 单元格第 1 段「图标：**X**」里的 X（去掉 `（随排版顺序变化）`）。 */
    private static String titleOf(String cell) {
        String head = cell.split("<br>")[0].trim();
        if (!head.startsWith("\u56fe\u6807\uff1a")) {   // 图标：
            return "";
        }
        String t = head.substring("\u56fe\u6807\uff1a".length()).replace("**", "").trim();
        return t.replace("\uff08\u968f\u6392\u7248\u987a\u5e8f\u53d8\u5316\uff09", "").trim();
    }

    /** 单元格最后一段正文（若该格只有图标说明 ⇒ 空串）。 */
    private static String bodyOf(String cell) {
        String[] parts = cell.split("<br>");
        String body = parts[parts.length - 1].trim();
        if (body.startsWith("\u56fe\u6807\uff1a")) {    // 图标：
            return "";
        }
        return body.replace("**", "").trim();
    }

    // ==================== ① 手册内容树 ====================

    private static Object fieldOf(Object target, String name) {
        Class<?> k = target.getClass();
        while (k != null) {
            try {
                Field f = k.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(target);
            } catch (NoSuchFieldException ex) {
                k = k.getSuperclass();
            } catch (Exception ex) {
                return null;
            }
        }
        return null;
    }

    private static void probeBook() {
        String[] snap = snapshotK3Row1();
        if (snap == null) {
            report("snapshot_loaded", false, "冻结快照 §6.3 第 1 行没读出来（期望值来源缺失）");
            return;
        }
        report("snapshot_loaded", snap[1].length() > 0 && snap[3].length() > 0,
                "快照 §6.3 第 1 行：左标题=" + snap[0] + " / 右标题=" + snap[1]
                        + " / 左正文 " + snap[2].length() + " 字 / 右正文 " + snap[3].length() + " 字");

        Map<ResourceLocation, Book> books = BookRegistry.INSTANCE.books;
        Book book = books.get(ResourceLocation.parse(BOOK_ID));
        report("book_registered", book != null, "books=" + books.keySet());
        if (book == null) {
            return;
        }
        BookContents c = book.getContents();
        report("book_contents_no_error", c != null && !c.isErrored(),
                "isErrored=" + (c != null && c.isErrored()) + " exception="
                        + (c == null ? "<null contents>" : String.valueOf(c.getException())));
        if (c == null) {
            return;
        }
        BookEntry e = c.entries.get(ResourceLocation.parse(ENTRY_ID));
        report("k3_entry_present", e != null, "entry=" + ENTRY_ID + " present=" + (e != null));
        if (e == null) {
            return;
        }
        List<BookPage> pages = e.getPages();
        report("k3_pages_10", pages.size() == 10, "章3 页数=" + pages.size() + " expect=10");
        if (pages.size() < 2) {
            return;
        }
        BookPage left = pages.get(0);
        BookPage right = pages.get(1);

        // ---- 右页：title（= "字幕"）的**实际解析值** + 按 render 的同一分支算"实际会画什么" ----
        JsonObject so = right.sourceObject;
        String rawTitle = String.valueOf(fieldOf(right, "title"));
        String titleKey = (so != null && so.has("title")) ? so.get("title").getAsString() : "<无 title 字段>";
        String resolvedTitle = right.i18nText(rawTitle).getString();
        Object stacksObj = fieldOf(right, "stacks");
        ItemStack[] stacks = (stacksObj instanceof ItemStack[]) ? (ItemStack[]) stacksObj : new ItemStack[0];
        int nonEmpty = 0;
        List<String> names = new ArrayList<>();
        for (ItemStack s : stacks) {
            if (s != null && !s.isEmpty()) {
                nonEmpty++;
                if (names.size() < 3) {
                    names.add(s.getHoverName().getString());
                }
            }
        }
        String header = (!rawTitle.isEmpty()) ? resolvedTitle : (nonEmpty > 0
                ? stacks[0].getHoverName().getString() : "<空>");
        readout("k3_p1_right_title_resolved",
                "JSON title=" + titleKey + " / 字段 title=" + rawTitle + " / i18nText(title)="
                        + resolvedTitle + " / stacks=" + stacks.length + "（非空 " + nonEmpty
                        + "，前几个物品名=" + names + "）/ **按 render 分支实际会画的中上边字幕=" + header + "**");
        report("k3_p1_right_title_literal", rawTitle.equals(snap[1]),
                "右页 title=" + rawTitle + " / 快照字幕=" + snap[1]);
        report("k3_p1_right_title_is_not_item_name", !rawTitle.isEmpty() && header.equals(resolvedTitle),
                "字幕不是物品名（分支取的是 title 而不是 stacks[0].getHoverName()）：header=" + header);
        report("k3_p1_right_stacks_8", stacks.length == 8 && nonEmpty == 8,
                "八张升级模板 stacks=" + stacks.length + " 非空=" + nonEmpty);

        // ---- 右页：text（= "正文"）的键与**逐字解析值** ----
        String textKey = (so != null && so.has("text")) ? so.get("text").getAsString() : "<无 text 字段>";
        String resolvedText = right.i18nText(textKey).getString();
        readout("k3_p1_right_text_resolved",
                "text 键=" + textKey + " / i18nText 解析值=" + resolvedText);
        report("k3_p1_right_text_key",
                "bettergold.handbook.page.knowledge_1_right".equals(textKey),
                "右页 text 键=" + textKey);
        report("k3_p1_right_text_verbatim", resolvedText.equals(snap[3]),
                "右页正文逐字比对冻结快照=" + resolvedText.equals(snap[3])
                        + "（实际 " + resolvedText.length() + " 字 / 快照 " + snap[3].length() + " 字）");

        // ---- 左页回归（这一跨页的另一半不许被顺手弄坏）----
        String leftTitle = String.valueOf(fieldOf(left, "title"));
        JsonObject soL = left.sourceObject;
        String leftTextKey = (soL != null && soL.has("text")) ? soL.get("text").getAsString() : "<无>";
        report("k3_p1_left_unchanged",
                leftTitle.equals(snap[0])
                        && "bettergold.handbook.page.knowledge_1_summary".equals(leftTextKey),
                "左页 title=" + leftTitle + "（快照 " + snap[0] + "）/ text 键=" + leftTextKey);

        // ---- 全书的条目/页数（回归：本轮只动了这一页）----
        int total = 0;
        for (BookEntry be : c.entries.values()) {
            total += be.getPages().size();
        }
        readout("book_totals", "entries=" + c.entries.size() + " pages=" + total
                + "（改前基线：entries=20 / pages=192 —— 本轮只加正文，页数不许变）");
        report("book_pages_unchanged", total == 192, "全书页数=" + total + " expect=192");
    }

    // ==================== ② 配置 spec ====================

    private static void probeConfigSpec() {
        UnmodifiableConfig values = Config.SPEC.getValues();
        UnmodifiableConfig spec = Config.SPEC.getSpec();
        readout("cfg_spec_loaded", "SPEC.getValues() 条目=" + values.valueMap().size()
                + " / SPEC.getSpec() 条目=" + spec.valueMap().size()
                + " / getSpec() 里第一项的类=" + spec.valueMap().values().stream()
                        .findFirst().map(v -> v.getClass().getName()).orElse("<空>"));
        report("cfg_spec_has_16", spec.valueMap().size() >= 25,
                "getSpec() 条目=" + spec.valueMap().size() + "（应为 25 = 既有 9 + 新增 16）");

        int checked = 0;
        for (String[] fam : FAMS) {
            for (String suffix : new String[] {"WeaponBuffChance", "ArmorBuffChance"}) {
                String key = fam[0] + suffix;
                String wantZh = suffix.startsWith("Weapon")
                        ? fam[1] + "\u00b7\u6b66\u5668\u5de5\u5177\u76fe\u724c\u89e6\u53d1Buff\u6982\u7387"
                        : fam[1] + "\u00b7\u76d4\u7532\u89e6\u53d1buff\u6982\u7387";
                try {
                    Object o = spec.get(key);
                    if (!(o instanceof ModConfigSpec.ValueSpec vs)) {
                        report("cfg_spec_" + key, false, "SPEC.getSpec() 里取不到 ValueSpec："
                                + (o == null ? "<null>" : o.getClass().getName()));
                        continue;
                    }
                    String tk = vs.getTranslationKey();
                    String comment = vs.getComment();
                    // ⚠ 本版 NeoForge（21.1.228）的 `ValueSpec.getTranslationKey()` 实测恒为 **null**
                    //   ⇒ 条目名**不从这个访问器来**（ConfigurationScreen 自己有 TranslationChecker +
                    //   fallback，见 §29.7 记账）。所以两处都读：
                    //     ① `.comment()`（= 提示行，**已加载的 spec 里读出来的**）
                    //     ② 语言文件那一把键经 I18n 解析出来的值（= 界面条目名的候选字面）
                    String langKey = "bettergold.configuration." + key;
                    String shown = I18n.get(langKey);
                    String flat = (comment == null) ? "<getComment()=null>"
                            : comment.replace("\n", " | ");
                    readout("cfg_" + key, "translationKey(null=本版常态)=" + tk
                            + " / I18n.get(" + langKey + ")=" + shown
                            + " / getComment()=" + flat);
                    report("cfg_label_" + key, wantZh.equals(shown),
                            "语言键解析出的条目名=" + shown + " / 作者字面=" + wantZh);
                    report("cfg_comment_" + key, comment != null && comment.contains(wantZh),
                            ".comment() 里含作者字面=" + (comment != null && comment.contains(wantZh)));
                    checked++;
                } catch (Throwable t) {
                    report("cfg_spec_" + key, false, "读该条配置时抛异常：" + t);
                }
            }
        }
        report("cfg_labels_checked_14", checked == 14, "核对的配置条目数=" + checked + " expect=14");

        // 负向：旧措辞不许在**已加载的 spec** 里出现
        int oldHits = 0;
        for (Object o : spec.valueMap().values()) {
            if (o instanceof ModConfigSpec.ValueSpec vs
                    && vs.getComment() != null && vs.getComment().contains(
                            "\u3010\u76d4\u7532\u76fe\u724c\u3011\u53cd\u5236 Buff\uff08")) {
                oldHits++;
            }
        }
        report("cfg_comment_old_gone", oldHits == 0, "spec 里含旧措辞的条目数=" + oldHits + " expect=0");

        // 万坚金两条：逐字不动（提示行 + 条目名）
        for (String[] sk : STURDY_KEYS) {
            try {
                Object o = spec.get(sk[0]);
                if (!(o instanceof ModConfigSpec.ValueSpec vs)) {
                    report("cfg_sturdygold_" + sk[0], false, "取不到 ValueSpec");
                    continue;
                }
                String comment = vs.getComment() == null ? "" : vs.getComment();
                String shown = I18n.get("bettergold.configuration." + sk[0]);
                readout("cfg_sturdygold_" + sk[0], "条目名=" + shown + " / getComment() 首行="
                        + comment.split("\n")[0]);
                report("cfg_sturdygold_" + sk[0],
                        comment.contains(sk[1]) && shown.contains("\u4e07\u575a\u91d1")
                                && shown.contains("\u89e6\u53d1\u80fd\u529b"),
                        "提示行含原措辞=" + comment.contains(sk[1]) + " / 条目名=" + shown
                                + "（万坚金两条**必须**保持自己的「能力/间隔」措辞："
                                + "它们的字面里本来就含「盔甲盾牌」，那不是本轮要改的 14 条）");
            } catch (Throwable t) {
                report("cfg_sturdygold_" + sk[0], false, "读万坚金配置时抛异常：" + t);
            }
        }

        // 16 条的默认值与范围（运行时读数 == 规格 §11.4）
        Map<String, String> wantDefaults = new LinkedHashMap<>();
        for (String[] fam : FAMS) {
            wantDefaults.put(fam[0] + "WeaponBuffChance", fam[0].equals("illusiongold") ? "0.16" : "1.0");
            wantDefaults.put(fam[0] + "ArmorBuffChance", fam[0].equals("illusiongold") ? "0.04" : "0.25");
        }
        wantDefaults.put("sturdygoldWeaponAbilityChance", "1.0");
        wantDefaults.put("sturdygoldArmorAbilityIntervalMultiplier", "1.0");
        int defOk = 0;
        for (Map.Entry<String, String> en : wantDefaults.entrySet()) {
            try {
                Object o = spec.get(en.getKey());
                if (!(o instanceof ModConfigSpec.ValueSpec vs)) {
                    report("cfg_defaults_runtime", false, "取不到 " + en.getKey());
                    continue;
                }
                String def = String.valueOf(vs.getDefault());
                String range = String.valueOf(vs.getRange());
                readout("cfg_frozen_" + en.getKey(),
                        "default=" + def + "（期望 " + en.getValue() + "）/ range=" + range);
                if (def.equals(en.getValue())) {
                    defOk++;
                } else {
                    report("cfg_defaults_runtime", false,
                            en.getKey() + " default=" + def + " 期望 " + en.getValue());
                }
            } catch (Throwable t) {
                report("cfg_defaults_runtime", false, en.getKey() + " 抛异常：" + t);
            }
        }
        report("cfg_defaults_runtime", defOk == 16, "默认值逐条通过 " + defOk + "/16");
    }

    private static void summary() {
        readout("forced_chunks_note", "客户端整合服务端：本轮**不做任何 forceload**（只读内容树/配置）");
        bettergold.LOGGER.info("{} SUMMARY pass={} fail={} skip={} levelName={} readouts={} worldTick={}",
                TAG, pass, fail, skip, levelName, readouts.size(), worldTick);
        for (String p : problems) {
            bettergold.LOGGER.error("{} PROBLEM {}", TAG, p);
        }
        bettergold.LOGGER.info("{} stopping client", TAG);
        done = true;
        armed = false;
        Minecraft.getInstance().stop();
    }
}
