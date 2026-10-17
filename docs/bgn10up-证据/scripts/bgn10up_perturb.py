# -*- coding: utf-8 -*-
"""bg-n10up 扰动矩阵：每个用例都要求「关卡真的变红/变绿」，改完**逐字节复原 + SHA256**。

用法: py -3 bgn10up_perturb.py [输出文件]

用例（7 个）：
  1 改一格      —— 熔炉配方的 ingredient（币 → 币串）
  2 改数量 3→2  —— 币串 → 币 的 count
  3 shapeless → shaped —— 币串 → 币 的 type
  4 给金币加高炉 —— 新增 chaos_coin_blasting.json
  5 手册删一页   —— chaos_materials(zh) 去掉最后一页
  6 9→1 挖一个洞 —— pattern 最后一格变空格（测"逐格"断言，计数相等抓不到）
  7 只改注释     —— 生成器里加一行注释（**必须仍 exit 0**）
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
GATE = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
RECIPE = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"
BOOK = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "patchouli_books" / \
    "alchemy_handbook" / "zh_cn" / "entries"
GEN = REPO / "tools" / "asset-generator" / "generate_chaosgold_recipes.py"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "docs" / "bgn10up-证据" / "03-扰动矩阵.txt"
ADDED = RECIPE / "chaos_coin_blasting.json"

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
WATCH = [RECIPE / "chaos_coin_smelting.json", RECIPE / "chaos_coin_from_string.json",
         RECIPE / "chaosgold_ingot_from_nugget.json", BOOK / "chaos_materials.json", GEN]


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def run_gate():
    proc = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=ENV)
    text = (proc.stdout or "") + (proc.stderr or "")
    bgn = [l.strip() for l in text.splitlines() if "bg-n10up" in l and "问题" in l]
    total = [l.strip() for l in text.splitlines() if "[bg-data-" in l]
    return proc.returncode, bgn[-1] if bgn else "(没打印 bg-n10up 段)", total[-1] if total else ""


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def case_ingredient_moved():
    p = RECIPE / "chaos_coin_smelting.json"
    o = load(p)
    o["ingredient"] = {"item": "bettergold:chaos_coin_string"}
    write_json(p, o)


def case_count_2():
    p = RECIPE / "chaos_coin_from_string.json"
    o = load(p)
    o["result"]["count"] = 2
    write_json(p, o)


def case_shaped():
    p = RECIPE / "chaos_coin_from_string.json"
    o = load(p)
    o["type"] = "minecraft:crafting_shaped"
    write_json(p, o)


def case_add_blasting():
    o = load(RECIPE / "chaos_coin_smelting.json")
    o["type"] = "minecraft:blasting"
    o["cookingtime"] = 100
    write_json(ADDED, o)


def case_drop_book_page():
    p = BOOK / "chaos_materials.json"
    o = load(p)
    o["pages"].pop()
    write_json(p, o)


def case_ingot_hole():
    p = RECIPE / "chaosgold_ingot_from_nugget.json"
    o = load(p)
    o["pattern"][-1] = "NN "
    write_json(p, o)


def case_comment_only():
    text = GEN.read_text(encoding="utf-8")
    GEN.write_text(text + "# perturbation: 只加一行注释（产物不变，关卡必须仍绿）\n",
                   encoding="utf-8", newline="\n")


CASES = [
    ("1 改一格（熔炉输入 币→币串）", "chaos_coin_smelting.json", case_ingredient_moved, 1, ("bgn10up-smelt",)),
    ("2 改数量 3→2", "chaos_coin_from_string.json", case_count_2, 1, ("bgn10up-string",)),
    ("3 shapeless → shaped", "chaos_coin_from_string.json", case_shaped, 1, ("bgn10up-string",)),
    ("4 给金币加高炉", "chaos_coin_blasting.json（新增）", case_add_blasting, 1, ("bgn10up-reverse",)),
    ("5 手册删一页", "chaos_materials.json(zh)", case_drop_book_page, 1, ("bgn10r9-book", "bgn10up-handbook")),
    ("6 9→1 挖一个洞", "chaosgold_ingot_from_nugget.json", case_ingot_hole, 1, ("bgn10up-ingot",)),
    ("7 只改注释", "generate_chaosgold_recipes.py", case_comment_only, 0, ()),
]

backup = {p: p.read_bytes() for p in WATCH if p.is_file()}
backup_sha = {p: sha_bytes(b) for p, b in backup.items()}
rows = []
ok_all = True
try:
    for name, target, fn, want_exit, want_tags in CASES:
        fn()
        code, bgn, total = run_gate()
        hit = any(t in bgn for t in want_tags) if want_tags else (code == 0)
        # 逐字节复原
        for p, b in backup.items():
            p.write_bytes(b)
        ADDED.unlink(missing_ok=True)
        same = all(p.read_bytes() == b for p, b in backup.items()) and not ADDED.exists()
        ok_all = ok_all and code == want_exit and hit and same
        rows.append((name, target, code, bgn, total, hit, same))
finally:
    for p, b in backup.items():
        p.write_bytes(b)
    ADDED.unlink(missing_ok=True)

lines = ["bg-n10up 扰动矩阵（判据 = exit 码 + 命中的 `[bgn10up-*]` 行 + 逐字节复原）",
         "=" * 100, ""]
for name, target, code, bgn, total, hit, same in rows:
    lines.append("用例 %s" % name)
    lines.append("  目标文件 : %s" % target)
    lines.append("  exit     : %d" % code)
    lines.append("  命中预期 : %s" % ("是" if hit else "**否**"))
    lines.append("  命中行   : %s" % bgn[:240])
    lines.append("  总问题行 : %s" % total[:160])
    lines.append("  复原     : %s" % ("逐字节一致（SHA256 相同）" if same else "**不一致**"))
    lines.append("")
lines.append("全部用例符合预期 = %s" % ok_all)
lines.append("复原后 SHA256：")
for p, h in backup_sha.items():
    now = sha_bytes(p.read_bytes()) if p.is_file() else "MISSING"
    lines.append("  %-46s %s %s" % (p.name, h[:32], "OK" if now == h else "**变了：%s**" % now[:32]))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
raise SystemExit(0 if ok_all else 1)
