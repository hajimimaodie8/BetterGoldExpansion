# -*- coding: utf-8 -*-
import json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LANG = os.path.join(REPO, "src", "main", "resources", "assets", "bettergold", "lang")
files = {
    "en_before": os.path.join(REPO, "probe", "bgfix10", "en_us.before.json"),
    "en_after": os.path.join(LANG, "en_us.json"),
    "zh": os.path.join(LANG, "zh_cn.json"),
}
out = []
keys = ["bettergold.handbook.page.knowledge_1_summary",
        "bettergold.handbook.page.knowledge_1_right",
        "item.bettergold.unwanted_antique",
        "item.bettergold.alchemy_student_handbook"]
d = {n: json.loads(open(p, "rb").read().decode("utf-8")) for n, p in files.items()}
for k in keys:
    out.append("== %s" % k)
    for n in ("en_before", "en_after", "zh"):
        out.append("   %-10s %r" % (n, d[n].get(k)))
out.append("")
out.append("== en_after 里含中日韩文字的键（全量）")
import re
CJK = re.compile("[\u3400-\u9fff\uf900-\ufaff]")
zh = d["zh"]
for k, v in d["en_after"].items():
    if CJK.search(str(v)):
        mark = "SAME-AS-ZH" if zh.get(k) == v else "DIFF"
        out.append("   [%s] %s = %r" % (mark, k, v))
out.append("")
out.append("== 这些键在改前的 en 里也是中文吗")
for k, v in d["en_after"].items():
    if CJK.search(str(v)):
        out.append("   before=%s after=%s  %s" % (CJK.search(str(d["en_before"].get(k, ""))) is not None,
                                                  CJK.search(str(v)) is not None, k))
open(os.path.join(REPO, "probe", "bgfix10", "cjk_audit.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("written")
