# -*- coding: utf-8 -*-
"""bg18b · 往 `docs/1.7-混沌金与崩乱合金-需求立档.md` **追加** §31.12–§31.17，
并在 §31.9 / §31.11 的旧结论上就地标注「已由本轮补做」（原文一个字都不删）。

纪律：
  * 只追加 / 只插入，`git diff --numstat` 的删除行必须是 0（本脚本自己断言锚点出现次数）；
  * UTF-8 无 BOM、LF。
"""
import hashlib
import os
import sys

DOC = os.path.join("docs", "1.7-混沌金与崩乱合金-需求立档.md")


def main():
    raw = open(DOC, "rb").read()
    before_lines = len(raw.splitlines())
    before_sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")

    # ---------- ① 旧结论就地标注（只插入，不删） ----------
    a1 = "### 31.9 P5 · 贴图（**未开始，一个字节没动**）\n"
    note1 = (
        "\n> **✅ 2026-10-25 `bg18b` 已补做**：P5 = 10 张（第七次授权，白名单 73 → **83**），"
        "见 §31.13；原始 zip 仍在跑前/跑后各核一次 SHA256（`f593d52d…`，一个字节没动）。\n"
        "> 下面这段是**上一轮的原文留档**（未删）。\n"
    )
    assert text.count(a1) == 1, "anchor 31.9 not unique"
    text = text.replace(a1, a1 + note1, 1)

    a2 = "### 31.11 人眼 / 未验证（诚实清单）\n"
    note2 = (
        "\n> **✅ 2026-10-25 `bg18b` 已补跑 A 级**（`runServer` 42 PASS / 0 FAIL；"
        "`runClient` 15 PASS / 0 FAIL），读数见 §31.12；下面第 1 条是**上一轮的原文留档**（未删）。\n"
    )
    assert text.count(a2) == 1, "anchor 31.11 not unique"
    text = text.replace(a2, a2 + note2, 1)

    # ---------- ② 追加新节 ----------
    appendix = """
---

### 31.12 A 级（`bg18b`，2026-10-25）：六项读数

> **环境**
> * 服务端：`gradlew.bat runServer`（专用服务端、`--nogui`）+ 本轮**自建** ASCII 探针世界
>   `run/bg18probe`（`server.properties` 的 `level-name` 临时改，收尾**逐字节复原**回
>   `A2229937…`；世界与 `_nether/_the_end` 收尾删除）。
> * 客户端：`gradlew.bat runClient` + `--quickPlayPath logs/quickplay/bg18qb.json`
>   `--quickPlaySingleplayer bg18cprobe`（世界 = 上面那个探针世界的副本）。
>   quickplay 日志原文：`[{"type":"singleplayer","id":"bg18cprobe","name":"bg18probe",…}]`
>   ⇒ **进的就是本轮自己的探针世界**。
> * 红线：**从未打开**作者的 `run/saves/新的世界`（跑前/跑后 29 文件 / 18,883,729 B / 逐文件
>   SHA256 全等）；**没有 UI 自动化建世界**；`build.gradle` 临时加参数后**逐字节复原**
>   （SHA256 回到 `2AAC7860…`）；`clientRunProgramArgs.txt` **全程没碰**。
> * 证据：`docs\\bg18-证据\\08-服务端探针原文.txt` / `10-客户端探针原文.txt` /
>   `09-客户端世界\\`（世界清单、作者存档跑前/跑后快照）/ `12-探针源码副本\\`。
>   ⚠ 探针用 `System.out` 打中文时被控制台按 GBK 写出 ⇒ 中文详情不可逆乱码；
>   **ASCII 段（id / 数字 / PASS/FAIL / 物品 id）完整可信**。

| # | 项 | 读数（原文摘录） | 判定 |
|---|---|---|---|
| 1 | 手册客户端**真加载** | `entries=27 pages=233 categories=5`；`errored=false` | **PASS** |
| 1a | 新章节 4 页页型 | `pages=4 types=[patchouli:text, patchouli:crafting, patchouli:text, patchouli:crafting]`；`page1.text=true page3.text=true`；`recipe1=bettergold:raw_sturdygold_doubled recipe2=bettergold:raw_sturdygold_chaosgold` | **PASS** |
| 1b | ★ P2-a 同屏（打印下标） | `smelting_index=2 crafting_index=3 spread=1/1`；`types=patchouli:smelting/patchouli:crafting`（一屏 = 下标 `2k/2k+1`） | **PASS** |
| 1c | ★ P2-b 该页正文 | 8/8 键都在加载后的内容树里；崩乱合金那页 `rendered=…50%…`、**不含** `Format error`、**不含** `%%`；8 条逐条「无 `Format error` + 含单个 `%` + 存储侧裸 `%` = 0」 | **PASS** |
| 2 | `I18n` 实测 | `Component.translatable(<8 键>).getString()`：`ok=8/8 bad=[]`，每条**不抛异常**且结果含 `%` | **PASS** |
| 3 | `RecipeManager` + 真合成 | 金钱贝两条 `catalyst=minecraft:gold_ingot` / `bettergold:golden_eggplant`、`variant=0/1`、序列化器不同；各真合成 1（`result=1x bettergold:golden_cowrie`，模具耐久 +1、兑换物消耗、落袋 1）。8 条九宫格各真合成 1：`result=2x bettergold:raw_<族>`（**count 2 记账**）、9 格逐格消耗、催化剂格返还 `glass_bottle`、落袋 2 | **PASS** |
| 4 | 音咆正负对照 | 施加者 `caster 20.0 -> 20.0`；同一 3×3×3 内 `victim 20.0 -> 19.0`、`bystander 20.0 -> 19.0`（`entities_in_3x3x3=3`）。反向对照（**不**记施加者）`caster 20.0 -> 17.0` ⇒ 排除逻辑真的在起作用 | **PASS** |

* 服务端探针 **`SUMMARY pass=42 fail=0 forcedNow=0`**；客户端探针 **`SUMMARY pass=15 fail=0 ticks=60`**；
  世界名闸门 `readout levelName=bg18probe worldTick=2` + `CHECK probe_world_guard PASS`。
* "真"在哪：`CraftingMenu` 用**真** `ContainerLevelAccess.create(level,pos)`，`slotsChanged` 走
  `CraftingMenu#slotChangedCraftingGrid` → 真 `RecipeManager#getRecipeFor` → 真 `assemble`；
  两次 `menu.clicked(…, PICKUP)` 是玩家那条路径，消耗由 `ResultSlot#onTake` 逐格 −1。
* 音咆那条走**真实体 tick**（`MobEffectInstance` + 真 `ServerPlayer` 进实体管理器 + forceload
  区块 + 45 tick），不是直接调 `echoRoarTick`。

**⚠ 本轮踩到的两个探针坑（已写进脚本注释）**
1. `tick` 从 `arm` 起算时，世界加载完早已 > 2 ⇒ 「第 2 tick 断言世界名」整段被跳过、一条都不打。
   改成 **`worldTick`**（只在 `mc.level != null` 之后自增）才是"进世界第 2 tick"。
2. `addFreshEntity` 的**同一 tick 内** `getEntitiesOfClass` 恒 0（实体管理器在 tick 末才并入索引）
   ⇒ 当场判「实体可见」是假阴性；要等到下一个 tick 结束后再判（本轮 `entities=3` 即读数）。

### 31.13 P5 · 贴图（第七次授权）：认亲表 + 替换 + 白名单 73 → 83

> **来源**：`E:\\mc\\mc资料\\1.7的贴图更新包第二关.zip`（9,202 B / 10 条目；
> SHA256 `f593d52dbce6d0322555a6ff4212f5db45a7a4a34c46d4332a19e1dd2ccb3172`）。
> **只读**：跑前/跑后各核一次 SHA256 ⇒ **原始 zip 一个字节没动**；归档解压到
> `docs\\1.7贴图更新包第二关-素材清单\\`（10 张原名 + `素材清单.tsv`，只增不改）。
>
> **认亲方法（可复算）**：同尺寸候选 + 逐像素 RGBA 平均绝对误差 `MAE = mean(|A-B|)`（含 alpha）；
> 三条硬校验：`alpha 掩码逐字节相同`、`不透明像素数相同`、`MAE <= 2.0`（本轮实际 0.005–1.98），
> 外加「类内次优/最优」比值（1.5×–888×）。脚本 `probe\\bg18b\\match_textures.py` / `match_detail.py`；
> 对照图（源 + 前 3 名候选，10× 放大）在 `docs\\bg18-证据\\05-P5-认亲\\`。

**认亲表（10/10 确定，0 疑似；1:1 字节复制）**

| # | zip 文件名（数字为原名） | 目标（`textures/` 下） | 改前 SHA256 | 改后 SHA256 | MAE / 改动像素 |
|---|---|---|---|---|---|
| 1 | `1792547527281.png` | `gui/container/sturdygold_anvil.png` | `24a277b99da860b9c012a1a68d3994648fca5466407be4eb61e70e6ba0e5625c` | `debe8cfc08707bb71d534dbd11876f83c2b5fdd1bf7009626d08f1812ad454b2` | 0.6466 / 688（alpha 掩码不变） |
| 2 | `1792547604001.png` | `gui/sprites/container/sturdygold_anvil/error.png` | `dcbac5908d8fec564db718860a3b39623e7ffebea6f19c2fb705ac0bcad1a989` | `b0c8aa737917bc39058a5b402b92bca294e90586b0e663be5daa05a7d14c21c3` | 22.02 / 217；**507 像素 = 新 256×256 的 (99,45)-(126,65)** + 81 红叉 |
| 3 | `1792829920491.png` | `block/flamegold_bricks.png` | `c590410b4c4193257decea647177e9247ebc421b7571175a047656a3ecaba510` | `07fc4dd08e8a915e9b72bc03c38659a53d294f2a8219daae4a8bad12269081f3` | 0.0557 / 24（次优差 **133×**） |
| 4 | `1792829936399.png` | `block/flamegold_pillar.png` | `3140f403f8fe39cee3ed83b26006518a44b75fdf020721fdd963fa304bea50ab` | `cce4d39ab696300be4f2ce86f8c00ec06ef5658f07da6326f09878fc19c9ce37` | 0.0967 / 36（**76×**） |
| 5 | `1792829981886.png` | `block/flamegold_block.png` | `5b808d633bb85fa71afac79b6f985d8b881cb82837e80f48a8362ff6f11a6506` | `69c3932960c92db156c548e5df601833e90b2797d442de58586de23c75b8d12f` | 0.0195 / 10（**334×**） |
| 6 | `1792829997817.png` | `item/flamegold_ingot.png` | `2db942543746951a6840c19dceba408bcf441cd66c0885fc066ab5c2b32978d3` | `616c80b5118025433768c3c24ecc90b80d876bfb0c4147d7db23b55902a932de` | 0.0049 / 4（**888×**） |
| 7 | `1792830024159.png` | `item/flamegold_upgrade_template.png` | `505964c6a7f304c2bf3ec3c2c81e92246e377d65b211fc747d7f3f8f89799621` | `5e7c5d1ed9704bc06fd01e15ad8094fa39959dcee10876a80ca3ffad74d3cf36` | 0.0166 / 6（**215×**） |
| 8 | `万坚金巧克力曲奇.png` | `item/sturdygold_chocolate_cookie.png` | `d74e24d31fa93d0196063ee8de53863fc012bb2014154bc287e367bbbdf73819` | `fe1814285bb8859526859c9851a5fbd7a0bc55d2203d8ac9a7764c3571a58973` | 1.9844 / 25（**5.1×**） |
| 9 | `新的混沌金纹饰色卡.png` | `trims/color_palettes/chaosgold.png` | `75587687ca69f5f24b2c0a09824950788c36a5acacc93804372ef2cceabf5416` | `25e9d4b7ff72814e970ddeca4601e2adfb0ab17b4fb249e838e9c9e13671b8e4` | 8×1 / 7 个像素；旧 `[255,253,224][253,245,95][250,214,74]…` → 新 `[255,253,224][242,208,139][229,163,54]…[52,2,43]` |
| 10 | `金巧克力曲奇.png` | `item/golden_chocolate_cookie.png` | `5c1ac52bc09e54c30aa36e8581da081fd553bc952ab927dad55e06f6c5ffb333` | `ec099054be279213e289378d4aa25c9b2927ed252b13a404bbe726f9ff4fbbd3` | 0.6865 / 14（**15.75×**） |

**尺寸/UV 核对（作者点名第 1 类）**：`SturdygoldAnvilScreen` 的常量是
`TEXTURE = bettergold:textures/gui/container/sturdygold_anvil.png`（`blit(…, 176, 166)` 从 256×256 取）、
`ERROR_SPRITE = bettergold:container/sturdygold_anvil/error`（`blitSprite(…, 28, 21)`）。
新图 **256×256 / 28×21，与旧图同尺寸** ⇒ **不需要改任何源码常量**（宽度/高度/UV 一字未动）。

**⚠ 与作者点名分类的字面偏差（不猜、不硬塞，按像素事实落）**
* 作者第 2 类写「部分烈燃金**物品** ⇒ `item/flamegold_*`」，但 5 张里只有 2 张是物品
  （锭 / 升级模板），另外 **3 张的像素事实是方块**（`block/flamegold_bricks|pillar|block`：
  MAE 0.020–0.097、类内次优差 76–335 倍，而它们与 `item/` 下任何一张的 MAE 都 ≥ 27）。
  ⇒ 按像素落方块；**这一条需要作者一句话确认**（若他要的是"把这三张也画到物品上"，那是另一件事）。
* 第 2 张（28×21 错误图标）在 `gui/sprites/…` 下，作者原话只写到目录 `sturdygold_anvil/*`，**完全吻合**。
* **认不准清单：空（10/10 确定）**。

**白名单**：73 张（72 + tremble）→ **83 张**（+10）。逐张列名见上表；
关卡锚点写进 `tools\\asset-generator\\validate_bg17_textures.py` 的 `AUTH7`（10 条，新 SHA + **反回退"不许等于旧 SHA"**）
与 `tools\\asset-generator\\bg18tex_auth.tsv`（认亲表机读版，10 行）；反空转 = `AUTH7` 条数必须 = 10、
认亲表必须 10 行、`checked >= 626`。

**顺带修的两处「旧期望」**（`validate_metal_data.py`，原文留档未删）：
万坚金砧 GUI 原先钉在**作者第一版原件**（`新约10\\万坚金砧 gui.png`）与旧精灵 SHA/414 B 上；
作者这次换了这两张 ⇒ 改成按**第二关**归档件比对（`[bgn10r8-assets]`），`[bgn10err-*]` 的三个常量
（GUI SHA / 精灵 SHA / 636 B）更新，**像素规则（507 + 81 / 红叉掩码 / 无灰）一字未改且实测仍成立**。

### 31.14 构建 + 八关卡（判据 = `exit` + 关键计数两列；`docs\\bg18-证据\\13-八关卡-最终.txt`）

| 步骤 | exit | 关键计数行 |
|---|---|---|
| `gradlew build` | **0** | `BUILD SUCCESSFUL`（4 tasks） |
| `validate_metal_assets.py` | **0** | `实际检查了 712 项`；`问题合计 0 条` |
| `validate_metal_data.py` | **0** | `[bg18-summary] 检查 104 项，问题 0 条`；`[bg-data-ok] 问题合计 0 条`；反空转 `310 键 + 1942 JSON` |
| `validate_advancements.py` | **0** | `成就 63 个 / criteria 146 条 / 语言键 126 条` |
| `validate_trim_assets.py` | **0** | `实际检查了 76 项`，问题 0 |
| `validate_bg17_textures.py` | **0** | `checked=643 authorized=72 untouched=544 modelrefs=64 auth7=10 problems=0` |
| `validate_golden_prison.py` | **0** | `problems=0 checked=16635 templates=26` |
| `check_jar_clean.py` | **0** | jar 条目 **2891**；`*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0` |
| `check_forced_chunks.py` | **0** | `data.Forced = []` |

### 31.15 扰动矩阵（`probe\\bg18b\\perturb_textures.py`；`docs\\bg18-证据\\14-P5-扰动.txt`）

| 用例 | want_exit | got_exit | 命中 |
|---|---|---|---|
| P0 基线 | 0 | 0 | PASS |
| P1 授权贴图被覆盖成别的字节 | 1 | 1 | `[bg18tex-auth-fail]` PASS |
| P2 未授权贴图动 1 个字节（`block/sturdygold_bricks.png`） | 1 | 1 | `[bg17tex-untouched-fail]` PASS |
| P3 **删认亲表一行**（`bg18tex_auth.tsv`） | 1 | 1 | `[bg18tex-manifest-fail]` PASS |
| P4 授权贴图回退成改前字节 | 1 | 1 | `[bg18tex-revert]` PASS |
| P5 **只改注释** | 0 | 0 | 绿 PASS |
| P6 GUI needle **只留在注释里**（代码里换掉） | 1 | 1 | `[bg18tex-needle-gui-fail]` PASS（证明 needle 跑在**去注释源码**上） |
| P7 复原后基线 | 0 | 0 | PASS |

每例都**逐字节复原并复核 SHA256**（6 个被扰动文件 `same`：`SturdygoldAnvilScreen.java`
`ffc19716…`、`flamegold_bricks.png` `07fc4dd0…`、`sturdygold_bricks.png` `846bf1cb…`、
`flamegold_ingot.png` `616c80b5…`、`bg18tex_auth.tsv` `bebd5af8…`、
`validate_bg17_textures.py` `4294edb1…`）。

### 31.16 收尾 / 逐字节复原 / 未验证（诚实清单）

* **`run\\` 独占**：开工前查过进程（只有 Gradle daemon）；`runServer` 1 次、`runClient` **2 次**
  （第一次世界名闸门因 `tick` 起算点被跳过 ⇒ 修好后复跑），每次都**确认退出**再起下一条。
* **`server.properties`**：跑前 `.bak` 字节复制 → 临时 `level-name=bg18probe` → 收尾 `.bak` 复制回，
  SHA256 回到 `A2229937…`（`11-收尾-客户端.txt`）。
* **`build.gradle`**：临时加 `--quickPlayPath/--quickPlaySingleplayer` → 逐字节复原，
  SHA256 回到 `2AAC7860…`。
* **`run/saves`**：跑后只剩作者的 `新的世界`（29 文件 / 18,883,729 B / SHA256 全等）；
  探针世界 `bg18probe`（27 文件）与客户端副本 `bg18cprobe`（36 文件）**先留清单再删**
  （`09-客户端世界\\删除的-*.txt`）。
* **forceload 双向归零**：运行期 `forcedNow=0`（探针内断言 PASS）+ 存盘侧
  `check_forced_chunks.py` 的 `data.Forced = []`。
* **探针**：`src\\…\\probe\\bg18b\\` 两个类**整块删除**（删前源码副本 → `12-探针源码副本\\`，
  `Bg18bProbe.java` 20,933 B / `Bg18bClientProbe.java` 13,691 B）；`src` 里 `Probe|halt(` 命中 **0**；
  删后重跑 `build` + 八关卡。
* **未 commit、未 push**；原始 zip / 归档 / 作者存档 / 贴图（除本次授权的 10 张）**0 字节改动**；
  `git status` 的 `M` = 22 个（其中**贴图 10 张**、代码/数据/语言/生成器/校验器 11 个 + 本立档）。

**未验证 / 人眼项**
1. 贴图**好不好看**只有作者能判；本轮只保证「换进去的就是他给的那张字节」。
2. 万坚金砧 GUI 的**实际打开效果**（新 GUI 的 `+`/`→` 变深红）没有截图；A 级只做到
   「字节换对 + 源码仍按 256×256/176×166 与 28×21 取图」。
3. P2-a 的"同屏"由**下标 (2,3)** 证明（Patchouli 一屏 = `2k/2k+1`），**没有截图**。
4. JEI 里两条金钱贝配方是否真的画成「金锭 / 金钱茄」没有截图；A 级证的是
   「加载后的配方实例 `catalyst` 正确 + 真合成产物正确 + `getIngredients()` 跟着 catalyst」。
5. 控制台把探针的中文详情按 GBK 写出 ⇒ 证据文件里的中文是乱码；
   **ASCII 段与数字完整**，本节的读数只引用 ASCII 段。

### 31.17 行数

本节是**追加**（§31.1–§31.11 原文一字未删，只在 §31.9 / §31.11 标题下**插入**两行「已补做」标注）；
`docs\\1.7-…md` 4812 → **见收尾核对**（`git diff --numstat` 删除行 = **0**）。
"""

    text = text.rstrip("\n") + "\n" + appendix
    out = text.encode("utf-8")
    open(DOC, "wb").write(out)
    after_lines = len(out.splitlines())
    print("doc before=%d lines sha=%s" % (before_lines, before_sha))
    print("doc after =%d lines sha=%s (+%d lines)" % (
        after_lines, hashlib.sha256(out).hexdigest(), after_lines - before_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
