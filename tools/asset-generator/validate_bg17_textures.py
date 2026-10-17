# -*- coding: utf-8 -*-
"""bg17tex 关卡：1.7 贴图更新包（第五次授权）替换结果的不变量检查。

退出码契约（与 tools/asset-generator 其余六个校验器统一）：
  0 = 全绿
  1 = 有「问题」（贴图与钉住的 SHA256 不符 / 被回退 / 模型引用丢失 / 锚点被动）
  2 = 基线被破坏 / 前置缺失 / 脚本自身出错 / 实际检查项数 = 0（反空转）

稳定 ASCII 结论码：
  [bg17tex-ok]                       总体绿灯
  [bg17tex-auth]                     72 张授权替换逐张通过
  [bg17tex-auth-fail] <path>         某张与钉住的改后 SHA 不符
  [bg17tex-revert] <path>            某张等于改前 SHA（被回退了，反空转）
  [bg17tex-untouched-fail] <path>    未授权贴图被改动（负向断言）
  [bg16-authorized-blank-texture]    golden_trident_blank.png 既有锚点未动
  [bgfinal3-indigosea-sha]           indigoseagold.png 既有锚点未动
  [bgfinal3-indigosea-not-quartz]    该色卡不是白灰阶（负向）
  [bg17tex-model-ref]                被替换贴图仍被模型 JSON 引用（正向 needle）
  [bg17tex-needle-src]               盔甲层命名约定仍在（正向 needle，跑在去注释源码上）
  [bg17tex-summary]                  计数行
"""
import sys, os, json, hashlib

sys.stdout.reconfigure(errors="replace")
sys.stderr.reconfigure(errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
MODELS = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "models")
JAVA = os.path.join(BASE, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material", "MetalFamily.java")
MANIFEST = os.path.join(BASE, "tools", "asset-generator", "bg17tex_manifest.tsv")
OLD_SHA = os.path.join(BASE, "tools", "asset-generator", "bg17tex_old_sha.tsv")

# 既有 SHA 锚点（AGENTS.md 第 6 条第一、三次授权）
ANCHORS = {
    "item/golden_trident_blank.png": (
        "73e4df0f098dced43d43f8529a7aa07c702e63e5aacd70d99a25fdfbb1e6f5b6",
        "bg16-authorized-blank-texture"),
    "trims/color_palettes/indigoseagold.png": (
        "9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d",
        "bgfinal3-indigosea-sha"),
}

EXPECT_AUTH = 72
EXPECT_UNTOUCHED = 554
EXPECT_TOTAL = 626


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def strip_java_comments(src):
    """去掉 // 行注释与 /* */ 块注释，字符串/字符字面量原样保留。"""
    out = []
    i, n = 0, len(src)
    state = "code"     # code | line | block | str | chr
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if state == "code":
            if two == "//":
                state = "line"
                i += 2
                continue
            if two == "/*":
                state = "block"
                i += 2
                continue
            if c == '"':
                state = "str"
            elif c == "'":
                state = "chr"
            out.append(c)
            i += 1
            continue
        if state == "line":
            if c == "\n":
                state = "code"
                out.append(c)
            i += 1
            continue
        if state == "block":
            if two == "*/":
                state = "code"
                i += 2
                continue
            i += 1
            continue
        if state == "str":
            if c == "\\":
                out.append(src[i:i + 2])
                i += 2
                continue
            if c == '"':
                state = "code"
            out.append(c)
            i += 1
            continue
        if state == "chr":
            if c == "\\":
                out.append(src[i:i + 2])
                i += 2
                continue
            if c == "'":
                state = "code"
            out.append(c)
            i += 1
            continue
    return "".join(out)


class Problems(object):
    def __init__(self):
        self.items = []

    def add(self, code, detail=""):
        self.items.append((code, detail))


def load_manifest():
    if not os.path.exists(MANIFEST):
        return None
    rows = []
    with open(MANIFEST, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            rows.append(dict(zip(hdr, line.split("\t"))))
    return rows


def load_old():
    if not os.path.exists(OLD_SHA):
        return None
    d = {}
    with open(OLD_SHA, encoding="utf-8") as f:
        f.readline()
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            k, v = line.split("\t")
            d[k] = v
    return d


def main():
    P = Problems()
    checked = 0

    rows = load_manifest()
    old = load_old()
    if rows is None or old is None or not os.path.isdir(TEX):
        sys.stdout.write("[bg17tex-summary] checked=0 authorized=0 untouched=0 modelrefs=0 problems=1\n")
        sys.stderr.write("[bg17tex-prereq-fail] manifest or textures dir missing\n")
        return 2
    if len(rows) != EXPECT_TOTAL:
        sys.stdout.write("[bg17tex-summary] checked=0 authorized=0 untouched=0 modelrefs=0 problems=1\n")
        sys.stderr.write("[bg17tex-prereq-fail] manifest rows {0} != {1}\n".format(len(rows), EXPECT_TOTAL))
        return 2

    auth = [r for r in rows if r["role"] == "authorized"]
    untouched = [r for r in rows if r["role"] == "untouched"]
    if len(auth) != EXPECT_AUTH or len(untouched) != EXPECT_UNTOUCHED:
        sys.stdout.write("[bg17tex-summary] checked=0 authorized=0 untouched=0 modelrefs=0 problems=1\n")
        sys.stderr.write("[bg17tex-prereq-fail] role split {0}/{1} != {2}/{3}\n".format(
            len(auth), len(untouched), EXPECT_AUTH, EXPECT_UNTOUCHED))
        return 2

    # ---- ① 72 张授权替换：SHA == 钉住的改后 SHA，且 != 改前 SHA ----
    auth_ok = 0
    for r in auth:
        p = os.path.join(TEX, r["path"].replace("/", os.sep))
        if not os.path.exists(p):
            P.add("bg17tex-auth-fail", "missing file " + r["path"])
            checked += 1
            continue
        s = sha(p)
        checked += 1
        if s != r["sha256"]:
            P.add("bg17tex-auth-fail", r["path"] + " sha mismatch")
            continue
        if r["path"] in old and s == old[r["path"]]:
            P.add("bg17tex-revert", r["path"] + " equals pre-round sha")
            continue
        auth_ok += 1

    # ---- ② 其余 554 张：负向断言 ----
    un_ok = 0
    for r in untouched:
        p = os.path.join(TEX, r["path"].replace("/", os.sep))
        if not os.path.exists(p):
            P.add("bg17tex-untouched-fail", "missing file " + r["path"])
            checked += 1
            continue
        s = sha(p)
        checked += 1
        if s != r["sha256"]:
            P.add("bg17tex-untouched-fail", r["path"] + " changed but not authorized")
            continue
        un_ok += 1

    # ---- ③ 两条既有锚点 ----
    anchor_ok = 0
    for rel, (want, code) in ANCHORS.items():
        p = os.path.join(TEX, rel.replace("/", os.sep))
        if not os.path.exists(p):
            P.add(code + "-fail", "missing anchor " + rel)
            continue
        checked += 1
        if sha(p) == want:
            anchor_ok += 1
            sys.stdout.write("[{0}] ok {1}\n".format(code, rel))
        else:
            P.add(code + "-fail", rel + " anchor sha moved")

    # 色卡负向：不是白灰阶
    indigo = os.path.join(TEX, "trims", "color_palettes", "indigoseagold.png")
    if os.path.exists(indigo):
        try:
            from PIL import Image
            im = Image.open(indigo).convert("RGBA")
            raw = im.tobytes()
            px = [raw[i:i + 4] for i in range(0, len(raw), 4)]
            grey = sum(1 for q in px if q[0] == q[1] == q[2])
            checked += 1
            if grey == len(px):
                P.add("bgfinal3-indigosea-not-quartz-fail", "palette is fully grey")
            else:
                sys.stdout.write("[bgfinal3-indigosea-not-quartz] ok coloured {} of {} px\n".format(
                    len(px) - grey, len(px)))
        except Exception as e:
            P.add("bgfinal3-indigosea-not-quartz-fail", "cannot read palette: " + str(e))

    # ---- ④ 正向 needle：被替换贴图仍被模型 JSON 引用 ----
    needles = set()
    for r in auth:
        if r["path"].startswith("models/armor/"):
            continue                      # 盔甲层由 ArmorMaterial 资产 id 解析，不走 JSON
        needles.add("bettergold:" + r["path"][:-4])
    corpus = []
    if os.path.isdir(MODELS):
        for dp, dn, fn in os.walk(MODELS):
            for f in fn:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(dp, f), encoding="utf-8") as fh:
                            txt = fh.read()
                    except Exception:
                        continue
                    # MC 模型 JSON 通常无注释；这里仍按"去注释"口径剥掉 // 行注释，
                    # 避免把注释里的 id 当成引用（假绿）
                    corpus.append("\n".join(l for l in txt.splitlines()
                                            if not l.lstrip().startswith("//")))
    blob = "\n".join(corpus)
    if not corpus:
        P.add("bg17tex-model-ref-fail", "no model json found")
    ref_ok = 0
    for nd in sorted(needles):
        if nd in blob:
            ref_ok += 1
        else:
            P.add("bg17tex-model-ref-fail", "no model references " + nd)
    sys.stdout.write("[bg17tex-model-ref] ok {0} of {1} replaced textures still referenced by model json\n"
                     .format(ref_ok, len(needles)))

    # ---- ⑤ 正向 needle 跑在「去注释源码」上 ----
    if not os.path.exists(JAVA):
        P.add("bg17tex-needle-src-fail", "MetalFamily.java missing")
    else:
        raw = open(JAVA, encoding="utf-8", errors="replace").read()
        stripped = strip_java_comments(raw)
        removed = len(raw) - len(stripped)
        checked += 1
        if removed <= 0:
            P.add("bg17tex-needle-src-fail", "comment stripping removed nothing")
        need = ["ArmorMaterial.Layer", "ResourceLocation.fromNamespaceAndPath(bettergold.MODID, this.id)"]
        hit = [x for x in need if x in stripped]
        if len(hit) != len(need):
            P.add("bg17tex-needle-src-fail", "needle missing on comment-stripped source")
        else:
            sys.stdout.write("[bg17tex-needle-src] ok armour layer convention present on stripped source "
                             "(stripped bytes {0})\n".format(removed))

    # ---- 汇总 ----
    sys.stdout.write("[bg17tex-auth] ok {0} of {1}\n".format(auth_ok, EXPECT_AUTH))
    sys.stdout.write("[bg17tex-untouched] ok {0} of {1}\n".format(un_ok, EXPECT_UNTOUCHED))
    sys.stdout.write("[bg17tex-summary] checked={0} authorized={1} untouched={2} modelrefs={3} problems={4}\n"
                     .format(checked, auth_ok, un_ok, ref_ok, len(P.items)))

    if checked == 0:
        sys.stderr.write("[bg17tex-prereq-fail] zero checks executed\n")
        return 2
    if checked < EXPECT_TOTAL:
        sys.stderr.write("[bg17tex-prereq-fail] checked {0} below expected {1}\n".format(checked, EXPECT_TOTAL))
        return 2
    if P.items:
        for code, detail in P.items[:40]:
            sys.stderr.write("[{0}] {1}\n".format(code, detail))
        sys.stderr.write("[bg17tex-fail] problems={0}\n".format(len(P.items)))
        return 1
    sys.stdout.write("[bg17tex-ok] all invariants hold\n")
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write("[bg17tex-prereq-fail] uncaught exception: {0}\n".format(exc))
        rc = 2
    sys.exit(rc)
