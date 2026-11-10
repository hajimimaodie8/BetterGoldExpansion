# -*- coding: utf-8 -*-
"""bg22 扰动矩阵 + A 级「改前」读数。

用法：
    <dsh python> probe\\bg22\\bg22_perturb.py gate     # A 红 / B 红 / C 绿（每个用例都逐字节复原 + SHA256）
    <dsh python> probe\\bg22\\bg22_perturb.py before   # 去掉 @SubscribeEvent（= 改前行为）跑一次 A 级

基线 = 本轮修好后的 MetalEvents.java（首次运行时冻结到 probe/bg22/MetalEvents.java.fixed）。
⚠ 只动 MetalEvents.java 与（C 用例临时占位的）立档；两者每次都逐字节复原并复核 SHA256。
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material",
                   "MetalEvents.java")
FIXED = os.path.join(HERE, "MetalEvents.java.fixed")
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
DOC = os.path.join(ROOT, "docs", "1.7-混沌金与崩乱合金-需求立档.md")
EVID = os.path.join(ROOT, "docs", "bg22-证据")
LOG = os.path.join(ROOT, "build", "bg22_perturb.txt")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def gate():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, env=env)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    all_tags = set(re.findall(r"\[(bg22-[a-z-]+)\]", out))
    tags = sorted(all_tags - {"bg22-summary", "bg22-ok"})
    summary = [ln for ln in out.splitlines() if "[bg22-summary]" in ln]
    total = [ln for ln in out.splitlines() if "[bg-data-" in ln]
    return p.returncode, tags, (summary[-1] if summary else ""), (total[-1] if total else ""), out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gate"
    base = open(SRC, "rb").read()
    base_sha = hashlib.sha256(base).hexdigest().upper()

    if mode == "before":
        # 冻结基线（若还没有）
        if not os.path.exists(FIXED):
            open(FIXED, "wb").write(base)
        assert sha(FIXED) == base_sha, "冻结基线 != 当前源（先确认源是修好后的版本）"
        text = base.decode("utf-8")
        old = "    @SubscribeEvent\n    public static void onArmorHurtBerryImmunity("
        assert text.count(old) == 1
        data = text.replace(old, "    public static void onArmorHurtBerryImmunity(", 1).encode("utf-8")
        open(SRC, "wb").write(data)
        print("改前态已应用（去掉 @SubscribeEvent）：SHA256", sha(SRC))
        try:
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            p = subprocess.run([sys.executable, os.path.join(HERE, "bg22_run.py"), "before"],
                               cwd=ROOT, capture_output=True, env=env)
            print(p.stdout.decode("utf-8", "replace"))
            print(p.stderr.decode("utf-8", "replace"))
            rc = p.returncode
        finally:
            open(SRC, "wb").write(base)
            print("复原 SHA256 =", sha(SRC), "== 基线?", sha(SRC) == base_sha)
        return 0 if sha(SRC) == base_sha else 1

    # ---------------- 三个关卡扰动 ----------------
    cases = []

    # A：去掉 @SubscribeEvent ⇒ 处理器不注册 ⇒ 关卡必须红
    def case_a(t):
        return t.replace("    @SubscribeEvent\n    public static void onArmorHurtBerryImmunity(",
                         "    public static void onArmorHurtBerryImmunity(", 1)

    # B：判据换成 cactus ⇒ "只针对浆果"破 ⇒ 关卡必须红
    def case_b(t):
        return t.replace("if (!isSweetBerryBush(event.getDamageSource())) {",
                         "if (!isCactus(event.getDamageSource())) {", 1)

    # C：只加一行注释 ⇒ 关卡必须绿
    def case_c(t):
        return t + "\n// bg22 perturb C: comment only (must stay green)\n"

    cases.append(("A_no_subscribe", case_a, False))
    cases.append(("B_predicate_cactus", case_b, False))
    cases.append(("C_comment_only", case_c, True))

    lines = ["bg22 扰动矩阵（基线 MetalEvents.java SHA256 = %s）" % base_sha, ""]
    all_ok = True
    for name, fn, want_green in cases:
        text = base.decode("utf-8")
        mutated = fn(text)
        assert mutated != text, name + " 没改动任何字节"
        open(SRC, "wb").write(mutated.encode("utf-8"))
        doc_backup = None
        try:
            if name.startswith("C"):
                # C 要"绿"，而立档 §35 还没写 ⇒ 临时占位（随后逐字节复原）
                doc_backup = open(DOC, "rb").read()
                stub = ("\n## 35. bg22 树棘金盔甲不因甜浆果丛伤害掉耐久（临时占位）\n\n"
                        "bg22 sweet_berry_bush ArmorHurtEvent berryResist 旧口径原文留档\n")
                open(DOC, "ab").write(stub.encode("utf-8"))
            rc, tags, summary, total, out = gate()
            if name.startswith("C"):
                open(DOC, "wb").write(doc_backup)
            ok = (rc == 0) if want_green else (rc == 1)
            hit = (not tags) if want_green else bool(tags)
            line = "%s 改什么=%s  期望=%s  exit=%d  tags=%s  %s" % (
                name, name.split("_", 1)[1], "绿" if want_green else "红", rc, tags, summary)
            lines.append(line)
            lines.append("    " + total)
            print(line, flush=True)
            if not (ok and hit):
                all_ok = False
                lines.append("    !! 期望未命中")
        finally:
            open(SRC, "wb").write(base)
            if doc_backup is not None:
                open(DOC, "wb").write(doc_backup)
            now = sha(SRC)
            doc_now = sha(DOC)
            lines.append("    复原：MetalEvents=%s(==基线? %s)" % (now, now == base_sha))
            print("    复原 MetalEvents =", now, "== 基线?", now == base_sha, flush=True)
            if doc_backup is not None:
                print("    复原 立档 =", doc_now, flush=True)
            if now != base_sha:
                all_ok = False

    lines.append("SUMMARY cases=%d all_ok=%s" % (len(cases), all_ok))
    os.makedirs(EVID, exist_ok=True)
    open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    shutil.copyfile(LOG, os.path.join(EVID, "03-扰动.txt"))
    print("\n".join(lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
