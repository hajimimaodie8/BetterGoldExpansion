# -*- coding: utf-8 -*-
"""修正 §21.9 里"收工态 git status"那句（本轮先误删过仓库跟踪的 pyc，已复原）。

旧句（原文照抄）：`收工时 9 个 M + 4 个 ?? 配方 + 1 个 ?? 证据目录 + 1 个 ?? probe/`
新句：加入 pyc 事故的如实记账 + 正确的计数（M 9 + ?? 5 = 14 行）。
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

OLD = """- **开工前的工作树**：HEAD `1d28341`、`git status --short` **空**（父代理已核）⇒ 本轮没有
  "别人的在制品"这一档；收工时 9 个 `M` + 4 个 `??` 配方 + 1 个 `??` 证据目录 + 1 个 `??` `probe/`，
  `git diff --stat` = **9 files changed, 776 insertions(+), 72 deletions(-)**（`data/bettergold/recipe/`
  下**只有 4 个 `??` 新文件**，既有配方 JSON 一个都没改 —— 这也是"混沌金锭上游未动"的一条侧证）。"""

NEW = """- **开工前的工作树**：HEAD `1d28341`、`git status --short` **空**（父代理已核）⇒ 本轮没有
  "别人的在制品"这一档；收工时 **9 个 `M` + 5 个 `??`（4 条新配方 + 1 个证据目录）= 14 行**，
  `git diff --stat` = **9 files changed, 776 insertions(+) / 72 deletions(-)**（`data/bettergold/recipe/`
  下**只有 4 个 `??` 新文件**，既有配方 JSON 一个都没改 —— 这也是"混沌金锭上游未动"的一条侧证）。
  ⚠ **一次自查抓到并已复原的事故（如实记账）**：清 `__pycache__` 时我**整个目录删**，其中
  `tools/asset-generator/__pycache__/metal_forms.cpython-314.pyc` 是**仓库跟踪的文件**
  （`git ls-files` 确认）⇒ `git status` 出现一条 `D`。立刻 `git checkout --` 把它**按原字节复原**，
  现在 `git status` 里**没有**这条 `D`；收尾脚本已改成"只删本轮生成的未跟踪 pyc"。
  （教训与 `AGENTS 红线 5` 同源：**删除前先确认目标是不是别人的/被跟踪的**。）"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def main() -> None:
    raw = DOC.read_bytes()
    old = raw.decode("utf-8")
    assert old.count(OLD) == 1, "锚点不唯一（%d）" % old.count(OLD)
    text = old.replace(OLD, NEW, 1)
    DOC.write_bytes(text.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    assert back.startswith(old[: old.index(OLD)]) and NEW in back
    print("patched: %d -> %d bytes, sha %s -> %s"
          % (len(raw), len(back.encode("utf-8")), sha(raw)[:16], sha(back.encode("utf-8"))[:16]))


if __name__ == "__main__":
    main()
