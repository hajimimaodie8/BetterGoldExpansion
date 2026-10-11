#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix9 扰动矩阵（关卡"能红"的自证 + 逐字节复原 + SHA256）。

判读口径（`docs\\构建与跑测注意事项.md` §七 / `ex/03` §3.19.1）：
  * exit 0 = 全绿；1 = 命中问题；2 = 前置坏 / 脚本自身出错（**用例坏了**，不算命中）。
  * 每条用例都要报三列：`exit` / 命中的断言 id（`hit`）/ 改动是否真的生效（`occ`）。
    `occ == 0` ⇒ **用例失效**（用例本身没把字符串改到），必须显式判 INVALID。

本轮用例（A/B = 进度判据，C = 金玫瑰丛 × 金染土）：
  adv-baseline / adv-old-shape / adv-drop-one-item / adv-mix-tag / adv-eggplant-structure /
  adv-all-collapse / adv-precondition-missing
  gen-old-shape / gen-eggplant-structure / gen-comment-only(反向对照，必须仍绿)
  md-baseline / md-blocks-revert / md-unconditional-true / md-dirt-tag /
  md-farmland-regression / md-comment-only(反向对照) / md-precondition-missing
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]                     # docs/bgfix9-证据 -> repo
TOOLS = REPO / "tools" / "asset-generator"
ADV = REPO / "src/main/resources/data/bettergold/advancement"
JAVA = REPO / "src/main/java/com/hjmmd_8/bettergold"
LANG = REPO / "src/main/resources/assets/bettergold/lang"

VA = TOOLS / "validate_advancements.py"
VM = TOOLS / "validate_metal_data.py"
GEN = TOOLS / "generate_advancements.py"
ANY_RAW = ADV / "treasure/any_raw_metal.json"
EGGPLANT = ADV / "agriculture/eggplant_seeds.json"
FEAST1 = ADV / "agriculture/midas_feast_1.json"
BLOCKS = JAVA / "registry/AllBlocks.java"
DIRT = JAVA / "block/GoldInfusedDirtBlock.java"
FARMLAND = JAVA / "block/GoldInfusedFarmlandBlock.java"
DIRT_TAG = REPO / "src/main/resources/data/minecraft/tags/block/dirt.json"

OLD_RAW = (HERE / "_adv-before/treasure/any_raw_metal.json")   # 改前副本（旧形状）
OLD_EGG = (HERE / "_adv-before/agriculture/eggplant_seeds.json")


def strip_py_comments(src: str) -> str:
    return re.sub(r"#[^\n]*", "", src)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def path_digest(p: Path) -> str:
    """文件 ⇒ 内容 SHA256；目录 ⇒ 递归（相对路径 + 内容哈希）清单的 SHA256。

    ⚠ 「前置缺失 ⇒ exit 2」那两条用例改的是**目录名**（adv / lang）⇒ 只算文件哈希会对目录
    恒返回 `<absent>`，让"逐字节复原"变成空话（承 `ex/03` §3.19.1 的"反空转"纪律）。
    """
    if p.is_file():
        return sha(p.read_bytes())
    if p.is_dir():
        items = []
        for f in sorted(x for x in p.rglob("*") if x.is_file()):
            items.append(f"{f.relative_to(p).as_posix()}:{sha(f.read_bytes())}")
        return sha("\n".join(items).encode("utf-8"))
    return "<absent>"


def run_validator(v: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(v)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(REPO))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


REPORT = HERE / "01-关卡扰动矩阵.txt"


class _Tee:
    """把 stdout 同时写进证据文件（**UTF-8 无 BOM / LF**）。

    ⚠ 别用 PowerShell 的 `*>` / `Tee-Object` 抓证据：那会写成 **UTF-16**（读回来是乱码），
    见 `ex/03` §3.21 ①。证据文件一律让 Python 自己写。
    """

    def __init__(self, path: Path):
        self.fh = path.open("w", encoding="utf-8", newline="\n")

    def write(self, s: str) -> int:
        sys.__stdout__.write(s)
        return self.fh.write(s)

    def flush(self) -> None:
        sys.__stdout__.flush()
        self.fh.flush()


class Case:
    def __init__(self, name, validator, expect, tags, kind, target, old=b"", new=b"",
                 expect_occ=None):
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


def apply(case: Case, backup: dict[Path, bytes]):
    t = case.target
    if case.kind == "copyfile":
        backup[t] = t.read_bytes()
        case.occ = 1
        shutil.copyfile(case.old, t)
    elif case.kind == "patch":
        src = t.read_bytes()
        backup[t] = src
        case.occ = src.count(case.old)
        if case.expect_occ is not None and case.occ != case.expect_occ:
            raise RuntimeError(f"{case.name}: occ={case.occ} 期望 {case.expect_occ}（用例失效）")
        if case.occ == 0:
            raise RuntimeError(f"{case.name}: 目标串 0 命中（用例失效）")
        t.write_bytes(src.replace(case.old, case.new))
    elif case.kind == "create":
        if t.exists():
            raise RuntimeError(f"{case.name}: 目标文件已存在（用例失效）")
        backup[t] = None
        case.occ = 1
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(case.new)
    elif case.kind == "rename":
        if not t.exists():
            raise RuntimeError(f"{case.name}: 目标目录不存在（用例失效）")
        backup[t] = b"<renamed>"
        case.occ = 1
        t.rename(t.with_name(t.name + "_moved_by_perturb"))
    elif case.kind == "none":
        case.occ = "-"
    else:
        raise RuntimeError(f"未知 kind {case.kind}")


def restore(case: Case, backup: dict[Path, bytes]):
    t = case.target
    if case.kind == "none":
        return                      # 基线 / MEASURED 用例：什么都没动
    orig = backup[t]
    if case.kind == "create":
        if t.exists():
            t.unlink()
    elif case.kind == "rename":
        moved = t.with_name(t.name + "_moved_by_perturb")
        moved.rename(t)
    else:
        t.write_bytes(orig)


def main() -> int:
    sys.stdout = _Tee(REPORT)
    if not OLD_RAW.is_file() or not OLD_EGG.is_file():
        print("前置缺失：缺 _adv-before 副本（本脚本必须与 docs/bgfix9-证据/_adv-before 一起用）")
        return 2

    one_pred = b'c_inv([RAW_MATERIALS])'
    raw_ids = ANY_RAW.read_bytes()

    gen_src = GEN.read_text(encoding="utf-8")
    occ_raw_code = gen_src.count(one_pred.decode())
    occ_raw_hint = strip_py_comments(gen_src).count("c_inv(RAW_MATERIALS)")
    gen_nc = strip_py_comments(gen_src)
    print(f"[用例前置] 生成器 raw 源码里 `c_inv([RAW_MATERIALS])` 出现 {occ_raw_code} 次；"
          f"去注释后旧形状 `c_inv(RAW_MATERIALS)` 出现 {occ_raw_hint} 次（应为 0）")
    if occ_raw_code != 1 or occ_raw_hint != 0:
        print("前置断言不成立 ⇒ 用例设计失效，先停下")
        return 2

    cases: list[Case] = []
    cases.append(Case("adv-baseline", VA, 0, [], "none", ADV))
    cases.append(Case("adv-old-shape", VA, 1,
                      ["bgfix9-inv-one-predicate", "bgfix9-raw-metal-shape"],
                      "copyfile", ANY_RAW, old=OLD_RAW))
    cases.append(Case("adv-drop-one-item", VA, 1, ["bgfix9-raw-metal-shape"], "patch", ANY_RAW,
                      old=b'              "bettergold:raw_echogold",\n', new=b"",
                      expect_occ=1))
    cases.append(Case("adv-mix-tag", VA, 1, ["bgfix9-items-homogeneous"], "patch", ANY_RAW,
                      old=b'              "bettergold:raw_flamegold",\n',
                      new=b'              "bettergold:raw_flamegold",\n'
                          b'              "#bettergold:raw_materials",\n',
                      expect_occ=1))
    cases.append(Case("adv-eggplant-structure", VA, 1,
                      ["bgfix9-eggplant-no-structure", "bgfix9-no-player-condition"],
                      "copyfile", EGGPLANT, old=OLD_EGG))
    feast = FEAST1.read_text(encoding="utf-8")
    reqs = re.search(r'"requirements": \[\n(.*?)\n  \]', feast, re.S)
    if not reqs:
        print("前置缺失：midas_feast_1 里找不到 requirements 块")
        return 2
    names = re.findall(r'"([a-z0-9_]+)"', reqs.group(1))
    collapsed = '"requirements": [\n    ' + ",\n    ".join(f'"{n}"' for n in names) + "\n  ]"
    cases.append(Case("adv-all-collapse", VA, 1, ["bgfix9-all-of-shape"], "patch", FEAST1,
                      old=reqs.group(0).encode(), new=collapsed.encode(), expect_occ=1))
    cases.append(Case("adv-precondition-missing", VA, None, [], "rename", ADV))
    cases.append(Case("gen-old-shape", VA, 1, ["bgfix9-generator-raw-metal"], "patch", GEN,
                      old=one_pred, new=b"c_inv(RAW_MATERIALS)", expect_occ=1))
    cases.append(Case("gen-eggplant-structure", VA, 1, ["bgfix9-generator-eggplant"], "patch", GEN,
                      old=b'c_inv([f"{NS}:golden_eggplant_seeds"])',
                      new=b'c_inv([f"{NS}:golden_eggplant_seeds"], '
                          b'structure="minecraft:bastion_remnant")',
                      expect_occ=1))
    cases.append(Case("gen-comment-only", VA, 0, [], "patch", GEN,
                      old=b'NS = "bettergold"',
                      # ⚠ 反向对照的目标串**不含行尾**：本仓 .py 是 CRLF、.java/JSON 是 LF，
                      #   带 `\n` 的锚点会静默 0 命中（`ex/03` §3.11 的 CRLF 陷阱）。
                      #   ASCII-only，且**逐字含**两条被禁写的 needle —— 关卡必须仍然绿。
                      new=b'NS = "bettergold"'
                          b'  # reverse-control: c_inv(RAW_MATERIALS) + '
                          b'structure="minecraft:bastion_remnant" must NOT turn the gate red',
                      expect_occ=1))

    cases.append(Case("md-baseline", VM, 0, [], "none", ADV))
    cases.append(Case("md-blocks-revert", VM, 1, ["bgfix9-rose-dirt-sustain-block"], "patch", BLOCKS,
                      old=b"new com.hjmmd_8.bettergold.block.GoldInfusedDirtBlock(",
                      new=b"new Block(", expect_occ=1))
    cases.append(Case("md-unconditional-true", VM, 1,
                      ["bgfix9-rose-dirt-sustain-whitelist"], "patch", DIRT,
                      old=b"        if (plant.is(AllBlocks.GOLDEN_ROSE_BUSH.get())) {\n"
                          b"            return TriState.TRUE;\n"
                          b"        }\n"
                          b"        return TriState.DEFAULT;\n",
                      new=b"        return TriState.TRUE;\n", expect_occ=1))
    cases.append(Case("md-dirt-tag", VM, 1, ["bgfix9-rose-dirt-not-in-dirt-tag"], "create", DIRT_TAG,
                      new=b'{\n  "replace": false,\n  "values": [\n'
                          b'    "bettergold:gold_infused_dirt"\n  ]\n}\n'))
    cases.append(Case("md-farmland-regression", VM, 1,
                      ["bgfix9-rose-farmland-regression"], "patch", FARMLAND,
                      old=b"        return net.neoforged.neoforge.common.util.TriState.TRUE;\n",
                      new=b"        return net.neoforged.neoforge.common.util.TriState.DEFAULT;\n",
                      expect_occ=1))
    cases.append(Case("md-comment-only", VM, 0, [], "patch", DIRT,
                      old=b"public class GoldInfusedDirtBlock extends Block {\n",
                      new=b"// \xe5\x8f\x8d\xe5\x90\x91\xe5\xaf\xb9\xe7\x85\xa7\xef\xbc\x9a\xe8\xbf\x99\xe9\x87\x8c"
                          b"\xe6\x8f\x90\xe4\xb8\x80\xe5\x8f\xa5 GOLDEN_ROSE_BUSH "
                          b"\xe4\xb8\x8e canSustainPlant \xe9\x83\xbd\xe4\xb8\x8d\xe8\xaf\xa5\xe8\xae\xa9\xe5\x85\xb3"
                          b"\xe5\x8d\xa1\xe5\x8f\x98\xe7\xba\xa2\n"
                          b"public class GoldInfusedDirtBlock extends Block {\n",
                      expect_occ=1))
    cases.append(Case("md-precondition-missing", VM, 2, [], "rename", LANG))

    # 先记全量 SHA256（用例的"改前基线"）—— 含两条"目录改名"用例的目标目录
    files = sorted({c.target for c in cases if c.kind in ("copyfile", "patch", "create", "rename")})
    before = {f: path_digest(f) for f in files}

    ok = True
    rows = []
    backup: dict[Path, bytes | None] = {}
    for c in cases:
        backup.clear()
        try:
            apply(c, backup)
        except Exception as exc:  # noqa: BLE001
            print(f"INVALID {c.name}: {exc}")
            ok = False
            continue
        try:
            c.exit, out = run_validator(c.validator)
            c.hit = sorted({t for t in c.tags if f"[{t}]" in out})
            if not c.tags and c.expect == 0:
                c.note = "基线/反向对照" if "comment" in c.name or "baseline" in c.name else ""
            elif c.tags:
                for t in c.tags:
                    if f"FAIL [{t}]" in out or f"[{t}]" in out:
                        pass
            fails = [ln for ln in out.splitlines() if ln.startswith("FAIL")][:2]
            rows.append((c, fails))
        finally:
            restore(c, backup)
        # 逐字节复原自证
        f = c.target
        after = path_digest(f)
        exp_before = before.get(f, "<absent>")
        restored = (after == exp_before)
        verdict = "?"
        if c.expect is None:
            verdict = "MEASURED"
        elif c.exit == c.expect and restored and (not c.tags or len(c.hit) > 0):
            verdict = "OK"
        elif c.exit == 2 and c.expect != 2:
            verdict = "INVALID(exit2=用例坏了)"
            ok = False
        else:
            verdict = "MISMATCH"
            ok = False
        print(f"{verdict:>22} | {c.name:<26} | validator={c.validator.name:<28} | exit={c.exit} "
              f"expect={c.expect} | hit={c.hit} | occ={c.occ} | 复原SHA256={'一致' if restored else '不一致'}")
        for ln in rows[-1][1]:
            print(f"{'':>22} |   └ {ln[:180]}")
        if c.expect is not None and not c.tags and c.expect == 0 and c.exit != 0:
            print(f"{'':>22} |   └ 反向对照红了 ⇒ 判据读到了注释（§3.17 的假绿镜像）")

    print()
    print(f"扰动矩阵：{len(cases)} 条用例，mismatches = {0 if ok else 1}")
    # 复原核对（全部复原后重算一遍摘要）
    drift = [str(f) for f in files if path_digest(f) != before[f]]
    print(f"复原核对：{len(drift)} 个目标与改前摘要不一致 {drift}")
    print("改前/改后逐目标 SHA256（前 16 位）：")
    for f in files:
        print(f"    {before[f][:16]}  {f.relative_to(REPO) if f.is_relative_to(REPO) else f}")
    return 0 if (ok and not drift) else 1


if __name__ == "__main__":
    raise SystemExit(main())
