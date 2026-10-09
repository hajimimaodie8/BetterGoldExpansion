
## 29.4 扰动实测（`probe/bgfix8/perturb.py`；证据 `docs/bgfix8-证据/04-关卡扰动矩阵.txt`）

| 类别 | 用例 | 期望 | 实测 |
|---|---|---|---|
| 基线 | — | exit 0 | **exit 0** |
| 改坏 | P01–P15（15 条） | exit 1 + 命中期望 id | **逐条命中**（表见下） |
| 反向对照 | P16（只在注释里写旧措辞 / 重复新字面）、P17（只加一个判据不看的语言键） | exit 0 | **exit 0** |
| 前置缺失 | P18（冻结快照改名搬走） | exit 2 + `[bgfix8-anti-vacuum]` | **exit 2** ✔ |

**总计：`cases run = 18 / 18`、`mismatches = 0`、`SETUP_FAILS = 0`、`RESTORE identical: True`**
（6 个被改文件**逐字节复原**：`Config.java` / `zh_cn.json` / `en_us.json` / 冻结快照 / 手册 zh JSON / 规格）。

★ **两处"用例本身失效"的当场修法**（`ex/03` §3.11/§3.12 的三档模式在这里正好各中一次）：

1. **P09 首版 = "删掉 `title` 那一行"** ⇒ 删掉的却是对象**最后一个键**，留下**尾逗号** ⇒ JSON 解析失败
   ⇒ 关卡 **exit 2**（= "脚本自己崩了"，**不是命中**）。改成**把 `title` 置成空串**（合法 JSON、语义相反）
   ⇒ `exit 1` 且命中 `[bgfix8-book-right-title]` + `[bgfix4-k3p1-restored]`。**承 §3.11 陷阱③。**
2. **P15 首版 = 把规格里的小节名 `# 二十九、bgfix8` 改成 `bgfix8-shifted`** ⇒ **needle `bgfix8` 仍是它的子串**
   ⇒ 照样 `exit 0`（"关卡没红"的假象）。改成**把那条 needle 在规格里全部替换掉**（`模式=all`）
   ⇒ `exit 1` 且命中 `[bgfix8-doc]`。**承 §3.12 陷阱④（needle 多处出现时的模式选择）。**

| 用例 | 扰动动作 | exit | 命中的 id |
|---|---|---|---|
| P01 | zh 条目名退回旧字面 | 1 | `[bgfix8-config-label-zh]` |
| P02 | en 条目名退回旧字面 | 1 | `[bgfix8-config-label-en]` |
| P03 | 把「盾牌」塞回**盔甲侧**（语义回退） | 1 | `[bgfix8-config-label-zh]` |
| P04 | 顺手改万坚金那条 | 1 | `[bgfix8-config-sturdygold-untouched]` |
| P05 | `Config.java` 提示行退回旧措辞 | 1 | `[bgfix8-config-comment-zh]` + `[bgfix8-config-comment-old-gone]` |
| P06 | 改默认值（0.04 → 0.05） | 1 | `[bgfix-config-defaults]` |
| P07 | 改取值范围（0~1 → 0~2） | 1 | `[bgfix8-config-keys-frozen]` |
| P08 | 删掉右页正文 | 1 | `[bgfix8-book-right-text]` + `[bgfix4-k3p1-restored]` |
| P09 | 右页 `title` 置空（**Patchouli 会退化成物品名**） | 1 | `[bgfix8-book-right-title]` + `[bgfix4-k3p1-restored]` |
| P10 | 右页正文换成自编文字 | 1 | `[bgfix8-book-right-text]` + `[bgfix8-book-right-text-source]` + `[bgbook2-texts-verbatim]` |
| P11 | 冻结快照里删掉那一段 | 1 | `[bgfix8-book-right-text]` + `[bgbook2-texts-verbatim]` |
| P12 | 冻结快照里的**字幕**被改 | 1 | `[bgfix8-book-right-title]` + `[bgfix4-k3p1-restored]` |
| P13 | 右页正文换成左页那句（等于没加） | 1 | `[bgfix8-book-right-text]` |
| P14 | 右页去引用**仍被禁**的 `knowledge_1_left` | 1 | `[bgappend-book-k3-old-text-gone]` |
| P15 | 规格里的 needle 全部改掉 | 1 | `[bgfix8-doc]` |
| P16 | **只在注释里**写旧措辞 / 重复新字面 | 0 | —（反向对照：正/负 needle **都跑在去注释源码上**） |
| P17 | 只加一个判据不看的语言键 | 0 | —（反向对照） |
| P18 | 冻结快照改名搬走 | 2 | `[bgfix8-anti-vacuum]` |

## 29.5 构建与六校验器（exit + 关键计数行，两列）

| 步骤 | 命令 | exit | 关键计数行 |
|---|---|---|---|
| 编译 + 数据生成 | `.\gradlew.bat compileJava runData` | **0** | `BUILD SUCCESSFUL in 35s`（`7 actionable tasks`） |
| 资源 + 打包 | `.\gradlew.bat processResources jar --rerun-tasks` | **0** | `BUILD SUCCESSFUL in 17s`；`build/libs/bettergold-1.6.0.jar` = **1,361,454 B** |
| 关卡 1 | `validate_metal_assets.py` | **0** | `[bg-assets-anti-vacuum] 实际检查了 595 项` / `[bg-assets-ok] 问题合计 0 条` |
| 关卡 2 | `validate_metal_data.py` | **0** | `bgfix8（配置显示文案 + 手册右页字幕/正文）问题: 0`；`配置条目名核对 14 条 / 键与范围 16/16 / 右页 title='"贵金"装备的升级锻造模版' / 右页正文 76 字`；`[bg-data-anti-vacuum] 实际检查了 307 项（语言键）+ 1660 个 JSON 产物` |
| 关卡 3 | `validate_trim_assets.py` | **0** | `[bgfinal3-anti-vacuum] 实际检查了 68 项` |
| 关卡 4 | `check_jar_clean.py` | **0** | **`jar 内 *Probe* 路径 = 0`** / `jar 内 'halt' 字节的 class = 0` / `jar 文件总数 = 2408` |
| 关卡 5 | `check_forced_chunks.py` | **0** | `data.Forced = []`（长度 0） |
| 关卡 6 | `validate_advancements.py` | **0** | `[bgach-ok] 问题 0 条 / 成就 51 条 / criteria 125 条` |

> ★ **六条都是"能失败"的关卡**（`bgfix6` 轮的退出码契约）；本轮 `validate_metal_data.py` 新增的
> `[bgfix8-anti-vacuum]` 与 `[bgfix8-*]` 族**在扰动矩阵里各被弄红过一次**（P18 走 exit 2，其余 exit 1）。

## 29.6 A 级读数

### 29.6.1 `runServer`（专用服务端 + 本轮自建 ASCII 探针世界 `bgfix8probe`）

日志 `run/logs/2026-10-09-4.log.gz`（**游戏自己写的 UTF-8**；抽出的探针行见 `docs/bgfix8-证据/05`）：

```
Done (5.132s)! For help, type "help"
BGFIX8S-PROBE probe_world_guard :: PASS levelName=bgfix8probe expect=bgfix8probe authorWorld=新的世界
BGFIX8S-PROBE config_readout :: READOUT bgfix16 flamegold[w=1.000 a=0.250] voodoogold[w=1.000 a=0.250]
    thundergold[w=1.000 a=0.250] indigoseagold[w=1.000 a=0.250] illusiongold[w=0.160 a=0.040]
    thornsgold[w=1.000 a=0.250] echogold[w=1.000 a=0.250] sturdygold[w=1.000 a=0.000]
    sturdygoldArmorIntervalMultiplier=1.000
BGFIX8S-PROBE forced_chunks :: READOUT forced=0 expect=0
BGFIX8S-PROBE SUMMARY problems=[] tick=40 levelName=bgfix8probe 探针收尾 = halt(false) 一次
Stopping server
```

⇒ ① **世界名断言 PASS**（并负向排除作者存档名）；② **16 条的运行期读数与规格 §11.4 逐位一致**
（幻惑 0.160/0.040、万坚金盔甲侧恒 0、间隔系数 1.000）；③ **forceload 双向 0**；④ `halt(false)` **只调一次**。

### 29.6.2 `runClient`（真客户端 + 整合服务端；读 **Patchouli 真加载后的内容树** 与 **已加载的 config spec**）

日志 `run/logs/latest.log`（抽出的 89 行见 `docs/bgfix8-证据/06`）：**`SUMMARY pass=47 fail=0 skip=0 readouts=39`**。

**（a）第 2 条 · 右页的"字幕"与"正文"——A 级实测的原值**

```
probe_world_guard :: PASS levelName=bgfix8probe expect=bgfix8probe authorWorld=新的世界
snapshot_loaded :: PASS 快照 .3 第 1 行：左标题=各种各样的"贵金"锭 / 右标题="贵金"装备的升级锻造模版
    / 左正文 104 字 / 右正文 76 字
book_registered :: PASS books=[bettergold:alchemy_handbook]
book_contents_no_error :: PASS isErrored=false exception=null
k3_pages_10 :: PASS 章3 页数=10 expect=10
k3_p1_right_title_resolved :: READOUT JSON title="贵金"装备的升级锻造模版 / 字段 title="贵金"装备的升级锻造模版
    / i18nText(title)="贵金"装备的升级锻造模版 / stacks=8（非空 8，前几个物品名=[烈燃金升级锻造模板,
    万坚金升级锻造模板, 树棘金升级锻造模板]）/ **按 render 分支实际会画的中上边字幕="贵金"装备的升级锻造模版**
k3_p1_right_title_is_not_item_name :: PASS 字幕不是物品名（分支取的是 title 而不是 stacks[0].getHoverName()）
k3_p1_right_text_resolved :: READOUT text 键=bettergold.handbook.page.knowledge_1_right
    / i18nText 解析值=当然"贵金"也可以用于制作功能性强大的武装使用，不过得先做出某样"贵金"锭和它所对应的
      核心材料所制成的锻造模板，再搭配上金装备和所相符的"贵金"锭即可。
k3_p1_right_text_verbatim :: PASS 右页正文逐字比对冻结快照=true（实际 76 字 / 快照 76 字）
k3_p1_left_unchanged :: PASS 左页 title=各种各样的"贵金"锭 / text 键=…knowledge_1_summary
book_pages_unchanged :: PASS 全书页数=192 expect=192
```

⇒ ★★ **"字幕"这一半的实测结论**：该页 `title` 字段**非空**、`i18nText()` 解析值 = 「"贵金"装备的升级锻造模版」，
且按 `PageSpotlight.render()` 的**同一个分支**算出来的"实际会画的中上边字幕"**就是它**（不是 `stacks[0]` 的物品名，
那 8 个物品名是「烈燃金升级锻造模板…」）。**即：当前构建里这一页的字幕本来就是作者在 §七.4 要的那句** ——
与作者本轮"你忘记填字幕了"的观察**不一致**（见 §29.7 第 1 条，如实记账、不擅自改字面）。
⇒ "正文"这一半：`text` 键 = `knowledge_1_right`，解析值 **逐字 == 冻结快照**（76 字 = 76 字）✔
⇒ 页数 **192 → 192 不变**（只加正文，不加页）✔

**（b）第 1 条 · 配置界面两处文案 —— 从**已加载的 spec/语言表**读到的运行期原值**

```
cfg_spec_loaded :: READOUT SPEC.getValues() 条目=25 / SPEC.getSpec() 条目=25
    / getSpec() 里第一项的类=net.neoforged.neoforge.common.ModConfigSpec$ValueSpec
cfg_flamegoldWeaponBuffChance :: READOUT translationKey(null=本版常态)=null
    / I18n.get(bettergold.configuration.flamegoldWeaponBuffChance)=烈燃金·武器工具盾牌触发Buff概率
    / getComment()=烈燃金·武器工具盾牌触发Buff概率 | 武器 / 工具 / 盾牌（含举盾反制）都走本条
      —— 盾牌的反制赋予 Buff 因此默认为 100%。 | 触发的是 Buff：高燃。0 = 永不触发；1 = 必定触发（默认）。
      |  Default: 1.0 |  Range: 0.0 ~ 1.0
cfg_labels_checked_14 :: PASS 核对的配置条目数=14 expect=14
cfg_sturdygold_sturdygoldArmorAbilityIntervalMultiplier :: READOUT
    条目名=万坚金 · 盔甲盾牌触发能力间隔（乘法系数；…取值范围 0 ~ 100）
    / getComment() 首行=万坚金【盔甲盾牌】触发能力（每 16 秒 1 份伤害吸收）的间隔乘法系数。
cfg_defaults_runtime :: PASS 默认值逐条通过 16/16
SUMMARY pass=47 fail=0 skip=0
```

⇒ ① **14 条**的 `.comment()` 首行与 `bettergold.configuration.*` 的字面**都** = 作者给的新文案（逐条 PASS）；
② **16 条的默认值逐条通过 16/16**（运行期读数）；③ **万坚金两条的提示行与条目名逐字未动**（PASS）。

## 29.7 未验证 / 人眼项 / 记账（诚实清单）

1. ★★ **"字幕"：作者报告与本轮实测不符 —— 需求没覆盖的新情况，已如实报告、不擅自改字面。**
   A 级（§29.6.2a）证明当前构建里该页 `title` 就是「"贵金"装备的升级锻造模版」、且渲染分支取的就是它。
   **可能性（都未验证）**：① 作者看的是**更早构建的包**；② 他说的"字幕"指的不是顶栏 `title` 而是别的观感；
   ③ 他期望的**字面**与现行那句不同（要改就是 `generate_handbook_data.py` 的 `KNOWLEDGE_1_TEMPLATE_TITLE`
   **一行** + 冻结快照那一格逐字 + 重跑生成器）。**本轮已加关卡 `[bgfix8-book-right-title]` 把这个故障模式钉死**
  （title 一空就红）——请作者确认要不要换字面。
2. ★ **正文的来源是"第三处"**：父代理口径是"§19.6.2 与冻结快照都没有 ⇒ 先停下报告"。
   实测：**§19.6.2 只有形状、没有那段正文**；**冻结快照 §6.3 第 1 行右格当时只有「图标：…」**。
   但仓库内还有**作者原文留档** `docs/bgbook2-证据/07-从需求文档解析出的22段逐字文案.txt:18`
   （`knowledge_1_right`，2026-10-05 从作者需求文档逐字解析出来的）⇒ 本轮**采用它**（不是自编），
   并**同步冻结快照 + 记一条搬运记录**。⇒ 若作者要的是**别的**文字，**改一处即可**：
   `zh_cn.json` / `en_us.json` 的 `bettergold.handbook.page.knowledge_1_right` 值 + 冻结快照那一格（重跑生成器不必改）。
3. **`ValueSpec.getTranslationKey()` 在 NeoForge 21.1.228 实测恒为 `null`**（A 级读数里 25 条全 null）。
   而 `ConfigurationScreen` 自带 `TranslationChecker` + "fallback" 机制 ⇒ **界面条目名的最终来源无法用探针钉死**
   （它是 `Component.translatable(...)` + fallback）。**本轮的处理 = 两处一起改**（`.comment` 首行 + 语言键值），
   所以无论界面取哪一处，玩家看到的都是作者要的字面。**像素级呈现属人眼项。**
4. **两处推断（作者一句话可改）**：① 分隔符统一 `·`（作者第 2 条原话里写的是半角 `.`）；
   ② 大小写照字面保留（武器侧 `Buff` / 盔甲侧 `buff`）。
5. **结雷金的旧字面是「触发**能力**概率」**（它的武器侧效果是落雷+颤栗），本轮按作者给的**统一模板**
   改成了「触发 **Buff** 概率」（作者原话里给的就是 Buff）——**旧字面原文留档在 §29.1.1**。
   若他要保留"能力"字样，改 1 个字符串即可。
6. **贴图：本轮 0 字节改动**。但**工作树里另有 10 张 PNG 处于"相对 HEAD 已修改"状态**
   （`flamegold_sword.png` 等 8 张 mtime **10-09 11:42**、`gold_door.png`/`chaos_coin_string.png` mtime **10-09 19:55**）
   —— **都不是本轮写的**（本轮的写操作发生在 21:2x）；⇒ ① `git status` 会把它们算成本轮的脏改动，**别误记**；
   ② **`processResources jar` 打出的那个 `bettergold-1.6.0.jar` 里含这 10 张 PNG**（共享工作树的既成事实），
      要不要用这个 jar 发布由父代理/作者决定；③ `validate_metal_assets.py` 对它们**不敏感**（exit 0）。
7. **`git checkout -- <path>` 会把工作区文件写成 CRLF**（本仓 `core.autocrlf=true`；`git status` 看不出来，
   因为它按规范化后的内容比较）。本轮实测：`git checkout` 两个语言文件后 size 75264 → 76006。**修法 = 用 Python
   把 `\r\n` 换回 `\n`**（`probe/bgfix8/fix_eol.py`）；**结论 = 临时改动一律"字节复制 .bak"复原，不要用 `git checkout`。**
8. **抓日志别用 PowerShell 管道**：`gradlew … | Out-File -Encoding utf8` 之后**中文是乱码且不可逆**
   （`�`）⇒ **一律从 `run/logs/latest.log` 或轮转归档 `run/logs/*.log.gz` 取**（游戏自己写的是 UTF-8）。
   本轮的 05/06/06b 三份证据就是这样生成的。
9. **"探针世界"用完即删** `run/saves/bgfix8probe`（已删）；**作者存档 `run/saves/新的世界`（29 文件）
   与 `run/world`（51 文件）跑前跑后逐文件 SHA256 全等（差异 0 行）**。
10. **人眼项**：① 配置界面里条目名/提示行的像素呈现（本机不能自动截图）；
    ② 手册该页的观感（字幕与图标是否重叠、正文排版换行）；③ 作者端的构建来源（见第 1 条）。
11. **本轮没有 commit、没有 push**（父代理处理）；`run/` 期间**独占**（开工前查过：只有一个 Gradle daemon，
    无任何游戏进程；上一轮提到的 PID 41884 **已不在**）。

## 29.8 证据清单（`docs/bgfix8-证据/`）

| 文件 | 内容 |
|---|---|
| `01-语言键改写.txt` | 两个语言文件的改写日志（逐条 旧值 → 新值 + 键数 741→742 + 无 BOM/LF 自证） |
| `02-Config代码骨架自证.txt` | `Config.java` 与 HEAD 的**代码骨架**比对：`.comment` 折叠后**逐字相同**、`define` 25/25、`range` 18/18、顺序相同 |
| `03-生成器重跑.txt` | `generate_handbook_data.py` 重跑输出（192 页 / 章3 32 页 / RETIRED 74 页自证） |
| `04-关卡扰动矩阵.txt` | **18 条用例**（1 基线 + 15 改坏 + 2 反向对照 + 1 前置缺失），`mismatches 0` / `RESTORE identical: True` |
| `05-A级-runServer-探针读数.txt` | `runServer` 探针 7 行（世界名 PASS / `bgfix16` 读数 / forceload 0 / halt 一次） |
| `06-A级-runClient-探针读数.txt` | `runClient` 探针 **89 行 / 47 PASS 0 FAIL**（含该页 `title`/`text` 的解析值与 16 条配置读数） |
| `06b-A级-runClient-首轮用例错留档.txt` | 首轮客户端探针的**用例错**留档（`translationKey` 恒 null、探针自己的期望字符串打错一个字） |
| `07-B级构建与六校验器.txt` | 三条构建命令 + 六个校验器的 **exit 与关键计数行**（全 exit 0） |
| `08-收尾清理与逐字节复原.txt` | 探针整块删除 / `grep` 零命中 / `build.gradle`、`clientRunProgramArgs.txt`、`server.properties` 的 SHA256 复原 / 探针世界删除 / 作者存档差异 0 |
| `探针源码副本-BgFix8ClientProbe.java.txt` / `探针源码副本-BgFix8ServerProbe.java.txt` | **删前留档**的两个探针源码 |
| `perturb.py` / `run_setup.py` / `collect_evidence2.py` / `fix_eol.py` / `config_skeleton_check.py` / `lang_apply.py` / `six_validators.py` | 可重跑的一次性脚本副本 |
| 贴图 | **0 字节改动** |
