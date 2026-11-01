# -*- coding: utf-8 -*-
"""bg20 扰动（≥2 个用例 + 逐字节复原 + SHA256 自证）。

用例（每个都跑「生成器 → `validate_metal_data.py`」，看 exit 与首个问题 tag）：
  A `page_type_name_wrong`：把生成器里**自定义页型名**改错（`bettergold:double_recipe` →
    `bettergold:double_recpe`）⇒ 期望 **红**（`[bgbook-page-type]` 未知页型 / 页型序列不符）。
  B `recipe1_doubled`：把自定义页**上边**换成 `raw_sturdygold_doubled`（那条"只有高精度炼金油、
    没有混沌金块"的双倍原料）⇒ 期望 **红**（不是"混沌金粒的配方"）。
  C `comment_only`：只在生成器里加一行注释（产物应**逐字节不变**）⇒ 期望 **绿**。

每个用例结束都：逐字节复原 `generate_handbook_data.py` → 复核 SHA256 → 重跑生成器 →
复核整棵手册树的摘要 == 基线 → 重跑关卡确认回到绿。
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN = os.path.join(ROOT, "tools", "asset-generator", "generate_handbook_data.py")
VAL = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
BOOK = os.path.join(ROOT, "src", "main", "resources")
PY = sys.executable
OUT = os.path.join(ROOT, "docs", "bg20-证据", "07-扰动.txt")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def tree_digest(*roots):
    h = hashlib.sha256()
    items = []
    for root in roots:
        for base, _dirs, fs in os.walk(root):
            for f in fs:
                p = os.path.join(base, f)
                items.append((os.path.relpath(p, ROOT).replace("\\", "/"), sha(p)))
    items.sort()
    for rel, s in items:
        h.update(("%s|%s\n" % (rel, s)).encode("utf-8"))
    return h.hexdigest().upper()


def run(script):
    p = subprocess.run([PY, script], cwd=ROOT, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    out = (p.stdout or b"").decode("utf-8", "replace")
    tags = []
    for line in out.splitlines():
        s = line.strip()
        if not s.startswith("["):
            continue
        if "问题 0 条" in s or "problems=0" in s:
            continue
        if any(k in s for k in ("问题", "fail", "FAIL")):
            tags.append(s[:200])
    return p.returncode, out, tags


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = ["bg20 扰动（≥2 用例 + 逐字节复原 + SHA256）", ""]
    raw = open(GEN, "rb").read()
    gen_sha = hashlib.sha256(raw).hexdigest().upper()
    base_book = tree_digest(os.path.join(BOOK, "assets", "bettergold", "patchouli_books"),
                            os.path.join(BOOK, "data", "bettergold", "patchouli_books"))
    lines.append("baseline: generator SHA256 = %s" % gen_sha)
    lines.append("baseline: 手册树摘要      = %s" % base_book)
    rc0, out0, tags0 = run(VAL)
    lines.append("baseline: validate_metal_data.py exit = %d" % rc0)
    lines.append("")
    ok_all = (rc0 == 0)

    cases = [
        ("A page_type_name_wrong",
         b'"type": "bettergold:double_recipe"',
         b'"type": "bettergold:double_recpe"',
         1),
        ("B recipe1_doubled",
         b'double_recipe_page("chaos_coin_smelting", "chaosgold_ingot_from_nugget")',
         b'double_recipe_page("raw_sturdygold_doubled", "chaosgold_ingot_from_nugget")',
         1),
        ("C comment_only",
         b'def double_recipe_page(',
         b'# bg20 perturb: comment only, no semantic change\ndef double_recipe_page(',
         0),
    ]

    for name, old, new, want in cases:
        if raw.count(old) != 1:
            lines.append("%s: !! 锚点命中 %d 次，用例跳过" % (name, raw.count(old)))
            ok_all = False
            continue
        open(GEN, "wb").write(raw.replace(old, new, 1))
        p_gen = subprocess.run([PY, GEN], cwd=ROOT, capture_output=True,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        rc, out, tags = run(VAL)
        lines.append("%s: generator exit=%d / validate exit=%d（期望 %d）"
                     % (name, p_gen.returncode, rc, want))
        for t in tags[:3]:
            lines.append("    " + t)
        hit = (rc != 0) if want else (rc == 0)
        if not hit:
            lines.append("    !! 用例没有按预期变%s" % ("红" if want else "绿"))
            ok_all = False

        # 逐字节复原
        open(GEN, "wb").write(raw)
        now = sha(GEN)
        regen = subprocess.run([PY, GEN], cwd=ROOT, capture_output=True,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        book_now = tree_digest(os.path.join(BOOK, "assets", "bettergold", "patchouli_books"),
                               os.path.join(BOOK, "data", "bettergold", "patchouli_books"))
        rc2, _o, _t = run(VAL)
        lines.append("    复原: generator SHA256 = %s == base? %s / 手册树 == base? %s / "
                     "关卡 exit=%d / 重生成 exit=%d"
                     % (now, now == gen_sha, book_now == base_book, rc2, regen.returncode))
        if now != gen_sha or book_now != base_book or rc2 != 0:
            ok_all = False
            lines.append("    !! 复原不干净")
        lines.append("")

    lines.append("结论: %s" % ("全部用例按预期 + 逐字节复原干净" if ok_all else "有异常，见上"))
    text = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
