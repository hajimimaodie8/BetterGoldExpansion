# -*- coding: utf-8 -*-
"""bgfix11 · 预检探针里的两个期望字面量（EXPECT_EN / EXPECT_ZH）与真实语言文件**逐字**一致。

理由：A 级客户端一次要跑好几分钟，不能让"期望字面量抄错了"变成一次假 FAIL。
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
JAVA = "src/main/java/com/hjmmd_8/bettergold/probe/bgfix11/BgFix11Probe.java"
src = open(JAVA, encoding="utf-8").read()
en = json.load(open("src/main/resources/assets/bettergold/lang/en_us.json", encoding="utf-8"))
zh = json.load(open("src/main/resources/assets/bettergold/lang/zh_cn.json", encoding="utf-8"))
KEY = "bettergold.handbook.page.knowledge_1_summary"


def literal(name):
    m = re.search(r"private static final String %s =\s*(.*?);\n" % name, src, re.S)
    if not m:
        return None
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    out = []
    for p in parts:
        # Java 源里的 \uXXXX 在**词法层**就被替换 ⇒ 与 Python 的 unicode_escape 同效
        out.append(p.encode("ascii", "backslashreplace").decode("unicode_escape"))
    return "".join(out)


ok = True
for name, want in (("EXPECT_EN", en[KEY]), ("EXPECT_ZH", zh[KEY])):
    got = literal(name)
    same = got == want
    ok &= same
    print("%-10s %s len=%s 前 60 字=%r" % (name, "OK" if same else "**MISMATCH**",
                                          len(got) if got is not None else None,
                                          (got or "")[:60]))
    if not same:
        print("   want:", repr(want[:120]))
        print("   got :", repr((got or "")[:120]))
print("RESULT", "ALL-PASS" if ok else "HAS-FAIL")
sys.exit(0 if ok else 1)
