# -*- coding: utf-8 -*-
"""bgfix8 收尾自证：探针删除 / grep 零命中 / 临时改动逐字节复原 / 世界差异 0 / 开关文件 0。"""
import hashlib
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
# ⚠ 证据文件**由 Python 自己写**（UTF-8 无 BOM、LF）—— 别用 `Tee-Object`（它写 UTF-16，
#   读回来会被判成 binary；本轮实测踩过）。
_EVID = os.path.join(REPO, "docs", "bgfix8-\u8bc1\u636e",
                     "08-\u6536\u5c3e\u6e05\u7406\u4e0e\u9010\u5b57\u8282\u590d\u539f.txt")
_fh = open(_EVID, "w", encoding="utf-8", newline="\n")
_orig_write = sys.stdout.write


class _Tee:
    @staticmethod
    def write(s):
        _orig_write(s)
        _fh.write(s)

    @staticmethod
    def flush():
        sys.__stdout__.flush()
        _fh.flush()


sys.stdout = _Tee()
BASE = {
    "build.gradle": "2AAC7860E5B1F03128D42637B9F002C7A44F37E269EE6B7BC9DFBE41AD478C2F",
    os.path.join("build", "moddev", "clientRunProgramArgs.txt"):
        "A365A5EDF7ABC44C576E5DD3F725A54D46658FCDDC1E3A0257BEC7C0AB2E4BDB",
    os.path.join("run", "server.properties"):
        "A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4",
}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


print("== 1) 临时改动逐字节复原（SHA256 与跑前基线比对） ==")
for rel, want in BASE.items():
    got = sha(os.path.join(REPO, rel))
    print("  %-45s %s  match=%s" % (rel, got, got.upper() == want.upper()))

print("== 2) 探针整块删除 + grep 零命中 ==")
probe_dir = os.path.join(REPO, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe")
print("  src/.../bettergold/probe 目录仍存在 = %s（应 False）" % os.path.isdir(probe_dir))
hits = []
for root, _dirs, files in os.walk(os.path.join(REPO, "src")):
    for f in files:
        p = os.path.join(root, f)
        try:
            t = open(p, "rb").read().decode("utf-8", errors="replace")
        except Exception:
            continue
        for pat in ("BGFIX8C-PROBE", "BGFIX8S-PROBE", "probe.bgfix8", "bgfix8c-probe",
                    "bgfix8s-probe", "server.halt(", "halt(false)"):
            if pat in t:
                hits.append("%s :: %s" % (os.path.relpath(p, REPO), pat))
print("  src 内探针/halt 命中 = %d %s（`bgfix8` 作为**轮次标签**出现在 Config.java 注释里是允许的）"
      % (len(hits), hits))

print("== 3) 开关文件 / 探针世界 ==")
flags = []
for root, _dirs, files in os.walk(os.path.join(REPO, "run")):
    for f in files:
        if f.endswith(".enabled"):
            flags.append(os.path.relpath(os.path.join(root, f), REPO))
print("  run/ 下 *.enabled = %d %s（应 0）" % (len(flags), flags))
print("  run/saves 目录 = %s" % sorted(os.listdir(os.path.join(REPO, "run", "saves"))))
for name in sorted(os.listdir(os.path.join(REPO, "run", "saves"))):
    p = os.path.join(REPO, "run", "saves", name)
    n = sum(len(fs) for _r, _d, fs in os.walk(p))
    print("    %s files=%d" % (name, n))

print("== 4) 作者存档 / run/world 逐文件 SHA256 与跑前清单比对 ==")
# ⚠ 跑前清单是 PowerShell `Get-FileHash` 写的（**大写**十六进制 + UTF-8 BOM）
#   ⇒ 两边统一 `upper()` 再比（首版忘统一 ⇒ 80+80 行全"差异"，纯属量具错）
before = open(os.path.join(REPO, "build", "bgfix8-baseline", "worlds-before.txt"),
              encoding="utf-8-sig").read().splitlines()
after = []
for sub in ("world", os.path.join("saves", "\u65b0\u7684\u4e16\u754c")):
    p = os.path.join(REPO, "run", sub)
    tag = "world" if sub == "world" else "saves"
    for root, _d, files in os.walk(p):
        for f in files:
            fp = os.path.join(root, f)
            after.append("%s  %s  %s" % (tag, sha(fp).upper(), os.path.relpath(fp, REPO)))
norm = lambda rows: sorted(r.strip().replace("  ", "  ") for r in rows if r.strip())
b, a = norm(before), norm(after)
diff = set(b) ^ set(a)
print("  跑前 %d 行 / 跑后 %d 行 / 差异行 = %d（应 0）" % (len(b), len(a), len(diff)))
for d in list(diff)[:5]:
    print("    DIFF " + d[:130])

print("== 5) 产物 jar 与 jar 洁净度 ==")
libs = os.path.join(REPO, "build", "libs")
for f in sorted(os.listdir(libs)):
    if f.endswith(".jar"):
        print("  %s  %d B  sha256=%s" % (f, os.path.getsize(os.path.join(libs, f)),
                                         sha(os.path.join(libs, f))))

print("== 6) git status（哪些是本轮的改动） ==")
r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, cwd=REPO)
print(r.stdout.decode("utf-8", errors="replace").rstrip())
