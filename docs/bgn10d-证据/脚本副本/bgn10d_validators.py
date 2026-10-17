# -*- coding: utf-8 -*-
"""跑七个关卡，记录 **exit 码 + 关键计数行** 两列（口径见 docs/构建与跑测注意事项.md §七）。

用法：py -3 docs/bgn10d-证据/scripts/bgn10d_validators.py
输出：docs/bgn10d-证据/10-七关卡.txt（同时打印到 stdout）
"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
GEN = os.path.join(ROOT, "tools", "asset-generator")
PY = sys.executable
OUT = os.path.join(ROOT, "docs", "bgn10d-证据", "10-七关卡.txt")

# 顺序 = AGENTS.md / docs 里的既有顺序（第七个是 1.7 贴图更新包那一关）
CASES = [
    ("validate_metal_assets.py", r"^\[bg-assets-(ok|fail)\]|实际检查了",
     "资产/贴图/模型/mixin + bgn10d tremble 锚点"),
    ("validate_metal_data.py", r"^\[bg-data-(ok|fail)\]|实际检查了",
     "语言键/数据/标签 + bgn10d 4 条种子标签"),
    ("validate_trim_assets.py", r"校验|问题|OK|FAIL",
     "纹饰色卡与图集置换"),
    ("validate_advancements.py", r"成就|问题|OK|FAIL|PASS",
     "51 条成就的落点与判据"),
    ("check_jar_clean.py", r"残留|探针|问题|OK|FAIL|PROBE",
     "jar 里不许有探针/临时物"),
    ("check_forced_chunks.py", r"forceload|强制加载|问题|OK|FAIL",
     "存档里 forceload 双向 0"),
    ("validate_bg17_textures.py", r"^\[bg17tex-(ok|fail|summary)\]|^\[bg17tex-auth6\]",
     "1.7 贴图更新包 72 张 + tremble 后加授权"),
]


def main():
    lines = []
    lines.append("bg-n10d 七关卡读数（exit 码 + 关键计数行）")
    lines.append("跑测时刻：" + __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("python：" + PY)
    lines.append("")
    bad = 0
    for script, pat, why in CASES:
        p = os.path.join(GEN, script)
        proc = subprocess.run([PY, p], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        out = (proc.stdout or "") + (proc.stderr or "")
        rx = re.compile(pat, re.M)
        keys = [ln.rstrip() for ln in out.splitlines() if rx.search(ln)]
        lines.append("=" * 100)
        lines.append("%-28s exit=%d   （%s）" % (script, proc.returncode, why))
        for k in keys[:8]:
            lines.append("    " + k)
        if proc.returncode != 0:
            bad += 1
            lines.append("    ⚠ 非 0 —— 原始尾部：")
            for ln in out.splitlines()[-6:]:
                lines.append("      " + ln)
    lines.append("=" * 100)
    lines.append("[bgn10d-validators] 非 0 的关卡数 = %d（共 %d 个）" % (bad, len(CASES)))
    text = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
