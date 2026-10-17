# -*- coding: utf-8 -*-
"""为归档目录补一份 README（新文件，不影响归档副本的既有内容）。"""
import sys, os
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
D = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")

TXT = """# 1.7 贴图更新包 —— 归档与认亲（只读副本）

> 来源：`E:\\mc\\mc资料\\1.7的贴图更新包.zip`（46,334 B / 72 个 PNG 条目，作者 2026-10-17 提供）
> **硬红线**：原始 zip **绝不修改 / 重打包 / 改名 / 移动**；本目录是**只读解压出来的归档副本**，
> **只增不改**（本目录里已有的副本文件不许改动；新增文件可以）。

## 目录内容

| 路径 | 内容 |
|---|---|
| `*.png`（72 个数字名） | 原样副本，**文件名与 zip 内条目名一字不差**（时间戳毫秒，如 `1792201245321.png`） |
| `素材清单.tsv` | 逐张 `file / bytes / width / height / mode / sha256` |
| `认亲表.tsv` | 机读版认亲结果（目标路径 / 类 / 族 / 判定 / MAE / 2nd / ratio / 原版 MAE / alpha 是否一致） |
| `认亲表.md` | 人读版认亲表，**每张一行**（142 行，按 9 类分节） |
| `_识别证据/` | 9 张 `diff_<类>.png`（OLD / NEW / DIFF 三联拼图）、各类 MAE 矩阵、`扰动矩阵.txt`、`六校验器.txt`、`A级读数.txt`、`替换记录/` |
| `_脚本/` | `01`…`21` 全部 `.py`，一律 `py -3` 可复算 |
| `README.md` | 本文件 |

## 认亲结论（摘要）

**9 类 × 8 族 = 72 张，全部判为「确定」**（0 疑似 / 0 认不出）：

| 类 | 目标 | 张数 |
|---|---|---|
| 灯笼 · 方块放置样式 | `block/<族>_lantern.png`（16×48） | 8 |
| 盔甲穿戴层 · 靴子区 | `models/armor/<族>_layer_1.png`（64×32） | 8 |
| 斧 / 锹 / 刀 · 物品图标 | `item/<族>_axe|_shovel|_knife.png`（16×16） | 24 |
| 链 · 方块样式 | `block/<族>_chain.png`（16×16） | 8 |
| 链 · 物品图标样式 | `item/<族>_chain.png`（16×16） | 8 |
| 栏杆 | `block/<族>_bars.png`（16×16） | 8 |
| 护腿 · 物品图标样式 | `item/<族>_leggings.png`（16×16） | 8 |

族 = 8 个贵金族：`flamegold / sturdygold / thornsgold / echogold / indigoseagold / voodoogold / thundergold / illusiongold`。

**判定方法**：同尺寸前提下算逐像素 RGBA 平均绝对误差 MAE；类内用 `scipy.optimize.linear_sum_assignment`
做全局一对一指派；三条硬校验（MAE ≤ 2、第二名差距 ≥ 1.5 倍、alpha 掩码与不透明像素数逐字节相同）。

**证据强度**：真配 MAE **0.10–1.88**，同尺寸次优目标 **1.3–14.1**（`ratio` 1.8×–75.5×）；
对原版 jar 的最小 MAE 是 **3.99–45.1**；**9 个类里的族顺序完全一致**。

详见 `认亲表.md`；落档与验证记录见 `docs/1.7-贴图更新包翻新.md`。
"""


def main():
    p = os.path.join(D, "README.md")
    if os.path.exists(p):
        print("[readme] already exists, skip (archive is append-only for copies)")
        return
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(TXT)
    print("[readme] wrote %s (%d B)" % (p, os.path.getsize(p)))


if __name__ == "__main__":
    main()
