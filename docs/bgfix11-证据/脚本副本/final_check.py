# -*- coding: utf-8 -*-
"""bgfix11 · 收尾总检（编码/EOL/哈希/探针残留/关卡退出码）。"""
import hashlib
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, REPO)

FILES = [
    "src/main/resources/assets/bettergold/lang/en_us.json",
    "src/main/resources/assets/bettergold/lang/zh_cn.json",
    "tools/asset-generator/validate_metal_data.py",
    "docs/1.6-规格.md",
]
out = []


def say(s=""):
    out.append(s)
    print(s)


say("== 形态与哈希 ==")
for rel in FILES:
    p = os.path.join(REPO, rel)
    b = open(p, "rb").read()
    try:
        b.decode("utf-8")
        dec = "utf-8 OK"
    except UnicodeDecodeError as e:
        dec = "**NOT UTF-8: %s**" % e
    say("%-58s bytes=%-7d CRLF=%-4d BOM=%-5s ends_nl=%-5s sha=%s  %s"
        % (os.path.basename(rel), len(b), b.count(b"\r\n"), b[:3] == b"\xef\xbb\xbf",
           b.endswith(b"\n"), hashlib.sha256(b).hexdigest().upper()[:16], dec))

say()
say("== en_us.json 目标键 ==")
import json  # noqa: E402
en = json.loads(open(os.path.join(REPO, FILES[0]), "rb").read().decode("utf-8"))
zh = json.loads(open(os.path.join(REPO, FILES[1]), "rb").read().decode("utf-8"))
K = "bettergold.handbook.page.knowledge_1_summary"
say("en == zh ? %s" % (en[K] == zh[K]))
say("en 含 CJK ? %s" % bool(re.search(u"[\u3400-\u9fff\uf900-\ufaff]", en[K])))
say("en 值 = %r" % en[K])
say("键数 en=%d zh=%d 键集一致=%s" % (len(en), len(zh), sorted(en) == sorted(zh)))

say()
say("== 探针残留（生产代码）==")
pats = ("BgFix11Probe", "BGFIX11-PROBE", "bgfix11-probe.enabled")
hits = []
for base, dirs, files in os.walk(os.path.join(REPO, "src")):
    for f in files:
        p = os.path.join(base, f)
        t = open(p, "rb").read().decode("utf-8", "replace")
        for pat in pats:
            if pat in t:
                hits.append((os.path.relpath(p, REPO), pat))
say("src/ 下探针命中 = %d %s" % (len(hits), hits[:5]))
say("probe/ 目录存在 = %s" % os.path.isdir(os.path.join(REPO, "probe")))
say("run/ 下 bgfix11* 文件 = %s"
    % sorted(f for f in os.listdir(os.path.join(REPO, "run")) if f.startswith("bgfix11")))
say("'halt(' 在生产代码（src/main/java）里的出现次数 = %d"
    % sum(open(os.path.join(b, f), "rb").read().decode("utf-8", "replace").count("halt(")
          for b, _d, fs in os.walk(os.path.join(REPO, "src/main/java")) for f in fs))

say()
say("== 关卡终检（validate_metal_data.py）==")
r = subprocess.run([sys.executable, os.path.join(REPO, "tools/asset-generator/validate_metal_data.py")],
                   cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-3:]
say("exit = %d" % r.returncode)
for l in tail:
    say("  " + l)

EVID = os.path.join(REPO, "docs", "bgfix11-证据")
open(os.path.join(EVID, "12-收尾清理与逐字节复原.txt"), "w", encoding="utf-8",
     newline="\n").write("\n".join(out) + "\n")
print("\n写出 12-收尾清理与逐字节复原.txt")
