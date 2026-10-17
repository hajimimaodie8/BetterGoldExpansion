# -*- coding: utf-8 -*-
"""跨项目经验回流（bg-n10d）：只**追加**，不删任何行。

四个分册 + 附录 D 一行。每处都先读原文件字节、追加后回读校验
（旧内容必须是新内容的**前缀**，即"删除 0 行"）。
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXP = r"E:\mc\mcmod\mod_experience"
EX = os.path.join(EXP, "ex")


def append(path, text):
    old = open(path, "rb").read()
    if text.encode("utf-8") in old:
        print("SKIP（已经追加过）:", os.path.basename(path))
        return
    new = old.rstrip(b"\n") + b"\n" + text.encode("utf-8")
    open(path, "wb").write(new)
    chk = open(path, "rb").read()
    assert chk.startswith(old.rstrip(b"\n")), "旧内容不是前缀 —— 有删除！"
    print("OK %-24s %d -> %d bytes（旧内容全在，删除 0 行）"
          % (os.path.basename(path), len(old), len(chk)))


EX02 = """

### 2.10 追加（2026-10-18 · bettergold `bg-n10d` #13）：**同名数据包标签是「合并」，写 `replace: true` 会静默清空原版条目**

| 现象 | 根因 | 规则（可执行的动作） | 依据 |
|---|---|---|---|
| 给自家物品补原版标签（例：把自家种子加进 `#minecraft:chicken_food`）时，若写成 `{"replace": true, "values": ["my:seed"]}` ⇒ **鸡不再吃小麦种子、鹦鹉不再吃西瓜种子**；游戏**不报错、日志一行 Warning 都没有**，只是原版行为集体消失 | 同名标签文件在多个数据包之间是**合并**语义，只有 `replace: true` 才会先 `list.clear()`：`TagLoader#load` 里 `if (tagfile.replace()) { list.clear(); }`（1.21.1）⇒ 高层包的 `replace:true` 把下层（原版）的条目**整份丢掉** | ① 往原版标签里加条目，一律 `"replace": false`（或干脆省略，默认就是 false）；② 关卡把这条钉成断言（`replace is not True`），并把「原版那几条必须都还在」写成**正向**断言；③ A 级必须**打印运行期成员列表**（`BuiltInRegistries.ITEM.getOrCreateTag(key)`），而不是只验 `stack.is(tag)` —— 后者在我们写 `replace:true` 时**依然为 true**（只是原版条目没了），完全抓不到 | 【读源码】`net/minecraft/tags/TagLoader.java:54-56`（1.21.1 sources jar）；【实测】bettergold `bg-n10d`：4 张标签的成员与「原版 N 条全在 + 我们 1 条」逐条对齐（`docs/bgn10d-证据/01-A级读数.txt`） |

> ⚠ 同族的第二个坑：**`stack.is(tag) == true` 不等于「这个标签只多了我们这一条」** ——
> 它只回答"我在不在里面"。要判"有没有顺手把原版冲掉 / 有没有混进别的物品"，必须读**成员集合**。
"""

EX03 = """

### 3.29 「照原版标签补条目」的三个判据坑：**成员总数会被别的模组打脸**、**"只改注释仍绿"不能用注释掉真实代码来证**、**验图集可以停在标题界面**（2026-10-18 bettergold `bg-n10d`，裁定 #12/#13）

| # | 现象 | 根因 | 规则（可执行的动作） | 依据 |
|---|---|---|---|---|
| ① | 探针断言「标签成员数 == 原版 6 + 我们 1 = 7」，A 级 **3 条 FAIL**（实测 10/10/2/10） | dev 环境常驻的**农夫乐事**也往 `chicken_food` / `parrot_food` / `villager_plantable_seeds` 里加了种子（`cabbage_seeds` / `rice` / `tomato_seeds` / `onion`）⇒ 写死总数会在**任何装了同类模组的环境**里假红；反过来若写成"成员数 == 我们自己那一条"就会假绿 | 标签类断言写**下界 + 结构**，不写总数：`原版那 N 条必须都在` + `我们的条目必须在` + `members.size() >= N + 1`；并把"**别的模组加的**条目录成读数"（`filter(!minecraft: && !本模组:)` 后打进日志）。这样别家加东西是信息、不是红 | 【实测】bettergold `bg-n10d` 服务端探针第一版 20 PASS / **3 FAIL**，第二版 23 PASS / 0 FAIL（`docs/bgn10d-证据/01-A级读数.txt`） |
| ② | 想证"正向 needle 跑在**去注释**源码上、注释里的字样不会让它假绿"，最直接的做法是**把真实注册行注释掉** | 那样源码**编译不过**；而当时同一工作树里**另一个会话正在构建** ⇒ 为了自证而制造别人的编译错误是不可接受的（多会话并发下的硬约束） | 把**关卡里那一个去注释函数原样抽出来**（正则截取 `def _strip_java_comments(...)` 到下一个锚点 → `exec` 到空命名空间 → 直接调），用它分别跑「真实文件」（针在）与「只写在 `//`、`/* */` 里的合成串」（针不在）⇒ 证明的是**同一份实现**，零副作用；"只改注释仍绿"的端到端对照另跑一条（真往源码插一行注释，两关卡必须仍 exit 0） | 【实测】bettergold `docs/bgn10d-证据/11-扰动矩阵.txt` 用例 ⑤a/⑤b |
| ③ | 想验"某个图集里这张图解析出来对不对"，直觉是"得进世界 + 打开界面看"（于是要建世界 / quickPlay，风险全上来） | 图集在**资源重载**阶段就缝合完了，与"有没有进世界"无关；标题界面就已经可以读 | 图集类验证一律**停在标题界面**（`ClientTickEvent.Post` 等 ~120 tick 后读，读完 `Runtime.halt(0)`）⇒ **不建世界、不碰存档**。判据至少三件：`SpriteContents#name()` == 期望 id（排除 missing sprite）、`width/height`、以及 **`getOriginalImage()` 的像素哈希** —— 只查名字只能排除"missing"，证明不了"图集里拿到的是**这一版**像素" | 【实测】bettergold `bg-n10d` 客户端探针 7 PASS / 0 FAIL（`docs/bgn10d-证据/02-客户端读数.txt`：name=`bettergold:tremble`、18×18、像素 RGBA-SHA256 与新 png 逐字节相符、`run/saves` mtime 跑前跑后不变） |
"""

EX06 = """

#### 10.11 规则 12（2026-10-18 · bettergold `bg-n10d` #12）：**状态效果图标走「独立的 `mob_effects` 图集」，18×18，文件名 stem 必须等于注册 id**

| 问题 | 结论 | 依据 |
|---|---|---|
| 状态效果（`textures/mob_effect/<id>.png`）走哪个图集？ | **独立的 `mob_effects` 图集**（既不是 `gui` 图集，也不是逐张直读）：`MobEffectTextureManager extends TextureAtlasHolder`，构造里写死 `textures/atlas/mob_effects.png` + 图集名 `mob_effects` | 【读源码】`net/minecraft/client/resources/MobEffectTextureManager.java:16`（1.21.1 sources） |
| 图集里有哪些贴图？sprite 叫什么？ | 由原版数据包 `assets/minecraft/atlases/mob_effects.json` 决定：`{"sources":[{"type":"directory","source":"mob_effect","prefix":""}]}` ⇒ `textures/mob_effect/` 下**每一个** png 都进图集，sprite 名 = `<命名空间>:<文件名>`；查表用 `MobEffectTextureManager#get(Holder<MobEffect>)`（拿注册 id 查）⇒ **文件名的 stem 必须与注册 id 完全一致**，改名 = 静默变 missing 图 | 【读源码】原版 jar `assets/minecraft/atlases/mob_effects.json` + `MobEffectTextureManager#get` |
| 尺寸？ | 引擎不按尺寸校验（图集按任意尺寸缝合），但**原版 39 张 `textures/mob_effect/*.png` 全部 18×18**（其中 8 张 8 位 RGBA），GUI 的图标方框也是 18×18 ⇒ **按原版 18×18**；替换时"新旧同尺寸"也要作为一条硬校验（18 vs 16 这类差异必须先报告再换） | 【实测】遍历原版 jar 的 39 个条目读 IHDR；【实测】本仓 10 张效果贴图全是 18×18 / 8 位 / RGBA |
| 怎么验"图集里真的拿到这一版像素"？ | 标题界面即可（图集在资源重载时定稿）：`Minecraft#getMobEffectTextures()` → `get(holder)` → `contents()` 的 `name()` / `width()` / `height()`，再加 **`getOriginalImage().getPixelRGBA(x,y)` 拼成行优先 RGBA 字节算 SHA-256**，与 PNG 侧 `PIL.convert("RGBA").tobytes()` 的哈希比对（本例 `6ae90277…`）。★ `SpriteContents#getFrameCount()` 是 private，帧数要么从 `toString()` 取、要么按"有没有 `.mcmeta`"判断 | 【实测】bettergold `bg-n10d`（7 PASS / 0 FAIL，`docs/bgn10d-证据/02-客户端读数.txt`） |

> 推论：换状态效果图标**不需要**动任何 JSON / 模型 / 语言键 —— 只换 png 一个文件；
> 但**关卡要两条**：新 SHA 锚点 + **反回退**（不许等于旧 SHA），否则"换回去"没人发现。
"""

EX08 = """

#### §9.10 追加（2026-10-18 · `bg-n10d` 侧的两条补充）

| # | 现象 | 根因 | 口径 | 依据 |
|---|---|---|---|---|
| ④ | 我要 `gradlew build`，编译却失败在**别人刚写的探针类**上（它用了 `MinecraftServer#storageSource`，1.21.1 里是 `protected`） | 共享工作树里 `compileJava` 是**全量**的：任何一方的在制品语法/可见性错误都会挡住另一方 | **绝不修别人的文件**（哪怕一行就能修好）：把编译错误原文（文件:行 + 报错）报给能指挥它的那一方，等它自己修。⚠ 也**不许**"只 javac 我自己的类"来凑 B 级证据 —— 那不是构建证据。判"对方是否在跑"的最便宜三读数：`Get-Process java`、`run/logs/latest.log` 的 mtime、`build/classes` 的 mtime | 【实测】本轮 `compileJava` 第一次 `BUILD FAILED`（错误在 `probe/BgN10rgClientProbe.java:108`），对方修好后同一命令 `BUILD SUCCESSFUL` |
| ⑤ | 往**共享的校验器/`AGENTS.md`** 里追加自己那一段，怎么保证不把对方同时在写的段落覆盖掉 | 追加型编辑没有版本控制语义（对方可能整文件重写） | ① 改前**重读**（记录文件 SHA + 对方前缀的 `grep -c` 计数）；② 插入点优先选**文件末尾**（离对方的段落最远）；③ 唯一锚点；④ 改后**立刻复核**：对方前缀计数不变 + 自己那段的结论行出现在最终的关卡输出里；⑤ 若对方后来又改了同一文件，**在收尾时再跑一次关卡**，确认自己那段仍然在（本轮实测：插入前后 `grep -c bgn10rg` 都是 82） | 【实测】bettergold `bg-n10d`：`validate_metal_data.py` 插入后 `bgn10rg` 计数不变；最终七关卡 `validate_metal_data` exit 0 且 `bgn10d` 段结论行在 |
"""

APPENDIX_D = """

| 2026-10-18 | bettergold | **`bg-n10d`：作者对「还缺什么」5 条裁定落地（#4/#5/#14 只核实不改 · #12 替换 `tremble.png`（第六次贴图授权）· #13 加 4 条原版种子标签）** | **指针**：① **状态效果图标走独立 `mob_effects` 图集**（`MobEffectTextureManager.java:16` + `atlases/mob_effects.json` = `directory: mob_effect`）+ sprite 名 = `<ns>:<文件名>` ⇒ **stem 必须等于注册 id** + 原版 39 张全 **18×18** + 「验到像素」的做法 → `ex\\06` **§10.11 规则 12**；② **同名数据包标签是合并、`replace:true` 会静默清空原版条目**（`TagLoader.java:54-56`），且 `stack.is(tag)` 抓不到 ⇒ `ex\\02` **§2.10**；③ **标签成员数写死会被别的模组打脸**（农夫乐事也加种子）、**"只改注释仍绿"不能靠注释掉真实代码来证**（会把别人的构建弄崩）、**验图集停在标题界面就够且必须比像素哈希** → `ex\\03` **§3.29**；④ 多会话并发：**别人的在制品编译不过时绝不修**、共享文件"改前重读 + 末尾插入 + 改后复核对方前缀计数" → `ex\\08` **§9.10 追加 ④⑤** | **未写**（只对本项目成立）：崩乱合金盔甲耐久 头 1924 / 胸 2368 / 腿 2220 / 靴 2035 的复算表（`Type.getDurability(37)` = 407/592/555/481 ⇒ 1924 = 4×靴基数、2035 = 5×头基数，"疑似写反"算术成立但**作者裁定不动**）、三叉戟投掷 9..13 按字面、"疑似笔误"标注保留、金火把花两个 loot_table 与原版逐字段同形 —— 全在 `docs\\1.7-裁定落实-4-5-12-13-14.md`；证据在 `docs\\bgn10d-证据\\`（21 份：对比图/ASCII、替换记录、A 级读数、七关卡、扰动矩阵、脚本副本）。**删除 0 行**（本文附录 D 与四个分册都是**追加**；`AGENTS.md` 第 6 条是追加第六次授权） |
"""


def main():
    append(os.path.join(EX, "02-静默失效.md"), EX02)
    append(os.path.join(EX, "03-验证与证据.md"), EX03)
    append(os.path.join(EX, "06-贴图模型素材.md"), EX06)
    append(os.path.join(EX, "08-流程与协作.md"), EX08)
    append(os.path.join(EXP, "mcmod_experience.md"), APPENDIX_D)
    return 0


if __name__ == "__main__":
    sys.exit(main())
