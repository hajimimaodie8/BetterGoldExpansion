# -*- coding: utf-8 -*-
"""看一下经验库三份文件的结构（只读）。"""
from pathlib import Path

BASE = Path(r"E:\mc\mcmod\mod_experience")
for name in ("mcmod_experience.md", "ex/06-贴图模型素材.md", "ex/03-验证与证据.md", "ex/09-回流日志-归档.md"):
    p = BASE / name
    t = p.read_text(encoding="utf-8")
    lines = t.splitlines()
    print("=" * 70)
    print(name, "行数 =", len(lines), "字节 =", p.stat().st_size)
    heads = [(i + 1, l) for i, l in enumerate(lines) if l.startswith("#")]
    for i, l in heads[-8:]:
        print("   ", i, l[:110])
    print("   末尾 3 行：")
    for l in lines[-3:]:
        print("     ", l[:160])
