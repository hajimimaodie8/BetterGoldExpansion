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
CHALLENGE_PATHS = {"metal/sturdygold/skeleton"}
TRIGGER_WHITELIST = {
    "minecraft:inventory_changed", "minecraft:recipe_crafted", "minecraft:villager_trade",
    "minecraft:player_hurt_entity", "minecraft:placed_block", "minecraft:item_used_on_block",
}
# 本仓只用到这两个原版物品（金苹果 / 金胡萝卜是原版金食物）
VANILLA_ITEMS = {"minecraft:gold_ingot", "minecraft:golden_apple", "minecraft:golden_carrot"}
VANILLA_TAGS = {"#minecraft:hoes", "#minecraft:skeletons"}

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
    want_root_kids = sorted([f"{NS}:alchemy/mixed_crystal_pile", f"{NS}:alchemy/alchemic_fuel",
                             f"{NS}:treasure/any_core_material",
                             f"{NS}:agriculture/gold_infused_dirt",
                             f"{NS}:agriculture/alchemical_meat"])
    if root_kids != want_root_kids:
        bad("bgach-shape-root-children", f"根的孩子不是 5 条并列：{root_kids}")
    tr_kids = sorted(children.get(f"{NS}:treasure/any_core_material", []))
    if len(tr_kids) != 9:
        bad("bgach-shape-treasure-children", f"「寻途千里的珍宝」的孩子应为 9 条（实际 {len(tr_kids)}）")
    gold_kids = sorted(children.get(f"{NS}:metal/sturdygold/weapon", []))
    want_gold_kids = sorted([f"{NS}:metal/sturdygold/skeleton", f"{NS}:metal/sturdygold/armor",
                             f"{NS}:merchant/gold_ticket"])
    if gold_kids != want_gold_kids:
        bad("bgach-shape-gold-split", f"「染上黄金吧」的 3 个孩子不对：{gold_kids}")

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
    if sorted(len(x) for x in g) != [1, 2]:
        bad("bgach-requirements-semantics",
            f"agriculture/plant_gold_crop 应为「耕地(1) AND (金麦 OR 金钱茄)(2)」，实际 {g}")

    # ---- 6. 物品存在性 ----
    refs: list[str] = []
    for k, v in advs.items():
        walk_items(v, refs)
        icon = (v.get("display") or {}).get("icon", {}).get("id")
        if icon:
            refs.append(icon)
    for r in sorted(set(refs)):
        if r.startswith("#"):
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
    recipe_refs = sorted({c["conditions"]["recipe_id"]
                          for v in advs.values() for c in (v.get("criteria") or {}).values()
                          if c.get("trigger") == "minecraft:recipe_crafted"})
    if not recipe_refs:
        bad("bgach-recipe-anti-vacuum", "一条 recipe_crafted 都没有（root 至少有一条）")
    for r in recipe_refs:
        short = r.split(":", 1)[1]
        if not (RECIPE / f"{short}.json").is_file():
            bad("bgach-recipe-exists", f"{r} 在 data/bettergold/recipe/ 下没有对应 JSON")

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
    _recipe_left = sorted(k for k, v in advs.items()
                          if "minecraft:recipe_crafted" in [c.get("trigger") for c in
                                                            (v.get("criteria") or {}).values()])
    if _recipe_left != ["root"]:
        bad("bgach-recipe-crafted-scope",
            f"还带 recipe_crafted 的成就应只有 root（实际 {_recipe_left}）")

    # §七.6：**刀不算器具** —— 8 条「获得任意一种 XX金武器工具」的 criteria 里一个 `_knife` 都不许有。
    KNIVES = set(manifest["lists"]["knives"])
    if len(KNIVES) != 8:
        bad("bgach-no-knife-in-gear", f"清单里的刀不是 8 把（实际 {len(KNIVES)}）—— 反空转守护")
    _weapon_paths = [f"metal/{m}/weapon" for m in
                     ["flamegold", "sturdygold", "thornsgold", "echogold",
                      "indigoseagold", "voodoogold", "thundergold", "illusiongold"]]
    if len(_weapon_paths) != 8:
        bad("bgach-no-knife-in-gear", "8 条武器工具成就的路径清单不是 8 条 —— 反空转守护")
    _gear_items: set[str] = set()
    for p in _weapon_paths:
        for _c in (advs.get(p, {}).get("criteria") or {}).values():
            for _pred in (_c.get("conditions") or {}).get("items") or []:
                _it = _pred.get("items")
                _gear_items.update([_it] if isinstance(_it, str) else (_it or []))
    if len(_gear_items) < 40:
        bad("bgach-no-knife-in-gear",
            f"8 条武器成就只解析到 {len(_gear_items)} 个物品（应 >= 40）—— 反空转守护")
    _knife_in_gear = sorted(_gear_items & KNIVES)
    if _knife_in_gear:
        bad("bgach-no-knife-in-gear",
            f"刀被算进了「获得武器工具」的成就里（作者 §七.6：「乐事的刀不会触发有关获得器具的进度」）："
            f"{_knife_in_gear}")

    # ---- 输出 ----
    for p in problems:
        print(f"FAIL {p}")
    if problems:
        print(f"bg-ach 进度系统问题: {len(problems)}")
        return 1
    print(f"OK [bgach] 51 个成就 / {total_criteria} 条 criteria / 触发类型 "
          f"{sorted(used_triggers)} / 配方引用 {len(recipe_refs)} 条 / 语言键 {lang_n} 条")
    print("OK [bgach] 树：根 5 孩子、寻途 9 孩子、染上黄金 3 孩子；3 条乐事条件；1 条 challenge")
    print("OK [bgach] 物品引用 %d 个全部存在于注册表真源；食物清单与 Java 真源逐条一致" % len(set(refs)))
    print(f"OK [bgfinal-adv-lang] {len(en_adv)} 条英文值全部是真英译"
          f"（en != zh、非空、含 ASCII 字母、长度 ≤ 120；中英键集完全一致，白名单 {len(SYMBOL_ONLY_OK)} 条）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"关卡自身出错（exit 2）：{exc!r}")
        raise SystemExit(2)
