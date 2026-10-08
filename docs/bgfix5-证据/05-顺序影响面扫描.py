# -*- coding: utf-8 -*-
"""
bgfix5 · 「8 族金属顺序」影响面扫描（可复算）

两节：
  §A 契约位逐个复核：对**已知把族顺序当契约**的文件，用**各文件自己的形态**抽顺序
     （Java 列表字面量 / `defineInRange` 声明序 / Python 常量 / manifest 的 lists.metals /
      Patchouli 图标数组 / 关卡期望常量），与真源 `CreativeSections.METAL_ORDER` 对比。
  §B 全仓粗扫：凡出现 ≥2 个族 id 的文本文件，按**首次出现位置**给一个粗糙的族序列
     （仅用于"还有哪个文件提到这些族"的完整性检查；日志/证据类文件的首次出现序**不是契约**）。

用法（仓库根）:
    python "docs/bgfix5-证据/05-顺序影响面扫描.py"
输出:
    docs/bgfix5-证据/06-顺序影响面扫描.txt
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTHOR_ORDER = ["flamegold", "sturdygold", "thornsgold", "echogold",
                "indigoseagold", "voodoogold", "thundergold", "illusiongold"]

JAVA = "src/main/java/com/hjmmd_8/bettergold"
GEN = "tools/asset-generator"
BOOK = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook"

out = []
def emit(s=""):
    out.append(s)
    print(s)


def read(rel):
    p = os.path.join(REPO, rel.replace("/", os.sep))
    if not os.path.isfile(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read()


def ids_in(block):
    return re.findall(r"[a-z_]*?(" + "|".join(AUTHOR_ORDER) + r")\b", block)


def family_core_map():
    """族 -> 该族的「核心材料/原料」进度节点 id（**从数据现算**，不硬编码）。

    来源 = 每个 `data/bettergold/advancement/metal/<族>/ingot.json` 的 `parent`
    （= `bettergold:treasure/<核心材料>`）⇒ 这是"族 ↔ 进度节点"映射的**唯一权威**，
    本轮与下一轮的关卡、mixin 排序都应以它为准，避免第二份硬编码映射。
    """
    out_map = {}
    for m in AUTHOR_ORDER:
        rel = "src/main/resources/data/bettergold/advancement/metal/%s/ingot.json" % m
        src = read(rel)
        if not src:
            continue
        try:
            out_map[m] = json.loads(src)["parent"]
        except Exception:
            pass
    return out_map


def verdict(seq, label):
    if seq is None:
        return "  ??  %s：读不到" % label
    if seq == AUTHOR_ORDER:
        return "  OK  %s：== 作者顺序（8 族齐全）" % label
    if len(seq) != 8:
        return "  --  %s：只含 %d 族（**不是** 8 族显示顺序契约；本仓多处把万坚金单列）→ %s" % (
            label, len(seq), seq)
    return "  !!  %s：!= 作者顺序 → %s" % (label, seq)


def check_java_list(rel, const, label):
    src = read(rel)
    if src is None:
        return "  ??  %s：读不到 %s" % (label, rel)
    m = re.search(re.escape(const) + r"\s*=\s*List\.of\((.*?)\);", src, re.S)
    if not m:
        return "  ??  %s：解析不到 %s" % (label, const)
    return verdict(re.findall(r'"([a-z_]+)"', m.group(1)), label)


def check_config(rel="src/main/java/com/hjmmd_8/bettergold/config/Config.java"):
    src = read(rel)
    if src is None:
        return "  ??  Config.java：读不到"
    order, seen = [], set()
    for k in re.findall(r'\.defineInRange\(\s*"([^"]+)"', src):
        for m in AUTHOR_ORDER:
            if k.startswith(m) and m not in seen:
                seen.add(m)
                order.append(m)
    n_keys = len(re.findall(r"\.defineInRange\(", src))
    return verdict(order, "Config.java 的 defineInRange 声明序（共 %d 个键）" % n_keys)


def check_py_list(rel, const, label, pat=None):
    src = read(rel)
    if src is None:
        return "  ??  %s：读不到 %s" % (label, rel)
    m = re.search(pat, src, re.S | re.M) if pat else None
    if m is None:
        for brack in (r"\[(.*?)\]", r"\((.*?)\)"):
            m = re.search(r"^" + re.escape(const) + r"\s*=\s*" + brack, src, re.S | re.M)
            if m:
                break
    if m is None:
        return "  ??  %s：解析不到 %s" % (label, const)
    body = m.group(1)
    seq = re.findall(r'\("([a-z_]+)",\s*"[a-z_]+"\)', body) or re.findall(r'"([a-z_]+)"', body)
    seq = [s for s in seq if s in AUTHOR_ORDER]
    return verdict(seq, label)


def check_manifest():
    rel = GEN + "/advancement_manifest.json"
    src = read(rel)
    if src is None:
        return "  ??  advancement_manifest.json：读不到"
    try:
        seq = json.loads(src).get("lists", {}).get("metals")
    except Exception as e:
        return "  ??  manifest 解析失败：%s" % e
    return verdict(seq, "advancement_manifest.json 的 lists.metals（产物）")


def check_book_entry(name, core_map):
    hits = []
    for side in ("zh_cn", "en_us"):
        rel = "%s/%s/entries/%s.json" % (BOOK, side, name)
        src = read(rel)
        if src is None:
            hits.append("  ??  %s/%s：读不到" % (name, side))
            continue
        try:
            data = json.loads(src)
        except Exception as e:
            hits.append("  ??  %s/%s 解析失败 %s" % (name, side, e))
            continue
        seq = []
        for page in data.get("pages", []):
            it = page.get("item")
            for x in ([it] if isinstance(it, str) else (it or [])):
                if not isinstance(x, str):
                    continue
                for fam in AUTHOR_ORDER:
                    core = core_map.get(fam, "")
                    core_bare = "bettergold:" + core.split("/")[-1] if core else ""
                    if x == core or x == core_bare \
                            or x.startswith("bettergold:%s_" % fam) or x == "bettergold:raw_%s" % fam:
                        if fam not in seq:
                            seq.append(fam)
        hits.append(verdict(seq, "%s.json（%s，Patchouli 图标出现序）" % (name, side)))
    return "\n".join(hits)


def main():
    emit("=" * 104)
    emit("bgfix5 · 「8 族金属顺序」影响面清单（scan = docs/bgfix5-证据/05-顺序影响面扫描.py）")
    emit("真源 = %s/material/CreativeSections.java 的 `METAL_ORDER`" % JAVA)
    emit("作者顺序 = " + ", ".join(AUTHOR_ORDER))
    emit("=" * 104)

    emit("")
    emit("§A · 契约位逐个复核（每个文件用它自己的形态抽顺序）")
    emit("-" * 104)
    emit(check_java_list(JAVA + "/material/CreativeSections.java", "METAL_ORDER",
                         "① 真源 CreativeSections.METAL_ORDER"))
    emit(check_config())
    emit(check_py_list(GEN + "/generate_advancements.py", "METALS",
                       "③ generate_advancements.py 的 METALS"))
    emit(check_py_list(GEN + "/generate_handbook_data.py", "METALS",
                       "④ generate_handbook_data.py 的 METALS"))
    emit(check_manifest())
    emit("")
    emit("  — 关卡（校验器）里的**期望常量副本**（故意各写一份，不读真源自比）：")
    emit(check_py_list(GEN + "/validate_metal_data.py", "_FX4_METALS", "⑤ validate_metal_data.py 的 _FX4_METALS"))
    emit(check_py_list(GEN + "/validate_metal_data.py", "_BG8_METAL_ORDER", "⑥ validate_metal_data.py 的 _BG8_METAL_ORDER"))
    emit(check_py_list(GEN + "/validate_metal_data.py", "_expected_order", "⑦ validate_metal_data.py 的 _expected_order"))
    emit(check_py_list(GEN + "/validate_advancements.py", "METALS_ORDER", "⑨ validate_advancements.py 的 METALS_ORDER"))
    emit("  --  ⑧ validate_advancements.py 没有 `METALS` 这个常量（它用 METALS_ORDER 元组）⇒ 无需复核")
    emit(check_py_list(GEN + "/generate_metal_tags.py", "METALS", "⑩ generate_metal_tags.py 的 METALS"))
    emit(check_py_list(GEN + "/generate_metal_trims.py", "METALS", "⑪ generate_metal_trims.py 的 METALS"))
    emit(check_py_list(GEN + "/generate_weapon_data.py", "METALS",
                       "⑫ generate_weapon_data.py 的 METALS（**生成/产物顺序，不是显示顺序契约**）"))
    emit(check_py_list(GEN + "/validate_metal_assets.py", "METALS", "⑬ validate_metal_assets.py 的 METALS"))
    emit(check_py_list(GEN + "/validate_trim_assets.py", "METALS", "⑭ validate_trim_assets.py 的 METALS"))
    emit("")
    emit("  — 手册产物（由 ④ 重生成；顺序体现在图标数组的轮换序）：")
    core_map = family_core_map()
    emit("  族 ↔ 进度节点映射（**从 metal/<族>/ingot.json 的 parent 现算**，不硬编码）：")
    for m in AUTHOR_ORDER:
        emit("    %-16s -> %s" % (m, core_map.get(m, "(读不到)")))
    emit(check_book_entry("core_materials", core_map))
    emit(check_book_entry("golden_knowledge", core_map))

    # 进度树：本轮新增的第 5 个同序位（兄弟集合，运行时由 mixin 决定）
    emit("")
    emit("  — 进度树（本轮新增的第 5 个同序位；**兄弟集合的迭代序由 JVM 随机**，数据侧无排序位）：")
    tree = {}
    for root, dirs, files in os.walk(os.path.join(
            REPO, "src", "main", "resources", "data", "bettergold", "advancement")):
        for f in files:
            if not f.endswith(".json"):
                continue
            p = os.path.join(root, f)
            try:
                j = json.loads(open(p, encoding="utf-8").read())
            except Exception:
                continue
            if j.get("parent"):
                tree.setdefault(j["parent"], []).append(
                    "bettergold:" + os.path.relpath(p, os.path.join(
                        REPO, "src", "main", "resources", "data", "bettergold", "advancement")
                    ).replace(os.sep, "/")[:-5])
    guard_parent = "bettergold:treasure/any_core_material"
    kids = sorted(tree.get(guard_parent, []))
    emit("    守卫父节点 = %s（本模组唯一要固定兄弟序的父节点）" % guard_parent)
    emit("    运行期兄弟集合（%d 个，JSON 里没有顺序可言）：" % len(kids))
    for k in kids:
        fam = [m for m, c in core_map.items() if c == k]
        emit("      - %-40s %s" % (k, ("=> 族 " + fam[0]) if fam else "(非族节点)"))

    emit("")
    emit("§B · 全仓粗扫（首次出现序；仅作「还有谁提到这些族」的完整性检查）")
    emit("-" * 104)
    scan_dirs = ["src", "tools", "docs"]
    scan_files = ["AGENTS.md", "README.md", "build.gradle", "gradle.properties"]
    EXT = {".java", ".py", ".json", ".md", ".txt", ".gradle", ".properties", ".toml"}
    rows = []

    def consider(p):
        if os.path.splitext(p)[1].lower() not in EXT:
            return
        if "bgfix5-证据" in p:
            return
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            return
        pos = {m: t.find(m) for m in AUTHOR_ORDER if t.find(m) >= 0}
        if len(pos) < 2:
            return
        seq = [m for m, _ in sorted(pos.items(), key=lambda kv: kv[1])]
        rows.append((os.path.relpath(p, REPO), len(seq), seq == AUTHOR_ORDER))

    for d in scan_dirs:
        for root, dirs, files in os.walk(os.path.join(REPO, d)):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", "build", "run", ".git")]
            for f in files:
                consider(os.path.join(root, f))
    for f in scan_files:
        p = os.path.join(REPO, f)
        if os.path.isfile(p):
            consider(p)

    full = [r for r in rows if r[1] == 8]
    emit("  提到 ≥2 个族的文件 %d 个；其中 8 族齐全 %d 个（首次出现序 == 作者顺序的 %d 个）。"
         % (len(rows), len(full), len([r for r in full if r[2]])))
    emit("  ⚠ `docs/*-证据/` 下的运行日志与历史留档**首次出现序不是契约**（它们的顺序是当时那次运行的顺序）。")
    emit("  8 族齐全 且 首次出现序 != 作者顺序 的（按 §A 复核后大多属于「非契约」）：")
    for rel, n, same in sorted(full):
        if not same:
            emit("    - " + rel)

    txt = "\n".join(out) + "\n"
    with open(os.path.join(REPO, "docs", "bgfix5-证据", "06-顺序影响面扫描.txt"),
              "w", encoding="utf-8", newline="\r\n") as f:
        f.write(txt)


if __name__ == "__main__":
    main()
