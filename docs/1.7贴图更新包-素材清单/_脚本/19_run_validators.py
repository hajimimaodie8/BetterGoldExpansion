# -*- coding: utf-8 -*-
"""顺序跑七道关卡（既有六校验器 + 本轮 bg17tex），输出 exit 码 + 关键计数行两列表。"""
import sys, os, re, subprocess
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TG = os.path.join(BASE, "tools", "asset-generator")
SCRIPTS = [
    ("validate_metal_assets.py", "[-]"),
    ("validate_metal_data.py", "[-]"),
    ("validate_trim_assets.py", "[-]"),
    ("validate_advancements.py", "[-]"),
    ("check_jar_clean.py", "[-]"),
    ("check_forced_chunks.py", "[-]"),
    ("validate_bg17_textures.py", "[-]"),
]
OUT = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单", "_证据")

KEYS = re.compile(r"(summary|SUMMARY|checked|OK=|problems|总计|计数|clean|forced|missing|count|^\s*\[[a-zA-Z0-9_-]+\])")


def dec(b):
    for enc in ("utf-8", "gbk", "cp936"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def main():
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    rows = []
    for name, _ in SCRIPTS:
        p = os.path.join(TG, name)
        r = subprocess.run([sys.executable, p], capture_output=True, cwd=BASE, env=env)
        out = dec(r.stdout)
        err = dec(r.stderr)
        lines = [l for l in (out + "\n" + err).splitlines() if l.strip()]
        picks = [l.strip() for l in lines if KEYS.search(l)]
        key = picks[-1] if picks else (lines[-1].strip() if lines else "")
        rows.append((name, r.returncode, key, out, err))
        print("%-32s exit=%d  %s" % (name, r.returncode, key[:150]))
    print("\n| 关卡 | exit | 关键计数行 |")
    print("|---|---|---|")
    lines_out = ["# 六校验器 + bg17tex 关卡：exit 码 + 关键计数行", ""]
    lines_out.append("| 关卡 | exit | 关键计数行 |")
    lines_out.append("|---|---|---|")
    for name, rc, key, _o, _e in rows:
        k = key.replace("|", "/")[:200]
        print("| %s | %d | %s |" % (name, rc, k))
        lines_out.append("| %s | %d | %s |" % (name, rc, k))
    with open(os.path.join(OUT, "六校验器.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines_out) + "\n")
    for name, rc, _k, o, e in rows:
        with open(os.path.join(OUT, "validator_%s.log" % name.replace(".py", "")),
                  "w", encoding="utf-8", newline="\n") as f:
            f.write("### stdout\n" + o + "\n### stderr\n" + e)
    bad = [r for r in rows if r[1] != 0]
    print("\n[runner] 非 0 关卡: %d" % len(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
