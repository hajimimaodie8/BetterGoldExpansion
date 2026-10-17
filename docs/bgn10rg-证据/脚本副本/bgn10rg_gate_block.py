# ==========================================================================================
# 1.7 bg-n10rg（2026-10-17）：两个缺口的落地关卡
#   ① 混沌金装备 = **工作台配方**（11 件，**逐格**照原版 1.21.1 的形状，金属格换混沌金锭）
#   ② 「双倍贵金原料」= 每一条「贵金原料合成」都有一条同形的双倍版
#      （催化剂换高阶炼金油 / 数量 2 / 返还玻璃瓶）
#
# 作者原话（新的权威口径，逐字）：
#   「混沌金是用工作台公式制作的，原版装备在工作台上面怎么来合成它就怎么来」
#   「而"贵金"原料双倍合成就是直接把炼金燃油的位置换成高阶炼金油，然后原料的合成量改为 2，
#     记得返还玻璃瓶」
#
# ⚠ 为什么这一段的形状表**不**从生成器 import：生成器自己抄原版抄错了，共用一份表就永远抓不到
#   （= 拿期望表自比的假绿）。本段这张 `_RG_VANILLA` 是**从 `data/minecraft/recipe/*.json`
#   逐字抄来的独立副本**，生成器那边另有一份；两边不一致就红 —— 这是刻意留的双份。
# ⚠ 本段所有正向 needle 都跑在 **`strip_comments()` 之后**的源码上（注释里写一句就能喂饱断言）。
# ⚠ 失败文案里**不出现裸百分号**（`%` 只用于格式化，字面量一律写成中文）。
# ==========================================================================================
bgn10rg_problems: list[str] = []
_bgn10rg_checked = 0


def _bgn10rg_bad(tag: str, msg: str) -> None:
    bgn10rg_problems.append("[{}] {}".format(tag, msg))


_RG_NS = "bettergold"
_RG_INGOT = _RG_NS + ":chaosgold_ingot"
_RG_OIL = _RG_NS + ":refined_alchemic_oil"
# 11 件**有**工作台配方的（顺序 = 生成器 GEAR / 手册配方页顺序）
_RG_GEAR = ("sword", "axe", "pickaxe", "shovel", "hoe",
            "helmet", "chestplate", "leggings", "boots", "shield", "crossbow")
# 4 件**没有**工作台配方的（原版那一格没有「锭」这一步 / 原版根本没配方 / 不是原版物品）
#   bow      : 3 棍 + 3 线，一格金属都没有
#   mace     : 重核 + 微风棒，没有锭
#   trident  : 原版没有合成配方（溺尸掉落 / 试炼密室）
#   knife    : 乐事小刀 farmersdelight:golden_knife = 1 锭 + 1 棍，不是原版
_RG_EXCLUDED = ("bow", "mace", "trident", "knife")
_RG_ROWS = ("第1行", "第2行", "第3行")
_RG_COLS = ("第1列(左)", "第2列(中)", "第3列(右)")

# 原版 1.21.1 的形状（**独立副本**，逐字抄自 `data/minecraft/recipe/<文件>`）：
#   件 -> (原版配方文件名, pattern, {图例字符: 单元格内容})
#   单元格内容 = "item:<id>" / "tag:<id>"（`minecraft:planks` 在原版 shield 里是 tag）
_RG_VANILLA = {
    "sword": ("golden_sword.json", ["X", "X", "#"],
              {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "axe": ("golden_axe.json", ["XX", "X#", " #"],
            {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "pickaxe": ("golden_pickaxe.json", ["XXX", " # ", " # "],
                {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "shovel": ("golden_shovel.json", ["X", "#", "#"],
               {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "hoe": ("golden_hoe.json", ["XX", " #", " #"],
            {"X": "item:minecraft:gold_ingot", "#": "item:minecraft:stick"}),
    "helmet": ("golden_helmet.json", ["XXX", "X X"],
               {"X": "item:minecraft:gold_ingot"}),
    "chestplate": ("golden_chestplate.json", ["X X", "XXX", "XXX"],
                   {"X": "item:minecraft:gold_ingot"}),
    "leggings": ("golden_leggings.json", ["XXX", "X X", "X X"],
                 {"X": "item:minecraft:gold_ingot"}),
    "boots": ("golden_boots.json", ["X X", "X X"],
              {"X": "item:minecraft:gold_ingot"}),
    "shield": ("shield.json", ["WoW", "WWW", " W "],
               {"W": "tag:minecraft:planks", "o": "item:minecraft:iron_ingot"}),
    "crossbow": ("crossbow.json", ["#&#", "~$~", " # "],
                 {"#": "item:minecraft:stick", "&": "item:minecraft:iron_ingot",
                  "~": "item:minecraft:string", "$": "item:minecraft:tripwire_hook"}),
}
# 原版里属于「金属」的两格 ⇒ 本轮一律换成混沌金锭（金锭在 golden_*，铁锭在 shield / crossbow）
_RG_SUBST = ("item:minecraft:gold_ingot", "item:minecraft:iron_ingot")
_RG_METAL_CELL = "item:" + _RG_INGOT


def _rg_key_cell(ing) -> str:
    """把 key 里的一条解析成 "item:<id>" / "tag:<id>" / "<缺失>" / "<形状不认识>"。"""
    if not isinstance(ing, dict):
        return "<缺失>"
    if isinstance(ing.get("item"), str):
        return "item:" + ing["item"]
    if isinstance(ing.get("tag"), str):
        return "tag:" + ing["tag"]
    return "<形状不认识>"


def _rg_grid(pattern, key) -> list[list[str]]:
    """展开成 3×3 的**单元格内容**网格（空格子 = 空串）；越界按原版语义补空格。"""
    grid = [["" for _ in range(3)] for _ in range(3)]
    rows = list(pattern or [])
    for i in range(min(3, len(rows))):
        row = str(rows[i])
        for j in range(min(3, len(row))):
            ch = row[j]
            if ch == " ":
                continue
            grid[i][j] = _rg_key_cell((key or {}).get(ch))
    return grid


def _rg_want_grid(gear: str) -> list[list[str]]:
    """原版那张表 → 期望的 3×3（金属格已替换成混沌金锭）。"""
    _src, pattern, key = _RG_VANILLA[gear]
    want = [["" for _ in range(3)] for _ in range(3)]
    for i in range(min(3, len(pattern))):
        for j in range(min(3, len(pattern[i]))):
            ch = pattern[i][j]
            if ch == " ":
                continue
            cell = key[ch]
            want[i][j] = _RG_METAL_CELL if cell in _RG_SUBST else cell
    return want


def _rg_grid_text(grid) -> str:
    out = []
    for i in range(3):
        out.append(" ".join((grid[i][j] or "-") for j in range(3)))
    return " / ".join(out)


def _rg_load(name: str):
    """读一条配方（稳定 ASCII 文件名 + 存在性 + 合法 JSON）。"""
    if not str(name).isascii() or re.fullmatch(r"[a-z0-9_]+", str(name)) is None:
        _bgn10rg_bad("bgn10rg-id", "配方文件名不是稳定 ASCII（只许小写字母数字下划线）：" + str(name))
        return None
    path = _RC_DATA / (str(name) + ".json")
    if not path.is_file():
        _bgn10rg_bad("bgn10rg-file", "缺配方 data/bettergold/recipe/" + str(name) + ".json")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as _e:                       # noqa: BLE001
        _bgn10rg_bad("bgn10rg-file", str(name) + ".json 不是合法 JSON：" + repr(_e))
        return None


# ---------- ① 11 件工作台配方：**逐格**（9 格逐格点名，出错的格子报「第N行第M列」） ----------
for _gear in _RG_GEAR:
    _name = "chaosgold_" + _gear
    _obj = _rg_load(_name)
    _bgn10rg_checked += 4
    if _obj is None:
        continue
    if _obj.get("type") != "minecraft:crafting_shaped":
        _bgn10rg_bad("bgn10rg-gear-type",
                     _name + " 的 type 不是 minecraft:crafting_shaped：" + str(_obj.get("type")))
    if _obj.get("category") != "equipment":
        _bgn10rg_bad("bgn10rg-gear-type",
                     _name + " 的 category 不是 equipment：" + str(_obj.get("category")))
    _want = _rg_want_grid(_gear)
    _got = _rg_grid(_obj.get("pattern"), _obj.get("key"))
    _pat = _obj.get("pattern") or []
    if len(_pat) > 3 or any(len(str(r)) > 3 for r in _pat):
        _bgn10rg_bad("bgn10rg-gear-shape",
                     _name + " 的 pattern 超过 3×3：" + repr(_pat))
    for _i in range(3):
        for _j in range(3):
            _bgn10rg_checked += 1
            if _got[_i][_j] != _want[_i][_j]:
                _bgn10rg_bad("bgn10rg-gear-cell",
                             _name + " 的「" + _RG_ROWS[_i] + _RG_COLS[_j] + "」是 "
                             + (_got[_i][_j] or "<空>") + "，原版同格换成混沌金锭后应为 "
                             + (_want[_i][_j] or "<空>")
                             + "（原版 " + _RG_VANILLA[_gear][0] + "；期望表： "
                             + _rg_grid_text(_want) + "；实际： " + _rg_grid_text(_got) + "）")
    # 产物：id + 数量 1（「换数量」这一格也要能单独变红）
    _res = _obj.get("result") or {}
    _bgn10rg_checked += 2
    if _res.get("id") != _RG_NS + ":chaosgold_" + _gear:
        _bgn10rg_bad("bgn10rg-gear-result",
                     _name + " 的产物不是 " + _RG_NS + ":chaosgold_" + _gear + "：" + repr(_res))
    if _res.get("count") != 1:
        _bgn10rg_bad("bgn10rg-gear-result", _name + " 的产物数量不是 1：" + repr(_res))
    _cells = [c for row in _got for c in row]
    if _cells.count(_RG_METAL_CELL) < 1:
        _bgn10rg_bad("bgn10rg-gear-metal", _name + " 里一个 " + _RG_INGOT + " 都没有")
    # 反向：原版金属一格都不许残留（换漏了就是「免费金装」）
    _left = sorted(set(c for c in _cells if c in _RG_SUBST))
    if _left:
        _bgn10rg_bad("bgn10rg-gear-metal",
                     _name + " 还残留原版金属 " + repr(_left) + " —— 换漏了")

# 反向：4 件**不许**偷偷有工作台配方（本轮明确「停下报告、等作者」）
for _gear in _RG_EXCLUDED:
    _bgn10rg_checked += 1
    _p = _RC_DATA / ("chaosgold_" + _gear + ".json")
    if _p.is_file():
        _bgn10rg_bad("bgn10rg-gear-excluded",
                     "chaosgold_" + _gear + ".json 不该存在：这一件本轮判定为「停下报告」"
                     "（原版没有可照抄的金属格），等作者裁定后再加")

# ---------- ② 双倍贵金原料：每一条「贵金原料合成」都必须有同形的双倍版 ----------
_rg_bases = []
for _p in sorted(_RC_DATA.glob("*.json")):
    if _p.stem.endswith("_doubled"):
        continue
    try:
        _o = json.loads(_p.read_text(encoding="utf-8"))
    except Exception:                             # noqa: BLE001  别的形状坏了不归本段管
        continue
    if str(_o.get("type") or "").startswith(_RG_NS + ":raw_sturdygold"):
        _rg_bases.append((_p, _o))
_bgn10rg_checked += 1
if len(_rg_bases) != 9:
    _bgn10rg_bad("bgn10rg-doubled-set",
                 "「贵金原料合成」的基础配方不是 9 条（8 族 + 万坚金金钱茄变体），实际 "
                 + str(len(_rg_bases)) + "：" + repr([p.stem for p, _ in _rg_bases]))
for _p, _base in _rg_bases:
    _dname = _p.stem + "_doubled"
    _dp = _RC_DATA / (_dname + ".json")
    _bgn10rg_checked += 5
    if not _dp.is_file():
        _bgn10rg_bad("bgn10rg-doubled-file", "缺双倍版 " + _dname + ".json（基础版 " + _p.name + "）")
        continue
    try:
        _d = json.loads(_dp.read_text(encoding="utf-8"))
    except Exception as _e:                       # noqa: BLE001
        _bgn10rg_bad("bgn10rg-doubled-file", _dname + ".json 不是合法 JSON：" + repr(_e))
        continue
    # (a) 双倍版 = 基础版 + **恰好** catalyst / count 两个字段（多一个少一个都红）
    _extra = sorted(set(_d) - set(_base))
    if _extra != ["catalyst", "count"]:
        _bgn10rg_bad("bgn10rg-doubled-fields",
                     _dname + " 比基础版多出的字段不是 [catalyst, count]：" + repr(_extra))
    _missing = sorted(set(_base) - set(_d))
    if _missing:
        _bgn10rg_bad("bgn10rg-doubled-fields", _dname + " 比基础版少了字段：" + repr(_missing))
    # (b) 催化剂 = 高阶炼金油；数量 = 2（作者原话两件事）
    if _d.get("catalyst") != _RG_OIL:
        _bgn10rg_bad("bgn10rg-doubled-catalyst",
                     _dname + " 的 catalyst 不是 " + _RG_OIL + "：" + repr(_d.get("catalyst")))
    if _d.get("count") != 2:
        _bgn10rg_bad("bgn10rg-doubled-count", _dname + " 的 count 不是 2：" + repr(_d.get("count")))
    # (c) 类型 / 兑换物 / 产物必须与基础版**逐字相同**（双倍只换催化剂与数量）
    for _f in ("type", "exchange", "result"):
        if _d.get(_f) != _base.get(_f):
            _bgn10rg_bad("bgn10rg-doubled-same",
                         _dname + " 的 " + _f + " 与基础版不同：" + repr(_d.get(_f))
                         + " != " + repr(_base.get(_f)))
    # (d) 基础版**不许**被改成双倍口径（作者没要求动既有那条 ⇒ 两条并存）
    if "catalyst" in _base or "count" in _base:
        _bgn10rg_bad("bgn10rg-doubled-base-untouched",
                     _p.name + " 自己被写进了 catalyst / count（本轮明确不改既有那条）")

# 反向：不许有「孤儿双倍版」（基础版没了 / 名字拼错）
for _dp in sorted(_RC_DATA.glob("*_doubled.json")):
    _bgn10rg_checked += 1
    _bp = _RC_DATA / (_dp.stem[:-len("_doubled")] + ".json")
    if not _bp.is_file():
        _bgn10rg_bad("bgn10rg-doubled-orphan",
                     _dp.name + " 没有对应的基础版（" + _bp.name + " 不存在）")

# ---------- ③ 返还玻璃瓶：机制在 Java 里，正向 needle 跑在**去注释源码**上 ----------
_rg_src_path = JAVA / "recipe" / "RawSturdygoldRecipe.java"
_bgn10rg_checked += 6
if not _rg_src_path.is_file():
    _bgn10rg_bad("bgn10rg-bottle", "缺 RawSturdygoldRecipe.java")
else:
    _rg_code = strip_comments(_rg_src_path.read_text(encoding="utf-8"))
    # (a) 剩余物按**催化剂那一格**返瓶：matches 与 getRemainingItems 各一次 ⇒ 恰好 2 处
    #     ⚠ 这一条就是「高阶炼金油那格也返瓶」的证明：写死 ALCHEMIC_FUEL 时这里会掉到 1 处
    _n_cat = _rg_code.count("stack.is(this.catalyst)")
    if _n_cat != 2:
        _bgn10rg_bad("bgn10rg-bottle",
                     "去注释后的 RawSturdygoldRecipe 里 stack.is(this.catalyst) 不是 2 处（实际 "
                     + str(_n_cat) + "）—— 匹配与返还玻璃瓶必须都按催化剂那一格判")
    if "stack.is(AllItems.ALCHEMIC_FUEL.get())" in _rg_code:
        _bgn10rg_bad("bgn10rg-bottle",
                     "去注释后的源码里仍在按 ALCHEMIC_FUEL 判格（高阶炼金油那格就不会返瓶）")
    if _rg_code.count("new ItemStack(Items.GLASS_BOTTLE)") != 1:
        _bgn10rg_bad("bgn10rg-bottle", "返瓶的 new ItemStack(Items.GLASS_BOTTLE) 不是恰好 1 处")
    # (b) 数量必须真的进产物（assemble + getResultItem 各一次）
    if _rg_code.count("new ItemStack(this.result, this.count)") != 2:
        _bgn10rg_bad("bgn10rg-doubled-count",
                     "去注释后的源码里 new ItemStack(this.result, this.count) 不是 2 处"
                     "（assemble / getResultItem 都要带数量，否则结果格仍显示 1）")
    # (c) 两个字段都进了 Codec 与 StreamCodec（少一个就是「服务端 2、客户端 1」）
    for _needle, _why in (('optionalFieldOf("catalyst")', "catalyst 没进 Codec"),
                          ('optionalFieldOf("count", 1)', "count 没进 Codec（缺省必须是 1）"),
                          ("RawSturdygoldRecipe::catalyst", "catalyst 没进 StreamCodec"),
                          ("RawSturdygoldRecipe::count", "count 没进 StreamCodec")):
        if _needle not in _rg_code:
            _bgn10rg_bad("bgn10rg-bottle", _why + "：缺 " + _needle)
    # (d) 缺省催化剂仍必须是炼金燃油（老 JSON 一字不改仍按老语义）
    if "defaultCatalyst = () -> AllItems.ALCHEMIC_FUEL.get()" not in _rg_code:
        _bgn10rg_bad("bgn10rg-bottle", "缺省的催化剂不是炼金燃油（老配方语义被改了）")

# ---------- ④ 生成器 = 唯一真源：它自己的自检 + 产物与磁盘逐字节一致 ----------
_bgn10rg_checked += 2
try:
    import importlib.util
    _dwb2 = sys.dont_write_bytecode
    sys.dont_write_bytecode = True            # 别在工作树里留 __pycache__
    try:
        _rg_gen_path = REPO / "tools" / "asset-generator" / "generate_chaosgold_recipes.py"
        _rg_metal_path = REPO / "tools" / "asset-generator" / "generate_metal_recipes.py"
        _spec2 = importlib.util.spec_from_file_location("_bgn10rg_gen", _rg_gen_path)
        _rg_gen = importlib.util.module_from_spec(_spec2)
        _spec2.loader.exec_module(_rg_gen)
        _spec3 = importlib.util.spec_from_file_location("_bgn10rg_metal", _rg_metal_path)
        _rg_metal = importlib.util.module_from_spec(_spec3)
        _spec3.loader.exec_module(_rg_metal)
    finally:
        sys.dont_write_bytecode = _dwb2
    # (a) 生成器自己的自检
    _rg_gen_bad = list(_rg_gen.check(_rg_gen.targets()))
    if _rg_gen_bad:
        _bgn10rg_bad("bgn10rg-generator", "混沌金配方生成器自检不通过：" + repr(_rg_gen_bad[:4]))
    if tuple(_rg_gen.GEAR) != _RG_GEAR:
        _bgn10rg_bad("bgn10rg-generator",
                     "生成器的 GEAR 与本段的 11 件不一致：" + repr(_rg_gen.GEAR))
    if tuple(sorted(_rg_gen.EXCLUDED)) != tuple(sorted(_RG_EXCLUDED)):
        _bgn10rg_bad("bgn10rg-generator",
                     "生成器的 EXCLUDED（停下报告的 4 件）与本段不一致："
                     + repr(sorted(_rg_gen.EXCLUDED)))
    # (b) 11 条产物与磁盘**逐字节**一致（手改产物立刻红）
    _rg_diff = []
    for _gname, _gobj in _rg_gen.targets():
        _bgn10rg_checked += 1
        _gpath = _RC_DATA / _gname
        if not _gpath.is_file():
            _rg_diff.append(_gname + "(缺文件)")
        elif _gpath.read_text(encoding="utf-8") != json.dumps(_gobj, ensure_ascii=False, indent=2) + "\n":
            _rg_diff.append(_gname)
    if _rg_diff:
        _bgn10rg_bad("bgn10rg-generator",
                     "混沌金配方产物与唯一真源不再逐字节一致：" + repr(_rg_diff[:6]))
    # (c) 双倍版那一批：生成器自检 + 9 条逐字节一致
    _rg_doubled_targets = _rg_metal.doubled_raw_targets()
    _rg_doubled_bad = list(_rg_metal.check_doubled(_rg_doubled_targets))
    if _rg_doubled_bad:
        _bgn10rg_bad("bgn10rg-generator", "双倍原料生成器自检不通过：" + repr(_rg_doubled_bad[:4]))
    _rg_ddiff = []
    for _gname, _gobj, _gbase in _rg_doubled_targets:
        _bgn10rg_checked += 1
        _gpath = _RC_DATA / _gname
        if not _gpath.is_file():
            _rg_ddiff.append(_gname + "(缺文件)")
        elif _gpath.read_text(encoding="utf-8") != json.dumps(_gobj, ensure_ascii=False, indent=2) + "\n":
            _rg_ddiff.append(_gname)
    if _rg_ddiff:
        _bgn10rg_bad("bgn10rg-generator",
                     "双倍原料产物与唯一真源不再逐字节一致：" + repr(_rg_ddiff[:6]))
except SystemExit:
    _bgn10rg_bad("bgn10rg-generator", "生成器被加载时自己 exit 了（自检失败）")
except Exception as _e:                           # noqa: BLE001
    _bgn10rg_bad("bgn10rg-generator", "生成器加载失败：" + repr(_e))

# ---------- ⑤ 手册：gear_chaosgold 的 13 页（3 文案 + 6 页配方 + 3 图标 + 1 附魔书配方） ----------
_RG_BOOK_PAGES = 13
_bgn10rg_checked += 5
for _d, _tag in ((_ZH_BOOK, "zh"), (_EN_BOOK, "en")):
    _ep = _d / "entries" / "gear_chaosgold.json"
    if not _ep.is_file():
        _bgn10rg_bad("bgn10rg-handbook", _tag + " 缺 entries/gear_chaosgold.json")
        continue
    _ej = json.loads(_ep.read_text(encoding="utf-8"))
    _pages = _ej.get("pages") or []
    if len(_pages) != _RG_BOOK_PAGES:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的 gear_chaosgold 页数不是 " + str(_RG_BOOK_PAGES)
                     + "（实际 " + str(len(_pages)) + "）")
        continue
    _types = [p.get("type") for p in _pages]
    _want_types = (["patchouli:text"] * 3 + ["patchouli:crafting"] * 6
                   + ["patchouli:spotlight"] * 3 + ["patchouli:crafting"])
    if _types != _want_types:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的页型序列不对：" + repr(_types))
    # 配方页（第 4~9 页）必须**恰好**是这 11 件、顺序 = _RG_GEAR、每页最多 2 条
    _refs = []
    for _pg in _pages[3:9]:
        _on_page = [x for x in (_pg.get("recipe"), _pg.get("recipe2")) if isinstance(x, str)]
        _bgn10rg_checked += 1
        if len(_on_page) > 2:
            _bgn10rg_bad("bgn10rg-handbook",
                         _tag + " 有配方页塞了 " + str(len(_on_page)) + " 条（Patchouli 上限 2）")
        _refs.extend(_on_page)
    _want_refs = [_RG_NS + ":chaosgold_" + _g for _g in _RG_GEAR]
    if _refs != _want_refs:
        _bgn10rg_bad("bgn10rg-handbook",
                     _tag + " 的 11 件配方引用与 _RG_GEAR 不一致：" + repr(_refs))
    # 死链：每条引用都要真的落在 data/bettergold/recipe/
    _dead = [_r for _r in _refs
             if not (_RC_DATA / (_r.split(":", 1)[1] + ".json")).is_file()]
    _bgn10rg_checked += 1
    if _dead:
        _bgn10rg_bad("bgn10rg-handbook", _tag + " 的配方页有死链：" + repr(_dead))
# zh / en 结构必须相同
_bgn10rg_checked += 1
_zh_ep = _ZH_BOOK / "entries" / "gear_chaosgold.json"
_en_ep = _EN_BOOK / "entries" / "gear_chaosgold.json"
if _zh_ep.is_file() and _en_ep.is_file():
    if (json.loads(_zh_ep.read_text(encoding="utf-8")).get("pages")
            != json.loads(_en_ep.read_text(encoding="utf-8")).get("pages")):
        _bgn10rg_bad("bgn10rg-handbook", "gear_chaosgold 的 zh / en 页列表不一致")

# ---------- ⑥ 文案口径 + 文档 ----------
_bgn10rg_checked += 4
try:
    _rg_zh_lang = json.loads((_RES / "assets" / "bettergold" / "lang" / "zh_cn.json")
                             .read_text(encoding="utf-8"))
except Exception as _e:                           # noqa: BLE001
    _rg_zh_lang = {}
    _bgn10rg_bad("bgn10rg-lang", "读不了 zh_cn.json：" + repr(_e))
_rg_text = _rg_zh_lang.get("bettergold.handbook.page.gear_chaosgold_1_right", "")
for _needle, _why in (("工作台", "新口径必须说清是「工作台」合成"),
                      ("11 件", "新口径必须写清 11 件（不是 14 件）"),
                      ("4 件", "新口径必须写清剩下 4 件没有工作台配方")):
    if _needle not in _rg_text:
        _bgn10rg_bad("bgn10rg-lang",
                     "手册「混沌金装备」正文没提「" + _needle + "」：" + _why)
if "只展示物品" in _rg_text:
    _bgn10rg_bad("bgn10rg-lang",
                 "手册正文仍是旧口径（「只展示物品，不展示配方」）—— 现在已经有配方页了")

_bgn10rg_checked += 5
_rg_doc = REPO / "docs" / "1.7-\u6df7\u6c8c\u91d1\u4e0e\u5d29\u4e71\u5408\u91d1-\u9700\u6c42\u7acb\u6863.md"
if not _rg_doc.is_file():
    _bgn10rg_bad("bgn10rg-doc", "缺 docs/1.7-混沌金与崩乱合金-需求立档.md")
else:
    _rg_doc_txt = _rg_doc.read_text(encoding="utf-8")
    for _needle, _why in (
            ("bg-n10rg", "立档里没有本轮标记（bg-n10rg）这一段"),
            ("混沌金是用工作台公式制作的", "没把作者「原版装备怎么合就怎么合」那句原话收进立档"),
            ("直接把炼金燃油的位置换成高阶炼金油", "没把作者双倍原料那句原话收进立档"),
            ("记得返还玻璃瓶", "没把作者「返还玻璃瓶」那句原话收进立档"),
            ("停下报告", "没把「4 件停下报告」的判据写进立档")):
        if _needle not in _rg_doc_txt:
            _bgn10rg_bad("bgn10rg-doc", _why + "：缺「" + _needle + "」")

_bgn10rg_checked += 1
if _bgn10rg_checked < 60:
    _bgn10rg_bad("bgn10rg-anti-vacuum",
                 "本段只检查了 " + str(_bgn10rg_checked) + " 项（反空转守护：应远大于 60）")
print("1.7 bg-n10rg（混沌金工作台配方 + 双倍贵金原料）问题: "
      + str(len(bgn10rg_problems)) + " " + str(bgn10rg_problems[:4])
      + "（本段判定 " + str(_bgn10rg_checked) + " 项）")
if not bgn10rg_problems:
    print("[bgn10rg-ok] 混沌金 11 件工作台配方逐格照原版（金属格 = 混沌金锭）+ 4 件按判定停下报告 / "
          "9 条双倍贵金原料（催化剂 = 高阶炼金油、数量 2、与基础版逐字段同形且基础版未被改）/ "
          "返还玻璃瓶按催化剂那一格判（去注释源码 2 处）/ 手册 gear_chaosgold 13 页 11 条配方无死链")

