# -*- coding: utf-8 -*-
"""bg18b · 跨项目经验回流：只在三个文件**末尾追加**（删除 0 行）。"""
import hashlib
import os
import sys

EXP = r"E:\mc\mcmod\mod_experience"
EX03 = os.path.join(EXP, "ex", "03-验证与证据.md")
EX06 = os.path.join(EXP, "ex", "06-贴图模型素材.md")
MAIN = os.path.join(EXP, "mcmod_experience.md")

SEC_03 = """
### §3.42 客户端探针的两条「时间轴」+ 一条输出通道（`bg18b` 轮，2026-10-25，bettergold）

| 现象（本轮实测） | 根因 | 规则 |
|---|---|---|
| 写「进世界第 2 tick 断言世界名」，结果**一条都没打**，探针却照常跑完 | 探针在 `ClientTickEvent` 一开始就武装、`tick` 从**标题界面**起算；世界加载完时 `tick` 早已 > 2 ⇒ `if (tick == 2)` 永远不成立 | 世界内的「第 N tick」必须用**只在 `mc.level != null` 之后自增的独立计数器**（本轮 `worldTick`）；`tick==2` 只在"进世界那一刻恰好是第 2 个 tick"时成立 |
| `addFreshEntity` 后**同一个 tick** 里 `getEntitiesOfClass(...).size()` 恒 **0**（看起来像"实体没加进去"） | 实体管理器把新实体并入索引是在 **tick 末** | 「实体可见」只能**跨 tick** 判（下一个 tick 的 `ServerTickEvent.Post` 里读）；同 tick 读到 0 是**假阴性**，不要据此改生产代码 |
| 客户端探针的 `System.out.println` 不在 `run/logs/latest.log` 里；重定向文件里的中文不可逆乱码 | 客户端 stdout 走控制台代码页（GBK）；log4j 才写 UTF-8 | 探针的**详情文本用 ASCII**（id / 数字 / PASS/FAIL），中文只写 docs；要中文取证就写进 `run/logs`（log4j） |

`【实测】` bettergold `bg18b`：第一次跑 `SUMMARY pass=15 fail=0` 但**世界名闸门 0 条输出**（`tick` 已 >2）；
改成 `worldTick` 后 `readout levelName=bg18probe worldTick=2` + `probe_world_guard PASS`。
"""

SEC_06 = """
### 规则 16（2026-10-25 · bettergold `bg18b`）：作者**第二批**贴图包会取代「作者原件」这个锚点 —— 更新锚点，别让旧断言拦住新授权

| 现象 | 根因 | 规则 |
|---|---|---|
| 换完新包，`validate_metal_data.py` 突然 **exit 1**：报「贴图不是作者原件的字节原样（GUI）」「新精灵字节数不是 414」 | 关卡把「GUI = 作者**第一版**原件」写成了契约（拿 `docs/新约10/万坚金砧 gui.png` 比 SHA、精灵 414 B） | 作者再交一版**同一张**的原件时事实变了：把**比对源**改成新包归档件、SHA/字节数改成新值；**旧值以注释原文留档**（"旧口径原文留档（未删）"），并确认**像素规则本身是否仍成立** —— 本例「507 作者像素 + 81 红叉」在新 GUI 上仍成立，所以规则一字未改 |
| 新包条目有 8 个数字名 + 2 个中文名 | 作者混用了两种命名 | 数字名仍按**同尺寸 + 逐像素 MAE** 认；**中文名是语义标签、不是判据** —— 必须让像素证据与名字**互相印证**（本轮两曲奇 + 色卡的 MAE 与名字一致） |
| 28×21 的 GUI 精灵"看起来像重新画的" | 它其实是**合成图**：作者 GUI 的 `(99,45)-(126,65)` 28×21 区域 + 原版 81 个红叉像素 | 认亲时把它**同时**和「GUI 同坐标区域」与「旧精灵」比；本轮 **507 像素逐像素等于新 GUI 区域** ⇒ 判定确定，不是新美术 |

`【像素实测】` bettergold `bg18b`：10/10 确定（MAE 0.0049–1.98、alpha 掩码不变、类内次优差 1.5–888×）；
认亲表 `docs/bg18-证据/06-P5-替换/认亲表.tsv`、对照图（源 + 前 3 名候选 10×）`docs/bg18-证据/05-P5-认亲/`。
"""

ROW = ("| 2026-10-25 | bettergold | **`bg18b`：A 级六项（手册真加载 / I18n / 真合成 / 音咆对照）"
       "+ P5 第七次贴图授权（10 张，白名单 73 → 83）** | **指针**：① 客户端探针的两条时间轴"
       "（世界内第 N tick 用 `worldTick`；`addFreshEntity` 同 tick 查询恒 0）→ `ex\\03` **§3.42**（新增）；"
       "② 作者**第二批**贴图包会取代「作者原件」锚点（改比对源 + 旧值留档 + 确认像素规则是否仍成立）"
       "→ `ex\\06` **规则 16**（新增）；③ 项目侧 `docs\\1.7-…md` §31.12–§31.17 | **未写**："
       "`I18n.java` 零参 `String.format` 已在 `bg18` 那行记过；音咆/九宫格细节只对本项目成立 |\n")


def append(path, text):
    raw = open(path, "rb").read()
    before = hashlib.sha256(raw).hexdigest()
    if not raw.endswith(b"\n"):
        raw += b"\n"
    out = raw + text.encode("utf-8")
    open(path, "wb").write(out)
    print("%s: %d -> %d lines, sha %s -> %s" % (
        os.path.basename(path), len(raw.splitlines()), len(out.splitlines()),
        before[:16], hashlib.sha256(out).hexdigest()[:16]))


def main():
    append(EX03, SEC_03)
    append(EX06, SEC_06)
    append(MAIN, ROW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
