#!/usr/bin/env python3
"""Fill the bg21 doc section with the real perturbation / gate readings (insertion-only vs HEAD)."""
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

OLD88 = """### 34.8 扰动（2 红 + 1 绿，逐字节复原 + SHA256）

见 §34.9 的构建后收尾轮读数（`probe/bg21/perturb.py`）：把某条紧邻关系改回 ⇒ 红（静态 `[bg21-creative-pins]` +
`[bg21-creative-order]` 同时命中）；只改注释 ⇒ 绿。每个用例收尾都逐字节复原并核对 SHA256。
"""

NEW88 = """### 34.8 扰动（`probe/bg21/perturb.py`：2 红 + 1 绿，逐字节复原 + SHA256）

基线：`CreativeTabSections.java` SHA256 `331DA7664D8E9771E23C20C7B281E36BD29CB3A5D430460DADC4FCA10852C69C`、
改后快照 SHA256 `715608EBC6953DACD18CE28BF28CA1C2086C3632A6D217E06FC383D6C5083F90`、关卡 exit=0（`[bg21-summary] 检查 63 项，问题 0 条`）。

| 用例 | 改什么 | 期望 | 实测 |
|---|---|---|---|
| A `pin_reverted` | 把④的 `golden_bone_meal ... true` 改成 `false`（= 把这条顺序改回） | 红 | **exit=1**；`[bg21-creative-pins]` 命中（问题 1 条，打印实际/期望两张表） |
| B `snapshot_reordered` | 把改后快照里 `refined_alchemic_oil` 与 `golden_shield_blank` 两行对调 | 红 | **exit=1**；`[bg21-creative-order]` 命中 4 条（指纹不符 + 两条不紧邻 + **408 件相对顺序变了**） |
| C `comment_only` | 只在 `CreativeTabSections.java` 里加一行注释 | 绿 | **exit=0**、问题 0 条、文件 SHA256 复原后逐字节相同 |

每个用例收尾都：逐字节复原 → SHA256 == 基线 ✓ → 重跑关卡回到 exit=0（`SUMMARY cases=3 all_ok=True`）。
"""

OLD89 = """* `.\\gradlew.bat build` = **BUILD SUCCESSFUL**；
* 八关卡 `exit` 全 0（关键计数见本轮汇报表；`validate_metal_data.py` 多出 `[bg21-summary]` 一行）；
* 本轮**只改 1 个生产 Java 文件**（`CreativeTabSections.java`，+4286 B）+ 关卡（`validate_metal_data.py`）+ 两份冻结快照 + 本档；
  **不 commit、不 push**。
"""

NEW89 = """`.\\gradlew.bat build` = **BUILD SUCCESSFUL**（探针删除后重跑；jar 条目 **2897**、`*Probe*` **0**、`halt` **0**）。

| 关卡 | exit | 关键计数行 |
|---|---|---|
| `validate_metal_assets.py` | 0 | `[bg-assets-ok]` 问题合计 0 条 |
| `validate_metal_data.py` | 0 | `[bg21-summary]` 检查 63 项 / 问题 0 条；`[bg-data-ok]` 问题合计 0 条 |
| `validate_advancements.py` | 0 | 成就 63 个 / criteria 157 条 / 语言键 126 条；问题 0 条 |
| `validate_trim_assets.py` | 0 | 检查 76 项 / 问题 0 条 |
| `validate_bg17_textures.py` | 0 | `checked=643 authorized=72 untouched=544 problems=0` |
| `validate_golden_prison.py` | 0 | `checked=16635 problems=0 templates=26` |
| `check_jar_clean.py` | 0 | 条目 2897 / `*Probe*` 0 / `halt` 0 |
| `check_forced_chunks.py` | 0 | `data.Forced` 为空 |

* 本轮**只改 1 个生产 Java 文件**（`CreativeTabSections.java`，+4286 B）+ 关卡（`validate_metal_data.py`）+ 两份冻结快照 + 本档；**不 commit、不 push**。
* `run\\` 独占的**诚实记账**：开工时 `run\\` 里**已经有一个 dev 客户端在跑**（PID 42896、12:06:37 启动，**早于本会话**；`devlaunch.Main @build\\moddev\\clientRunProgramArgs.txt`）⇒ 严格意义上**没拿到独占**；按红线**没有杀它**。它一直在写作者的 `新的世界`（region 文件 mtime 持续变化），所以**存档 mtime 不能当「本轮没碰」的证据** —— 本轮证据是探针**第 2 tick 的存档身份闸门**（`levelId=bg21probe` / `levelName=world` / 不含作者存档名）+ `run/saves/新的世界` **文件数 29 前后不变**。
* `build.gradle` 临时加过 quickPlay 参数（走 `client()` 块），跑完**逐字节复原**：SHA256 `2AAC7860E5B1F03128D42637B9F002C7A44F37E269EE6B7BC9DFBE41AD478C2F` 前后一致；`run/server.properties` **没碰**（不用 `runServer`）；`build\\moddev\\clientRunProgramArgs.txt` 开工时是 **519 B**（带上一轮遗留的 user args），`runClient` 自己把它重写成规范的 **394 B**（SHA `A365A5ED…2E4BDB`）—— Gradle 生成物，**没有手改**。
* 探针世界 `run/saves/bg21probe`（84 → 89 文件）**删前留档**（文件数 / mtime 见 `01`/`02` 读数），用完已删；`run/bg21-order-*.txt`、开关文件、quickplay json 收尾清理。
"""


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main():
    print("SHA BEFORE = %s" % sha(DOC))
    text = DOC.read_text(encoding="utf-8").replace("\r\n", "\n")
    for old, new, name in ((OLD88, NEW88, "34.8"), (OLD89, NEW89, "34.9")):
        if text.count(old) != 1:
            print("ERROR anchor %s count=%d" % (name, text.count(old)))
            return 2
        text = text.replace(old, new, 1)
    total = text.count("\n")
    inserted = total - 5454
    import re
    old_line = re.search(r"从 \*\*5454 → \d+ 行\*\*（`git diff --numstat` 对该文档\*\*插入 \d+ 行、删除 0 行\*\*）", text)
    if not old_line:
        print("ERROR line-count sentence not found")
        return 2
    text = text.replace(old_line.group(0),
                        "从 **5454 → %d 行**（`git diff --numstat` 对该文档**插入 %d 行、删除 0 行**）"
                        % (total, inserted), 1)
    DOC.write_text(text, encoding="utf-8")
    print("SHA AFTER  = %s (%d lines, inserted=%d)" % (sha(DOC), total, inserted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
