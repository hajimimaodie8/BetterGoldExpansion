"""bg-fix4 §四：给手册章3 的 8 个建材页追加「中上边字幕」语言键（唯一锚点、只追加）。

* **zh 值逐字来自仓库内冻结快照** `tools/asset-generator/bgappend-requirements-snapshot/bg-book-6.1-6.3.md`
  的 §6.3 第 2~5 行「图标：**X**」—— 不自己编。
* **en 值机械派生**自既有的 `block.bettergold.<金属>_bricks` 英文名（把结尾的 `Bricks` 换成
  `Building Blocks`）—— 同样是"已有的字"，不是新编的英译。
* 两份语言文件一律：**读 → 解析校验 → 在文件末尾 `\\n}` 这个唯一锚点前追加 → 再解析校验**
  （断言：既有键**一个都没少**、既有键的**值逐字未变**、新增恰好 8 键）。

用法：
    python build/bgfix4_add_lang.py            # 演练（只打印，不写盘）
    python build/bgfix4_add_lang.py --apply    # 写盘
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parent.parent
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"
SNAPSHOT = REPO / "tools" / "asset-generator" / "bgappend-requirements-snapshot" / "bg-book-6.1-6.3.md"
KEYFMT = "bettergold.handbook.page.knowledge_%d_%s_title"
# 快照 §6.3 第 2~5 行 × 左/右 -> (行号, 侧, 金属 id)；顺序 = 生成器的 METALS 两两配对
SLOTS = [
    (2, "left", "flamegold"), (2, "right", "sturdygold"),
    (3, "left", "thornsgold"), (3, "right", "echogold"),
    (4, "left", "indigoseagold"), (4, "right", "voodoogold"),
    (5, "left", "thundergold"), (5, "right", "illusiongold"),
]


def snapshot_titles() -> dict:
    """从冻结快照解析 {(行, 侧): 标题}（§6.3 第 2~5 行）。"""
    lines = SNAPSHOT.read_text(encoding="utf-8").split("\n")
    active, rows = False, []
    for ln in lines:
        if ln.startswith("### 6.3"):
            active = True
            continue
        if active and ln.startswith("---"):
            break
        if active and ln.startswith("|") and "|---" not in ln:
            cells = [c for c in ln.split("|")][1:-1]
            if not re.fullmatch(r"\d+", cells[0].strip().replace("*", "")):
                continue
            rows.append(cells)
    out = {}
    for cells in rows:
        idx = int(cells[0].strip().replace("*", ""))
        for col, side in ((1, "left"), (2, "right")):
            cell = cells[col] if col < len(cells) else ""
            head = cell.split("<br>")[0].strip()
            if not head.startswith("图标："):
                continue
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", head[len("图标："):]).strip()
            title = title.replace("（随排版顺序变化）", "").strip()
            out[(idx, side)] = title
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    titles = snapshot_titles()
    print("快照 §6.3 解析到 %d 个「图标：」标题" % len(titles))
    want = {}
    for idx, side, metal in SLOTS:
        key = KEYFMT % (idx, side)
        t = titles.get((idx, side))
        if not t:
            print("FATAL 快照里取不到 (%d, %s) 的标题" % (idx, side))
            return 2
        want[key] = (metal, t)
    if len(want) != 8:
        print("FATAL 槽位不是 8 个：%d" % len(want))
        return 2

    zh_path, en_path = LANG / "zh_cn.json", LANG / "en_us.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    en = json.loads(en_path.read_text(encoding="utf-8"))

    new_zh, new_en = {}, {}
    for key, (metal, title) in want.items():
        if key in zh or key in en:
            print("FATAL 语言键已存在（不许覆盖）：%s" % key)
            return 2
        bricks_key = "block.bettergold.%s_bricks" % metal
        en_bricks = en.get(bricks_key)
        if not en_bricks or not en_bricks.endswith(" Bricks"):
            print("FATAL 取不到 %s 的英文砖块名（en=%r）" % (bricks_key, en_bricks))
            return 2
        new_zh[key] = title
        new_en[key] = en_bricks[: -len("Bricks")] + "Building Blocks"
        print("  %-58s zh=%-14s en=%s" % (key, title, new_en[key]))

    for path, mapping in ((zh_path, new_zh), (en_path, new_en)):
        text = path.read_text(encoding="utf-8")
        # ⚠ 实测：两份语言文件**末尾没有换行**，最后两个字符就是 "\n}"（734 个 LF、无 CRLF、无 BOM）
        if not text.endswith("\n}"):
            print("FATAL %s 的末尾不是 '\\n}'（唯一锚点不成立）" % path.name)
            return 2
        head = text[:-2].rstrip("\n")
        add = ",\n".join('  "%s": %s' % (k, json.dumps(v, ensure_ascii=False))
                         for k, v in mapping.items())
        out = head + ",\n" + add + "\n}"          # 末尾同样**不带**换行（与原文形状一致）
        old = json.loads(text)
        fresh = json.loads(out)
        if set(fresh) != set(old) | set(mapping):
            print("FATAL %s 的键集合不对（多了或少了）" % path.name)
            return 2
        for k, v in old.items():
            if fresh[k] != v:
                print("FATAL %s 的既有键 %s 的值被改了" % (path.name, k))
                return 2
        print("%s: %d 行 -> %d 行（+%d 键；既有 %d 键逐个值不变；锚点 = 末尾 '}\\n' 唯一命中）"
              % (path.name, len(text.split("\n")), len(out.split("\n")), len(mapping), len(old)))
        if apply:
            path.write_bytes(out.encode("utf-8"))
    if not apply:
        print("（演练模式：没有写盘；加 --apply 才写）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
