#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验新生成的三套金属资产：JSON 能否解析 + 模型引用的贴图是否都存在。

==================== 关卡退出码契约（bgfix6，2026-10-08）====================
  0 = 全绿；1 = 有「问题」（下面 10 个问题列表任一非空）；
  2 = 基线被破坏 / 前置缺失 / 脚本自身出错（资产根目录不存在、**JSON 扫描到 0 项**、
      未捕获异常）。★ 任何未捕获异常都不许变成 0；顶层兜底一律转成 2。
  ★ 反空转：必须打印「实际检查了 N 项」并断言 N > 0。
  依据：`docs/构建与跑测注意事项.md`「关卡的退出码契约」；
        `mod_experience\\ex\\03-验证与证据.md` §3.19。

⚠ bgfix6 就地标注（旧行为原文保留）：原先只有最后那一行
  `sys.exit(1 if (10 个列表) else 0)` —— **能 exit 1、没有 exit 2**，而且 `checked`
  （扫描到的 JSON 数）**只 print 从不断言** ⇒ 把 `assets/bettergold` 改名/搬走后
  10 个列表全空 ⇒ **exit 0**（"压根没检查"被当成"没问题"）。判定口径未动。
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _bgfix6_excepthook(exc_type, exc, tb):
    """未捕获异常 ⇒ **绝不许变成 0**；本关卡的顶层兜底把它变成 2。

    为什么不改写成 `main()` + `try/except`：本脚本是 400 行**模块级**脚本，整体缩进
    既大又容易切错（`docs/构建与跑测注意事项.md` §四「删代码块要按标记+锚点成对定位」）。
    `sys.excepthook` 只拦"真正没被接住"的异常，语义等价、零侵入；
    `SystemExit`（= 脚本自己的 exit 0/1/2）不会走这里（Python 不对它调 excepthook）。
    """
    if issubclass(exc_type, SystemExit):
        sys.__excepthook__(exc_type, exc, tb)
        return
    traceback.print_exception(exc_type, exc, tb)
    print("[bg-assets-crash] 关卡自身出错（未捕获异常）⇒ exit 2")
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(2)


sys.excepthook = _bgfix6_excepthook
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"
DATA = REPO / "src" / "main" / "resources" / "data"
METALS = ["flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
          # 1.6（bg-16）：两套新金属 —— 关卡必须跟着扫描表一起加，否则新族"零检查"也会全绿
          "thornsgold", "echogold"]
ALL_METALS = ["sturdygold", *METALS]
# 1.5 武器轮：五类武器的 wid（武器 id 前缀）= 六套金属（金制武器不存在，见 1.5 修正轮）
WEAPON_WIDS = ALL_METALS
# 1.5 修正轮：五件「胚底」= 最普通的 item/generated 单层模型（没有任何 override），
# 贴图沿用作者素材里的 16×16「胚底」图。
BLANK_WIDS = [f"golden_{w}_blank" for w in ("mace", "bow", "crossbow", "trident", "shield")]
# 各金属的专属材料（走 SPECIAL_TEXTURES，不在金属模板集里）：必须有贴图 + 物品模型，
# 否则客户端会刷「Unable to load model ... FileNotFoundException」并渲染成紫黑格。
SPECIAL_ITEMS = ["blazing_rod", "voodoo_feather", "amethyst_energy_dust",
                 "indigo_ocean_heart", "chorus_cherry_branch",
                 # 1.6（bg-16）：树棘金 / 幽咆金 的核心材料（前者是掉落物、后者由合成得到）
                 "glittering_vine", "bundled_echo_shard"]

bad_json, missing_tex, checked = [], [], 0
tex_roots = [ASSETS / "textures"]
vanilla = {"minecraft"}


def tex_exists(ref: str) -> bool:
    ns, _, path = ref.partition(":")
    if not path:
        ns, path = "minecraft", ns
    if ns in vanilla and not ref.startswith("bettergold:"):
        return True  # 原版贴图无法在这里校验，跳过
    return (ASSETS / "textures" / f"{path}.png").is_file()


for metal in METALS:
    for pattern in ("blockstates", "models/block", "models/item"):
        for f in sorted((ASSETS / pattern).glob(f"*{metal}*.json")):
            checked += 1
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                bad_json.append(f"{f.name}: {e}")
                continue
            for key in ("textures",):
                for name, ref in (obj.get(key) or {}).items():
                    if ref.startswith("#"):
                        continue
                    if not tex_exists(ref):
                        missing_tex.append(f"{f.name} -> {name}={ref}")

print(f"检查 JSON: {checked} 个")
print(f"解析失败: {len(bad_json)}")
for b in bad_json[:10]:
    print("   ", b)
print(f"贴图缺失: {len(missing_tex)}")
for m in sorted(set(missing_tex))[:20]:
    print("   ", m)

# 专属材料：贴图 + models/item/<id>.json（layer0 的贴图也要在）
missing_special = []
for special in SPECIAL_ITEMS:
    tex = ASSETS / "textures" / "item" / f"{special}.png"
    model = ASSETS / "models" / "item" / f"{special}.json"
    if not tex.is_file():
        missing_special.append(f"贴图 textures/item/{special}.png")
    if not model.is_file():
        missing_special.append(f"模型 models/item/{special}.json")
        continue
    try:
        obj = json.loads(model.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        missing_special.append(f"模型 {special}.json 解析失败: {e}")
        continue
    layer0 = (obj.get("textures") or {}).get("layer0")
    if not layer0 or not tex_exists(layer0):
        missing_special.append(f"{special}.json 的 layer0={layer0} 贴图不存在")
print(f"专属材料缺件: {len(missing_special)}")
for m in missing_special[:10]:
    print("   ", m)

# ==================== 1.5 武器轮：五类武器的贴图 + 模型 ====================
# 每一件武器要有的东西（缺一个客户端就刷「Unable to load model」或紫黑格）：
#   贴图：item/<wid>_mace / _bow(+3 帧) / _crossbow(+5 帧) / _trident；
#         entity/shield_<wid>（64×64 实体）/ entity/trident_<wid>（32×32 投掷实体）
#   模型：models/item/<wid>_*（弓 4、弩 6、三叉戟 3、盾牌 2、重锤 1 = 16 个）
#         ⚠ 三叉戟是 **3 个**（bg-15w 续工轮 §7.1 按原版 1:1 落成：
#           平面 `<w>_trident` / 手持 `<w>_trident_in_hand` / 蓄力 `<w>_trident_throwing`）
WEAPON_TEXTURES = [
    "textures/item/{w}_mace.png",
    "textures/item/{w}_bow.png",
    "textures/item/{w}_bow_pulling_0.png",
    "textures/item/{w}_bow_pulling_1.png",
    "textures/item/{w}_bow_pulling_2.png",
    "textures/item/{w}_crossbow.png",
    "textures/item/{w}_crossbow_pulling_0.png",
    "textures/item/{w}_crossbow_pulling_1.png",
    "textures/item/{w}_crossbow_pulling_2.png",
    "textures/item/{w}_crossbow_arrow.png",
    "textures/item/{w}_crossbow_firework.png",
    "textures/item/{w}_trident.png",
    "textures/entity/shield_{w}.png",
    "textures/entity/trident_{w}.png",
]
WEAPON_MODELS = [
    "models/item/{w}_mace.json",
    "models/item/{w}_bow.json",
    "models/item/{w}_bow_pulling_0.json",
    "models/item/{w}_bow_pulling_1.json",
    "models/item/{w}_bow_pulling_2.json",
    "models/item/{w}_crossbow.json",
    "models/item/{w}_crossbow_pulling_0.json",
    "models/item/{w}_crossbow_pulling_1.json",
    "models/item/{w}_crossbow_pulling_2.json",
    "models/item/{w}_crossbow_arrow.json",
    "models/item/{w}_crossbow_firework.json",
    "models/item/{w}_trident.json",
    "models/item/{w}_trident_in_hand.json",
    # bg-15w 续工轮 §7.1：蓄力姿态那一档（原版 `trident_throwing` 的同构件）
    "models/item/{w}_trident_throwing.json",
    "models/item/{w}_shield.json",
    "models/item/{w}_shield_blocking.json",
]
missing_weapon_assets = []
for wid in WEAPON_WIDS:
    for tpl in WEAPON_TEXTURES:
        rel = tpl.format(w=wid)
        if not (ASSETS / rel).is_file():
            missing_weapon_assets.append(rel)
    for tpl in WEAPON_MODELS:
        rel = tpl.format(w=wid)
        if not (ASSETS / rel).is_file():
            missing_weapon_assets.append(rel)
print(f"武器贴图/模型缺件: {len(missing_weapon_assets)} {missing_weapon_assets[:8]}")

# ==================== 1.5 修正轮：五件「胚底」的贴图与模型 ====================
# 胚底只有「一张 16×16 贴图 + 一个最简单的 item/generated 模型」，
# **不许有任何 override 谓词**（上一轮给它们做的拉弓 / 蓄力 / 投掷 / 格挡变体与 entity 贴图全部撤掉了）。
missing_blank_assets = []
for wid in BLANK_WIDS:
    tex = ASSETS / "textures" / "item" / f"{wid}.png"
    model = ASSETS / "models" / "item" / f"{wid}.json"
    if not tex.is_file():
        missing_blank_assets.append(f"贴图 textures/item/{wid}.png")
    if not model.is_file():
        missing_blank_assets.append(f"模型 models/item/{wid}.json")
        continue
    try:
        obj = json.loads(model.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        missing_blank_assets.append(f"模型 {wid}.json 解析失败: {e}")
        continue
    if obj.get("parent") != "minecraft:item/generated":
        missing_blank_assets.append(f"{wid}.json 的 parent 不是 minecraft:item/generated（{obj.get('parent')}）")
    layer0 = (obj.get("textures") or {}).get("layer0")
    if layer0 != f"bettergold:item/{wid}":
        missing_blank_assets.append(f"{wid}.json 的 layer0 不是 bettergold:item/{wid}（{layer0}）")
    elif not tex_exists(layer0):
        missing_blank_assets.append(f"{wid}.json 的 layer0 贴图不存在: {layer0}")
    if obj.get("overrides"):
        missing_blank_assets.append(f"{wid}.json 还带着 override 谓词（胚底不该有）：{len(obj['overrides'])} 条")
print(f"胚底贴图/模型问题: {len(missing_blank_assets)} {missing_blank_assets[:8]}")

# 尺寸不变量：六套金属的盾牌必须是 64×64（原版 entity/shield_base_nopattern 的构图）、
# 三叉戟投掷实体必须是 32×32（原版 entity/trident.png 的构图）。
# 1.5 修正轮：金制盾牌 / 金制三叉戟与它们的 entity 贴图已删除（作者澄清没有金制系列工具），
# 所以这里不再有「已知缺口」的例外打印。
def png_size(path):
    import struct as _s
    with open(path, "rb") as fh:
        data = fh.read(24)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return _s.unpack(">II", data[16:24])


size_bad = []
for metal in ALL_METALS:
    p = ASSETS / f"textures/entity/shield_{metal}.png"
    if p.is_file() and png_size(p) != (64, 64):
        size_bad.append(f"shield_{metal}.png = {png_size(p)}（期望 64×64）")
    p = ASSETS / f"textures/entity/trident_{metal}.png"
    if p.is_file() and png_size(p) != (32, 32):
        size_bad.append(f"trident_{metal}.png = {png_size(p)}（期望 32×32）")
print(f"盾牌/三叉戟实体贴图尺寸不符: {len(size_bad)} {size_bad[:4]}")
# 1.5 修正轮：entity/shield_golden.png 与 entity/trident_golden.png 必须**不存在**（金制武器已撤）
stale_golden = [f"textures/entity/{n}" for n in ("shield_golden.png", "trident_golden.png")
                if (ASSETS / f"textures/entity/{n}").exists()]
if stale_golden:
    size_bad.append(f"残留金制实体贴图: {stale_golden}")

# ==================== bg-15w 续工轮 §7.1：三叉戟「三模型」结构 + mixin 接线 ====================
# 这一类的失败方式**全是静默的**：平面那份多带 / 少带一个 override、in_hand 指错蓄力模型、
# mixin 配置没接进 toml —— 客户端只会"看起来还是平面图标"或"拿到 missing model"，不报错。
trident_problems = []
for wid in WEAPON_WIDS:
    try:
        flat = json.loads((ASSETS / f"models/item/{wid}_trident.json").read_text(encoding="utf-8"))
        in_hand = json.loads((ASSETS / f"models/item/{wid}_trident_in_hand.json").read_text(encoding="utf-8"))
        throwing = json.loads((ASSETS / f"models/item/{wid}_trident_throwing.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        trident_problems.append(f"{wid}: 三个三叉戟模型读取失败 {e}")
        continue
    # 平面那份：与原版 trident.json 同构 —— item/generated + 单层，**没有 overrides**
    if flat.get("parent") != "minecraft:item/generated":
        trident_problems.append(f"{wid}_trident.json 的 parent 不是 minecraft:item/generated")
    if flat.get("overrides"):
        trident_problems.append(f"{wid}_trident.json 不该有 overrides（原版 trident.json 没有）")
    # 手持那份：builtin/entity + throwing override -> _trident_throwing
    if in_hand.get("parent") != "builtin/entity":
        trident_problems.append(f"{wid}_trident_in_hand.json 的 parent 不是 builtin/entity")
    want_override = [{"predicate": {"throwing": 1}, "model": f"bettergold:item/{wid}_trident_throwing"}]
    if in_hand.get("overrides") != want_override:
        trident_problems.append(f"{wid}_trident_in_hand.json 的 overrides 不是 {want_override}")
    # 蓄力那份：builtin/entity + 原版 trident_throwing 的第三人称姿态
    if throwing.get("parent") != "builtin/entity":
        trident_problems.append(f"{wid}_trident_throwing.json 的 parent 不是 builtin/entity")
    display = throwing.get("display") or {}
    if (display.get("thirdperson_righthand") or {}).get("rotation") != [0, 90, 180]:
        trident_problems.append(f"{wid}_trident_throwing.json 的第三人称姿态不是原版的 [0,90,180]")
    if (display.get("thirdperson_lefthand") or {}).get("rotation") != [0, 90, 180]:
        trident_problems.append(f"{wid}_trident_throwing.json 的左持第三人称姿态不是原版的 [0,90,180]")
    # 手持那份是**正常持握**姿态（原版 trident_in_hand 的 [0,60,0]）
    if ((in_hand.get("display") or {}).get("thirdperson_righthand") or {}).get("rotation") != [0, 60, 0]:
        trident_problems.append(f"{wid}_trident_in_hand.json 的第三人称姿态不是原版的 [0,60,0]")
print(f"三叉戟三模型结构问题: {len(trident_problems)} {trident_problems[:6]}")

mixin_problems = []
MIXIN_JSON = REPO / "src/main/resources/bettergold.mixins.json"
TOML = REPO / "src/main/resources/META-INF/neoforge.mods.toml"
MIXIN_JAVA = REPO / "src/main/java/com/hjmmd_8/bettergold/mixin/ItemRendererTridentMixin.java"
if not MIXIN_JSON.is_file():
    mixin_problems.append("缺 bettergold.mixins.json")
else:
    cfg = json.loads(MIXIN_JSON.read_text(encoding="utf-8"))
    if "ItemRendererTridentMixin" not in (cfg.get("client") or []):
        mixin_problems.append("bettergold.mixins.json 的 client 列表里没有 ItemRendererTridentMixin")
    if not cfg.get("package"):
        mixin_problems.append("bettergold.mixins.json 缺 package")
if not MIXIN_JAVA.is_file():
    mixin_problems.append("缺 mixin/ItemRendererTridentMixin.java")
if not TOML.is_file():
    mixin_problems.append("缺 META-INF/neoforge.mods.toml")
else:
    toml_text = TOML.read_text(encoding="utf-8")
    if 'config="${mod_id}.mixins.json"' not in toml_text:
        mixin_problems.append("neoforge.mods.toml 没有启用 [[mixins]] config=${mod_id}.mixins.json")
    elif "#config=\"${mod_id}.mixins.json\"" in toml_text:
        mixin_problems.append("neoforge.mods.toml 里那一行仍是注释态")
print(f"mixin 接线问题: {len(mixin_problems)} {mixin_problems[:6]}")

# 贴图文件计数
for metal in METALS:
    items = list((ASSETS / "textures/item").glob(f"*{metal}*"))
    blocks = list((ASSETS / "textures/block").glob(f"*{metal}*"))
    armor = list((ASSETS / "textures/models/armor").glob(f"*{metal}*"))
    print(f"{metal:<12} item={len(items):<3} block={len(blocks):<3} armor={len(armor)}")

# ==================== bg-16：作者"第二次贴图授权"的文件级白名单 ====================
# 口径（作者 2026-10-04 原话「需要替换！」）：**只换这一张** ——
#   assets/bettergold/textures/item/golden_trident_blank.png 的内容换成作者 zip 里那张
#   `金三叉戟胚底(这是新贴图记得换!).png` 的**字节原样**。
# 这条断言把它钉成 **SHA256 锚点 + 文件级白名单**（而不是"某处有一张图"）：
#   ① 内容必须是那次授权的字节（哈希不符 ⇒ 有人又动过这张图，或者换了别的东西）；
#   ② 尺寸必须是 16×16（胚底红线：中间物只需一张 16×16 图标）；
#   ③ 反向：**除了这一张，不许有第二张既有贴图被改写** —— 由 `git status` 人工复核，
#      关卡这边守住"这一张就是授权的那一张"。
# ⚠ 这是本项目第二次"逐一授权改贴图"（第一次 = textures/trims/color_palettes/indigoseagold.png，
#   见 docs/1.5-规格.md §16.4）。
blank_tex_hash_problems = []
AUTHORIZED_BLANK_TEXTURE = {
    "textures/item/golden_trident_blank.png":
        "73e4df0f098dced43d43f8529a7aa07c702e63e5aacd70d99a25fdfbb1e6f5b6",
}
for rel, want in AUTHORIZED_BLANK_TEXTURE.items():
    path = ASSETS / rel
    if not path.is_file():
        blank_tex_hash_problems.append(f"缺 {rel}（反空转守护）")
        continue
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != want:
        blank_tex_hash_problems.append(
            f"{rel} 的 SHA256 不是作者授权的那一张 [bg16-authorized-blank-texture] "
            f"(got {got}, want {want})")
    w, h = png_size(path)
    if (w, h) != (16, 16):
        blank_tex_hash_problems.append(f"{rel} 不是 16x16（实际 {w}x{h}）")
print(f"bg-16 授权贴图（golden_trident_blank）问题: {len(blank_tex_hash_problems)} "
      f"{blank_tex_hash_problems[:4]}")

# ==================== bgfinal3：作者"第三次贴图授权"的文件级白名单 ====================
# 口径（作者 2026-10-06 原话「靛海金在这里，改手册，需要」+ 素材 zip `更有用的金 新约7.zip`）：
#   assets/bettergold/textures/trims/color_palettes/indigoseagold.png 换成该 zip 里
#   `靛海金/靛海金纹饰色卡.png` 的**字节原样**（8×1 / 8 位 / RGBA，120 B）。
#
# 历史链（三段，都是可复算的字节级事实）：
#   ① 原始件 = SHA256 `9C966B7F…E6B6D`（docs/bg7-证据/04a-资源哈希-before.txt:720 留档的就是它）；
#   ② bg-15w 续工轮 §7.3（作者当时原话「靛海金纹饰，这个甚至改得都不如之前的纯白边，能调回来不」）
#      把它**回退成原版 quartz 的白灰阶** ⇒ SHA256 `360B62970F90…FE1E`（101 B）；
#   ③ bg-fix2 第 1 条（2026-10-06）**只取证、未动贴图**，并刻意只写成报告行
#      （「已知缺陷写成契约会在修复时反过来拦住修复」—— mcmod_experience §2.2 / §2.7）；
#   ④ **bgfinal3（本轮）**：作者把原始素材 zip 交回来 ⇒ **恢复成 ① 的字节**。
#
# 这条断言把它钉成 **SHA256 锚点 + "不许等于 quartz" 的负向判据**：
#   ① 内容必须回到作者那一张（哈希不符 ⇒ 有人又动过，或换了别的东西）；
#   ② 尺寸必须是 8×1 / 8 位 / RGBA（纹饰色卡的结构硬约束）；
#   ③ **负向**：8 个像素**不许逐像素等于原版 quartz** —— 那正是本次 bug 的判据
#      （quartz 的 8 个像素是常量，直接写死在这里，不依赖原版 jar，任何环境都能复算）；
#   ④ 反空转：必须真的解出 8 个像素，解不出就是判据自己坏了。
# ⚠ 本项目"逐一授权改贴图"的**授权记录从此为三条**（**两个文件**）：
#   ① bg-15w §7.3：indigoseagold.png（当时授权"回退成白灰阶"）
#   ② bg-16：golden_trident_blank.png（作者「需要替换！」）
#   ③ **bgfinal3（本轮）：indigoseagold.png 恢复成原件**（作者交回素材 zip）
#   除这两张文件、这三次授权之外一律不许改或自己画（AGENTS.md 红线 6）。
palette_hash_problems = []
AUTHORIZED_PALETTE_TEXTURE = {
    "textures/trims/color_palettes/indigoseagold.png":
        "9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d",
}
# 原版 quartz 色卡（= bg-15w §7.3 回退后的那张"白灰阶"）的 8 个像素，逐字节常量。
VANILLA_QUARTZ_PIXELS = [(242, 239, 237, 255), (246, 234, 223, 255), (227, 219, 196, 255),
                         (182, 173, 150, 255), (144, 142, 128, 255), (101, 97, 86, 255),
                         (69, 67, 60, 255), (42, 40, 34, 255)]


def _png_decode_8x1(path: Path):
    """极简 PNG 解码（8×1 / 8 位 / 非隔行）：返回 ((w, h), bitdepth, colortype, [(r,g,b,a)...])。"""
    import struct
    import zlib
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"not a png: {path}"
    pos, idat, size, bitdepth, colortype = 8, b"", None, None, None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            size = struct.unpack(">II", chunk[:8])
            bitdepth, colortype = chunk[8], chunk[9]
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = size[0] * bpp
    out, prev = [], bytearray(stride)
    for y in range(size[1]):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ft == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        for x in range(size[0]):
            px = line[x * bpp:(x + 1) * bpp]
            out.append(tuple(px) if bpp == 4 else (px[0], px[1], px[2], 255))
        prev = line
    return size, bitdepth, colortype, out


for rel, want in AUTHORIZED_PALETTE_TEXTURE.items():
    path = ASSETS / rel
    if not path.is_file():
        palette_hash_problems.append(f"缺 {rel}（反空转守护）")
        continue
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != want:
        palette_hash_problems.append(
            f"{rel} 的 SHA256 不是作者授权恢复的那一张 [bgfinal3-indigosea-palette-restored] "
            f"(got {got}, want {want})")
    size, bd, ct, px = _png_decode_8x1(path)
    if size != (8, 1) or bd != 8 or ct != 6:
        palette_hash_problems.append(
            f"{rel} 不是 8x1 / 8 位 / RGBA（实际 {size[0]}x{size[1]} bd={bd} ct={ct}）"
            f" [bgfinal3-indigosea-palette-restored]")
    if len(px) != 8:
        palette_hash_problems.append(
            f"{rel} 只解出 {len(px)} 个像素（应 8；反空转守护）[bgfinal3-indigosea-not-quartz]")
    elif px == VANILLA_QUARTZ_PIXELS:
        palette_hash_problems.append(
            f"{rel} 逐像素等于原版 quartz 色卡（= bg-15w §7.3 的白灰阶回退现状，"
            f"bgfix2 第 1 条报的 bug 本体）[bgfinal3-indigosea-not-quartz]")
print(f"bgfinal3 授权色卡（靛海金纹饰）问题: {len(palette_hash_problems)} {palette_hash_problems[:4]}")

# ==================== bgfix6（2026-10-08）：前置缺失 / 反空转 ⇒ exit 2 ====================
# 旧行为（原文保留）：`checked` 只在上面 print，从不影响退出码 ⇒ "扫描到 0 个 JSON" 也会全绿。
print(f"[bg-assets-anti-vacuum] 实际检查了 {checked} 项"
      f"（blockstates / models 里名字含金属的 JSON；必须 > 0）")
if not ASSETS.is_dir():
    print(f"FAIL [bg-assets-missing-root] 资产根目录不存在：{ASSETS} ⇒ 基线被破坏（前置缺失）⇒ 本关卡 exit 2")
    sys.exit(2)
if checked <= 0:
    print("FAIL [bg-assets-anti-vacuum] JSON 扫描到 0 项 ⇒ 基线坏了"
          "（目录改名 / 扫描表被清空；**不许把「没扫到」当成「没问题」**）⇒ 本关卡 exit 2")
    sys.exit(2)

# 结论行（稳定 ASCII 结论码，便于扰动矩阵逐条命中）；判据与下面那行 sys.exit 完全一致。
_problem_total = sum(len(_x) for _x in (
    bad_json, missing_tex, missing_special, missing_weapon_assets, missing_blank_assets,
    size_bad, trident_problems, mixin_problems, blank_tex_hash_problems, palette_hash_problems))
print(f"[bg-assets-{'fail' if _problem_total else 'ok'}] 问题合计 {_problem_total} 条"
      f"（契约：0 绿 / 1 有问题 / 2 前置坏）")

sys.exit(1 if (bad_json or missing_tex or missing_special or missing_weapon_assets
               or missing_blank_assets or size_bad or trident_problems or mixin_problems
               or blank_tex_hash_problems or palette_hash_problems) else 0)
