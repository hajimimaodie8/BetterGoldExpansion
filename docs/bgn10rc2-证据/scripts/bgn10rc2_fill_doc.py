# -*- coding: utf-8 -*-
"""回填 §21 的 5 个占位块（扰动矩阵 / 构建与七关卡 / A 级读数 / 共享文件与 run / 未验证项）。

每个占位都是**唯一**的 HTML 注释；替换后回读断言"其它内容一字未动"（用前后缀比对）。
"""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"
EV = REPO / "docs" / "bgn10rc2-证据"

PERTURB = """判据 = 真扰动必须让**本段**红且点名 tag、只改注释必须仍 0 条、每例**逐字节复原 + SHA256 自证**。
记录两列：`script_exit`（整脚本 exit，参考）+ `本段问题数`（判据）。6 用例 / 6 命中 / 复原 6/6。

| 用例 | 改什么 | script_exit | 本段问题数 | 命中的 tag | 复原 |
|---|---|---|---|---|---|
| `grid-swap` | 三叉戟 **第2行中列**「锭 → 棍」 | 1 | **3** | `bgn10rc2-cell` + `bgn10rc2-trident` | 逐字节 ✓ |
| `result-count` | 弓 产物数量 `1 → 2` | 1 | **1** | `bgn10rc2-result` | 逐字节 ✓ |
| `drop-fd-condition` | 抽掉乐事刀的 `neoforge:conditions` | 1 | **1** | `bgn10rc2-knife-cond` | 逐字节 ✓ |
| **`double-bottle`** | 配方层**第二格也塞一个玻璃瓶**（模拟双返） | 1 | **2** | `bgn10rc2-remainder-unique` | 逐字节 ✓ |
| **`comment-only`** | 只往 `RawSturdygoldRecipe` 加注释，注释里**逐字写出**被禁的三串（`Recipe.super.getRemainingItems` / `craftRemainder(Items.GLASS_BOTTLE)` / `getCraftingRemainingItem`） | **0** | **0** | —（仍绿） | 逐字节 ✓ |
| `mace-block-to-ingot` | 重锤的**混沌金块 → 混沌金锭** | 1 | **3** | `bgn10rc2-cell` + `bgn10rc2-mace-block` | 逐字节 ✓ |

> ⚠ `comment-only` 这一例就是"正向 needle 必须跑在**去注释源码**上"的证明：三串禁用词**全在注释里**，
> 若关卡读的是原始源码，那么"`Recipe.super` 0 处 / 互斥"这类断言会被注释直接喂饱（假绿）。
"""

GATES = """| 命令 / 脚本 | exit | 关键计数行 |
|---|---|---|
| `gradlew compileJava` | **0** | `BUILD SUCCESSFUL in 2s` |
| `gradlew build` | **0** | `BUILD SUCCESSFUL in 2s`；`build/libs/bettergold-1.6.0.jar` **1,602,019 B / 2791 条目**（= 上一轮 2787 + 本轮 4 条新配方） |
| `validate_metal_assets.py` | **0** | `[bg-assets-ok] 问题合计 0 条` |
| `validate_metal_data.py` | **0** | `[bgn10rc2-ok] …（本段判定 149 项）` + `[bgn10rg-ok] 混沌金 15 件…` + `[bg-data-ok] 问题合计 0 条` |
| `validate_trim_assets.py` | **0** | `[bgfinal3-ok] 问题 0 条 / 检查 76 项` |
| `validate_advancements.py` | **0** | `[bgach-ok] 成就 59 个 / criteria 142 条 / 语言键 118 条` |
| `check_jar_clean.py` | **0** | `[jar-clean-ok] 产物 jar 干净（条目 2791；*Probe* 0 / 'halt' 字节 0 / 'BG-PROBE' 0）` |
| `check_forced_chunks.py` | **0** | `[chunks-forced-ok] data.Forced 为空` |
| `validate_bg17_textures.py` | **0** | `[bg17tex-summary] checked=630 authorized=72 untouched=553 modelrefs=64 problems=0` |

原始输出：`docs/bgn10rc2-证据/10-七关卡.txt`（脚本 `scripts/bgn10rc2_gates.py`）。
"""

ALEVEL = """证据：`docs/bgn10rc2-证据/01-A级读数.txt`（`runServer` stdout 的 UTF-8 逐行摘录，45 行）、
`02-双返负向读数.txt`、探针源码留档 `脚本副本/BgN10rc2Probe.java.txt`。
**`SUMMARY pass=34 fail=0 forcedNow=0`**；世界 = `run/world`（`level-name=world`），
**没有打开作者的 `run/saves/新的世界`**（跑前/跑后 29 文件 / 18,862,026 B / 逐文件全等）。
**农夫乐事在 dev 里装着**（`ModList.get().isLoaded("farmersdelight") = true`，它由 `build.gradle` 的
`localRuntime` 常驻）⇒ 乐事刀那条**真合成过**，不是静态验证。

| 组 | 用例 | 读数 |
|---|---|---|
| ⓪ 机制（物品级 remainder） | `c2_oil_has_remainder` / `c2_oil_remainder_is_bottle` | `hasCraftingRemainingItem()=true`、`getCraftingRemainingItem()=minecraft:glass_bottle` |
| ⓪ 负向（别加到燃油上） | `c2_fuel_no_remainder` | `alchemic_fuel.hasCraftingRemainingItem()=false` |
| ① 弓 | `c2_bow_result` / `_consumed` / `_landed` | `1x bettergold:chaosgold_bow`；9 格逐格 −1 全对；落袋 1；摆位 `- 锭 线 / 锭 - 线 / - 锭 线` |
| ① 重锤 | `c2_mace_*` | `1x bettergold:chaosgold_mace`；逐格 −1；摆位 `- 块 - / - 微风棒 - / - - -` |
| ① 三叉戟 | `c2_trident_*` | `1x bettergold:chaosgold_trident`；逐格 −1；摆位 `锭 锭 锭 / - 锭 - / - 棍 -` |
| ① 乐事刀 | `c2_knife_*` | `1x bettergold:chaosgold_knife`；逐格 −1；摆位 `锭 - - / 棍 - -` |
| ② 双倍贵金原料 | `c2_doubled_echogold_result` / `_consumed` / `_landed` | 结果格 **`2x bettergold:raw_echogold`**；9 格逐格 −1；落袋 2 |
| ② 催化剂格 | `c2_doubled_echogold_bottle_total` / `_bottle_in_inventory` | **整张菜单 + 光标 + 背包合计玻璃瓶 = 1**；把瓶子真点进背包后背包里 = 1 |
| ★ **只返 1 个瓶**（负向） | 同一读数 + `02-双返负向读数.txt` | 干净构建 **1**；**故意注入"第二格也塞瓶"之后同一个读数变 2 ⇒ 4 条 FAIL**（`_bottle_total` 两条 + `_consumed` 两条，`pass=30 fail=4`）⇒ 这条断言**不是空转** |
| ③ 另一条吃高阶油的配方 | `c2_chaosalloy_ingot_result` / `_bottle_total` / `_bottle_in_inventory` | `1x bettergold:chaosalloy_ingot`；玻璃瓶合计 **1**；背包 **1** ⇒ **"扩"生效**（这条以前不返瓶） |
| ④ 炼金燃油那条 | `c2_base_fuel_echogold_result` / `_bottle_total` / `_bottle_in_inventory` | `1x bettergold:raw_echogold`（不是 2）；玻璃瓶合计 **1**；背包 **1** ⇒ **与扩之前一致**（1.5 起的既有行为，原样保留） |

> ⚠ 双返注入是怎么做的、怎么复原：`scripts/bgn10rc2_inject_double.py`（`probe/bgn10rc2/` 里留 `.orig`），
> 注入后 `sha 6A21F97C… → 32A9D785…`，跑完 `restore` 回 `6A21F97C…`（`byte-identical=True`）。
> 注入形态 = 配方层给**兑换物那格**也塞一个玻璃瓶 —— 真实世界里"双返"最可能长这样
> （单格语义下 `set()` 会覆盖，所以"同一格返 2 个"物理上写不出来；能写出来的双返一定是**两格各一个瓶**）。
"""

SHARED = """- **开工前的工作树**：HEAD `1d28341`、`git status --short` **空**（父代理已核）⇒ 本轮没有
  "别人的在制品"这一档；收工时 9 个 `M` + 4 个 `??` 配方 + 1 个 `??` 证据目录 + 1 个 `??` `probe/`，
  `git diff --stat` = **9 files changed, 776 insertions(+), 72 deletions(-)**（`data/bettergold/recipe/`
  下**只有 4 个 `??` 新文件**，既有配方 JSON 一个都没改 —— 这也是"混沌金锭上游未动"的一条侧证）。
- **`run\\` 独占**：开工查进程 = 只有 Gradle daemon（pid 12344，`GradleDaemon 8.8`），**没有**任何
  `runServer` / `runClient` 的 `java` ⇒ 独占成立。本轮 `runServer` 跑 **2** 次
  （① 干净构建；② 双返注入那次），**每次都确认进程退出后才起下一条**；`runClient` **没跑**（原因见 §21.10）。
- **`run/server.properties`**：服务器启动时自己重写（`A2229937…` → `20278CA0…`）⇒ 收尾用跑前
  `run/server.properties.bgn10rc2.bak` **字节复制**复原，回到 `A2229937BA8AB742…`（与跑前逐字节相同；
  两列 SHA 见 `06-跑测留档与复原.txt`）。
- **作者的存档** `run/saves/新的世界`：跑前/跑后 **29 文件 / 18,862,026 B / 逐文件（size+mtime）全等**
  ⇒ 一个字节没动。`run/world`（探针服端世界）63 → 63 文件（字节数 −1，属服务器正常存盘）。
- **探针**：`src` 内 `BgN10rc2` / `BGN10RC2` 命中 **0**、`halt(` 命中 **0**、`src/…/probe/` 目录已删；
  源码**删前已复制**到 `脚本副本/BgN10rc2Probe.java.txt`；开关文件 `run/bgn10rc2-probe.enabled` 已删；
  `halt(false)` **只调一次**；forceload **双向 0**（`forcedNow=0`，`check_forced_chunks` 也 0）。
- **未 commit、未 push**；**原始 zip 与归档素材本轮一个字节没碰**（本轮没有任何贴图/素材动作，
  `git status` 里 `textures/` 命中 **0**）。
"""

UNVERIFIED = """1. **手册页真渲染出来长什么样 —— 本轮没人眼看过**（没跑 `runClient`：本轮 A 级只需要
   服务端 + 真 `CraftingMenu`，而 `run\\` 是独占资源、且客户端要 `quickPlayPath` + `--quickPlaySingleplayer`
   两个都带才敢进世界）。替代证据：15 条 `recipeId` 与 Patchouli 走**同一个** `RecipeManager`
   （`PageDoubleRecipe#build` → `getRecipeManager().byKey(...)`），而这 15 条在本轮**真服务端**里
   被真 `CraftingMenu` 真合成过（其中 4 条就是本轮新补的）+ 关卡 `[bgn10rg-handbook]` 静态核对了
   15 页 / 15 条引用 / 每页 ≤2 / 无死链。
2. **JEI / 配方书里这 4 条新配方的显示**没有截图（A 级验的是服务端匹配 + 产出 + 消耗）。
3. **"没装农夫乐事"那一档没有实机跑**：dev 环境里 FD 由 `build.gradle` 的 `localRuntime` **常驻**
   ⇒ `isLoaded=true`（见 01 号证据第 5 行），乐事刀那条**在"装着"的环境里真合成过**；
   "没装 ⇒ 配方不产出"这一档只有**静态**证据（`neoforge:conditions` + `[bgn10rc2-knife-cond]` +
   与既有的 `smithing_*_knife.json` 同一种写法）。**这是本轮唯一一条"没在目标环境实测"的项**，如实记账。
4. **三叉戟是原创形状**：格数/位置已被关卡逐格钉住，但"它像不像三叉戟""作者认不认这个形状"
   需要作者一句话（**已同时写进手册正文与本节**）。
5. **混沌金锭上游（第三条）本轮未动 —— 自证**：
   - `git status` 里 `data/bettergold/recipe/` **只有** `chaosgold_{bow,mace,trident,knife}.json`
     四个 `??`；**没有任何** `chaosgold_ingot*` 的新文件，也没有任何既有配方被改（`M` 计数 0）；
   - `chaosgold_ingot_from_nugget.json` / `chaosgold_ingot_from_block.json` / `chaosgold_block_from_ingot.json`
     / `chaosgold_nugget_from_ingot.json` 四个文件**不在 `git status` 里** ⇒ 与 HEAD 逐字节一致；
   - 没有新增任何 loot table / 矿物 / 掉落 / 世界生成（`git status` 里 `loot_table/` / `worldgen/` 命中 0）；
   - 关卡 `[bgn10rg-gear-metal]` 仍然要求"每条配方至少一格混沌金材料"，**没有**任何断言把
     "锭怎么来"写死 ⇒ 下一轮作者给了上游口径就能直接加，不会与本轮冲突。
   ⇒ **按作者原话，此项"我再问一问"= 待定，本轮未改。**
"""

FILLS = [
    ("<!--PERTURB-TABLE-->", PERTURB),
    ("<!--GATES-TABLE-->", GATES),
    ("<!--ALEVEL-TABLE-->", ALEVEL),
    ("<!--SHARED-TEXT-->", SHARED),
    ("<!--UNVERIFIED-TEXT-->", UNVERIFIED),
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def main() -> None:
    raw = DOC.read_bytes()
    old = raw.decode("utf-8")
    text = old
    for key, body in FILLS:
        assert text.count(key) == 1, "占位不唯一：%s（%d 次）" % (key, text.count(key))
        text = text.replace(key, body)
    DOC.write_bytes(text.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    assert "<!--" not in back.split("## 21. ")[1], "还有没回填的占位"
    print("filled: %d -> %d bytes; sha %s -> %s"
          % (len(raw), len(back.encode("utf-8")), sha(raw)[:16], sha(back.encode("utf-8"))[:16]))


if __name__ == "__main__":
    main()
