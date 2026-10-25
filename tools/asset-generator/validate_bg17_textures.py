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
  [bg17tex-auth6]                    1.7 bg-n10d 裁定 #12「第六次授权」：tremble.png 后加替换
  [bg17tex-auth6-anchor]             该行在 manifest 里仍是 untouched（第五次授权快照没被改）
  [bg18tex-auth] <path>              第七次授权（bg18 P5）：逐张 SHA == 钉住的归档件
  [bg18tex-auth-fail] <path>         某张与钉住的改后 SHA 不符
  [bg18tex-revert] <path>            某张等于改前 SHA（被回退了，反空转）
  [bg18tex-anchor]                   manifest 身份对不上 / 跳过的行数不对
  [bg18tex-needle-model]             7 张（3 方块 + 锭 + 模板 + 2 曲奇）仍被模型 JSON 引用
  [bg18tex-needle-gui]               主面板 + 错误图标两个路径仍在去注释的 Java 里
  [bg18tex-needle-trim]              纹饰 JSON 的 asset_name=chaosgold（色卡换名就红）
  [bg18tex-anti-vacuum]              AUTH7 条数不是 10
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

# ==================== 1.7 bg-n10d（2026-10-18，裁定 #12）：第六次贴图授权 ====================
# manifest 是**第五次授权那一刻**的 626 张快照（72 `authorized` + 554 `untouched`），其中
#   `mob_effect/tremble.png` 被记为 `untouched`。作者 2026-10-18 另外授权替换了这一张
#   （原话「第 12 条，你可以看看备份，然后替换掉」）⇒ **不改 manifest**（保住第五次授权的 72/554 口径，
#   否则"72 张"这个证据就再也无法复算），而是把这一行读成「后加的单独授权」，在这里单独判：
#   ① 内容 = 归档那一张（`validate_metal_assets.py` 的 `[bgn10d-tremble-*]` 是主锚点）；
#   ② **反回退**：不许等于改前那张；
#   ③ manifest 里这一行必须仍是 `untouched` 单行 —— 有人删/改它，`[bg17tex-auth6-anchor]` 当场红。
LATER_AUTH = {
    "mob_effect/tremble.png": (
        "2f912961e4ed5a4337a6f81b911575b169e97172a81e7ee194653ba5fd9ce768",  # 改后（授权件）
        "82db54af5f9de098203cd26e42e3922f46335b09c014609830f7b91fe83be422",  # 改前（反回退）
    ),
}

# ==================== 1.7 bg18（2026-10-25，P5）：第七次贴图授权 ====================
# 作者交付 `E:\mc\mc资料\1.7的贴图更新包第二关.zip`（10 张，**文件名有 8 个是数字**）。
# 认亲方法 = 同尺寸 + 像素相似度（`docs\bg18-证据\05-P5-认亲\`），逐张 1:1 字节复制；
# 认亲表 + 改前/改后全树快照在 `docs\bg18-证据\06-P5-替换\`。
#
# ⚠ 与第五、六次授权的关系：manifest 仍是**第五次授权那一刻**的 626 行快照（72 authorized +
#   554 untouched），这 10 张在里面全都是 `untouched`。这里**不改 manifest**（保住 72/554 可复算），
#   把它们读成「后加的单独授权」，逐张判：① SHA == 归档件 ② **!= 改前**（反回退）
#   ③ manifest 里必须仍是 untouched 单行（身份）；另加「8 条模型 needle + 2 条 Java/JSON needle」。
#
# 归属（作者点名四类）与**与字面的偏差**：
#   1 万坚金砧 GUI 主面板（gui/container/sturdygold_anvil.png，256×256，与原图同尺寸）
#   2 万坚金砧 错误图标（gui/sprites/container/sturdygold_anvil/error.png，28×21 = 507 像素
#     **逐像素等于新 256×256 的 (99,45)-(126,65)** + 81 个红叉像素 ⇒ 就是那张精灵）
#   3 巧克力曲奇 ×2（sturdygold / golden）
#   4 混沌金纹饰色卡（8×1）
#   5 ★「部分烈燃金」：作者点名写的是 `item/flamegold_*`，但像素认亲的结论是
#     **3 张方块（bricks / pillar / block）+ 1 张锭 + 1 张升级模板**（bricks/pillar/block 的
#     MAE 0.020–0.097、类内次优差 76–335 倍；与 item/ 下任何一张的 MAE 都 >= 27）。
#     ⇒ 按像素事实落 `block/flamegold_*` 三张，与点名分类的字面不符，已在 docs 记账（不猜、不硬塞）。
AUTH7 = {
    # 路径: (改后 SHA256 = zip 内条目 SHA256, 改前 SHA256)
    "gui/container/sturdygold_anvil.png":
        ("debe8cfc08707bb71d534dbd11876f83c2b5fdd1bf7009626d08f1812ad454b2",
         "24a277b99da860b9c012a1a68d3994648fca5466407be4eb61e70e6ba0e5625c"),
    "gui/sprites/container/sturdygold_anvil/error.png":
        ("b0c8aa737917bc39058a5b402b92bca294e90586b0e663be5daa05a7d14c21c3",
         "dcbac5908d8fec564db718860a3b39623e7ffebea6f19c2fb705ac0bcad1a989"),
    "block/flamegold_bricks.png":
        ("07fc4dd08e8a915e9b72bc03c38659a53d294f2a8219daae4a8bad12269081f3",
         "c590410b4c4193257decea647177e9247ebc421b7571175a047656a3ecaba510"),
    "block/flamegold_pillar.png":
        ("cce4d39ab696300be4f2ce86f8c00ec06ef5658f07da6326f09878fc19c9ce37",
         "3140f403f8fe39cee3ed83b26006518a44b75fdf020721fdd963fa304bea50ab"),
    "block/flamegold_block.png":
        ("69c3932960c92db156c548e5df601833e90b2797d442de58586de23c75b8d12f",
         "5b808d633bb85fa71afac79b6f985d8b881cb82837e80f48a8362ff6f11a6506"),
    "item/flamegold_ingot.png":
        ("616c80b5118025433768c3c24ecc90b80d876bfb0c4147d7db23b55902a932de",
         "2db942543746951a6840c19dceba408bcf441cd66c0885fc066ab5c2b32978d3"),
    "item/flamegold_upgrade_template.png":
        ("5e7c5d1ed9704bc06fd01e15ad8094fa39959dcee10876a80ca3ffad74d3cf36",
         "505964c6a7f304c2bf3ec3c2c81e92246e377d65b211fc747d7f3f8f89799621"),
    "item/sturdygold_chocolate_cookie.png":
        ("fe1814285bb8859526859c9851a5fbd7a0bc55d2203d8ac9a7764c3571a58973",
         "d74e24d31fa93d0196063ee8de53863fc012bb2014154bc287e367bbbdf73819"),
    "item/golden_chocolate_cookie.png":
        ("ec099054be279213e289378d4aa25c9b2927ed252b13a404bbe726f9ff4fbbd3",
         "5c1ac52bc09e54c30aa36e8581da081fd553bc952ab927dad55e06f6c5ffb333"),
    "trims/color_palettes/chaosgold.png":
        ("25e9d4b7ff72814e970ddeca4601e2adfb0ab17b4fb249e838e9c9e13671b8e4",
         "75587687ca69f5f24b2c0a09824950788c36a5acacc93804372ef2cceabf5416"),
}
EXPECT_AUTH7 = 10
# 认亲表（机读版）：`zip 文件名 -> 目标 -> 改前/改后 SHA256` 10 行。
# 关卡逐行比对 AUTH7；**删一行 ⇒ 行数不对 ⇒ 红**（这就是「删认亲表一行」那条扰动）。
AUTH7_TSV = os.path.join(BASE, "tools", "asset-generator", "bg18tex_auth.tsv")
# ⚠ 这 1 张**不在**第五次授权的 626 行快照里：`gui/sprites/container/sturdygold_anvil/error.png`
#   是 bg-n10err（2026-10-18）**新建**的精灵（作者贴图区域 + 原版红叉拼出来），
#   所以 manifest 里查不到它 —— 这里显式声明「缺席」，而不是把它当成身份对不上。
AUTH7_MANIFEST_ABSENT = {"gui/sprites/container/sturdygold_anvil/error.png"}


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


def load_auth7_tsv():
    """bg18 第七次授权的认亲表（10 行）。"""
    if not os.path.exists(AUTH7_TSV):
        return None
    rows = []
    with open(AUTH7_TSV, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            rows.append(dict(zip(hdr, line.split("\t"))))
    return rows


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

    # ---- ② 其余 554 张：负向断言（其中 `LATER_AUTH` / `AUTH7` 的那几张走 ②-b / ②-c 单独判） ----
    un_ok = 0
    later_skipped = 0
    auth7_skipped = 0
    for r in untouched:
        if r["path"] in LATER_AUTH:
            later_skipped += 1     # 交给 ②-b；总数不算丢，见下面的身份断言
            continue
        if r["path"] in AUTH7:
            auth7_skipped += 1     # 交给 ②-c
            continue
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

    # ---- ②-b 第六次授权（后加）：manifest 里记为 untouched 的那一张，单独判 SHA + 反回退 ----
    later_ok = 0
    for rel, (want, old_sha) in sorted(LATER_AUTH.items()):
        rows_hit = [r for r in rows if r["path"] == rel]
        if len(rows_hit) != 1 or rows_hit[0]["role"] != "untouched":
            P.add("bg17tex-auth6-anchor",
                  rel + " 在 manifest 里不再是 untouched 单行（第五次授权快照被改）")
        p = os.path.join(TEX, rel.replace("/", os.sep))
        checked += 1
        if not os.path.exists(p):
            P.add("bg17tex-auth6-fail", "missing file " + rel)
            continue
        s = sha(p)
        if s == old_sha:
            P.add("bg17tex-revert", rel + " 等于改前那张（#12 的替换被回退了）")
            continue
        if s != want:
            P.add("bg17tex-auth6-fail", rel + " sha mismatch")
            continue
        later_ok += 1
        sys.stdout.write("[bg17tex-auth6] ok {0} sha256={1}\n".format(rel, s))
    if later_skipped != len(LATER_AUTH):
        P.add("bg17tex-auth6-anchor",
              "被跳过的 untouched 行 {0} != LATER_AUTH {1}（身份对不上）".format(
                  later_skipped, len(LATER_AUTH)))

    # ---- ②-c 第七次授权（bg18 P5）：10 张，逐张 SHA + 反回退 + manifest 身份 ----
    auth7_ok = 0
    if len(AUTH7) != EXPECT_AUTH7:
        P.add("bg18tex-anti-vacuum", "AUTH7 条数 {0} != {1}".format(len(AUTH7), EXPECT_AUTH7))
    for rel, (want, old_sha) in sorted(AUTH7.items()):
        rows_hit = [r for r in rows if r["path"] == rel]
        if rel in AUTH7_MANIFEST_ABSENT:
            if rows_hit:
                P.add("bg18tex-anchor",
                      rel + " 应在 manifest 之外（bg-n10err 新建），却出现在快照里")
        elif len(rows_hit) != 1 or rows_hit[0]["role"] != "untouched":
            P.add("bg18tex-anchor",
                  rel + " 在 manifest 里不再是 untouched 单行（第五次授权快照被改）")
        p = os.path.join(TEX, rel.replace("/", os.sep))
        checked += 1
        if not os.path.exists(p):
            P.add("bg18tex-auth-fail", "missing file " + rel)
            continue
        s = sha(p)
        if s == old_sha:
            P.add("bg18tex-revert", rel + " 等于改前那张（bg18 的替换被回退了）")
            continue
        if s != want:
            P.add("bg18tex-auth-fail", rel + " sha mismatch")
            continue
        auth7_ok += 1
        sys.stdout.write("[bg18tex-auth] ok {0} sha256={1}\n".format(rel, s))
    if auth7_skipped != len(AUTH7) - len(AUTH7_MANIFEST_ABSENT):
        P.add("bg18tex-anchor",
              "被跳过的 untouched 行 {0} != AUTH7 {1}（身份对不上）".format(
                  auth7_skipped, len(AUTH7) - len(AUTH7_MANIFEST_ABSENT)))
    # ---- ②-d 认亲表逐行比对（删一行 / 改一个 SHA 都红） ----
    tsv_rows = load_auth7_tsv()
    if tsv_rows is None:
        P.add("bg18tex-manifest-fail", "missing tools/asset-generator/bg18tex_auth.tsv")
    elif len(tsv_rows) != EXPECT_AUTH7:
        P.add("bg18tex-manifest-fail",
              "认亲表行数 {0} != {1}（删了一行就会红）".format(len(tsv_rows), EXPECT_AUTH7))
    else:
        hit = 0
        for r in tsv_rows:
            rel = r.get("path", "")
            ent = AUTH7.get(rel)
            checked += 1
            if ent is None:
                P.add("bg18tex-manifest-fail", "认亲表里有未知目标 " + rel)
                continue
            if r.get("sha256_new") != ent[0] or r.get("sha256_old") != ent[1]:
                P.add("bg18tex-manifest-fail", "认亲表 SHA 与代码锚点不一致 " + rel)
                continue
            hit += 1
        if hit != EXPECT_AUTH7:
            P.add("bg18tex-manifest-fail",
                  "认亲表与代码锚点只对上 {0} 行（期望 {1}）".format(hit, EXPECT_AUTH7))
        sys.stdout.write("[bg18tex-manifest] ok {0} rows match code anchors\n".format(hit))
    # 7 张里 5 张（3 方块 + 锭 + 模板）与 2 张曲奇 = item/block；色卡 + GUI 走另外的 needle。
    _b18_model = [rel for rel in AUTH7
                  if rel.startswith("block/") or rel.startswith("item/")]
    if len(_b18_model) != 7:
        P.add("bg18tex-needle-model-fail",
              "走模型 needle 的应有 7 张（3 方块 + 锭 + 模板 + 2 曲奇），实际 {0}".format(len(_b18_model)))

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

    # ---- ⑥ bg18 第七次授权（10 张）的正向 needle：模型 7 + Java 2 + 纹饰 JSON 1 ----
    b18_need_ok = 0
    for rel in _b18_model:
        nd = "bettergold:" + rel[:-4]
        if nd in blob:
            b18_need_ok += 1
        else:
            P.add("bg18tex-needle-model-fail", "no model references " + nd)
    sys.stdout.write("[bg18tex-needle-model] ok {0} of {1}（三张方块 + 锭 + 模板 + 两张曲奇）\n"
                     .format(b18_need_ok, len(_b18_model)))

    # GUI 的两张：正向 needle 跑在**去注释**的 `SturdygoldAnvilScreen.java` 上
    GUI_SRC = os.path.join(BASE, "src", "main", "java", "com", "hjmmd_8", "bettergold",
                           "client", "SturdygoldAnvilScreen.java")
    if not os.path.exists(GUI_SRC):
        P.add("bg18tex-needle-gui-fail", "SturdygoldAnvilScreen.java missing")
    else:
        gsrc = strip_java_comments(open(GUI_SRC, encoding="utf-8", errors="replace").read())
        checked += 1
        gneed = ["textures/gui/container/sturdygold_anvil.png", "container/sturdygold_anvil/error"]
        ghit = [x for x in gneed if x in gsrc]
        if len(ghit) != len(gneed):
            P.add("bg18tex-needle-gui-fail", "GUI needle missing on comment-stripped source")
        else:
            sys.stdout.write("[bg18tex-needle-gui] ok 主面板 + 错误图标两处引用都在（去注释源码）\n")

    # 色卡：正向 needle = 纹饰材质 JSON 的 asset_name（它决定 color_palettes/<asset>.png）
    TRIM_JSON = os.path.join(BASE, "src", "main", "resources", "data", "bettergold",
                             "trim_material", "chaosgold.json")
    if not os.path.exists(TRIM_JSON):
        P.add("bg18tex-needle-trim-fail", "trim_material/chaosgold.json missing")
    else:
        checked += 1
        tjs = open(TRIM_JSON, encoding="utf-8").read()
        if '"asset_name": "chaosgold"' in tjs:
            sys.stdout.write("[bg18tex-needle-trim] ok asset_name=chaosgold -> color_palettes/chaosgold.png\n")
        else:
            P.add("bg18tex-needle-trim-fail", "asset_name 不是 chaosgold（色卡换了名就对不上）")

    # ---- 汇总 ----
    sys.stdout.write("[bg17tex-auth] ok {0} of {1}\n".format(auth_ok, EXPECT_AUTH))
    # ⚠ bg-n10d 就地标注（旧形态原文留档、未删）：
    #   `sys.stdout.write("[bg17tex-untouched] ok {0} of {1}\n".format(un_ok, EXPECT_UNTOUCHED))`
    #   —— 现在分母要减去"后加授权"的那几张（本轮 1 张），否则 553/554 看起来像少查了一张。
    # ⚠ bg18 就地标注（旧分母 `EXPECT_UNTOUCHED - len(LATER_AUTH)` 原文留档、未删）：
    #   第七次授权又从 untouched 里拿走 9 张（error.png 本来就不在快照里）⇒ 分母再减这 9 张。
    sys.stdout.write("[bg17tex-untouched] ok {0} of {1}\n"
                     .format(un_ok, EXPECT_UNTOUCHED - len(LATER_AUTH)
                             - (len(AUTH7) - len(AUTH7_MANIFEST_ABSENT))))
    sys.stdout.write("[bg17tex-auth6] ok {0} of {1}（第五次授权之外、作者 #12 另批的那一张）\n"
                     .format(later_ok, len(LATER_AUTH)))
    sys.stdout.write("[bg18tex-auth7] ok {0} of {1}（第七次授权：1.7 贴图更新包第二关）\n"
                     .format(auth7_ok, EXPECT_AUTH7))
    # 身份断言：554 = 未动 + 第六次 1 + 第七次里有 manifest 的那 9 张
    #（第七次的 error.png 是 bg-n10err 新建、不在快照里，所以要从 auth7 里减掉）
    if un_ok + later_ok + (auth7_ok - len(AUTH7_MANIFEST_ABSENT)) != EXPECT_UNTOUCHED:
        P.add("bg18tex-anchor",
              "untouched 身份对不上：{0} + {1} + {2} != {3}".format(
                  un_ok, later_ok, auth7_ok - len(AUTH7_MANIFEST_ABSENT), EXPECT_UNTOUCHED))
    if auth7_ok != EXPECT_AUTH7:
        P.add("bg18tex-anti-vacuum", "AUTH7 通过 {0} != {1}".format(auth7_ok, EXPECT_AUTH7))
    sys.stdout.write("[bg17tex-summary] checked={0} authorized={1} untouched={2} modelrefs={3} "
                     "auth7={4} problems={5}\n"
                     .format(checked, auth_ok, un_ok, ref_ok, auth7_ok, len(P.items)))

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
