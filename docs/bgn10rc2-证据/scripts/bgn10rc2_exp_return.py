# -*- coding: utf-8 -*-
"""经验回流（跨项目层）：3 个分册各追加一节 + 主文档附录 D 追加一行。

纪律：**只追加、删除 0 行**。自证 = 写完回读，断言 `new.startswith(old)`（旧内容是新文件的前缀）。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

EXP = Path(r"E:\mc\mcmod\mod_experience")
MAIN = EXP / "mcmod_experience.md"

EX03 = r"""

### 3.30 「只返 1 个」类断言的验收口径：**全量合计恰好 N**，不是"那一格有没有"

**现象**：1.21.1 里"合成后返还瓶子"可以同时有两条路径 —— **配方层**（配方类覆盖 `getRemainingItems`）
与**物品级**（`Item.Properties#craftRemainder`）。验收若只写"催化剂那一格点击后是不是玻璃瓶"，
**双返时那张断言照样是绿的**：两条路径的瓶子落在**不同的格**，被盯的那一格永远只有 1。
本轮的真实读数：故意注入双返后，`_bottle_total`（整张菜单 + 光标 + 背包合计）= **2**，
而"催化剂格 = 1x glass_bottle"仍然 PASS ⇒ **盯单格 = 假绿**。

**根因**：`ResultSlot#onTake`（1.21.1 `ResultSlot.java:85-106`）对每格 `removeItem(i,1)` 之后
`setItem(i, remainder)` —— **一格只放得下一份剩余物**，所以"同一格返 2 个"在代码里**写不出来**；
能真发生的双返**必然是"两格各一个瓶"**（或背包里多出一份）。
⇒ 判据必须是**跨容器全量合计**，而不是单格存在性。

**规则**：
1. 计数口径 = **容器菜单所有槽 + 光标栈 + 玩家背包**，断言 `== 期望值`（**不是 `>=`**）；
2. 负向不能只靠读代码：**真注入一次双返**（给第二格也塞一个瓶），跑一遍确认断言**变红**，
   再逐字节复原 + SHA256 自证 —— 否则你无法区分"断言是绿的"与"断言是空转的"；
3. 静态侧配一条互斥断言（两文件里 `GLASS_BOTTLE` 合计**恰好 2 处** + 配方层里**不许**出现
   `Recipe.super` / `getCraftingRemainingItem`），**动静两条都要有**：静态管"写法没退化成双路径"，
   动态管"实际只给了一份"。

**依据等级**：`【实测】`bettergold `bg-n10rc2`（干净构建 `SUMMARY pass=34 fail=0`；
双返注入 `pass=30 fail=4`，见 `docs/bgn10rc2-证据/01-A级读数.txt` / `02-双返负向读数.txt`）；
`【读源码】` `ResultSlot.java:85-106`、`RecipeManager.java:122-134`（每张配方只取一次剩余物列表）。
"""

EX04 = r"""

### 数值 / API 备案：2026-10-18 bettergold `bg-n10rc2` —— **1.21.1 的"合成返瓶"仍是物品属性，不是数据组件；它的全部读取点只有 5 处**

- **事实**（`【读源码】` 1.21.1 sources jar）：`Item.Properties#craftRemainder(Item)` 在 `Item.java:436`，
  值存进 `Item.java:70` 的 `craftingRemainingItem` 字段；`net/minecraft/core/component/DataComponents.java`
  全文 grep `CRAFTING|REMAINDER` = **0 命中** ⇒ "1.21 已迁到 `CRAFTING_REMAINDER` 数据组件"这个说法
  **在本版本不成立**。要给"当原料会返瓶"的物品补行为，写的仍是 `.craftRemainder(...)`。
- **原版先例**：蜂蜜瓶 `Items.java:1935-1936` `.craftRemainder(GLASS_BOTTLE)`；龙息 `Items.java:1770`；
  水/岩浆/奶桶 `Items.java:1215-1222`。⚠ **药水三件套没有 remainder**（`Items.java:1368` / `1772` / `1779`）——
  药水的瓶子由**酿造台**返还，不是合成返还 ⇒ **别把"药水不返瓶"当成反例**去否定物品级写法。
- **影响面（给物品挂 remainder 会动到谁，全版本仅 5 个读取点）**：
  ① `Recipe#getRemainingItems` 默认实现（`Recipe.java:30-41`，**合成**）；
  ② `AbstractFurnaceBlockEntity:303-310`（**燃料格**）；
  ③ `BrewingStandBlockEntity:179`（**酿造原料格**）；
  ④ `BannerDuplicateRecipe:82`；⑤ `BookCloningRecipe:86`（旗帜 / 成书，与普通物品无关）。
  ⇒ "某个配方还返不返瓶"最终取决于**那张配方有没有覆盖** `getRemainingItems`。
- **「物品级 + 配方层并存」的互斥证明法**：配方类只要**覆盖**了 `getRemainingItems`、且**不调**
  `Recipe.super.getRemainingItems`、**不读** `getCraftingRemainingItem`，物品级 remainder 就**不参与**
  那条配方 ⇒ 两条路径**按配方类型互斥**，一次合成只可能有一处给出剩余物。
  这套三条可以直接写成静态断言（本轮 `[bgn10rc2-remainder-exclusive]` / `-unique`）。
"""

EX05 = r"""

## 第5 追加（2026-10-18 `bg-n10rc2`）：PowerShell 的 `1>` 把 `gradlew` 输出写成 **UTF-16LE** ⇒ 读日志前必须先嗅探编码

- **现象**：`.\gradlew.bat runServer 1>build\x.log` 之后用 Python 以 UTF-8 读那个文件，整篇带 `\x00`，
  `if 'PROBE' in line` **一条都匹配不到** ⇒ 我先得出了"第二次 runServer 里探针根本没跑"这个**错误结论**
  （其实它跑了，而且全绿/全红的行都在）。同一份文件用 `Select-String` 能读到，是因为它自己嗅探 BOM。
- **规则**：
  1. 读任何 native/`gradlew` 的重定向产物前，先判 `raw[:2] == BOM_UTF16_LE` 或 `raw[1:2] == b"\x00"`，
     再选 `utf-16-le`；
  2. 提取脚本要**先把"识别到的编码 + 行数"打出来**（本轮 `utf-16-le 624`）——
     把"我读到了什么"变成一条读数，而不是一个假设；
  3. Python 往 GBK 控制台打中文会 `UnicodeEncodeError`（`⇒` 这类符号直接炸）⇒
     `$env:PYTHONIOENCODING="utf-8"` + `[Console]::OutputEncoding=[Text.Encoding]::UTF8`，
     或者干脆**把结果写文件再用读文件工具看**。
- **依据等级**：`【实测】`本轮 `build/bgn10rc2-runserver-2-double.log`（第一遍误读成"无输出"，
  嗅探后读出 `SUMMARY pass=30 fail=4`）。
"""

ROW = ("| 2026-10-18 | bettergold | **`bg-n10rc2` 执行轮：4 件混沌金装备补工作台配方 + 返瓶扩到物品级** | "
       "**指针**：① 1.21.1「合成返瓶」= `Item.Properties#craftRemainder`（**不是**数据组件）+ 全部 5 个读取点"
       " + 「物品级 vs 配方层」的互斥证明法 → `ex\\04` **新增块（2026-10-18）**；"
       "② 「只返 1 个」类断言要按**全量合计恰好 N** 判、并**注入一次双返**证明断言非空转 → `ex\\03` **§3.30**（新增）；"
       "③ PowerShell `1>` 把 native 输出写成 UTF-16LE ⇒ 读日志先嗅探编码（本轮真翻车）→ "
       "`ex\\05` **第5 追加（2026-10-18）** | "
       "**未写**（只对本项目成立）：4 件的逐格形状与来源逐字、三叉戟「原创形状、待作者确认」的口径、"
       "手册 13→15 页与语言文件 SHA 第九次换锚点、A 级 34/0 与双返负向 30/4 的逐条读数 —— 全在 "
       "`docs\\1.7-混沌金与崩乱合金-需求立档.md` **§21** 与 `docs\\bgn10rc2-证据\\` |\n")


def append(path: Path, block: str, label: str) -> None:
    old = path.read_bytes()
    new = old + block.encode("utf-8")
    path.write_bytes(new)
    back = path.read_bytes()
    assert back.startswith(old), "%s: 旧内容不是前缀（有行被改动）" % label
    print("%-22s %7d -> %7d bytes (+%d)  sha %s -> %s  prefix_ok=True"
          % (label, len(old), len(back), len(back) - len(old),
             hashlib.sha256(old).hexdigest()[:12].upper(),
             hashlib.sha256(back).hexdigest()[:12].upper()))


def main() -> None:
    append(EXP / "ex" / "03-验证与证据.md", EX03, "ex/03 §3.30")
    append(EXP / "ex" / "04-数值与API.md", EX04, "ex/04 新增块")
    append(EXP / "ex" / "05-工具链与环境.md", EX05, "ex/05 第5 追加")
    old = MAIN.read_bytes()
    text = old.decode("utf-8")
    assert ROW not in text, "回流行已经追加过了"
    assert text.endswith("\n"), "主文档末尾不是换行（不敢直接追加）"
    append(MAIN, ROW, "附录 D +1 行")


if __name__ == "__main__":
    main()
