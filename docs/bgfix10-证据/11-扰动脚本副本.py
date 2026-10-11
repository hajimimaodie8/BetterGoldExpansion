# -*- coding: utf-8 -*-
"""bgfix10 扰动矩阵：关卡"能红"的自证 + 逐字节复原 + SHA256。

守的是本轮新增/改动的断言：
  validate_metal_data.py  `[bgfix10-lang-*]` / `[bgfix10-archive-kept]` / `[bgfix10-doc]`
                          / `[bgbook10-lang-bilingual]`（那条**正 → 负**的改动）
  validate_advancements.py `[bgach-lang-verbatim]`（期望值现在来自同步后的 manifest）

口径（`docs/构建与跑测注意事项.md` 六 / 七 + `ex/03` §3.11 / §3.19.1）：
  * 每条"弄脏"用例都必须 **exit 1 + 命中期望断言 id**；
  * **反向对照**（只加空行 / 只加一行非数据文字）必须 **仍然 exit 0**；
  * **前置缺失** 必须 **exit 2**（不是"没有问题"）；
  * 用例本身失效（目标串 0 命中 / 次数不符）⇒ 报 `SETUP-FAIL`，**不算命中**；
  * 收尾每个被改文件**逐字节复原**并复核 SHA256。
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TOOLS = REPO / "tools" / "asset-generator"
LANG = REPO / "src/main/resources/assets/bettergold/lang"
EN = LANG / "en_us.json"
ZH = LANG / "zh_cn.json"
MANIFEST = TOOLS / "advancement_manifest.json"
SNAP6 = TOOLS / "bgappend-requirements-snapshot" / "bg-book-6.1-6.3.md"
SPEC = REPO / "docs" / "1.6-规格.md"

VM = TOOLS / "validate_metal_data.py"
VA = TOOLS / "validate_advancements.py"

REPORT = HERE / "01-关卡扰动矩阵.txt"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def path_digest(p: Path) -> str:
    if p.is_file():
        return sha(p.read_bytes())
    if p.is_dir():
        items = [f"{f.relative_to(p).as_posix()}:{sha(f.read_bytes())}"
                 for f in sorted(x for x in p.rglob("*") if x.is_file())]
        return sha("\n".join(items).encode("utf-8"))
    return "<absent>"


def run_validator(v: Path):
    p = subprocess.run([sys.executable, str(v)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


class _Tee:
    def __init__(self, path: Path):
        self.fh = path.open("w", encoding="utf-8", newline="\n")

    def write(self, s: str) -> int:
        sys.__stdout__.write(s)
        return self.fh.write(s)

    def flush(self) -> None:
        sys.__stdout__.flush()
        self.fh.flush()


class Case:
    def __init__(self, name, validator, expect, tags, kind, target, old=b"", new=b"", expect_occ=None):
        self.name = name
        self.validator = validator
        self.expect = expect
        self.tags = tags
        self.kind = kind
        self.target = Path(target)
        self.old = old
        self.new = new
        self.expect_occ = expect_occ
        self.occ = None
        self.exit = None
        self.hit = []
        self.note = ""
        self.good = None


def apply(case: Case, backup: dict):
    t = case.target
    if case.kind == "patch":
        src = t.read_bytes()
        backup[t] = src
        case.occ = src.count(case.old)
        if case.occ == 0:
            raise RuntimeError("%s: 目标串 0 命中（用例失效）" % case.name)
        if case.expect_occ is not None and case.occ != case.expect_occ:
            raise RuntimeError("%s: occ=%d 期望 %d（用例失效）" % (case.name, case.occ, case.expect_occ))
        t.write_bytes(src.replace(case.old, case.new))
    elif case.kind == "rename":
        if not t.exists():
            raise RuntimeError("%s: 目标不存在（用例失效）" % case.name)
        backup[t] = b"<renamed>"
        case.occ = 1
        t.rename(t.with_name(t.name + "_moved_by_perturb"))
    elif case.kind == "none":
        case.occ = "-"
    else:
        raise RuntimeError("未知 kind %s" % case.kind)


def restore(case: Case, backup: dict):
    t = case.target
    if case.kind == "none":
        return
    if case.kind == "rename":
        t.with_name(t.name + "_moved_by_perturb").rename(t)
    else:
        t.write_bytes(backup[t])


def line(key, value, indent="  ", comma=","):
    return ("%s%s: %s%s\n" % (indent, json.dumps(key, ensure_ascii=False),
                              json.dumps(value, ensure_ascii=False), comma)).encode("utf-8")


def main() -> int:
    sys.stdout = _Tee(REPORT)
    en = json.loads(EN.read_bytes().decode("utf-8"))
    zh = json.loads(ZH.read_bytes().decode("utf-8"))

    # 先做"用例前置"：下面每条 patch 的锚点都必须真的存在（否则用例失效，不是关卡的问题）
    K_ITEM = "item.bettergold.unwanted_antique"
    K_SWORD = "item.bettergold.antique_sword"
    K_AXE = "item.bettergold.antique_axe"
    K_MERCH = "bettergold.handbook.category.merchant_antiques.name"
    K_GAST = "bettergold.handbook.category.golden_feast.name"
    for k in (K_ITEM, K_SWORD, K_AXE, K_MERCH, K_GAST):
        if k not in en or k not in zh:
            print("前置缺失：%s 不在语言文件里" % k)
            return 2
    if en[K_ITEM] != "Useless Old Antique":
        print("前置缺失：%s 不是本轮定的新英文（实际 %r）" % (K_ITEM, en[K_ITEM]))
        return 2

    cases = []
    cases.append(Case("md-baseline", VM, 0, [], "none", EN))
    cases.append(Case("adv-baseline", VA, 0, [], "none", EN))

    # ① 删一个 en 键 ⇒ 键集不一致
    cases.append(Case("md-drop-en-key", VM, 1, ["bgfix10-lang-keyset"], "patch", EN,
                      old=line(K_ITEM, "Useless Old Antique"), new=b"", expect_occ=1))
    # ② 把某条 en 值改回中文 ⇒ "把中文拷进英文"
    cases.append(Case("md-zh-copy", VM, 1, ["bgfix10-lang-en-not-zh"], "patch", EN,
                      old=line(K_SWORD, en[K_SWORD]),
                      new=line(K_SWORD, zh[K_SWORD]), expect_occ=1))
    # ③ 空值
    cases.append(Case("md-empty-value", VM, 1, ["bgfix10-lang-no-empty"], "patch", EN,
                      old=line(K_AXE, en[K_AXE]), new=line(K_AXE, ""), expect_occ=1))
    # ④ 作废键回来（§十 那条"正 → 负"与 bgfix10 的负向都该命中）
    #    `entry.merchant` 命中 bgfix10 的 20 条负向；`entry.golden_feast` 命中 §十 那条改成正→负的断言
    cases.append(Case("md-retired-back", VM, 1,
                      ["bgfix10-lang-retired-gone", "bgbook10-lang-bilingual"], "patch", EN,
                      old=line(K_MERCH, en[K_MERCH]),
                      new=line("bettergold.handbook.entry.merchant", "The Gold Exchange Merchant")
                          + line("bettergold.handbook.entry.golden_feast", "Gild Your Food")
                          + line(K_GAST, en[K_GAST]),
                      expect_occ=1))
    # ⑤ 动一个"本轮不该动"的键 ⇒ 冻结子集 SHA256 变
    cases.append(Case("md-untouched-changed", VM, 1, ["bgfix10-lang-untouched-frozen"], "patch", EN,
                      old=line(K_SWORD, en[K_SWORD]),
                      new=line(K_SWORD, "Ancient Antique Sword"), expect_occ=1))
    # ⑥ 把本轮定的新英文改回旧值 ⇒ 产物被钉死的那条
    cases.append(Case("md-changed-revert", VM, 1, ["bgfix10-lang-changed-frozen"], "patch", EN,
                      old=line(K_ITEM, "Useless Old Antique"),
                      new=line(K_ITEM, "Unwanted Old Antique"), expect_occ=1))
    # ⑦ 规格里的口径句被删 ⇒ doc 断言
    cases.append(Case("md-doc-needle-gone", VM, 1, ["bgfix10-doc"], "patch", SPEC,
                      old=u"语言键删掉 ≠ 档案丢掉".encode("utf-8"), new=b""))
    # ⑧ manifest 回退 ⇒ 成就关卡的逐字断言
    cases.append(Case("adv-manifest-revert", VA, 1, ["bgach-lang-verbatim"], "patch", MANIFEST,
                      old=json.dumps("台上这鼓手有力气", ensure_ascii=False).encode("utf-8"),
                      new=json.dumps("等着看好戏吧，关于鼓手的", ensure_ascii=False).encode("utf-8"),
                      expect_occ=1))
    # ⑨ 反向对照：只加空行（JSON 里的空行合法，且不属于任何键）
    #    ⚠ 锚点用 `\n}`（本文件**不以换行结尾**，`}\n` 会 0 命中 —— 用例失效，实测踩过）
    cases.append(Case("md-reverse-blank-line", VM, 0, [], "patch", EN,
                      old=b"\n}", new=b"\n\n}", expect_occ=1))
    # ⑩ 反向对照：冻结快照里只加一行**非表格**说明（解析器只认 `|` 行）
    cases.append(Case("md-reverse-snap-prose", VM, 0, [], "patch", SNAP6,
                      old=b"## \xe5\xbf\xab\xe7\x85\xa7\xe6\x90\xac\xe8\xbf\x90\xe8\xae\xb0\xe5\xbd\x95",
                      new=b"<!-- bgfix10 reverse control: \xe8\xbf\x99\xe4\xb8\x80\xe8\xa1\x8c\xe4\xb8\x8d"
                          b"\xe6\x98\xaf\xe8\xa1\xa8\xe6\xa0\xbc\xe8\xa1\x8c -->\n"
                          b"## \xe5\xbf\xab\xe7\x85\xa7\xe6\x90\xac\xe8\xbf\x90\xe8\xae\xb0\xe5\xbd\x95",
                      expect_occ=1))
    # ⑪ 前置缺失：§6 冻结快照改名搬走 ⇒ exit 2
    cases.append(Case("md-precondition-missing", VM, 2, [], "rename", SNAP6))

    files = sorted({c.target for c in cases if c.kind in ("patch", "rename")})
    before = {f: path_digest(f) for f in files}
    print("[用例前置] 被扰动文件 %d 个；改前 SHA256 已记" % len(files))

    ok = True
    rows = []
    backup = {}
    for c in cases:
        try:
            apply(c, backup)
        except RuntimeError as e:
            print("SETUP-FAIL %s" % e)
            ok = False
            restore(c, backup)
            continue
        code, txt = run_validator(c.validator)
        c.exit = code
        c.hit = [t for t in c.tags if t in txt]
        restore(c, backup)
        same = path_digest(c.target) == before[c.target]
        if not same:
            ok = False
            c.note += "【复原失败】"
        if c.expect is None:
            pass
        elif c.expect == 0:
            good = (code == 0)
            if not good:
                c.note += "期望 exit 0（反向对照）"
            ok = ok and good
            c.good = good
        elif c.expect == 2:
            good = (code == 2)
            if not good:
                c.note += "期望 exit 2（前置缺失）"
            ok = ok and good
            c.good = good
        else:
            good = (code == 1 and len(c.hit) == len(c.tags))
            if not good:
                c.note += "期望 exit 1 + 命中 %s" % c.tags
            ok = ok and good
            c.good = good
        rows.append(c)
        print("%-26s kind=%-6s occ=%-4s exit=%-4s hit=%-58s %s"
              % (c.name, c.kind, c.occ, c.exit, ",".join(c.hit) or "-", c.note))

    print("")
    print("== 逐字节复原 ==")
    allsame = True
    for f in files:
        d = path_digest(f)
        same = d == before[f]
        allsame = allsame and same
        print("%-4s %s  %s" % ("OK" if same else "BAD", d[:16], f.relative_to(REPO)))
    ok = ok and allsame

    n_red = sum(1 for c in rows if c.expect == 1)
    n_zero = sum(1 for c in rows if c.expect == 0)
    n_two = sum(1 for c in rows if c.expect == 2)
    n_bad = sum(1 for c in rows if c.good is False) + (len(cases) - len(rows))
    print("")
    print("总计：cases run = %d / %d（弄脏⇒1 = %d / 反向对照⇒0 = %d / 前置缺失⇒2 = %d）；"
          "mismatches = %d；SETUP_FAILS = %d；RESTORE identical: %s"
          % (len(rows), len(cases), n_red, n_zero, n_two, n_bad, len(cases) - len(rows), allsame))
    print("RESULT %s" % ("ALL-PASS" if ok else "HAS-FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
