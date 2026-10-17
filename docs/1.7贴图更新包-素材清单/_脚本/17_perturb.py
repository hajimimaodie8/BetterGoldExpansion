# -*- coding: utf-8 -*-
"""validate_bg17_textures.py 的扰动自证（每例逐字节复原 + SHA256 自证）。

用例：
  P0  基线                                  -> exit 0
  P1  把某张授权贴图覆盖成别的字节           -> exit 1（命中 auth-fail / revert）
  P2  改一张"没授权"的贴图（动 1 个字节）    -> exit 1（命中 untouched-fail）
  P3  只改注释 / 只加空行（MetalFamily.java）-> exit 0（仍绿）
  P4  删掉一张授权贴图（前置缺失）           -> exit 1
  P5  清单文件搬走（基线被破坏）             -> exit 2

纪律：所有被碰的文件先记录 SHA256；每例结束逐字节复原并复核 SHA256。
MetalFamily.java 采用"写前比对"保护：若在扰动窗口内被别人改过，立即中止且不做覆盖式复原。
"""
import sys, os, hashlib, subprocess, shutil
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
JAVA = os.path.join(BASE, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material", "MetalFamily.java")
MANIFEST = os.path.join(BASE, "tools", "asset-generator", "bg17tex_manifest.tsv")
GATE = os.path.join(BASE, "tools", "asset-generator", "validate_bg17_textures.py")
ARCH = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
EVID = os.path.join(ARCH, "_证据")

P1_PATH = "item/flamegold_axe.png"
P1_ZIP = "1792201515426.png"
P2_PATH = "item/echogold_sword.png"
P4_PATH = "block/thornsgold_bars.png"
P4_ZIP = "1792201299889.png"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def run_gate():
    r = subprocess.run([sys.executable, GATE], capture_output=True, cwd=BASE)
    return (r.returncode,
            r.stdout.decode("utf-8", "replace"),
            r.stderr.decode("utf-8", "replace"))


def main():
    os.makedirs(EVID, exist_ok=True)
    results = []

    def rec(name, want, got, note=""):
        ok = (want == got)
        results.append((name, want, got, "PASS" if ok else "FAIL", note))
        print("[%s] %-46s want_exit=%d got_exit=%d  %s"
              % ("PASS" if ok else "FAIL", name, want, got, note))
        return ok

    # ---------------- P0 基线 ----------------
    rc, out, err = run_gate()
    rec("P0 baseline", 0, rc, "[bg17tex-ok]" if "[bg17tex-ok]" in out else "")

    # ---------------- P1 授权贴图被覆盖 ----------------
    p = os.path.join(TEX, P1_PATH.replace("/", os.sep))
    orig = open(p, "rb").read()
    s0 = sha(p)
    try:
        other = open(os.path.join(ARCH, "1792201550342.png"), "rb").read()
        assert other != orig
        with open(p, "wb") as f:
            f.write(other)
        assert sha(p) != s0
        rc, out, err = run_gate()
        hit = ("bg17tex-auth-fail" in err) or ("bg17tex-revert" in err)
        rec("P1 authorized texture overwritten", 1, rc, "code_hit" if hit else "CODE MISSING")
        if not hit:
            results.append(("P1 conclusion code", 1, 0, "FAIL", "no auth-fail/revert"))
    finally:
        with open(p, "wb") as f:
            f.write(orig)
        assert sha(p) == s0, "P1 restore failed"
        print("     restore P1 sha=%.16s OK" % sha(p))

    # ---------------- P2 改一张没授权的贴图 ----------------
    p2 = os.path.join(TEX, P2_PATH.replace("/", os.sep))
    orig2 = open(p2, "rb").read()
    s2 = sha(p2)
    try:
        b = bytearray(orig2)
        b[-1] = (b[-1] + 1) & 0xFF
        with open(p2, "wb") as f:
            f.write(bytes(b))
        assert sha(p2) != s2
        rc, out, err = run_gate()
        hit = "bg17tex-untouched-fail" in err
        rec("P2 unauthorized texture touched", 1, rc, "code_hit" if hit else "CODE MISSING")
        if not hit:
            results.append(("P2 conclusion code", 1, 0, "FAIL", "no untouched-fail"))
    finally:
        with open(p2, "wb") as f:
            f.write(orig2)
        assert sha(p2) == s2, "P2 restore failed"
        print("     restore P2 sha=%.16s OK" % sha(p2))

    # ---------------- P3 只改注释 / 只加空行 ----------------
    orig3 = open(JAVA, "rb").read()
    s3 = hashlib.sha256(orig3).hexdigest()
    try:
        add = ("\r\n// bg17tex perturbation: this comment mentions ArmorMaterial.Layer and "
               "ResourceLocation.fromNamespaceAndPath(bettergold.MODID, this.id) on purpose\r\n"
               "\r\n\r\n").encode("utf-8")
        with open(JAVA, "r+b") as f:
            f.seek(0, os.SEEK_END)
            f.write(add)
        # 写前比对保护：确认文件仍是"我们刚写的那份"，没被别人动过
        now = open(JAVA, "rb").read()
        if now != orig3 + add:
            raise SystemExit("MetalFamily.java 在扰动窗口内被他人修改，已中止且不做覆盖复原")
        rc, out, err = run_gate()
        rec("P3 comment-only + blank lines", 0, rc, "[bg17tex-ok]" if "[bg17tex-ok]" in out else "")
    finally:
        now = open(JAVA, "rb").read()
        if now == orig3:
            pass                      # 已经是原样（异常路径下可能未写入）
        elif now == orig3 + add:
            with open(JAVA, "wb") as f:
                f.write(orig3)
        else:
            raise SystemExit("MetalFamily.java 内容不是本脚本写的版本，拒绝覆盖式复原")
        assert hashlib.sha256(open(JAVA, "rb").read()).hexdigest() == s3, "P3 restore failed"
        print("     restore P3 sha=%.16s OK" % s3)

    # ---------------- P3b 反向对照：needle 只出现在注释里 => 去注释后必须找不到 ----------------
    sys.path.insert(0, os.path.join(BASE, "tools", "asset-generator"))
    import importlib
    gate_mod = importlib.import_module("validate_bg17_textures")
    probe = (
        'class X {\n'
        '  // ArmorMaterial.Layer ResourceLocation.fromNamespaceAndPath(bettergold.MODID, this.id)\n'
        '  /* ArmorMaterial.Layer 块注释里 */\n'
        '  String s = "// 这是字符串里的双斜杠，不是注释";\n'
        '}\n'
    )
    stripped = gate_mod.strip_java_comments(probe)
    in_comment_only = ("ArmorMaterial.Layer" not in stripped)
    rec("P3b needle only in comments -> not matched", 1, 1 if in_comment_only else 0,
        "stripped_len=%d" % len(stripped))
    results[-1] = (results[-1][0], 1, 1 if in_comment_only else 0,
                   "PASS" if in_comment_only else "FAIL", "去注释后 needle 消失")
    # 对照：同一段 needle 写进代码 => 必须找得到
    probe2 = probe.replace('  String s =', '  Object o = new ArmorMaterial.Layer(ns, id);\n  String s =')
    stripped2 = gate_mod.strip_java_comments(probe2)
    rec("P3c needle in code -> matched", 1, 1 if ("ArmorMaterial.Layer" in stripped2) else 0,
        "stripped_len=%d" % len(stripped2))

    # ---------------- P4 删掉一张授权贴图 ----------------
    p4 = os.path.join(TEX, P4_PATH.replace("/", os.sep))
    orig4 = open(p4, "rb").read()
    s4 = sha(p4)
    try:
        os.remove(p4)
        assert not os.path.exists(p4)
        rc, out, err = run_gate()
        hit = ("bg17tex-auth-fail" in err) or ("bg17tex-summary" in out)
        rec("P4 authorized texture deleted", 1, rc, "code_hit" if hit else "CODE MISSING")
    finally:
        with open(p4, "wb") as f:
            f.write(orig4)
        assert sha(p4) == s4, "P4 restore failed"
        print("     restore P4 sha=%.16s OK" % sha(p4))

    # ---------------- P5 清单搬走（基线被破坏） ----------------
    bak = MANIFEST + ".bak-bg17tex"
    try:
        shutil.move(MANIFEST, bak)
        assert not os.path.exists(MANIFEST)
        rc, out, err = run_gate()
        rec("P5 manifest missing (prereq broken)", 2, rc,
            "prereq-fail" if "bg17tex-prereq-fail" in err else "CODE MISSING")
    finally:
        if os.path.exists(bak):
            shutil.move(bak, MANIFEST)
        assert os.path.exists(MANIFEST), "P5 restore failed"
        print("     restore P5 manifest OK sha=%.16s" % sha(MANIFEST))

    # ---------------- 复归基线 ----------------
    rc, out, err = run_gate()
    rec("P9 re-baseline green", 0, rc)

    # ---------------- 落证 ----------------
    lines = ["# validate_bg17_textures.py 扰动矩阵（%d 例）" % len(results), ""]
    lines.append("| 用例 | want_exit | got_exit | 结果 | 备注 |")
    lines.append("|---|---|---|---|---|")
    for name, want, got, verdict, note in results:
        lines.append("| %s | %d | %d | %s | %s |" % (name, want, got, verdict, note))
    npass = sum(1 for r in results if r[3] == "PASS")
    lines.append("")
    lines.append("合计 %d 例，PASS %d，FAIL %d" % (len(results), npass, len(results) - npass))
    with open(os.path.join(EVID, "扰动矩阵.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n[done] %d cases, PASS %d, FAIL %d" % (len(results), npass, len(results) - npass))
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
