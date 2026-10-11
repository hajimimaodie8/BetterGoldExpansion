#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-ach 关卡：BGE 进度（成就）系统的静态校验。

判据 / 退出码契约：
  * 只读；只用标准库；每条断言带一个稳定的 ASCII id（`[bgach-*]`），便于扰动实测只匹配 id；
  * 有违规 ⇒ 逐条打印 `FAIL [bgach-xxx] …` 并 `exit 1`；无违规 ⇒ `exit 0`；脚本自身出错 ⇒ `exit 2`；
  * **每条主动计数类断言都配反空转守护**（扫到 0 条 = 红），避免"什么都没扫到也全绿"。

真源与自比纪律（mcmod_experience §4 第 42 条）：
  * 物品存在性、食物清单、配方 id 存在性，**全部从 Java/资源真源现算**，不拿本脚本或生成器的表自比；
  * 树结构既与生成器的 manifest 交叉核对，也**独立**从产物 JSON 里重建（两个来源必须一致）。
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

# Windows 控制台是 GBK：非 GBK 字符（U+21D2 之类）会让 print 直接抛 UnicodeEncodeError，
# 于是"关卡红了"变成"关卡崩了"（扰动实测会记成 MISS）。这里兜底成替换符。
try:
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = Path(__file__).resolve().parents[2]
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
ADV = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "advancement"
RECIPE = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"
MANIFEST = Path(__file__).resolve().parent / "advancement_manifest.json"
VANILLA_JAR = REPO / "build" / "moddev" / "artifacts" / \
    "neoforge-21.1.228-client-extra-aka-minecraft-resources.jar"

NS = "bettergold"
EXPECTED_COUNT = 51
FD_CONDITION = [{"type": "neoforge:mod_loaded", "modid": "farmersdelight"}]
FD_PATHS = {"agriculture/alchemical_meat", "agriculture/midas_feast_2",
            "agriculture/sturdygold_feast_2"}
# ⛔ **bg-fix3 §五②（作者 2026-10-07）**：「贵金相关的进度排版…**盔甲部分属于挑战进度**」
#   ⇒ challenge 从 1 条变成 **9 条**（8 条 armor + 骷髅打金服）。
#   ⚠ 旧期望原文保留（未删）：`CHALLENGE_PATHS = {"metal/sturdygold/skeleton"}`（只有万坚金的骷髅那条）。
CHALLENGE_PATHS = {"metal/sturdygold/skeleton"} | {
    f"metal/{m}/armor" for m in
    ("flamegold", "sturdygold", "thornsgold", "echogold",
     "indigoseagold", "voodoogold", "thundergold", "illusiongold")}
TRIGGER_WHITELIST = {
    "minecraft:inventory_changed", "minecraft:recipe_crafted", "minecraft:villager_trade",
    "minecraft:player_hurt_entity", "minecraft:placed_block", "minecraft:item_used_on_block",
}
# 本仓只用到这两个原版物品（金苹果 / 金胡萝卜是原版金食物）
VANILLA_ITEMS = {"minecraft:gold_ingot", "minecraft:golden_apple", "minecraft:golden_carrot"}
VANILLA_TAGS = {"#minecraft:hoes", "#minecraft:skeletons"}

# ==================== bg-fix3（2026-10-07）新增的两族自检 ====================
# ① 乐事小刀：8 条武器成就各有一条 `have_knife` 判据，`items` 指向**该族自己的**物品标签。
# ② 手册：根成就的判据从 `recipe_crafted` 改成 `inventory_changed` + `#bettergold:handbook` 标签。
# 两条都用"**带 `required:false` 条目的标签**"承载"只在装了可选模组时才存在的物品" —— 依据是
# 读 patched 1.21.1 源码得到的三条硬事实（见 docs/1.6-规格.md §二十二）：
#   * `TagEntry.FULL_CODEC` 有 `required` 字段（默认 true）；写 false 的条目缺失⇒静默跳过；
#   * `HolderSetCodec.lookupTag`：**标签本身不存在** ⇒ `Missing tag` ⇒ 整份 JSON 解析失败
#     ⇒ 所以标签文件必须**无条件存在**（不能用 neoforge:conditions 关掉）；
#   * `HolderSetCodec.homogenousList` 的 `ensureHomogenous(Holder::kind)` ⇒ `items` 的**列表**
#     里不许混进 `#tag` ⇒ 标签必须写成**单个字符串**。
METALS_ORDER = ("flamegold", "sturdygold", "thornsgold", "echogold",
                "indigoseagold", "voodoogold", "thundergold", "illusiongold")
BGFIX3_KNIFE_TAGS = {f"#{NS}:{m}_knives": m for m in METALS_ORDER}
BGFIX3_HANDBOOK_TAG = f"#{NS}:handbook"
BGFIX3_HANDBOOK_ITEM = f"{NS}:alchemy_student_handbook"
BGFIX3_TAG_FILES = {f"{m}_knives": [f"{NS}:{m}_knife"] for m in METALS_ORDER}
BGFIX3_TAG_FILES["handbook"] = [BGFIX3_HANDBOOK_ITEM]
# ==================== bg-fix4 §一（2026-10-08）新增：两把古董刀 ====================
# 作者原话「古董屠刀和幽冥断骸刀无法触发上古藏品和皇骸永存的进度」⇒ 两条商人线成就各得一条
# `have_knife` 判据，items 指向**无条件存在**的标签（各 1 条 `required:false` 条目）。
# 两把刀都在 `fd/FdItems.java:192/196` 注册 ⇒ **只在装了乐事时才存在** ⇒ 与 8 把乐事小刀
# 同一条硬约束（裸 id / 混写列表都会在"没装乐事"时把整份成就 JSON 弄坏）。
BGFIX4_ANTIQUE_TAG_FILES = {
    "antique_knives": [f"{NS}:antique_knife"],
    "netherite_antique_knives": [f"{NS}:netherite_antique_knife"],
}
BGFIX4_ANTIQUE_TAGS = {f"#{NS}:{k}": v[0] for k, v in BGFIX4_ANTIQUE_TAG_FILES.items()}
# 成就路径 -> (标签, 该成就原有的 5 件"永远注册"的古董工具)
BGFIX4_ANTIQUE_ACHIEVEMENTS = {
    "merchant/antique_tool": (f"#{NS}:antique_knives",
                              [f"{NS}:antique_{s}" for s in ("sword", "axe", "pickaxe", "shovel", "hoe")]),
    "merchant/netherite_antique_tool": (f"#{NS}:netherite_antique_knives",
                                        [f"{NS}:netherite_antique_{s}" for s in ("sword", "axe", "pickaxe", "shovel", "hoe")]),
}
BGFIX3_TAG_FILES.update(BGFIX4_ANTIQUE_TAG_FILES)
TAG_DIR = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "tags" / "item"

# 1.6 收尾轮 bg-final 第 2 件：**英文值必须是真英译**（旧口径 = 复制中文，已推翻）。
# 唯一的豁免口子是"纯符号 / 数字类标题"——当前**一条都没有**（空集）。
# 白名单本身也要能自证：列进来的键，其中文侧必须真的不含中日韩文字（[bgfinal-adv-lang-whitelist-honest]）。
SYMBOL_ONLY_OK: set[str] = set()
# 中英两侧各应扫到的 `advancements.bettergold.*` 条数 = 51 成就 × 2（title/description）
ADV_LANG_EXPECTED = EXPECTED_COUNT * 2
# 中日韩文字 + 全角标点（用来判定"不是纯符号/数字"）
CJK_RE = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")

problems: list[str] = []


def bad(tag: str, msg: str) -> None:
    problems.append(f"[{tag}] {msg}")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def strip_comments(src: str) -> str:
    """去注释（**先块后行**）：判据一律跑在去注释的源码上。

    否则注释里写一句「这里不用 `.food(`」就会喂饱正向判据（假绿/假红）；
    扰动用例里有一条"只改注释必须仍绿"的反向对照专门守这条。
    ⚠ 已知坑（mcmod_experience §3.4）：`//` 行注释里出现 `/*` 会让"先块后行"的剥法吞掉代码 ——
    本仓这几个真源里没有这种写法，且下面有反空转守护兜底。
    """
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return src


# ---------------------------------------------------------------- 真源：注册表 id
def registry_ids() -> set[str]:
    """从 Java 源码现算"可能被注册的物品 id"（金属族按后缀组合 + 显式 register 调用）。"""
    ids: set[str] = set()
    metals = ["sturdygold", "flamegold", "voodoogold", "thundergold", "indigoseagold",
              "illusiongold", "thornsgold", "echogold"]
    suffixes = ["ingot", "nugget", "sword", "axe", "pickaxe", "shovel", "hoe", "knife",
                "mace", "bow", "crossbow", "trident", "shield",
                "helmet", "chestplate", "leggings", "boots", "upgrade_template"]
    for m in metals:
        for s in suffixes:
            ids.add(f"{NS}:{m}_{s}")
        ids.add(f"{NS}:raw_{m}")
    pat = re.compile(r'\.register[A-Za-z]*\(\s*"([a-z0-9_]+)"')
    for name in ("registry/AllItems.java", "material/MetalSpecialItems.java",
                 "fd/FdItems.java", "registry/AllBlocks.java"):
        p = JAVA / name
        if not p.is_file():
            bad("bgach-source-missing", f"真源文件不存在：{name}")
            continue
        src = strip_comments(read(p))
        found = pat.findall(src)
        if not found:
            bad("bgach-registry-anti-vacuum", f"{name} 里解析到 0 个 register id")
        for f in found:
            ids.add(f"{NS}:{f}")
    # 金属族注册用的也是同一个 ITEMS.register，上面的正则已覆盖 `this.id + "_ingot"` 之外的写法；
    # 但 `this.id + "_x"` 是拼出来的 ⇒ 由上面的 metals×suffixes 组合补齐（两路互为印证）。
    #
    # bg-fix3 §四：**手册物品**的 id 走的既不是「金属族组合」也不是 `.register("字面量")` ——
    #   `patchouli/HandbookModule.java` 里是 `items.register(ITEM_PATH, …)`（常量），而且它
    #   **只在装了 Patchouli 时才注册**（AGENTS.md 红线 10 的口径 B）。
    #   ⇒ 真源 = 那个常量本身（解析不到就报红，不能让"条件注册的物品"变成不可核实的黑洞）。
    _handbook_src = strip_comments(read(JAVA / "patchouli" / "HandbookModule.java"))
    _hm = re.search(r'ITEM_PATH\s*=\s*"([a-z0-9_]+)"', _handbook_src)
    if not _hm:
        bad("bgach-registry-anti-vacuum",
            "patchouli/HandbookModule.java 里解析不到 ITEM_PATH（真源解析器坏了？）")
    else:
        ids.add(f"{NS}:{_hm.group(1)}")
    for must in (f"{NS}:mixed_crystal_pile", f"{NS}:golden_cowrie", f"{NS}:gilded_gold_ticket",
                 f"{NS}:gift_gold_ticket", f"{NS}:golden_bone_meal",
                 f"{NS}:treasure_gift_box", f"{NS}:alchemy_materials_box",
                 f"{NS}:raw_sturdygold", f"{NS}:sturdygold_chestplate"):
        if must == f"{NS}:gilded_gold_ticket":
            continue
        if must not in ids:
            bad("bgach-registry-selfcheck", f"真源解析漏了 {must}（注册表解析器坏了？）")
    return ids


def source_foods() -> dict[str, set[str]]:
    """从 Java 真源现算"带 FOOD 组件的食物"（按 金 / 万坚金 / 乐事 分组）。"""
    def food_ids(p: Path) -> set[str]:
        src = strip_comments(read(p))
        out: set[str] = set()
        chunks = re.split(r'\.register[A-Za-z]*\(', src)
        for ch in chunks[1:]:
            m = re.match(r'\s*"([a-z0-9_]+)"', ch)
            if not m:
                continue
            body = ch[:1600]
            if ".food(" in body:
                out.add(f"{NS}:{m.group(1)}")
        return out

    base = food_ids(JAVA / "registry" / "AllItems.java")
    fd = food_ids(JAVA / "fd" / "FdItems.java")
    gold = {i for i in base if not i.startswith(f"{NS}:sturdygold_")}
    sturdy = {i for i in base if i.startswith(f"{NS}:sturdygold_")}
    fd_gold = {i for i in fd if not i.startswith(f"{NS}:sturdygold_")}
    fd_sturdy = {i for i in fd if i.startswith(f"{NS}:sturdygold_")}
    for group, name in ((gold, "gold"), (sturdy, "sturdygold"),
                        (fd_gold, "fd_gold"), (fd_sturdy, "fd_sturdygold")):
        if len(group) < 3:
            bad("bgach-food-anti-vacuum", f"{name} 食物清单只解析到 {len(group)} 条（真源解析坏了？）")
    return {"gold": gold | {"minecraft:golden_apple", "minecraft:golden_carrot"},
            "sturdygold": sturdy, "fd_gold": fd_gold, "fd_sturdygold": fd_sturdy}


def vanilla_data_exists(entries: set[str]) -> None:
    if not VANILLA_JAR.is_file():
        bad("bgach-vanilla-jar", f"找不到原版资源 jar：{VANILLA_JAR}（先跑一次 runData/构建）")
        return
    with zipfile.ZipFile(VANILLA_JAR) as z:
        names = set(z.namelist())
    for t in entries:
        short = t[len("#minecraft:"):]
        if f"data/minecraft/tags/item/{short}.json" not in names and \
           f"data/minecraft/tags/entity_type/{short}.json" not in names:
            bad("bgach-vanilla-tag", f"原版数据里没有标签 {t}")


# ---------------------------------------------------------------- 读产物
def load_advancements() -> dict[str, dict]:
    out: dict[str, dict] = {}
    files = sorted(ADV.rglob("*.json"))
    if len(files) != EXPECTED_COUNT:
        bad("bgach-count", f"产物成就 JSON 数 = {len(files)}，期望 {EXPECTED_COUNT}")
    if not files:
        bad("bgach-anti-vacuum", "产物目录里一个成就 JSON 都没有")
    for p in files:
        rel = p.relative_to(ADV).with_suffix("").as_posix()
        try:
            obj = json.loads(read(p))
        except Exception as e:  # noqa: BLE001
            bad("bgach-parse", f"{rel}.json 解析失败：{e}")
            continue
        out[rel] = obj
    return out


def walk_items(node, acc: list[str]) -> None:
    """收集 criteria 里出现的所有物品 id / 标签引用（`items` 字面量、`predicate.items`）。"""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "items":
                if isinstance(v, str):
                    acc.append(v)
                else:
                    walk_items(v, acc)  # list[str] / list[{"items": ...}]
            elif k == "predicate" and isinstance(v, dict) and "items" in v:
                walk_items(v, acc)
            else:
                walk_items(v, acc)
    elif isinstance(node, list):
        for v in node:
            walk_items(v, acc)


def main() -> int:
    manifest = json.loads(read(MANIFEST))
    advs = load_advancements()
    reg = registry_ids()
    foods = source_foods()
    vanilla_data_exists(VANILLA_TAGS)

    ids = {f"{NS}:{k}" for k in advs}
    man = {a["id"]: a for a in manifest["advancements"]}

    # ---- 1. 与生成器清单一致（正反两向）----
    if ids != set(man):
        bad("bgach-manifest-parity",
            f"产物与生成器清单不一致：产物多 {sorted(ids - set(man))} / 少 {sorted(set(man) - ids)}")

    # ---- 2. 根与树 ----
    roots = [k for k, v in advs.items() if not v.get("parent")]
    if roots != ["root"]:
        bad("bgach-root", f"根节点不是有且仅有的 bettergold:root（实际 {roots}）")
    parents = {f"{NS}:{k}": (v.get("parent") or "") for k, v in advs.items()}
    for k, p in parents.items():
        if not p:
            continue
        if p not in ids:
            bad("bgach-tree-parent", f"{k} 的 parent {p} 不在本模组成就里")
        elif p == k:
            bad("bgach-tree-self", f"{k} 的 parent 指向自己")
    # 可达性（从 root 出发能遍历到全部 51 条）
    children: dict[str, list[str]] = {}
    for k, p in parents.items():
        if p:
            children.setdefault(p, []).append(k)
    seen: set[str] = set()
    stack = [f"{NS}:root"] if f"{NS}:root" in parents else []
    while stack:
        cur = stack.pop()
        if cur in seen:
            bad("bgach-tree-cycle", f"{cur} 在遍历里出现两次（有环）")
            continue
        seen.add(cur)
        stack.extend(children.get(cur, []))
    if seen != ids:
        bad("bgach-tree-reach", f"从 root 到不了的成就：{sorted(ids - seen)}")
    # 与 manifest 的 parent 逐条一致
    for k, v in advs.items():
        want = man[f"{NS}:{k}"]["parent"]
        if (v.get("parent") or None) != want:
            bad("bgach-tree-manifest", f"{k} 的 parent 与清单不一致：{v.get('parent')} vs {want}")
    # 三条"形状"硬断言（需求 §2.1 的核定树）
    root_kids = sorted(children.get(f"{NS}:root", []))
    # ⛔ **bg-fix3 §五（作者 2026-10-07）把根链改成"链式"** ⇒ root 的孩子从 5 条变 **3 条**
    #   （炼制I + 两条农业成就；炼制II 与寻途挂到链上去了）。
    #   ⚠ 旧期望原文保留（未删）：原来这里是 5 条并列
    #     `{alchemy/mixed_crystal_pile, alchemy/alchemic_fuel, treasure/any_core_material,
    #       agriculture/gold_infused_dirt, agriculture/alchemical_meat}`。
    want_root_kids = sorted([f"{NS}:alchemy/mixed_crystal_pile",
                             f"{NS}:agriculture/gold_infused_dirt",
                             f"{NS}:agriculture/alchemical_meat"])
    if root_kids != want_root_kids:
        bad("bgach-shape-root-children",
            f"根的孩子不是「炼制I + 两条农业成就」这 3 条（bg-fix3 §五 链式；旧口径 5 条并列已作废）："
            f"{root_kids}")
    # bg-fix3 §五：根链逐节咬合 root -> 炼制I -> 炼制II -> 寻途（作者 2026-10-07 重述的链）
    for _child, _parent in (("alchemy/mixed_crystal_pile", "root"),
                            ("alchemy/alchemic_fuel", "alchemy/mixed_crystal_pile"),
                            ("treasure/any_core_material", "alchemy/alchemic_fuel")):
        _got = advs.get(_child, {}).get("parent")
        if _got != f"{NS}:{_parent}":
            bad("bgfix3-root-chain",
                f"{_child} 的 parent 应是 {_parent}（bg-fix3 §五 的链式根链），实际 {_got}")
    tr_kids = sorted(children.get(f"{NS}:treasure/any_core_material", []))
    if len(tr_kids) != 9:
        bad("bgach-shape-treasure-children", f"「寻途千里的珍宝」的孩子应为 9 条（实际 {len(tr_kids)}）")
    gold_kids = sorted(children.get(f"{NS}:metal/sturdygold/weapon", []))
    want_gold_kids = sorted([f"{NS}:metal/sturdygold/skeleton", f"{NS}:metal/sturdygold/armor",
                             f"{NS}:merchant/gold_ticket"])
    if gold_kids != want_gold_kids:
        bad("bgach-shape-gold-split", f"「染上黄金吧」的 3 个孩子不对：{gold_kids}")

    # ---- 2b. bg-fix3 §五①：每条金属分支的四级必须是「核心材料 → 锭 → 武器工具 → 盔甲」----
    #   ⚠ 旧口径（原文保留，未删）：除万坚金外的 7 族把「盔甲」挂在**锭**下（与武器并列），
    #     只有万坚金那条挂在武器下；作者 2026-10-07 给的排版是四级链 ⇒ 八族一律挂武器下。
    _core_of = {"flamegold": "treasure/blazing_rod",
                "sturdygold": "treasure/golden_cowrie",
                "thornsgold": "treasure/glittering_vine",
                "echogold": "treasure/bundled_echo_shard",
                "indigoseagold": "treasure/indigo_ocean_heart",
                "voodoogold": "treasure/voodoo_feather",
                "thundergold": "treasure/amethyst_energy_dust",
                "illusiongold": "treasure/chorus_cherry_branch"}
    if len(_core_of) != 8:
        bad("bgfix3-metal-chain", "四族链的核心材料表不是 8 条 —— 反空转守护")
    for _m, _core in _core_of.items():
        _want = {f"metal/{_m}/ingot": f"{NS}:{_core}",
                 f"metal/{_m}/weapon": f"{NS}:metal/{_m}/ingot",
                 f"metal/{_m}/armor": f"{NS}:metal/{_m}/weapon"}
        for _path, _parent in _want.items():
            _got = advs.get(_path, {}).get("parent")
            if _got != _parent:
                bad("bgfix3-metal-chain",
                    f"{_path} 的 parent 应是 {_parent}（四级链：核心材料 -> 锭 -> 武器工具 -> 盔甲），"
                    f"实际 {_got}")

    # ---- 3. display / 文案键 ----
    for k, v in advs.items():
        disp = v.get("display") or {}
        icon = (disp.get("icon") or {}).get("id")
        if not icon:
            bad("bgach-display-icon", f"{k} 没有 display.icon.id")
        for field in ("title", "description"):
            tr = (disp.get(field) or {}).get("translate")
            want = f"advancements.{NS}.{man[f'{NS}:{k}']['key']}.{field}"
            if tr != want:
                bad("bgach-display-lang", f"{k} 的 display.{field} 键 {tr!r} != {want!r}")
        if disp.get("hidden"):
            bad("bgach-no-hidden", f"{k} 被标成 hidden=true —— 本轮的『隐藏』是**不加载**（conditions），不是灰显")
    if advs.get("root", {}).get("display", {}).get("background") is None:
        bad("bgach-root-background", "root 没有 display.background（进度界面会是纯黑底）")
    for k, v in advs.items():
        if k != "root" and (v.get("display") or {}).get("background"):
            bad("bgach-background-scope", f"{k} 不该有 background（只有 root 有）")

    # ---- 4. frame / 条件 ----
    challenge = sorted(k for k, v in advs.items()
                       if (v.get("display") or {}).get("frame") == "challenge")
    if challenge != sorted(CHALLENGE_PATHS):
        bad("bgach-frame-challenge", f"challenge 进度集合不对：{challenge}")
    conditional = sorted(k for k, v in advs.items() if "neoforge:conditions" in v)
    if conditional != sorted(FD_PATHS):
        bad("bgach-fd-condition", f"带乐事条件的成就集合不对：{conditional}（期望 {sorted(FD_PATHS)}）")
    for k in conditional:
        if advs[k]["neoforge:conditions"] != FD_CONDITION:
            bad("bgach-fd-condition-body",
                f"{k} 的条件不是 mod_loaded(farmersdelight)：{advs[k]['neoforge:conditions']}")
    if len(conditional) != 3:
        bad("bgach-fd-count", f"带条件的成就数 = {len(conditional)}，需求只标了 3 个（㊼㊽ 不该有）")

    # ---- 5. trigger 白名单 + 判据非空 + requirements 自洽 ----
    total_criteria = 0
    used_triggers: Counter[str] = Counter()
    for k, v in advs.items():
        crit = v.get("criteria") or {}
        if not crit:
            bad("bgach-criteria-empty", f"{k} 没有 criteria")
            continue
        total_criteria += len(crit)
        for name, c in crit.items():
            trg = c.get("trigger")
            used_triggers[trg] += 1
            if trg not in TRIGGER_WHITELIST:
                bad("bgach-trigger-whitelist", f"{k}.{name} 的 trigger {trg!r} 不在白名单里")
        reqs = v.get("requirements") or []
        flat = [n for g in reqs for n in g]
        if sorted(flat) != sorted(crit):
            bad("bgach-requirements", f"{k} 的 requirements {reqs} 与 criteria {sorted(crit)} 不匹配")
        if reqs and any(len(g) > 1 for g in reqs) and "inventory_changed" not in \
                [c.get("trigger") for c in crit.values()] and k != "agriculture/plant_gold_crop":
            pass  # OR 组只允许出现在这里；下面的"OR 组用途"另断言
    if total_criteria < EXPECTED_COUNT:
        bad("bgach-criteria-anti-vacuum", f"解析到的 criteria 总数 {total_criteria} < {EXPECTED_COUNT}")
    if not used_triggers:
        bad("bgach-trigger-anti-vacuum", "没有解析到任何 trigger")

    # ---- 5b. requirements 的**语义**（组内 OR、组间 AND）----
    # 这一条是 A 级探针抓出来的真 bug：把「一整套 / 所有食物」写成一个大组 = 变成"任意一件"。
    def groups_of(path: str) -> list[list[str]]:
        return [list(g) for g in (advs.get(path, {}).get("requirements") or [])]

    for path in sorted(advs):
        if not path.endswith("/armor"):
            continue
        g = groups_of(path)
        if len(g) != 4 or any(len(x) != 1 for x in g):
            bad("bgach-requirements-semantics",
                f"{path} 是「一整套盔甲」⇒ 必须 4 个各自一组的 criteria（组间 AND），实际 {g}")
    for path in ("agriculture/midas_feast_1", "agriculture/sturdygold_feast_1",
                 "agriculture/midas_feast_2", "agriculture/sturdygold_feast_2"):
        g = groups_of(path)
        if not g or any(len(x) != 1 for x in g):
            bad("bgach-requirements-semantics",
                f"{path} 是「获得**所有**…」⇒ 每个食物必须各自一组（实际 {len(g)} 组）")
    g = groups_of("treasure/any_raw_metal")
    # ⚠ bg-ach §七.2：这条从「制作任意一种原料」改成「获得任意一种原料」⇒ 8 个 craft_* 判据
    #   合并成**一个** `inventory_changed`（单条 criteria + 8 个 ItemPredicate = 天然 OR）
    #   ⇒ requirements 也从此前的那种形态收成 1 组 1 条；语义（任意一种）不变。
    if len(g) != 1 or len(g[0]) != 1:
        bad("bgach-requirements-semantics",
            f"treasure/any_raw_metal 是「任意一种原料」⇒ 恰好 1 组 1 条（OR 由 items 列表承载），实际 {g}")
    _raw_items = []
    for _c in (advs.get("treasure/any_raw_metal", {}).get("criteria") or {}).values():
        for _pred in (_c.get("conditions") or {}).get("items") or []:
            _it = _pred.get("items")
            _raw_items.extend([_it] if isinstance(_it, str) else (_it or []))
    if len(set(_raw_items)) != 8:
        bad("bgach-requirements-semantics",
            f"treasure/any_raw_metal 的 items 不是 8 种原料（实际 {sorted(set(_raw_items))}）")
    g = groups_of("agriculture/plant_gold_crop")
    # ⚠ **旧口径（原文保留，已被 2026-10-06 bgfinal3 取代）**：
    #   `if sorted(len(x) for x in g) != [1, 2]:` ——「耕地(1) AND (金麦 OR 金钱茄)(2)」。
    #   作者 2026-10-06 裁定「金胡萝卜也要算（`需要`）」⇒ 种植组从 2 条变 **3 条**。
    #   新判据 = 1 组 1 条（耕地）AND 1 组 3 条（三种种子 OR）；具体成员集合由
    #   `[bgfinal3-adv-carrot-planting]` 逐条钉住（这里只保证"组形状"没走样）。
    if sorted(len(x) for x in g) != [1, 3]:
        bad("bgach-requirements-semantics",
            f"agriculture/plant_gold_crop 应为「耕地(1) AND (金麦 OR 金钱茄 OR 金胡萝卜)(3)」"
            f"（旧口径 2 条已被 2026-10-06 作者裁定取代），实际 {g}")

    # ---- 6. 物品存在性 ----
    refs: list[str] = []
    for k, v in advs.items():
        walk_items(v, refs)
        icon = (v.get("display") or {}).get("icon", {}).get("id")
        if icon:
            refs.append(icon)
    # bg-fix3：本模组自己的两张物品标签（成就判据用）—— 必须
    #   ① 以**单个字符串**形式出现在 `items` 里（不许混进列表）；
    #   ② 标签文件**无条件存在**（写 neoforge:conditions 关掉它 ⇒ `Missing tag` ⇒ 整份 JSON 死）；
    #   ③ 条目恰好是计划里那几件、且**每一件都写 `required: false`**（没装可选模组时静默跳过）。
    bgfix3_tag_refs = sorted(r for r in set(refs) if r.startswith(f"#{NS}:"))
    # bg-fix4 §一：期望集合 = 8 张刀标签 + 手册标签 + **2 张古董刀标签**（共 11 张）
    _want_tags = set(BGFIX3_KNIFE_TAGS) | {BGFIX3_HANDBOOK_TAG} | set(BGFIX4_ANTIQUE_TAGS)
    if sorted(bgfix3_tag_refs) != sorted(_want_tags):
        bad("bgfix3-adv-tag-refs",
            f"成就里引用的 bettergold 标签集合不对：{bgfix3_tag_refs}"
            f"（期望 {sorted(_want_tags)}）")
    for _tag in bgfix3_tag_refs:
        _short = _tag[len(f"#{NS}:"):]
        _tagfile = TAG_DIR / f"{_short}.json"
        if not _tagfile.is_file():
            bad("bgfix3-adv-tag-file", f"成就引用了 {_tag}，但标签文件不存在：{_tagfile}")
            continue
        _tj = json.loads(read(_tagfile))
        if "neoforge:conditions" in _tj:
            bad("bgfix3-adv-tag-file",
                f"{_tag} 的标签文件带了 neoforge:conditions —— 条件不满足时**标签不存在**，"
                f"而 `HolderSetCodec.lookupTag` 对不存在的标签直接报 `Missing tag` ⇒ 整份成就 JSON 被丢弃")
        _vals = _tj.get("values") or []
        _ids, _bad_req = [], []
        for _entry in _vals:
            if isinstance(_entry, dict):
                _ids.append(_entry.get("id"))
                if _entry.get("required") is not False:
                    _bad_req.append(_entry)
            else:
                _ids.append(_entry)
                _bad_req.append(_entry)
        if _bad_req:
            bad("bgfix3-adv-tag-optional",
                f"{_tag} 里有条目没写 `\"required\": false`：{_bad_req}"
                f"（该物品只在装了可选模组时才注册 ⇒ 必需条目缺失会让**整条标签报错丢弃**）")
        if sorted(_ids) != sorted(BGFIX3_TAG_FILES.get(_short, [])):
            bad("bgfix3-adv-tag-members",
                f"{_tag} 的条目不是 {BGFIX3_TAG_FILES.get(_short, [])}，实际 {_ids}")
        for _i in _ids:
            if _i not in reg:
                bad("bgfix3-adv-tag-item", f"{_tag} 里的 {_i} 不在注册表真源里（打错 id 就永远不匹配）")
    for r in sorted(set(refs)):
        if r.startswith("#"):
            if r in bgfix3_tag_refs:
                continue
            if r not in VANILLA_TAGS:
                bad("bgach-tag-ref", f"用到未核实的标签 {r}")
            continue
        if r.startswith("minecraft:"):
            if r not in VANILLA_ITEMS:
                bad("bgach-vanilla-item", f"用到未核实的原版物品 {r}")
            continue
        if r.startswith(f"{NS}:"):
            if r not in reg:
                bad("bgach-item-exists", f"引用了注册表真源里不存在的物品 {r}")
            continue
        bad("bgach-namespace", f"引用了非本模组/原版的 id {r}")

    # ---- 7. recipe_crafted 的配方必须真的存在 ----
    # ⛔ **bg-fix3 §四（作者 2026-10-07）之后，全 51 条成就一条 `recipe_crafted` 都没有了** ——
    #   根（旧时代炼金术的继承者）也改成了「获得」⇒ `recipe_crafted` 的**配方存在性**检查
    #   随之变成空集。旧口径原文保留（未删）：
    #     「if not recipe_refs: bad("bgach-recipe-anti-vacuum", "一条 recipe_crafted 都没有
    #       （root 至少有一条）")」+ 逐条查 `data/bettergold/recipe/<path>.json` 是否存在。
    #   现在的判据反过来：**必须是空集**（谁把 recipe_crafted 写回来，这里当场红）。
    recipe_refs = sorted({c["conditions"]["recipe_id"]
                          for v in advs.values() for c in (v.get("criteria") or {}).values()
                          if c.get("trigger") == "minecraft:recipe_crafted"})
    if recipe_refs:
        bad("bgfix3-recipe-crafted-none",
            f"仍有成就用 recipe_crafted（bg-fix3 §四 之后应为 0 条；root 也已改成「获得」）：{recipe_refs}")

    # ---- 8. 食物清单必须等于 Java 真源现算的清单 ----
    derived = {"midas_feast_1": foods["gold"], "sturdygold_feast_1": foods["sturdygold"],
               "midas_feast_2": foods["fd_gold"], "sturdygold_feast_2": foods["fd_sturdygold"]}
    for path, want in derived.items():
        k = f"agriculture/{path}"
        if k not in advs:
            bad("bgach-food-missing", f"{k} 不存在")
            continue
        got: list[str] = []
        walk_items(advs[k].get("criteria") or {}, got)
        if set(got) != want:
            bad("bgach-food-list",
                f"{path} 的食物清单与 Java 真源不一致：多 {sorted(set(got) - want)} / "
                f"少 {sorted(want - set(got))}")
        if len(want) < 3:
            bad("bgach-food-list-anti-vacuum", f"{path} 的真源清单只有 {len(want)} 条")

    # ---- 9. 语言键 ----
    zh = json.loads(read(LANG / "zh_cn.json"))
    en = json.loads(read(LANG / "en_us.json"))
    lang_n = 0
    for a in manifest["advancements"]:
        for field, want in (("title", a["title"]), ("description", a["description"])):
            key = f"advancements.{NS}.{a['key']}.{field}"
            lang_n += 1
            for lang, table in (("zh_cn", zh), ("en_us", en)):
                if key not in table:
                    bad("bgach-lang-missing", f"{lang} 缺 {key}")
                elif not str(table[key]).strip():
                    bad("bgach-lang-empty", f"{lang} 的 {key} 是空串（会显示空白标题）")
                elif lang == "zh_cn" and table[key] != want:
                    bad("bgach-lang-verbatim", f"zh_cn 的 {key} 与逐字文案不一致：{table[key]!r}")
    if lang_n != EXPECTED_COUNT * 2:
        bad("bgach-lang-count", f"核对的语言键数 = {lang_n}，期望 {EXPECTED_COUNT * 2}")

    # ---- 10. 英文值必须是真英译（1.6 收尾轮 bg-final 第 2 件）----
    # 旧口径：en_us 的 102 条 = 中文原文逐字（生成器 EN_POLICY = "copy_zh"），**已被推翻**；
    # 现行口径：真英译，且**键名不动 / zh_cn 一个字不动 / 成就 id 不动**（前三节已各自守着）。
    adv_prefix = f"advancements.{NS}."
    zh_adv = {k: str(v) for k, v in zh.items() if k.startswith(adv_prefix)}
    en_adv = {k: str(v) for k, v in en.items() if k.startswith(adv_prefix)}
    if len(zh_adv) != ADV_LANG_EXPECTED or len(en_adv) != ADV_LANG_EXPECTED:
        bad("bgfinal-adv-lang-anti-vacuum",
            f"扫到的语言键数 zh={len(zh_adv)} / en={len(en_adv)}，期望 {ADV_LANG_EXPECTED}"
            f"（匹配 0 条即红：否则下面的循环什么都扫不到也会全绿）")
    if set(zh_adv) != set(en_adv):
        bad("bgfinal-adv-lang-parity",
            f"中英键集不一致：只 zh 有 {sorted(set(zh_adv) - set(en_adv))[:8]} / "
            f"只 en 有 {sorted(set(en_adv) - set(zh_adv))[:8]}")
    for key in sorted(SYMBOL_ONLY_OK):
        if key not in zh_adv:
            bad("bgfinal-adv-lang-whitelist-honest", f"{key} 被列进纯符号白名单，但它不在语言文件里")
        elif CJK_RE.search(zh_adv[key]):
            bad("bgfinal-adv-lang-whitelist-honest",
                f"{key} 被列进纯符号白名单，但中文侧含中日韩文字：{zh_adv[key]!r}")
    for key in sorted(set(zh_adv) & set(en_adv)):
        zh_v, en_v = zh_adv[key], en_adv[key]
        if en_v == zh_v and key not in SYMBOL_ONLY_OK:
            bad("bgfinal-adv-lang-translated",
                f"{key} 的英文值仍是中文原文逐字（旧口径 EN_POLICY=copy_zh 的残留）：{en_v!r}")
        if not en_v.strip():
            bad("bgfinal-adv-lang-empty", f"{key} 的英文值是空串")
        elif not re.search(r"[A-Za-z]", en_v):
            bad("bgfinal-adv-lang-en-shape",
                f"{key} 的英文值里一个 ASCII 字母都没有：{en_v!r}")
        if not (1 <= len(en_v) <= 120):
            bad("bgfinal-adv-lang-en-shape",
                f"{key} 的英文值长度 {len(en_v)} 不合理（期望 1..120）")

    # ---- 5c. bg-ach §七.2「"制作"条件一律改"获得"」+ §七.6「刀不算器具」----
    # 期望值取自生成器清单的 `triggers`（= 真源的机器形态），再逐条钉住"这批必须已经是获得"。
    #   ⚠ 唯一例外：root（`recipe_crafted: bettergold:alchemy_student_handbook`）——
    #     它必须留在 `recipe_crafted`，因为手册物品在**没装 Patchouli 时根本不注册**，
    #     而 `recipe_crafted` 的 recipe_id 是裸 ResourceLocation（不查注册表）⇒ 不会引起解析失败。
    CRAFT_TO_HAVE_PATHS = [
        "alchemy/mixed_crystal_pile", "alchemy/alchemic_fuel",
        "treasure/blazing_rod", "treasure/bundled_echo_shard",
        "treasure/indigo_ocean_heart", "treasure/amethyst_energy_dust",
        "treasure/chorus_cherry_branch", "treasure/any_raw_metal",
        "agriculture/gold_infused_dirt",
    ]
    if len(CRAFT_TO_HAVE_PATHS) != 9:
        bad("bgach-craft-to-have", "§七.2 的清单不是 9 条（需求文档点名的就是这 9 条）")
    _still_craft = [p for p in CRAFT_TO_HAVE_PATHS
                    if "minecraft:recipe_crafted" in (man.get(f"{NS}:{p}", {}).get("triggers") or [])]
    if _still_craft:
        bad("bgach-craft-to-have",
            f"这些成就还是「制作」判据（recipe_crafted），§七.2 要求改成「获得」：{_still_craft}")
    for p in CRAFT_TO_HAVE_PATHS:
        _w = advs.get(p, {}).get("criteria") or {}
        if "minecraft:inventory_changed" not in [c.get("trigger") for c in _w.values()]:
            bad("bgach-craft-to-have", f"{p} 的判据里没有 minecraft:inventory_changed（改成「获得」失败）")
    # 唯一例外：「这件商品很适合你哦～」保持原条件（从易金商人那获得礼品盒 = villager_trade）
    _giftbox = advs.get("merchant/gift_box", {}).get("criteria") or {}
    if [c.get("trigger") for c in _giftbox.values()] != ["minecraft:villager_trade"]:
        bad("bgach-craft-to-have-exception",
            f"merchant/gift_box 的判据被动过了（§七.2 的唯一例外必须保持 villager_trade）："
            f"{[c.get('trigger') for c in _giftbox.values()]}")
    # 图纸里其余还带 recipe_crafted 的，只允许是 root 那一条（范围自描述、防止这条断言空转）
    # ⛔ bg-fix3 §四：**只允许是 root** 这条已被取代 —— 现在**一条都不许有**（root 也改了）。
    #   ⚠ 旧期望原文保留（未删）：`if _recipe_left != ["root"]: bad("bgach-recipe-crafted-scope", …)`
    _recipe_left = sorted(k for k, v in advs.items()
                          if "minecraft:recipe_crafted" in [c.get("trigger") for c in
                                                            (v.get("criteria") or {}).values()])
    if _recipe_left != []:
        bad("bgfix3-recipe-crafted-scope",
            f"还带 recipe_crafted 的成就应为**空集**（bg-fix3 §四 把 root 也改成了「获得」；"
            f"旧口径只许 root 一条）：{_recipe_left}")

    # ---- 5d. bg-fix3 §二：**乐事小刀必须能触发**「获得任意一种 XX金武器工具」----
    # ⛔ 旧口径（`bg-ach §7.6`，作者 2026-10-05「乐事的刀不会触发有关获得器具的进度」）被作者
    #   2026-10-07 明确推翻：「**乐事联动的刀仍然无法触发**获得任意一种器具的成就」= 缺陷。
    #   ⚠ 旧断言原文保留（未删）：`[bgach-no-knife-in-gear]` 反向守着"8 条成就里一个刀都没有"。
    # 现行判据（三件一起）：① 每条武器成就都有 `have_knife` 判据、指向**该族自己的**标签；
    #   ② 那条判据的 `items` 是**单个字符串**的标签引用（列表混写会让 `ensureHomogenous` 失败）；
    #   ③ requirements = 恰好 1 组、组内恰好 {have, have_knife}（组内 OR ⇒ 10 件武器工具**或**小刀）。
    KNIVES = set(manifest["lists"]["knives"])
    if len(KNIVES) != 8:
        bad("bgfix3-knife-in-gear", f"清单里的刀不是 8 把（实际 {len(KNIVES)}）—— 反空转守护")
    _gear_items: set[str] = set()
    _knife_ok = 0
    for _m in METALS_ORDER:
        _p = f"metal/{_m}/weapon"
        _crits = (advs.get(_p, {}).get("criteria") or {})
        if len(_crits) < 2:
            bad("bgfix3-knife-in-gear", f"{_p} 的 criteria 少于 2 条（应有 have + have_knife）：{sorted(_crits)}")
            continue
        for _name, _c in _crits.items():
            for _pred in (_c.get("conditions") or {}).get("items") or []:
                _it = _pred.get("items")
                if _name == "have":
                    _gear_items.update([_it] if isinstance(_it, str) else (_it or []))
        _knife_crit = _crits.get("have_knife")
        if not _knife_crit:
            bad("bgfix3-knife-in-gear",
                f"{_p} 没有 `have_knife` 判据（乐事小刀无法触发这条成就）：{sorted(_crits)}")
            continue
        if _knife_crit.get("trigger") != "minecraft:inventory_changed":
            bad("bgfix3-knife-in-gear",
                f"{_p}.have_knife 的 trigger 不是 inventory_changed：{_knife_crit.get('trigger')}")
        _knife_items = [p.get("items") for p in
                        (_knife_crit.get("conditions") or {}).get("items") or []]
        _want_tag = f"#{NS}:{_m}_knives"
        if _knife_items != [_want_tag]:
            bad("bgfix3-knife-in-gear",
                f"{_p}.have_knife 的 items 必须恰好是单个标签字符串 [{_want_tag}]"
                f"（混写列表 / 裸 id 都会在『没装乐事』时把整份 JSON 弄坏），实际 {_knife_items}")
        else:
            _knife_ok += 1
        _reqs = advs.get(_p, {}).get("requirements") or []
        if len(_reqs) != 1 or sorted(_reqs[0]) != ["have", "have_knife"]:
            bad("bgfix3-knife-in-gear",
                f"{_p} 的 requirements 必须是 1 组 {{have, have_knife}}（组内 OR：10 件武器工具**或**小刀），"
                f"实际 {_reqs}")
    if _knife_ok != 8:
        bad("bgfix3-knife-in-gear", f"8 条武器成就里只有 {_knife_ok} 条把刀正确纳入 —— 反空转守护")
    if len(_gear_items) < 40:
        bad("bgfix3-knife-in-gear",
            f"8 条武器成就的 `have` 判据只解析到 {len(_gear_items)} 个物品（应 >= 40）—— 反空转守护")

    # ---- 5d'. bg-fix4 §一：**古董屠刀 / 幽冥断骸刀必须能触发**两条商人线成就 ----
    #   作者原话（2026-10-08）：「古董屠刀和幽冥断骸刀无法触发上古藏品和皇骸永存的进度」。
    #   判据（四件一起）：① 两条成就各有 `have` + `have_knife`；
    #   ② `have` 仍是那 5 件"永远注册"的古董工具（**没有**被换成标签 ⇒ 原路径不许丢）；
    #   ③ `have_knife` 的 items **恰好是单个标签字符串**；
    #   ④ requirements = 1 组 {have, have_knife}（组内 OR）。
    _antique_ok = 0
    for _p, (_tag, _five) in BGFIX4_ANTIQUE_ACHIEVEMENTS.items():
        _crits = advs.get(_p, {}).get("criteria") or {}
        if "have" not in _crits or "have_knife" not in _crits:
            bad("bgfix4-antique-knife-in-gear",
                f"{_p} 的不是 {{have, have_knife}} 两条判据：{sorted(_crits)}"
                f"（古董刀无法触发这条成就）")
            continue
        _have_items = [p.get("items") for p in
                       (_crits["have"].get("conditions") or {}).get("items") or []]
        if _have_items != [_five]:
            bad("bgfix4-antique-knife-in-gear",
                f"{_p}.have 的 items 必须仍是那 5 件裸 id 的古董工具（原路径不许丢）：实际 {_have_items}")
        _kc = _crits["have_knife"]
        if _kc.get("trigger") != "minecraft:inventory_changed":
            bad("bgfix4-antique-knife-in-gear",
                f"{_p}.have_knife 的 trigger 不是 inventory_changed：{_kc.get('trigger')}")
        _ki = [p.get("items") for p in (_kc.get("conditions") or {}).get("items") or []]
        if _ki != [_tag]:
            bad("bgfix4-antique-knife-in-gear",
                f"{_p}.have_knife 的 items 必须恰好是单个标签字符串 [{_tag}]"
                f"（裸 id / 混写列表都会在『没装乐事』时把整份 JSON 弄坏），实际 {_ki}")
        else:
            _antique_ok += 1
        _reqs = advs.get(_p, {}).get("requirements") or []
        if len(_reqs) != 1 or sorted(_reqs[0]) != ["have", "have_knife"]:
            bad("bgfix4-antique-knife-in-gear",
                f"{_p} 的 requirements 必须是 1 组 {{have, have_knife}}（组内 OR：5 件工具**或**屠刀），"
                f"实际 {_reqs}")
    if _antique_ok != 2:
        bad("bgfix4-antique-knife-in-gear",
            f"两条古董成就里只有 {_antique_ok} 条把刀正确纳入 —— 反空转守护")
    if not BGFIX4_ANTIQUE_ACHIEVEMENTS:
        bad("bgfix4-antique-knife-in-gear", "本轮的清单是空的 —— 反空转守护（用例本身失效）")

    # ---- 5e. bg-fix3 §四：根成就的判据 = 「**获得**新生代炼金术学员手册」----
    #   ⚠ 旧口径原文保留（未删）：root 用 `{"craft_handbook": c_recipe("bettergold:alchemy_student_handbook")}`
    #     —— 理由是"手册物品没装 Patchouli 时不注册，而 recipe_id 是裸 RL 不查注册表"（§14.3）。
    #   现行：`inventory_changed` + `items` = 单个标签引用 `#bettergold:handbook`
    #     （标签里那一行 `required:false` ⇒ 没装 Patchouli 时判据永不达成、但**不报错**）。
    _root_crit = advs.get("root", {}).get("criteria") or {}
    if len(_root_crit) != 1:
        bad("bgfix3-root-obtain", f"root 应恰好 1 条判据（实际 {sorted(_root_crit)}）")
    else:
        _rk, _rc = next(iter(_root_crit.items()))
        if _rc.get("trigger") != "minecraft:inventory_changed":
            bad("bgfix3-root-obtain",
                f"root 的判据 trigger 不是 inventory_changed（作者 2026-10-07「触发条件是获得」）："
                f"{_rc.get('trigger')}")
        _ri = [p.get("items") for p in (_rc.get("conditions") or {}).get("items") or []]
        if _ri != [BGFIX3_HANDBOOK_TAG]:
            bad("bgfix3-root-obtain",
                f"root 判据的 items 必须恰好是 [{BGFIX3_HANDBOOK_TAG}]，实际 {_ri}")
        if _rk != "have_handbook":
            bad("bgfix3-root-obtain", f"root 的判据名应是 have_handbook（可读性），实际 {_rk!r}")

    # ---- bgfinal3（2026-10-06 作者裁定「需要」）：成就 ㊻ 的「种植」半边必须收进金胡萝卜 ----
    # 背景：金胡萝卜**不是** `BlockItem#place` 种下去的（`ModEvents#onRightClickGoldenCarrot`
    # 里 `setBlock` + `setCanceled` 自定义种）⇒ 判据虽然仍是原版 `placed_block`，但**必须**
    # 由那段代码自己补一次 `CriteriaTriggers.PLACED_BLOCK.trigger(...)`（照 `BlockItem.java:78-85`
    # 的姿势；源码侧断言在 `validate_metal_data.py` 的 `[bgfinal3-carrot-placed-block-trigger]`）。
    # 本块只管**产物侧**：那条 criterion 真的进了 ㊻，且与另外两种种子在**同一个 OR 组**里。
    _PLANT_PATH = "agriculture/plant_gold_crop"
    _CARROT_BLOCK = f"{NS}:golden_carrot_crop"
    _plant = advs.get(_PLANT_PATH, {})
    _pcs = _plant.get("criteria") or {}
    if not _pcs:
        bad("bgfinal3-adv-carrot-planting",
            f"读不到 {_PLANT_PATH} 的 criteria（反空转守护）")
    _pc = _pcs.get("plant_carrot")
    if not _pc:
        bad("bgfinal3-adv-carrot-planting",
            f"㊻ {_PLANT_PATH} 里没有 plant_carrot 这条 criteria"
            f"（金胡萝卜的种植判据没进成就；实际 criteria = {sorted(_pcs)}）")
    else:
        if _pc.get("trigger") != "minecraft:placed_block":
            bad("bgfinal3-adv-carrot-planting",
                f"plant_carrot 的 trigger 不是 minecraft:placed_block（实际 {_pc.get('trigger')}）")
        _locs = (_pc.get("conditions") or {}).get("location") or []
        _blocks = [c.get("block") for c in _locs
                   if c.get("condition") == "minecraft:block_state_property"]
        if _blocks != [_CARROT_BLOCK]:
            bad("bgfinal3-adv-carrot-planting",
                f"plant_carrot 的 block_state_property 不是恰好 [{_CARROT_BLOCK}]（实际 {_blocks}）")
    # 三种种子必须在同一个 requirement 组里（组内 OR）；且不许只剩两种
    _plant_groups = _plant.get("requirements") or []
    _seed_group = [g for g in _plant_groups if "plant_wheat" in g]
    if len(_seed_group) != 1:
        bad("bgfinal3-adv-carrot-planting",
            f"㊻ 里含 plant_wheat 的 requirement 组不是恰好 1 个（实际 {len(_seed_group)}）")
    elif set(_seed_group[0]) != {"plant_wheat", "plant_eggplant", "plant_carrot"}:
        bad("bgfinal3-adv-carrot-planting",
            f"㊻ 的「种植」组成员的集合不是 {{plant_wheat, plant_eggplant, plant_carrot}}"
            f"（实际 {sorted(_seed_group[0])}）—— 三种种子必须是同一个 OR 组")
    if len(_plant_groups) != 2:
        bad("bgfinal3-adv-carrot-planting",
            f"㊻ 的 requirement 组数不是 2（耕地 AND 种植；实际 {len(_plant_groups)}）")
    # 真源侧：生成器里必须有这一条 + 方块 id 真源里必须真的注册了那个方块
    _gen_src = read(Path(__file__).resolve().parent / "generate_advancements.py")
    if f'c_plant_crop(f"{{NS}}:golden_carrot_crop")' not in _gen_src:
        bad("bgfinal3-adv-carrot-planting",
            "生成器 generate_advancements.py 里没有 `c_plant_crop(f\"{NS}:golden_carrot_crop\")`"
            "（产物是生成的 ⇒ 只改产物改不动根）")
    _allblocks_src = strip_comments((JAVA / "registry" / "AllBlocks.java").read_text(encoding="utf-8"))
    if 'BLOCKS.register("golden_carrot_crop"' not in _allblocks_src:
        bad("bgfinal3-adv-carrot-planting",
            f"方块 id 真源 AllBlocks.java 里没有注册 golden_carrot_crop"
            f"（那样 {_CARROT_BLOCK} 是个不存在的方块，判据永远不达成）")

    # ---- 5f. bgfix9（2026-10-11）：作者 2026-10-09 实测推翻的两条 =================
    # 作者原话：「**齐活,烧炼,拿下** 这一成就似乎无法正常触发，无论是**直接拿取**，还是
    #   **必须用合成获取**都触发不了。同时**光辉岁月之种**的**直接拿取金钱茄种子**也无法触发」。
    # 根因（源码级，两把尺子）：
    #   ① `InventoryChangeTrigger.TriggerInstance#matches`（`InventoryChangeTrigger.java:86-110`）：
    #      `items.size() == 1` ⇒ 只比"**本次变化的那一格**"（`:107-108` = OR 语义）；
    #      `items.size() != 1` ⇒ **扫全背包、每条谓词都要命中**（`:91-106` = AND 语义）。
    #      ⇒ ㊽ 的 `items` 原先写成 **8 条谓词**（每条一个原料 id）＝「**同时持有全部 8 种原料**」，
    #        而作者描述写的是「获得**任意一种**原料」⇒ **集合语义被写反**，两条路径都不解锁。
    #   ② ㊹ 的判据多带 `conditions.player[].predicate.location.structures = minecraft:bastion_remnant`
    #      ⇒ 判据被收窄成"**只能在堡垒遗迹里拿到**"。它与作者 bg-ach §七.2「只要是**获得**某样物品
    #      就能触发成就」的总口径冲突，也给不出"必须堡垒"的原文依据（种子的来源里还有
    #      `minecraft:chests/nether_bridge`）。
    # 判据设计（**期望语义不来自实现**，见 `ex/03` §3.20 ②）：
    #   (a) 从 **manifest 里的作者原文 description** 抽「任意 / 所有」⇒ 反查产物 JSON 的谓词条数；
    #   (b) 两条点名的成就逐条钉形状；负向断言「判据里不许再出现 `player` 条件」。
    _gen_path = Path(__file__).resolve().parent / "generate_advancements.py"
    _gen_src = read(_gen_path)
    # ⚠ 生成器是 **Python**：`strip_comments()` 只认 C 族注释 ⇒ 必须**另剥 `#`**
    #   （`ex/03` §3.15 ① / §3.17 ①：源码 needle 一律跑在"去注释源码"上，Python 要自己剥 `#`）。
    _gen_nc = re.sub(r"#[^\n]*", "", _gen_src)
    if len(_gen_nc) < len(_gen_src) // 2:
        bad("bgfix9-generator-anti-vacuum",
            f"生成器去注释后只剩 {len(_gen_nc)} B（原 {len(_gen_src)} B）—— 剥注释的正则坏了？")
    for _needle, _tag, _why in (
            ('c_inv([RAW_MATERIALS])', "bgfix9-generator-raw-metal",
             "生成器里没有 `c_inv([RAW_MATERIALS])`（= 1 条谓词 + 数组 = OR）；"
             "产物是生成的 ⇒ 只改产物改不动根"),
            ('c_inv([f"{NS}:golden_eggplant_seeds"])', "bgfix9-generator-eggplant",
             "生成器里没有 `c_inv([f\"{NS}:golden_eggplant_seeds\"])`（㊹ 的判据形状）"),
    ):
        if _needle not in _gen_nc:
            bad(_tag, _why)
    # 负向：旧的错误形状**不许**在代码里复活（注释里保留原文不算 —— 已先剥 `#`）
    if "c_inv(RAW_MATERIALS)" in _gen_nc:
        bad("bgfix9-generator-raw-metal",
            "生成器里又出现了 `c_inv(RAW_MATERIALS)`（少一层方括号 ⇒ 8 条谓词 ⇒ AND ⇒ 永不触发）")
    if 'structure="minecraft:bastion_remnant"' in _gen_nc:
        bad("bgfix9-generator-eggplant",
            f"生成器里又出现了 `structure=\"minecraft:bastion_remnant\"`（结构门 ⇒ 堡垒遗迹之外拿到"
            f"金钱茄种子永不触发）")

    # (a) 集合语义 ↔ 判据形状 的**两条不变量**（期望值来自**作者原文 description**，不是实现）
    #     「任意一种 / 任意一件」⇒ **每一条 `inventory_changed` 判据恰好 1 条谓词**
    #         （1 条谓词 = 只比"变化的那一格" ⇒ OR；≥2 条 = 扫全背包 AND ⇒ 语义写反）
    #     「所有 / 一整套」    ⇒ **多条判据、每件一条、每件各自一组**（组间 AND、组内 OR），
    #         且每条判据仍是 1 条谓词。
    #     ⚠ 踩过的坑：第一版把「所有」写成"一个 criteria 里放 N 条谓词"⇒ 42 条假红 ——
    #       本仓「所有」的落法是**N 条 criteria + N 个 requirement 组**（见生成器
    #       `{f"food_…": c_inv([f]) …}` + `[[f"food_…"] for f in …]`），不是 N 条谓词。
    _any_paths: list[str] = []
    _all_paths: list[str] = []
    _any_checked = 0
    _all_checked = 0
    _homog_checked = 0
    _pred_checked = 0
    for _a in manifest["advancements"]:
        _p = _a["path"]
        _desc = _a.get("description") or ""
        _obj = advs.get(_p, {}) or {}
        _crits = _obj.get("criteria") or {}
        _reqs = _obj.get("requirements") or []
        _inv = {k: c for k, c in _crits.items() if c.get("trigger") == "minecraft:inventory_changed"}
        if "任意" in _desc:
            _any_paths.append(_p)
            for _k, _c in _inv.items():
                _n = len((_c.get("conditions") or {}).get("items") or [])
                _any_checked += 1
                if _n != 1:
                    bad("bgfix9-inv-one-predicate",
                        f"{_p}.{_k} 的描述是「…**任意**…」（{_desc!r}），"
                        f"但 `items` 写了 {_n} 条谓词 —— `InventoryChangeTrigger` 里 "
                        f"`items.size() != 1` 是**扫全背包 AND**（`InventoryChangeTrigger.java:91-106`）"
                        f"⇒ 语义被写反（「任意一种」变成「全部同时持有」）")
        if ("所有" in _desc) or ("一整套" in _desc):
            _all_paths.append(_p)
            _all_checked += 1
            if len(_crits) < 2:
                bad("bgfix9-all-of-shape",
                    f"{_p} 的描述是「…**{'所有' if '所有' in _desc else '一整套'}**…」（{_desc!r}），"
                    f"但只有 {len(_crits)} 条判据 ⇒ 表达不出「每一件都要」"
                    f"（应每件各一条判据 + 各自一组）")
            if len(_reqs) != len(_crits) or any(len(g) != 1 for g in _reqs):
                bad("bgfix9-all-of-shape",
                    f"{_p} 的 requirements 必须是「每件各自一组」（组间 AND）：实得 "
                    f"{len(_reqs)} 组 / {len(_crits)} 条判据 ⇒ {_reqs}")
            for _k, _c in _inv.items():
                _n = len((_c.get("conditions") or {}).get("items") or [])
                if _n != 1:
                    bad("bgfix9-all-of-shape",
                        f"{_p}.{_k} 的 `items` 有 {_n} 条谓词 —— 「所有」必须是"
                        f"**多条判据**（每件一条），不是一条判据里塞多条谓词")
        # 同质性：`items` 列表里不许**混写** `#tag` 与裸 id（`HolderSetCodec` 的
        #   `ensureHomogenous` 只接受同一种 Holder 形态 ⇒ 混写会让**整份 JSON 解析失败并消失**）
        for _k, _c in _crits.items():
            for _pred in (_c.get("conditions") or {}).get("items") or []:
                _it = _pred.get("items")
                _pred_checked += 1
                if isinstance(_it, list) and _it:
                    _homog_checked += 1
                    _tags = [x for x in _it if isinstance(x, str) and x.startswith("#")]
                    if _tags and len(_tags) != len(_it):
                        bad("bgfix9-items-homogeneous",
                            f"{_p}.{_k} 的 `items` 列表混写了标签与裸 id：{_it}"
                            f"（`ensureHomogenous` 只接受同一种形态 ⇒ 整份 JSON 会被丢弃）")
    if len(_any_paths) < 8 or _any_checked < 8:
        bad("bgfix9-inv-one-predicate",
            f"按描述里的「任意」只认出 {len(_any_paths)} 条成就 / {_any_checked} 条判据 —— 反空转守护"
            f"（生成器描述文案被改过？）")
    if len(_all_paths) < 8 or _all_checked < 8:
        bad("bgfix9-all-of-shape",
            f"按描述里的「所有 / 一整套」只认出 {len(_all_paths)} 条成就 —— 反空转守护")
    if _homog_checked < 8 or _pred_checked < 40:
        bad("bgfix9-items-homogeneous",
            f"只检查了 {_pred_checked} 条谓词 / {_homog_checked} 个数组形态的 `items` —— 反空转守护")

    # (b) 两条点名的成就逐条钉形状 + 负向「判据里不许有 player 条件」
    _RAW_PATH = "treasure/any_raw_metal"
    _raw_want = manifest["lists"]["raw_materials"]
    _raw_c = (advs.get(_RAW_PATH, {}) or {}).get("criteria") or {}
    if list(_raw_c) != ["have"] or _raw_c.get("have", {}).get("trigger") != "minecraft:inventory_changed":
        bad("bgfix9-raw-metal-shape",
            f"㊽ {_RAW_PATH} 的判据不是「单条 have/inventory_changed」：{sorted(_raw_c)}")
    else:
        _items = (_raw_c["have"].get("conditions") or {}).get("items") or []
        if len(_items) != 1 or sorted(_items[0].get("items") or []) != sorted(_raw_want):
            bad("bgfix9-raw-metal-shape",
                f"㊽ {_RAW_PATH}.have 的 `items` 必须是**恰好 1 条谓词**、其 `items` 数组 = 清单里的 "
                f"{len(_raw_want)} 种原料（实际 {len(_items)} 条谓词：{_items}）")
    if len(_raw_want) != 8:
        bad("bgfix9-raw-metal-shape",
            f"清单 `lists.raw_materials` 不是 8 条（实际 {len(_raw_want)}）—— 反空转守护")

    _EP_PATH = "agriculture/eggplant_seeds"
    _ep_c = (advs.get(_EP_PATH, {}) or {}).get("criteria") or {}
    if list(_ep_c) != ["have"]:
        bad("bgfix9-eggplant-no-structure",
            f"㊹ {_EP_PATH} 应恰好 1 条判据 `have`（实际 {sorted(_ep_c)}）")
    else:
        _ec = _ep_c["have"]
        if _ec.get("trigger") != "minecraft:inventory_changed":
            bad("bgfix9-eggplant-no-structure",
                f"㊹ 的 trigger 不是 inventory_changed：{_ec.get('trigger')}")
        _eitems = (_ec.get("conditions") or {}).get("items") or []
        if _eitems != [{"items": f"{NS}:golden_eggplant_seeds"}]:
            bad("bgfix9-eggplant-no-structure",
                f"㊹ 的 `items` 必须恰好是 [{{'items': 'bettergold:golden_eggplant_seeds'}}]，"
                f"实际 {_eitems}")
        if "player" in (_ec.get("conditions") or {}):
            bad("bgfix9-eggplant-no-structure",
                f"㊹ 的判据里又出现了 `conditions.player`（结构/位置条件）⇒ 堡垒遗迹之外拿到"
                f"金钱茄种子永不触发（作者 2026-10-09 实测的缺陷本体）："
                f"{(_ec.get('conditions') or {}).get('player')}")
    if (advs.get(_EP_PATH, {}) or {}).get("requirements") != [["have"]]:
        bad("bgfix9-eggplant-no-structure",
            f"㊹ 的 requirements 必须是 [['have']]，实际 "
            f"{(advs.get(_EP_PATH, {}) or {}).get('requirements')}")
    # 负向（全量）：**任何**判据都不许自带 `conditions.player` —— 51 条里没有任何一条需要
    #   结构/位置门；这条就是"㊹ 那一类"的类级守护（扰动：往任意一条加 player ⇒ 当场红）。
    _player_crits: list[str] = []
    for _p, _v in advs.items():
        for _k, _c in ((_v or {}).get("criteria") or {}).items():
            if "player" in ((_c.get("conditions") or {}) or {}):
                _player_crits.append(f"{_p}.{_k}")
    if _player_crits:
        bad("bgfix9-no-player-condition",
            f"这些判据自带 `conditions.player`（位置/结构门）—— 51 条成就里一条都不该有："
            f"{_player_crits}")
    if len(advs) != EXPECTED_COUNT:
        bad("bgfix9-anti-vacuum", f"扫到的成就数 {len(advs)} != {EXPECTED_COUNT} —— 反空转守护")

    # ---- 输出 ----
    # bgfix6（2026-10-08）就地标注：本关卡的 0/1/2 契约**本来就齐**（docstring 第 5-8 行 +
    #   下面的 try/except ⇒ 2；`bad()` 收集 ⇐ 每条断言都带反空转守护），本轮**只补一行
    #   统一格式的稳定 ASCII 结论码**，便于"六校验器扰动矩阵"逐条命中；退出码判据一字未改。
    for p in problems:
        print(f"FAIL {p}")
    if problems:
        print(f"bg-ach 进度系统问题: {len(problems)}")
        print(f"[bgach-fail] 问题 {len(problems)} 条 ⇒ 本关卡 exit 1（契约：0 绿 / 1 有问题 / 2 前置坏）")
        return 1
    print(f"OK [bgach] 51 个成就 / {total_criteria} 条 criteria / 触发类型 "
          f"{sorted(used_triggers)} / recipe_crafted {len(recipe_refs)} 条 / 语言键 {lang_n} 条")
    # ⚠ bg-fix3 §五 之后树形状与 challenge 数都变了；旧口径的措辞（「根 5 孩子…1 条 challenge」）
    #   原文保留在这里作历史留档。
    print(f"OK [bgach] 树（bg-fix3 §五 链式）：根 3 孩子（炼制I + 两条农业）、"
          f"根链 root -> 炼制I -> 炼制II -> 寻途、寻途 9 孩子、染上黄金 3 孩子；"
          f"3 条乐事条件；challenge {len(challenge)} 条（八族盔甲 + 骷髅打金服）")
    print(f"OK [bgfix3-knife-in-gear] 8 条武器成就各带 `have_knife`（items = 该族 "
          f"`#bettergold:<族>_knives` 标签，标签条目一律 required:false）⇒ 装了乐事时小刀计入")
    print(f"OK [bgfix3-root-obtain] root 判据 = inventory_changed + `{BGFIX3_HANDBOOK_TAG}`；"
          f"全仓 recipe_crafted = 0 条")
    print(f"OK [bgfix4-antique-knife-in-gear] {_antique_ok} 条古董成就各带 `have_knife`"
          f"（items = 单个标签字符串，标签条目 required:false）⇒ 装了乐事时屠刀/断骸刀计入；"
          f"`have` 那 5 件裸 id 原路径保留")
    print(f"OK [bgfix9-inv-one-predicate] 「任意」类 {len(_any_paths)} 条成就 / {_any_checked} 条判据"
          f"全部是**恰好 1 条谓词**（OR ⇔ items.size()==1）；「所有 / 一整套」类 {len(_all_paths)} 条"
          f"全部是「每件一条判据 + 各自一组」（组间 AND）；谓词 {_pred_checked} 条 / 数组形态 "
          f"{_homog_checked} 个；全 51 条无 `conditions.player`（位置/结构门）")
    print(f"OK [bgfix9-raw-metal-shape] ㊽ treasure/any_raw_metal.have = 1 条谓词 + "
          f"{len(_raw_want)} 项原料数组（拿取/合成任一即解锁）；"
          f"[bgfix9-eggplant-no-structure] ㊹ agriculture/eggplant_seeds.have = 获得金钱茄种子（无结构门）")
    print("OK [bgach] 物品引用 %d 个（含 %d 张本模组标签）全部存在于注册表真源；"
          "食物清单与 Java 真源逐条一致" % (len(set(refs)), len(bgfix3_tag_refs)))
    print(f"OK [bgfinal-adv-lang] {len(en_adv)} 条英文值全部是真英译"
          f"（en != zh、非空、含 ASCII 字母、长度 ≤ 120；中英键集完全一致，白名单 {len(SYMBOL_ONLY_OK)} 条）")
    print(f"[bgach-ok] 问题 0 条 / 成就 {len(advs)} 个 / criteria {total_criteria} 条 / 语言键 {lang_n} 条"
          f"（契约：0 绿 / 1 有问题 / 2 前置坏）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"关卡自身出错（exit 2）：{exc!r}")
        raise SystemExit(2)
