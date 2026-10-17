# -*- coding: utf-8 -*-
"""bg-n10up 经验回流（跨项目层）：三个分册各追加一块 + 附录 D 一行。

只用**追加**（改前字节必须是改后字节的前缀），并把每个文件的字节/行数变化打出来。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXP = Path(r"E:\mc\mcmod\mod_experience")

EX03 = r"""
### 3.32 测「经验球 / 实体」的 A 级探针：先 forceload + 等到真 tick；经验读数用增量（2026-10-18 bettergold `bg-n10up`）

| # | 现象 | 根因 | 规则（可执行的动作） | 依据 |
|---|---|---|---|---|
| ① | 在 `ServerStartedEvent` 里跑探针：熔炉**真烧出了物品**，但 `orbValue()=0`、玩家 `totalExperience=0` | `ExperienceOrb.award` → `ServerLevel.addFreshEntity` 只往 **ticking chunk** 的实体段里加；`ServerStartedEvent` 阶段服务器还没 tick，区块不是 ticking ⇒ 实体加不进去、**不抛异常**（静默） | 要测"掉经验 / 掉实体"：**先 `level.setChunkForced(cx, cz, true)`，把探针挂到 `ServerTickEvent.Post`、等 `server.getTickCount() >= 40` 再跑**；收尾 `setChunkForced(false)` 并断言 `getForcedChunks()` 为空（**双向 0**） | 【实测】前两轮 `up_coin_one_xp_orbs=0`/`FAIL`，改完 `=1`（`docs/bgn10up-证据/01-A级读数.txt`） |
| ② | 循环 `orb.playerTouch(player)` 吃 21 个球，玩家 `totalExperience` 只 **+1** | `ExperienceOrb#playerTouch` 每次只 `take(orb, 1)`，并把 `player.takeXpDelay` 设成 **2 tick** ⇒ 同一 tick 里后续调用全被挡 | 经验**发放量**用增量判：`award` 前后各算一次 `orbValue()`（`getValue()` 求和）取差；"玩家真的拿到"只断言 `> 0`，别指望同 tick 全吃进去 | 【读源码】`ExperienceOrb#playerTouch`；【实测】 |
| ③ | 第二个用例的"燃料消耗 = 1"红了（实际 0） | 复用**同一个热炉**：上一把还剩 `litTime = 15800`，第二把不会再吃燃料 —— 不是 bug | 每个用例**重建冷炉**（`setBlock(AIR)` → `setBlock(FURNACE)` → 重取方块实体 + 重建菜单）再断言燃料 == 1；否则这条断言测的是"炉子热不热" | 【实测】`e2e_smelt_9_fuel_consumed` |
| ④ | "与既有同档一致"的取值，关卡若写成"期望值 == 1.0"就是**拿期望表自比** | 期望值是人眼从仓库里抄来的数字 | "同档"要**扫仓库里同档的全部 N 条**，要求 `(category, experience, cookingtime)` **逐条相同**，并断言 N 恰为 8（反空转）；新值是常量、由关卡与那 N 条对齐（扰动改一格立刻红） | 【实测】`[bgn10up-smelt]` |

> ⚠ 同类陷阱的另一面（`bg-n10hv` §3.31 ③）：这一步的"读不到"和"对象不对"要分开 ——
> 实体读不到先怀疑**区块没 tick**，不要先怀疑"熔炉没发经验"。
"""

EX04 = r"""
### 追加块（2026-10-18，bettergold `bg-n10up`）：熔炉经验的**唯一管道**与 `xp < 1` 的坑

- **管道（全链路读源码）**：`AbstractFurnaceBlockEntity#serverTick` 在 `burn(...)` 成功时
  `setRecipeUsed(recipeholder)` 把 `recipesUsed[<recipeId>] += 1` ⇒ 玩家取走产品时
  `FurnaceResultSlot#checkTakeAchievements`（**唯一**发经验的地方，由 `slot.onTake` 触发，**不看**
  `removeCount`）调 `awardUsedRecipesAndPopExperience(ServerPlayer)` ⇒
  `getRecipesToAwardAndPopExperience` 对每个条目
  `createExperience(level, player.position(), count, recipe.experience)` ⇒
  `i = floor(count × experience)`，再把**小数部分**当概率 +1，最后 `ExperienceOrb.award(level, pos, i)`。
- **推论（选 xp 时必看）**：**`experience < 1` 时，单个产物可能一个经验球都不掉**
  （0.1 × 1 = 0.1 ⇒ `floor = 0`，只有 10% 概率 +1）⇒ 如果需求里有"经验累积 > 0"这种**要稳定读到**的
  判据，xp 要么 ≥ 1.0，要么让 count 累计（批量烧）后再读。`【读源码】`
- **同档取值的做法**：别抄数字，去**数仓库**（本仓 15 条 `*_smelting.json` 的实际分布：8 条 `1.0/200/misc`
  = 「原料 → 锭」、4 条 `0.1/0.4` = 金类小件、2 条 `0.2/0.3` = 种子→金粒、1 条 `0.35/food`），
  按**输入在链条里的角色**选档，再让关卡把"同档的那 N 条"逐条对齐。
- **注意 `playerTouch` 的 `takeXpDelay = 2`**：同一 tick 里连着吃多个球只会进一个（见 `ex\03` §3.32 ②）。
"""

EX05 = r"""
### 第6 追加（2026-10-18，bettergold `bg-n10up`）：批量跑校验器时，**子进程 stdout 的编码不统一**

- **现象**：用 Python `subprocess.run(..., text=True, encoding="utf-8")` 汇总七个校验器的输出，
  其中三个脚本的中文变成一片 `U+FFFD`（写成证据文件后就是"锟斤拷"），而**所有脚本仍然 exit 0**
  ⇒ 证据文件坏了、判据却全绿（第三种假绿：**收集端坏了**，不是关卡坏了）。
- **根因**：`tools/asset-generator/` 下各脚本对 stdout 的处理不统一 —— 有的自己
  `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`（输出 UTF-8），有的没有、跟随 locale
  （本机 = **GBK cp936**）；`PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1` 在部分脚本里也不生效
  （它们在启动后又 `reconfigure(errors=...)`）。同一个循环里混着两种编码。
- **规则**：
  1. 收集端**不要** `text=True`；`capture_output=True` 拿 **bytes**；
  2. 解码**先严格按 UTF-8**，`UnicodeDecodeError` 再回退 `gbk`（**两种都试过**才落盘）；
  3. 落盘后自检：读回证据文件断言 `U+FFFD == 0`（本例第一次写出来就是 248 个）；
  4. 顺带记住：PowerShell 的 `>` 仍是 **UTF-16LE + BOM**（与 §5 第 5 追加同一条纪律），
     要中文取证就**只用 Python 写文件**、不要经过 PS 重定向。
- **依据等级**：`【实测】`本轮 `docs/bgn10up-证据/07-七关卡.txt`（第一版 248 个 U+FFFD → 改成 bytes+回退后 0 个）。
"""

APPENDIX_D = (
    "| 2026-10-18 | bettergold | **`bg-n10up` 执行轮：混沌金锭**上游**三条（币串→3 币 / 币→（只 smelting）→粒 / 9 粒→1 锭既有）+ 手册 16→18 页** | "
    "**指针**：① 测经验球/实体的 A 级探针必须**先 forceload + 等真 tick**（`ExperienceOrb.award` 在非 ticking 区块里**静默不生效**）、"
    "`playerTouch` 的 `takeXpDelay=2` 使「同 tick 吃多个球」只进一个、**热炉不重复吃燃料**（断言前重建冷炉）、"
    "\"同档取值\"要扫仓库同档 N 条逐条对齐 ⇒ `ex\\03` **§3.32**（新增 4 条）；"
    "② 熔炉经验的唯一管道 = `recipesUsed → onTake → floor(count×xp)` ⇒ **xp<1 时单个产物可能一个球都不掉**，"
    "\"经验>0\"要稳定读到就得 xp≥1 ⇒ `ex\\04` 追加块；"
    "③ 批量跑校验器时子进程 stdout 编码不统一（自 reconfigure=UTF-8 / 跟随 locale=GBK）⇒ 一律拿 bytes、"
    "UTF-8 失败回退 GBK，否则证据文件全是 U+FFFD 而关卡仍 exit 0 ⇒ `ex\\05` **第6 追加** | "
    "**未写**（只对本项目成立）：三条的正/反向判据、smelting 同档依据（8 条 `raw_*_smelting` 全 `1.0/200/misc`）、"
    "成本 **3 个币串 = 1 个锭**、手册 18 页与旧句留档、`[bgn10up-*]` 115 项 + 7 例扰动（含\"只改注释仍绿\"）、"
    "A 级 85 PASS/0 FAIL + 客户端启动探针 12/0、七关卡 exit 0 —— 全在 `docs\\1.7-混沌金与崩乱合金-需求立档.md` **§23** 与 "
    "`docs\\bgn10up-证据\\`（11 份）。**删除 0 行** |\n"
)


def append(path: Path, block: str) -> str:
    old = path.read_bytes()
    text = old.decode("utf-8")
    marker = block.strip().splitlines()[0].strip()
    if marker and marker in text:
        return "%s: 已经追加过（含 %s），跳过" % (path.name, marker[:40])
    if not text.endswith("\n"):
        block = "\n" + block
    new = text + block
    path.write_bytes(new.encode("utf-8"))
    back = path.read_bytes()
    assert back.startswith(old), "%s: 不是纯追加" % path.name
    return ("%s: %d -> %d 行（%+d）/ %d -> %d 字节（%+d）/ SHA256 %s -> %s"
            % (path.name, text.count("\n"), new.count("\n"),
               new.count("\n") - text.count("\n"),
               len(old), len(back), len(back) - len(old),
               hashlib.sha256(old).hexdigest().upper()[:16],
               hashlib.sha256(back).hexdigest().upper()[:16]))


def main() -> None:
    out = []
    out.append(append(EXP / "ex" / "03-验证与证据.md", EX03))
    out.append(append(EXP / "ex" / "04-数值与API.md", EX04))
    out.append(append(EXP / "ex" / "05-工具链与环境.md", EX05))
    out.append(append(EXP / "mcmod_experience.md", APPENDIX_D))
    print("\n".join(out))


if __name__ == "__main__":
    main()
