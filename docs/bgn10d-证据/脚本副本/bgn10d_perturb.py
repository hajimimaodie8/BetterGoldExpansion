# -*- coding: utf-8 -*-
"""bg-n10d 扰动矩阵：每个用例跑完**逐字节复原**并复核 SHA256。

用例（全部只碰本轮自己的文件；不碰别的会话的在制品）：
  ① 把 tremble.png 换回改前那张  ⇒ validate_metal_assets / validate_bg17_textures 都必须 exit 1
  ② 删掉 chicken_food.json        ⇒ validate_metal_data 必须 exit 1
  ③ chicken_food 里混进别的物品    ⇒ validate_metal_data 必须 exit 1
  ④ 把种子塞进无关标签 axes.json   ⇒ validate_metal_data 必须 exit 1
  ⑤a 把真实注册行**注释掉**（针只在注释里）⇒ validate_metal_assets 必须 exit 1（证明针不去注释就假绿）
  ⑤b **只加一行注释**（含登记字样的注释）  ⇒ 两关卡仍 exit 0（只改注释必须仍绿）

运行：py -3 docs/bgn10d-证据/scripts/bgn10d_perturb.py
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOOLS = os.path.join(ROOT, "tools", "asset-generator")
PY = sys.executable

TREMBLE = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "textures",
                       "mob_effect", "tremble.png")
TREMBLE_OLD = os.path.join(ROOT, "docs", "bgn10d-证据", "12-颤栗贴图对比",
                           "tremble.png.before-82db54af.png")
TAGDIR = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft", "tags", "item")
CHICKEN = os.path.join(TAGDIR, "chicken_food.json")
AXES = os.path.join(TAGDIR, "axes.json")
EFFECTS = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "registry",
                       "AllEffects.java")

VAL_ASSETS = os.path.join(TOOLS, "validate_metal_assets.py")
VAL_BG17 = os.path.join(TOOLS, "validate_bg17_textures.py")
VAL_DATA = os.path.join(TOOLS, "validate_metal_data.py")


def sha(path):
    if not os.path.exists(path):
        return "<missing>"          # 用例②会临时删文件，这里必须容忍"文件不存在"
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run(script):
    p = subprocess.run([PY, script], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def hits(out, needles):
    found = []
    for n in needles:
        if n in out:
            found.append(n)
    return found


class Case(object):
    def __init__(self, name, note):
        self.name = name
        self.note = note
        self.saved = {}          # path -> original bytes

    def __enter__(self):
        return self

    def backup(self, path):
        if path not in self.saved:
            self.saved[path] = open(path, "rb").read()
        return self.saved[path]

    def restore_all(self):
        bad = []
        for path, data in self.saved.items():
            with open(path, "wb") as f:
                f.write(data)
            now = open(path, "rb").read()
            if now != data:
                bad.append(path)
        return bad


RESULTS = []


def check_case(name, note, steps, expect, needles, prepare):
    case = Case(name, note)
    ok_before = {}
    try:
        # 先记"改前"的 SHA（复原后要逐字节一致）
        for p in steps:
            case.backup(p)
            ok_before[p] = sha(p)
        prepare(case)
        # 改后哈希必须真的变了（否则这一轮扰动是空转）
        changed = [p for p in steps if sha(p) != ok_before[p]]
        verdicts = []
        for script, want_rc in expect:
            rc, out = run(script)
            verdicts.append((os.path.basename(script), rc, want_rc, hits(out, needles)))
        RESULTS.append((name, note, changed, verdicts))
    finally:
        bad = case.restore_all()
        after = {p: sha(p) for p in steps}
        RESULTS.append((name + " :: 复原", "逐字节复原校验",
                        ["MISMATCH:" + p for p in bad] or ["all-restored"],
                        [("sha256 一致", 0, 0, [p for p in steps if after[p] != ok_before[p]])]))


def main():
    # ---------- ① 把 tremble.png 换回改前那张 ----------
    def prep1(case):
        case.backup(TREMBLE)
        shutil.copyfile(TREMBLE_OLD, TREMBLE)

    check_case("① 回退 tremble.png", "换回改前 82db54af… 那张",
               [TREMBLE],
               [(VAL_ASSETS, 1), (VAL_BG17, 1)],
               ["bgn10d-tremble-sha", "bgn10d-tremble-revert",
                "bg17tex-revert", "bg17tex-auth6-fail"],
               prep1)

    # ---------- ② 删掉 chicken_food.json ----------
    def prep2(case):
        case.backup(CHICKEN)
        os.remove(CHICKEN)

    check_case("② 删 chicken_food.json", "4 条里少一条",
               [CHICKEN],
               [(VAL_DATA, 1)],
               ["bgn10d-seed-tags-missing"],
               prep2)

    # ---------- ③ 混进别的本模组物品 ----------
    def prep3(case):
        case.backup(CHICKEN)
        obj = json.loads(open(CHICKEN, encoding="utf-8").read())
        obj["values"].append("bettergold:chaos_coin")
        with open(CHICKEN, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

    check_case("③ chicken_food 混进别的物品", "values 里多一条 bettergold:chaos_coin",
               [CHICKEN],
               [(VAL_DATA, 1)],
               ["bgn10d-seed-tags-extra"],
               prep3)

    # ---------- ④ 把种子塞进无关标签 ----------
    def prep4(case):
        case.backup(AXES)
        obj = json.loads(open(AXES, encoding="utf-8").read())
        obj["values"].append("bettergold:golden_torchflower_seeds")
        with open(AXES, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

    check_case("④ 种子塞进 axes.json", "不该出现的地方出现一次",
               [AXES],
               [(VAL_DATA, 1)],
               ["bgn10d-seed-tags-scope"],
               prep4)

    # ---------- ⑤a 「针只在注释里」也必须红：从**活的关卡源码**里取出同一个去注释器来证明 ----------
    # ⚠ 这一条刻意**不去改** `AllEffects.java` 的真实注册行（把注册行注释掉会让源码编译不过，
    #   而当时另一个会话正在这个工作树里构建 —— 绝不制造别人的编译错误）。
    #   做法：把 `validate_metal_assets.py` 里那段 `_strip_java_comments` **原样抽出来**再跑
    #   ⇒ 证明的是"关卡用的就是这一个去注释器"，而它对注释里的登记字样确实视而不见。
    src = open(VAL_ASSETS, encoding="utf-8").read()
    m = re.search(r"\ndef _strip_java_comments\(src: str\) -> str:.*?\n(?=_tremble_path)", src, re.S)
    ns = {}
    if not m:
        RESULTS.append(("⑤a 取去注释器", "在关卡源码里找不到 _strip_java_comments",
                        [], [("extract", 1, 0, [])]))
    else:
        exec(m.group(0), ns)                      # noqa: S102  只执行关卡里那一个函数定义
        strip = ns["_strip_java_comments"]
        real = strip(open(EFFECTS, encoding="utf-8").read())
        only_comment = strip(
            'class A {\n'
            '    // EFFECTS.register("tremble", () -> new MobEffect() {}\n'
            '    /* EFFECTS.register("tremble", () -> new MobEffect() {} */\n'
            '    static void x() {}\n'
            '}\n')
        s_ok = 'EFFECTS.register("tremble"' in real
        c_ok = 'EFFECTS.register("tremble"' not in only_comment
        RESULTS.append(("⑤a 去注释器（同一份实现）", "真实文件里有针 / 只写在注释里就没有针",
                        ["real_has_needle=%s" % s_ok, "comment_only_has_needle=%s" % (not c_ok)],
                        [("⑤a", 0 if (s_ok and c_ok) else 1, 0, ["real", "comment-only"])]))

    # ---------- ⑤b 只加一行注释（不改代码）----------
    def prep5b(case):
        case.backup(EFFECTS)
        b = open(EFFECTS, "rb").read()
        anchor = b'    public static final DeferredHolder<MobEffect, MobEffect> TREMBLE ='
        assert b.count(anchor) == 1, "锚点不唯一"
        ins = (b'    // bgn10d \xe5\x8f\xaa\xe6\x94\xb9\xe6\xb3\xa8\xe9\x87\x8a\xe7\x94\xa8\xe4\xbe\x8b'
               b'\xef\xbc\x9a\xe8\xbf\x99\xe9\x87\x8c\xe5\x86\x99 EFFECTS.register("tremble" '
               b'\xe4\xb9\x9f\xe4\xb8\x8d\xe8\xaf\xa5\xe8\xae\xa9\xe5\x85\xb3\xe5\x8d\xa1\xe5\x8f\x98\xe7\xbb\xbf\n')
        open(EFFECTS, "wb").write(b.replace(anchor, ins + anchor))

    check_case("⑤b 只加一行注释", "注释里写登记字样，两关卡仍须绿",
               [EFFECTS],
               [(VAL_ASSETS, 0), (VAL_BG17, 0)],
               [],
               prep5b)

    print("=" * 100)
    all_ok = True
    for name, note, changed, verdicts in RESULTS:
        line = "[{0}] {1} :: {2}".format(name, note, ",".join(changed) if changed else "-")
        print(line)
        for s, rc, want, hs in verdicts:
            flag = "OK " if rc == want and (want == 0 or hs) else "BAD"
            if flag == "BAD":
                all_ok = False
            print("    {0} {1} exit={2} 期望={3} 命中={4}".format(flag, s, rc, want, hs or "-"))
    print("=" * 100)
    print("[bgn10d-perturb] {0}".format("ALL CASES OK" if all_ok else "SOME CASES BAD"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
