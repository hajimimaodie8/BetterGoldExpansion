# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"docs\gpq-证据\06-收尾核对.md"
t = open(p, encoding="utf-8").read()
dup = "- `06-收尾核对.md`（本节）\n- `09-构建.txt`（`gradlew.bat build` 尾部 + jar 字节数/SHA256）\n"
assert t.count(dup) == 1, t.count(dup)
t = t.replace(dup, "")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("dup removed, size", len(t.encode("utf-8")))
print(t.split("## 6.")[1][:700])
