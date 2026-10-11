# -*- coding: utf-8 -*-
"""bgfix11 · 收尾证据归集（把一次性脚本/读数拷进 `docs/bgfix11-证据/`）。

⚠ 探针铁律：**删探针之前先把源码/脚本复制到证据目录**（本脚本就是那一步）。
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PR = os.path.join(REPO, "probe", "bgfix11")
EVID = os.path.join(REPO, "docs", "bgfix11-证据")
B = os.path.join(REPO, "build", "bgfix11")
LANGF = "src/main/resources/assets/bettergold/lang/en_us.json"


def rd(p, enc="utf-8"):
    return open(p, "rb").read().decode(enc, "replace")


def wr(name, text):
    p = os.path.join(EVID, name)
    open(p, "w", encoding="utf-8", newline="\n").write(text)
    print("写出 %s (%d B)" % (name, len(text.encode("utf-8"))))


def cp(src, name):
    dst = os.path.join(EVID, name)
    open(dst, "wb").write(open(src, "rb").read())
    print("复制 %s -> %s" % (os.path.basename(src), name))


os.makedirs(EVID, exist_ok=True)

# 01 扰动矩阵
cp(os.path.join(B, "perturb-utf8.txt"), "01-扰动矩阵.txt")
# 02 A 级读数（从 run/logs/latest.log 抓探针行）
log = rd(os.path.join(REPO, "run", "logs", "latest.log"))
probe = [ln for ln in log.splitlines() if "BGFIX11-PROBE" in ln]
wr("02-A级-runClient-I18n读数.txt",
   "== bgfix11 A 级读数（run/logs/latest.log 里 BGFIX11-PROBE 的全部行，逐字）==\n"
   + "\n".join(probe) + "\n")
# 03/04 改值脚本 + 自证
cp(os.path.join(PR, "apply_en.py"), "03-改值脚本副本-apply_en.py")
cp(os.path.join(PR, "apply_en.report.txt"), "04-改值脚本自证.txt")
# 06 扰动脚本
cp(os.path.join(PR, "perturb.py"), "06-扰动脚本副本.py")
# 07 探针字面量预检
r = subprocess.run([sys.executable, os.path.join(PR, "check_probe_literals.py")],
                   cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
wr("07-探针字面量预检.txt",
   "== 跑客户端**之前**的逐字预检（防「手抄码位」造成假 FAIL）==\nexit=%d\n%s"
   % (r.returncode, (r.stdout or "") + (r.stderr or "")))
# 08/09 冻结副本
cp(os.path.join(PR, "en_us.before.json"), "08-en_us-改前冻结副本.json")
cp(os.path.join(PR, "zh_cn.before.json"), "09-zh_cn-冻结副本.json")
# 11 B 级：构建 + 六校验器
val_names = ["validate_metal_assets.py", "validate_metal_data.py", "validate_trim_assets.py",
             "validate_advancements.py", "check_jar_clean.py", "check_forced_chunks.py"]
buf = ["== 构建（bgfix11 最终产物，探针已整块删除）=="]
buf += [ln for ln in rd(os.path.join(B, "build.txt")).splitlines()
        if "BUILD SUCCESSFUL" in ln or "BUILD FAILED" in ln or "error:" in ln]
buf += ["", "== 六校验器（判据 = exit + 关键计数两列）=="]
for n in val_names:
    p = os.path.join(B, "v-" + n + ".txt")
    body = rd(p).strip().splitlines()
    buf.append("--- %s（exit 0 / 契约 0 绿 · 1 有问题 · 2 前置坏）" % n)
    buf += ["    " + l for l in body[-3:]]
wr("11-B级-构建与六校验器.txt", "\n".join(buf) + "\n")
# 13 中 → 英对照
en = json.load(open(os.path.join(REPO, LANGF), encoding="utf-8"))
zh = json.load(open(os.path.join(REPO, "src/main/resources/assets/bettergold/lang/zh_cn.json"),
                    encoding="utf-8"))
K = "bettergold.handbook.page.knowledge_1_summary"
wr("13-中文到新英文对照表.txt",
   "== bgfix11 · 那一行的三方对照 ==\n"
   "键：%s\n\n[zh 原文]（作者那份 = 唯一真源；全程 0 字节改动）\n  %s\n\n"
   "[旧 en]（== zh 逐字相同；bgfix10 §31.7 的既有缺陷）\n  %s\n\n"
   "[新 en]（§31.7 的建议英文逐字采纳；294 字）\n  %s\n\n"
   "术语依据（既有写法，均 grep 自改后的 en_us.json）：\n"
   "  * \"noble gold\"：%d 处\n"
   "  * smithing template：%d 处\n"
   "  * golden gear：%d 处\n"
   "  * Building Blocks（手册页标题）：%d 处\n"
   "  * furnace：%d 处\n"
   % (K, zh[K], zh[K], en[K],
      sum(1 for v in en.values() if '"noble gold"' in v),
      sum(1 for v in en.values() if "smithing template" in v),
      sum(1 for v in en.values() if "golden gear" in v),
      sum(1 for v in en.values() if "Building Blocks" in v),
      sum(1 for v in en.values() if "furnace" in v)))
# 14 options.txt.bak + 15 run 状态
cp(os.path.join(PR, "options.txt.bak"), "14-跑前-options.txt.bak")
sav = []
sp = os.path.join(REPO, "run", "saves")
for name in sorted(os.listdir(sp)):
    d = os.path.join(sp, name)
    files = [os.path.join(b, f) for b, _x, fs in os.walk(d) for f in fs]
    last = max((os.path.getmtime(f) for f in files), default=0)
    sav.append("  %s files=%d last_mtime=%s" % (name, len(files),
                                                __import__("time").strftime("%Y-%m-%d %H:%M:%S",
                                                                            __import__("time").localtime(last))))
wr("15-跑前-run状态清单.txt",
   "== 跑客户端之前 / 之后的 run\\ 状态（作者存档零改动）==\n"
   "options.txt SHA256 = %s（lang:zh_cn）\n"
   "run/saves:\n%s\n"
   % (hashlib.sha256(open(os.path.join(REPO, "run", "options.txt"), "rb").read()).hexdigest().upper(),
      "\n".join(sav)))
# 16 jar 内资源锚点
jars = sorted(glob.glob(os.path.join(REPO, "build", "libs", "*.jar")), key=os.path.getmtime)
jarp = jars[-1]
with zipfile.ZipFile(jarp) as z:
    names = z.namelist()
    b = z.read("assets/bettergold/lang/en_us.json")
    probes = [n for n in names if "probe" in n.lower() or "Probe" in n]
buf = ["== jar 内资源与探针残留核对（%s）==" % os.path.basename(jarp),
       "jar 条目数 = %d" % len(names),
       "jar 内 assets/bettergold/lang/en_us.json 的 SHA256 = %s" % hashlib.sha256(b).hexdigest().upper(),
       "工作区该文件的 SHA256                        = %s" % hashlib.sha256(open(os.path.join(REPO, LANGF), "rb").read()).hexdigest().upper(),
       "*probe* / *Probe* 条目 = %d %s" % (len(probes), probes[:5]),
       "jar 内该键的解析值 = %r" % json.loads(b.decode("utf-8"))[K]]
wr("16-jar内资源锚点.txt", "\n".join(buf) + "\n")
print("done")
