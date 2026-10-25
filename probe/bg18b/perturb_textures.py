# -*- coding: utf-8 -*-
"""bg18b · P5 贴图关卡的扰动矩阵（每例都逐字节复原 + SHA256 复核）。

用例：
  P0 基线                                                          want 0
  P1 把一张**授权**贴图覆盖成别的字节                                want 1  [bg18tex-auth-fail]
  P2 改一张**没授权**贴图的 1 个字节                                 want 1  [bg17tex-untouched-fail]
  P3 删掉认亲表 `bg18tex_auth.tsv` 的一行                            want 1  [bg18tex-manifest-fail]
  P4 把一张授权贴图回退成**改前**字节                                want 1  [bg18tex-revert]
  P5 只改关卡脚本里的一行注释                                        want 0  （绿）
  P6 把 Java 里的 GUI needle 挪进**注释**（代码里换成别串）          want 1  [bg18tex-needle-gui-fail]
  P7 复原后再跑基线                                                  want 0
"""
import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = os.path.join(BASE, "tools", "asset-generator", "validate_bg17_textures.py")
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
TSV = os.path.join(BASE, "tools", "asset-generator", "bg18tex_auth.tsv")
JAVA = os.path.join(BASE, "src", "main", "java", "com", "hjmmd_8", "bettergold",
                    "client", "SturdygoldAnvilScreen.java")

AUTH = "block/flamegold_bricks.png"
AUTH_REVERT = "item/flamegold_ingot.png"
UNTOUCHED = "block/sturdygold_bricks.png"
PY = sys.executable


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    with open(p, "rb") as f:
        return f.read()


def write(p, b):
    with open(p, "wb") as f:
        f.write(b)


def run_gate():
    r = subprocess.run([PY, "-X", "utf8", GATE], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    results = []
    guards = {}

    def guard(path):
        if path not in guards:
            guards[path] = read(path)
        return guards[path]

    def restore(path):
        write(path, guards[path])
        assert sha(read(path)) == sha(guards[path]), "restore failed " + path

    def case(name, mutate, restore_paths, want_exit, needle):
        for p in restore_paths:
            guard(p)
        try:
            mutate()
            code, out = run_gate()
            hit = (code == want_exit) and (needle in out if needle else True)
            results.append((name, want_exit, code, hit, needle or "-"))
            print("[%s] want=%d got=%d needle=%s %s"
                  % (name, want_exit, code, needle or "-", "PASS" if hit else "FAIL"))
            if not hit:
                tail = "\n".join(out.strip().splitlines()[-6:])
                print("   ---- gate tail ----\n" + tail)
        finally:
            for p in restore_paths:
                restore(p)

    # P0 基线
    code, out = run_gate()
    ok = code == 0
    results.append(("P0 baseline", 0, code, ok, "-"))
    print("[P0 baseline] want=0 got=%d %s" % (code, "PASS" if ok else "FAIL"))

    # P1 授权贴图被覆盖成别的字节
    def m1():
        p = os.path.join(TEX, AUTH.replace("/", os.sep))
        other = os.path.join(TEX, "block", "flamegold_pillar.png")
        write(p, read(other))

    case("P1 authorized-overwritten", m1, [os.path.join(TEX, AUTH.replace("/", os.sep))],
         1, "bg18tex-auth")

    # P2 未授权贴图改 1 个字节
    def m2():
        p = os.path.join(TEX, UNTOUCHED.replace("/", os.sep))
        b = bytearray(read(p))
        b[-1] = (b[-1] + 1) % 256
        write(p, bytes(b))

    case("P2 untouched-1byte", m2, [os.path.join(TEX, UNTOUCHED.replace("/", os.sep))],
         1, "bg17tex-untouched-fail")

    # P3 删认亲表一行
    def m3():
        lines = read(TSV).split(b"\n")
        assert len([l for l in lines if l.strip()]) == 11, "tsv head+10 expected"
        # 删掉第一张数据行
        keep = [lines[0]] + lines[2:]
        write(TSV, b"\n".join(keep))

    case("P3 auth-table-row-deleted", m3, [TSV], 1, "bg18tex-manifest-fail")

    # P4 授权贴图回退成改前字节
    def m4():
        p = os.path.join(TEX, AUTH_REVERT.replace("/", os.sep))
        old = subprocess.run(["git", "show", "HEAD:src/main/resources/assets/bettergold/textures/"
                              + AUTH_REVERT], cwd=BASE, capture_output=True).stdout
        assert old, "git show failed"
        write(p, old)

    case("P4 authorized-reverted-to-old", m4, [os.path.join(TEX, AUTH_REVERT.replace("/", os.sep))],
         1, "bg18tex-revert")

    # P5 只改注释 ⇒ 必须绿
    def m5():
        b = read(GATE)
        write(GATE, b + b"\n# bg18b perturb: comment-only edit, must stay green\n")

    case("P5 comment-only-edit", m5, [GATE], 0, "")

    # P6 GUI needle 只在注释里 ⇒ 必须红（证明 needle 跑在去注释源码上）
    def m6():
        b = read(JAVA).decode("utf-8")
        a = '"textures/gui/container/sturdygold_anvil.png"'
        c = '"container/sturdygold_anvil/error"'
        assert a in b and c in b
        b = b.replace(a, '"textures/gui/container/MOVED_AWAY.png"')
        b = b.replace(c, '"container/MOVED_AWAY/error"')
        b = b.replace("public class SturdygoldAnvilScreen",
                      "// textures/gui/container/sturdygold_anvil.png container/sturdygold_anvil/error\n"
                      "public class SturdygoldAnvilScreen", 1)
        write(JAVA, b.encode("utf-8"))

    case("P6 gui-needle-in-comment-only", m6, [JAVA], 1, "bg18tex-needle-gui-fail")

    # P7 复原后基线
    code, out = run_gate()
    ok = code == 0
    results.append(("P7 baseline-after-restore", 0, code, ok, "-"))
    print("[P7 baseline-after-restore] want=0 got=%d %s" % (code, "PASS" if ok else "FAIL"))

    # 复原自证
    print("\n[restore-sha]")
    for p, b in sorted(guards.items()):
        print("  %s  %s  %s" % (os.path.relpath(p, BASE), sha(read(p)), "same" if read(p) == b else "DIFF"))
    bad = [r for r in results if not r[3]]
    print("\nSUMMARY cases=%d pass=%d fail=%d" % (len(results), len(results) - len(bad), len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
