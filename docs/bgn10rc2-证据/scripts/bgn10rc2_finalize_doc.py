# -*- coding: utf-8 -*-
"""§21 收尾两处：① 修正 `[bgn10rc2-*]` 段的行号引用；② 追加 §21.11 经验回流（行数变化）。"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

OLD = "**8939-9286（新增 `[bgn10rc2-*]` 段 ≈ 350 行）**"
NEW = "**8928-9290（新增 `[bgn10rc2-*]` 段 ≈ 363 行 / 本段判定 149 项）**"

TAIL = r"""

### 21.11 经验回流（跨项目层）与行数变化

回流按 `mod_experience\mcmod_experience.md` 页首第 ② 条的**强制**要求做，**只追加、删除 0 行**。
自证方式：追加脚本 `bgn10rc2_exp_return.py` 写完回读，断言 **原文件字节是新文件的前缀**
（`new.startswith(old)`）—— 前缀成立即等价于"旧内容一行未动、只在尾部追加"。

| 分册 | 追加位置 | 字节变化 | 一句话 |
|---|---|---|---|
| `mod_experience\ex\03-验证与证据.md` | **§3.30（新增）** | 153,557 → 155,629（**+2,072**） | 「只返 1 个」类断言必须按**全量合计恰好 N**（菜单+光标+背包）判，而不是"那一格有没有"；负向要**真注入一次双返**证明断言不是空转 |
| `mod_experience\ex\04-数值与API.md` | **新增块（2026-10-18）** | 123,230 → 125,224（**+1,994**） | 1.21.1 的"合成返瓶"仍是 `Item.Properties#craftRemainder`（**不是**数据组件）；全版本只有 **5 个读取点**；「物品级 + 配方层」的互斥证明法 |
| `mod_experience\ex\05-工具链与环境.md` | **第5 追加（2026-10-18）** | 46,617 → 47,918（**+1,301**） | PowerShell `1>` 把 `gradlew` 输出写成 **UTF-16LE** ⇒ 读日志先嗅探编码（本轮真翻车：第一遍读成"探针没跑"） |
| `mod_experience\mcmod_experience.md` | **附录 D +1 行** | 65,590 → 66,578（**+988**，其中 1 行是回流行） | 指针式：三条规律各自指向上面那一节 |

> `probe\bgn10rc2\` 与 `run\bgn10rc2-probe.enabled` 已删；`src` 内 `BgN10rc2` / `BGN10RC2` / `halt(`
> 命中 **0**；证据目录 = `docs\bgn10rc2-证据\`（清单见 `清单.txt`，收尾核对见 `09-收尾核对.txt`）。
"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def main() -> None:
    raw = DOC.read_bytes()
    old = raw.decode("utf-8")
    assert old.count(OLD) == 1, "行号引用锚点不唯一（%d）" % old.count(OLD)
    assert "### 21.11 " not in old, "§21.11 已追加过"
    text = old.replace(OLD, NEW, 1) + TAIL
    DOC.write_bytes(text.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    assert back.startswith(old.replace(OLD, NEW, 1)), "旧内容不是前缀"
    print("patched+appended: %d -> %d bytes, sha %s -> %s"
          % (len(raw), len(back.encode("utf-8")), sha(raw)[:16], sha(back.encode("utf-8"))[:16]))


if __name__ == "__main__":
    main()
