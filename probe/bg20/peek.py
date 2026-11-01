# -*- coding: utf-8 -*-
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = r"E:\mc\mcmod\mod_experience"

p = root + r"\ex\04-数值与API.md"
t = io.open(p, encoding="utf-8").read()
nums = re.findall(r"(?m)^(\d+)\. ", t)
print("ex04 lines", t.count("\n") + 1, "numbered items", len(nums), "max", nums[-1] if nums else None)
print("...TAIL...")
print(t[-1200:])

t2 = io.open(root + r"\mcmod_experience.md", encoding="utf-8").read()
print("=== appendix D tail ===")
print(t2[-1200:])
