#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgn10hv_check.py —— 三路对穿：**真源（生成器）** ↔ **资产（跑的 JSON）** ↔ **运行时（客户端探针读数）**。

用法： py -3 bgn10hv_check.py [log文件]      默认 build/bgn10hv/client.out

输出： docs/bgn10hv-证据/01-三路对穿.txt（同时打印摘要）

口径：
  * 真源 = tools/asset-generator/generate_handbook_data.py 里那 5 个 entry builder **直接调用**得到的 dict；
  * 资产 = src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/*.json
    （客户端 lang=zh_cn ⇒ Patchouli 加载的就是这一份）；
  * 运行时 = 客户端探针的 HVROW / HVPG 行。
三份的每一页按 type / recipe / recipe2 / item / text 逐项对齐。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "build" / "bgn10hv" / "client.out"
LOG = LOG if LOG.is_absolute() else (REPO / LOG)
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "patchouli_books" / "alchemy_handbook"
EVID = REPO / "docs" / "bgn10hv-证据"
OUT = EVID / "01-三路对穿.txt"

ENTRIES = ["chaos_materials", "chaos_feast", "gear_chaosgold", "gear_chaosalloy", "gear_echogold"]
LANG = "bettergold"


def load_generator():
    gen = REPO / "tools" / "asset-generator"
    sys.path.insert(0, str(gen))
    spec = importlib.util.spec_from_file_location("ghd", gen / "generate_handbook_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gen_entry(m, short):
    direct = {
        "chaos_materials": "entry_chaos_materials",
        "chaos_feast": "entry_chaos_feast",
        "gear_chaosgold": "entry_gear_chaosgold",
        "gear_chaosalloy": "entry_gear_chaosalloy",
    }
    if short in direct:
        return getattr(m, direct[short])()
    for b in m.GEAR_ENTRIES:
        if getattr(b, "__name__", "") == "entry_%s" % short:
            return b()
    raise SystemExit("[check] 生成器里找不到 %s" % short)


def norm_items(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def parse_runtime(lines):
    """HVPG 行 -> {entry_short: [page dict, ...]}；HVROW 行 -> 页数"""
    rows = {}
    counts = {}
    pat = re.compile(r"BGN10HVCPROBE HVPG entry=(\S+) idx=(\d+) type=(\S+) cls=(\S+) err=(\S+) "
                     r"r1=(\S+) ok1=(\S+) r2=(\S+) ok2=(\S+) stacks=(\S+) items=(\S+) "
                     r"text=(\S*) textOk=(\S+) body=(\S*) title=(\S*)")
    cp = re.compile(r"BGN10HVCPROBE HVROW entry=(\S+) pages=(\d+) icon=(.*)")
    for line in lines:
        m = cp.search(line)
        if m:
            counts[m.group(1)] = int(m.group(2))
            continue
        m = pat.search(line)
        if not m:
            continue
        entry, idx, typ, cls, err, r1, ok1, r2, ok2, stacks, items, text, textok, body, title = m.groups()
        rows.setdefault(entry, []).append({
            "idx": int(idx), "type": typ, "cls": cls, "err": err,
            "r1": None if r1 == "-" else r1, "ok1": ok1,
            "r2": None if r2 == "-" else r2, "ok2": ok2,
            "stacks": None if stacks == "-" else int(stacks),
            "items": None if items == "-" else items,
            "text": None if text == "-" else text.strip('"'), "textOk": textok,
            "body": body, "title": title,
        })
    return rows, counts


def asset_pages(short):
    p = ASSETS / "zh_cn" / "entries" / ("%s.json" % short)
    return json.loads(p.read_text(encoding="utf-8"))


def read_text_auto(path: Path) -> str:
    """PowerShell 5.1 的 `1>` 重定向写的是 **UTF-16LE + BOM**；Gradle 自己写的是 UTF-8。这里按 BOM 自动判。"""
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-16-le", errors="replace")


def main() -> int:
    if not LOG.exists():
        raise SystemExit("[check] 找不到日志 %s" % LOG)
    log = read_text_auto(LOG).splitlines()
    m = load_generator()
    rt_rows, rt_counts = parse_runtime(log)

    out = []
    w = out.append
    w("bgn10hv 三路对穿（真源 = generate_handbook_data.py / 资产 = zh_cn JSON / 运行时 = 客户端探针）")
    w("日志 = %s" % LOG.relative_to(REPO))
    w("")

    problems = []
    total_pages_gen = total_pages_asset = total_pages_rt = 0

    for short in ENTRIES:
        eid = "%s:%s" % (LANG, short)
        gen = gen_entry(m, short)
        asset = asset_pages(short)
        rt = rt_rows.get(eid, [])
        gp, ap, rp = gen["pages"], asset["pages"], rt
        total_pages_gen += len(gp)
        total_pages_asset += len(ap)
        total_pages_rt += len(rp)
        w("### %s" % eid)
        w("  页数：真源=%d 资产=%d 运行时=%d  HVROW=%s"
          % (len(gp), len(ap), len(rp), rt_counts.get(eid)))
        if not (len(gp) == len(ap) == len(rp) == rt_counts.get(eid, -1)):
            problems.append("%s 页数三路不一致：%d/%d/%d/%s"
                            % (eid, len(gp), len(ap), len(rp), rt_counts.get(eid)))
        for i in range(max(len(gp), len(ap), len(rp))):
            g = gp[i] if i < len(gp) else None
            a = ap[i] if i < len(ap) else None
            r = rp[i] if i < len(rp) else None
            diffs = []
            if g is None or a is None or r is None:
                diffs.append("页缺失 gen=%s asset=%s rt=%s" % (g is not None, a is not None, r is not None))
            else:
                if g.get("type") != a.get("type") or g.get("type") != r["type"]:
                    diffs.append("type 真源=%s 资产=%s 运行时=%s" % (g.get("type"), a.get("type"), r["type"]))
                for key, rkey in (("recipe", "r1"), ("recipe2", "r2")):
                    gv, av, rv = g.get(key), a.get(key), r[rkey]
                    if not (gv == av == rv):
                        diffs.append("%s 真源=%s 资产=%s 运行时=%s" % (key, gv, av, rv))
                if g.get("type") == "patchouli:spotlight":
                    gi, ai = norm_items(g.get("item")), norm_items(a.get("item"))
                    if gi != ai:
                        diffs.append("item 真源=%s 资产=%s" % (gi, ai))
                    if r["stacks"] != len(ai):
                        diffs.append("spotlight 栈数 资产=%d 运行时=%s" % (len(ai), r["stacks"]))
                    if ai and r["items"] and not ai[0] == r["items"].split("|")[0]:
                        diffs.append("spotlight 首项 资产=%s 运行时=%s" % (ai[0], r["items"]))
                for key in ("text", "title"):
                    gv, av = g.get(key), a.get(key)
                    if gv != av:
                        diffs.append("%s 真源=%s 资产=%s" % (key, gv, av))
                if a.get("text") and r["text"] not in (None, "-") and a["text"] != r["text"] \
                        and not a["text"].startswith(r["text"]):
                    diffs.append("text 资产=%s 运行时=%s" % (a["text"], r["text"]))
            w("  p%-2d 真源=%-20s 资产=%-20s 运行时=%-20s err=%-14s r1=%-46s r2=%-46s stacks=%s"
              % (i, (g or {}).get("type"), (a or {}).get("type"), r["type"] if r else "-",
                 r["err"] if r else "-", r["r1"] if r else "-", r["r2"] if r else "-",
                 r["stacks"] if r else "-"))
            if r and (r.get("body") not in (None, "-") or r.get("title") not in (None, "-")):
                w("      页上文字：body=%s title=%s textOk=%s"
                  % (r.get("body"), r.get("title"), r.get("textOk")))
            if diffs:
                problems.append("%s 第 %d 页：%s" % (eid, i, "；".join(diffs)))
        w("")

    w("### 汇总")
    w("  页数合计：真源=%d 资产=%d 运行时=%d" % (total_pages_gen, total_pages_asset, total_pages_rt))
    w("  页级不一致条数 = %d" % len(problems))
    for p in problems:
        w("   ✗ %s" % p)

    # ---- 其余运行时读数（PASS/FAIL、世界名、配方表、日志） ----
    w("")
    w("### 运行时读数摘要")
    for line in log:
        if "BGN10HVCPROBE" in line or "BGN10HVGEN" in line:
            w("  " + line.split("] ", 1)[-1] if "] " in line else "  " + line)
    w("")
    err_lines = [l for l in log if "/ERROR" in l]
    unable = [l for l in log if "Unable to " in l]
    notfound = [l for l in log if "not found" in l and "patchouli" in l.lower()]
    w("### 日志扫描（整份客户端日志）")
    w("  含 /ERROR 的行数 = %d" % len(err_lines))
    for l in err_lines[:10]:
        w("   ! " + l[:220])
    w("  含 'Unable to ' 的行数 = %d" % len(unable))
    for l in unable[:10]:
        w("   ! " + l[:220])
    w("  Patchouli 'Recipe ... not found' 警告行数 = %d" % len(notfound))
    for l in notfound[:10]:
        w("   ! " + l[:220])

    EVID.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(("\n".join(out) + "\n").encode("utf-8"))
    print("\n".join(out[-60:]))
    print("\n[check] 报告 -> %s" % OUT.relative_to(REPO))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
