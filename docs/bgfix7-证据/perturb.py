# -*- coding: utf-8 -*-
"""bgfix7 关卡扰动矩阵（可复算 / 逐字节复原）。

只钉本轮新增的那一条关卡族 `[bgfix7-*]`（`validate_metal_data.py` 里）。

口径（每个用例五步，与 `docs/bgfix6-证据/perturb.py` 同形）：
  ① 记录目标文件的 SHA256
  ② 施加**最小**改动，并显式报出「改动真的生效了吗」（hit / occ=N）—— ex/03 §3.11：
     必须能区分「关卡漏了」与「扰动没生效」；目标串不唯一就**判用例失效**（不谎报命中）
  ③ 跑关卡（stdout+stderr 落**文件**，不走管道），记**退出码**与关键行
  ④ **逐字节复原**（从原始 `bytes` 写回，不是文本往返 ⇒ 不会有 BOM / 行尾漂移）
  ⑤ 复核 SHA256 与改前**完全相同**

退出码契约：0 绿 / 1 有「问题」 / 2 前置坏。
⚠ 本脚本**不碰** `run\\`、**不碰任何贴图**、**不 commit**。
用法: python perturb.py
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "tools" / "asset-generator"
EVID = Path(__file__).resolve().parent

ROWS: list[dict] = []
MISMATCH = 0
RESTORE_BAD = 0
CASE_OUT: list[str] = []


class _Tee:
    """同时写「UTF-8 证据文件」与「控制台」（Windows 控制台是 GBK，非 GBK 字符会抛）。"""

    def __init__(self, path: Path):
        self.fh = open(path, "w", encoding="utf-8", newline="\n")
        self.out = sys.__stdout__

    def write(self, s):
        self.fh.write(s)
        try:
            self.out.write(s)
        except Exception:  # noqa: BLE001
            pass
        return len(s)

    def flush(self):
        self.fh.flush()
        try:
            self.out.flush()
        except Exception:  # noqa: BLE001
            pass


sys.stdout = _Tee(EVID / "07-扰动矩阵.txt")

KEY_RE = re.compile(
    r"bgfix7|\[bgfix7-[a-z0-9-]*\]|\[bg-data-(?:ok|fail|crash)\]|问题合计|问题: [1-9]|前置缺失")


def run_gate(script: str, extra: tuple = ()) -> tuple[int, str]:
    fd, tmp = tempfile.mkstemp(prefix="bgfix7-out-", suffix=".txt")
    os.close(fd)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [sys.executable, str(GEN / script)] + [str(a) for a in extra]
    with open(tmp, "wb") as fh:
        proc = subprocess.run(cmd, cwd=str(REPO), stdout=fh, stderr=subprocess.STDOUT, env=env)
    out = Path(tmp).read_text(encoding="utf-8", errors="replace")
    Path(tmp).unlink()
    return proc.returncode, out


def key_lines(out: str) -> str:
    hits = [ln.strip() for ln in out.splitlines() if KEY_RE.search(ln)]
    return " | ".join(hits[:3])


def record(cid, gate, op, expect, got, hit, restore, note) -> None:
    global MISMATCH, RESTORE_BAD
    verdict = "OK" if got == expect else "MISMATCH"
    if verdict == "MISMATCH":
        MISMATCH += 1
    if restore != "ok":
        RESTORE_BAD += 1
    ROWS.append(dict(id=cid, gate=gate, op=op, expect=expect, got=got,
                     verdict=verdict, hit=hit, restore=restore, note=note))
    print(f"[{verdict:8s}] {cid:6s} {gate:26s} expect={expect} got={got} hit={hit} restore={restore}")
    if note:
        print(f"           {note}")


def log_case(cid, gate, out) -> None:
    CASE_OUT.append(f"\n########## {cid}  {gate}  ##########\n{out.rstrip()}\n")


def _run_one(cid, gate, rel, mutate, expect, extra=()):
    """mutate(text) -> (new_text, hit_note)；改动没生效 / 目标不唯一 ⇒ 用例失效。"""
    path = REPO / rel
    orig = path.read_bytes()
    sha0 = hashlib.sha256(orig).hexdigest()
    hit = "n/a"
    try:
        text = orig.decode("utf-8")
        new_text, hit = mutate(text)
        if new_text == text:
            raise RuntimeError("改动没有生效（new == old）—— 用例本身失效（ex/03 §3.11）")
        path.write_bytes(new_text.encode("utf-8"))
        code, out = run_gate(gate, extra)
        log_case(cid, gate, out)
        record(cid, gate, f"edit@{rel}", expect, code, hit, "ok", key_lines(out))
    except Exception as exc:  # noqa: BLE001
        record(cid, gate, f"edit@{rel}", expect, -1, f"ERROR {exc!r}", "ok", "用例自身失效（ex/03 §3.11）")
    finally:
        path.write_bytes(orig)
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha0:
            print(f"[RESTORE-FAIL] {cid} 复原后哈希不符")
            globals()["RESTORE_BAD"] += 1


def one(text, old, new):
    occ = text.count(old)
    if occ != 1:
        raise RuntimeError(f"扰动目标不唯一（occ={occ}）：{old!r}")
    return text.replace(old, new), f"occ=1"


def swap(text, a, b):
    oa, ob = text.count(a), text.count(b)
    if oa != 1 or ob != 1:
        raise RuntimeError(f"交换目标不唯一（occ {a!r}={oa} / {b!r}={ob}）")
    return text.replace(a, "\x00").replace(b, a).replace("\x00", b), f"swap occ={oa}/{ob}"


def rename_case(cid, gate, rel, expect, extra=()):
    """前置缺失（文件改名搬走）⇒ 期望 exit 2；finally 一定搬回来。"""
    path = REPO / rel
    bak = path.with_name(path.name + ".bgfix7bak")
    sha0 = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        path.rename(bak)
        code, out = run_gate(gate, extra)
        log_case(cid, gate, out)
        record(cid, gate, f"rename-away@{rel}", expect, code, "moved", "ok", key_lines(out))
    except Exception as exc:  # noqa: BLE001
        record(cid, gate, f"rename-away@{rel}", expect, -1, f"ERROR {exc!r}", "ok", "用例自身失效")
    finally:
        if bak.exists():
            bak.rename(path)
        if not path.exists():
            print(f"[RESTORE-FAIL] {cid} 没复原")
            globals()["RESTORE_BAD"] += 1
        elif hashlib.sha256(path.read_bytes()).hexdigest() != sha0:
            print(f"[RESTORE-FAIL] {cid} 复原后哈希不符")
            globals()["RESTORE_BAD"] += 1


SECT = "src\\main\\java\\com\\hjmmd_8\\bettergold\\material\\CreativeTabSections.java"
SNAP_A = "tools\\asset-generator\\bgfix7-creative-material-baseline.txt"
SNAP_B = "tools\\asset-generator\\bgfix7-creative-material-prefix-order.txt"
GATE = "validate_metal_data.py"

print("=" * 78)
print("bgfix7 扰动矩阵：打乱/删项/移末尾/注释假绿 ⇒ exit 1；快照缺失 ⇒ exit 2；只改注释 ⇒ exit 0")
print("=" * 78)

# ---------- 基线（改前 / 收尾各一次） ----------
code, out = run_gate(GATE)
log_case("X7-BASE", GATE, out)
record("X7-BASE", GATE, "基线（无扰动）", 0, code, "n/a", "ok", key_lines(out))

# ---------- 1. 打乱一项（交换第 6/7 项 = 重锤/三叉戟）⇒ exit 1 ----------
_run_one("X7-D1", GATE, SECT,
         lambda t: swap(t, '"golden_mace_blank",', '"golden_trident_blank",'), 1)

# ---------- 2. 删一项（把小下界合金碎片那个 id 从表里删掉，留空行）⇒ exit 1 ----------
# ⚠ 目标必须**唯一**：`"gourmet_box",` 在本文件里出现 2 次（前缀表 + `isTraderRelated` 的白名单）
#   ⇒ 用它会被判"用例失效"（ex/03 §3.11）。这里选只用在前缀表里的那一个。
_run_one("X7-D2", GATE, SECT,
         lambda t: one(t, '"small_netherite_scrap",', ''), 1)

# ---------- 3. 移一项到末尾（把手册挪到最后 = 与末项对调）⇒ exit 1 ----------
_run_one("X7-D3", GATE, SECT,
         lambda t: swap(t, '"alchemy_student_handbook",', '"alchemy_materials_box");'), 1)

# ---------- 4. §3.17 反向对照：只在**注释**里逐字写出一个假的前缀表 ⇒ 必须仍绿 ----------
_run_one("X7-W1", GATE, SECT,
         lambda t: one(t, 'public static final List<String> MATERIAL_PREFIX_ORDER = List.of(',
                       '// MATERIAL_PREFIX_ORDER = List.of("hacked");\n    '
                       'public static final List<String> MATERIAL_PREFIX_ORDER = List.of('), 0)

# ---------- 5. 只改注释（段标签里的一个中文注释）⇒ 必须仍绿 ----------
_run_one("X7-W2", GATE, SECT,
         lambda t: one(t, '"alchemy_student_handbook",                    // 手册（新生代炼金术学员手册）',
                       '"alchemy_student_handbook",                    // 手册（新生代炼金术学员手册）XX'), 0)

# ---------- 6. 前置缺失：两个期望值快照各自搬走 ⇒ exit 2 ----------
rename_case("X7-T1", GATE, SNAP_A, 2)
rename_case("X7-T2", GATE, SNAP_B, 2)

# ---------- 7. 快照 A 被改坏形状（少一行 ⇒ 不是 61 件）⇒ exit 1 ----------
_run_one("X7-D4", GATE, SNAP_A,
         lambda t: one(t, "61 bettergold:illusiongold_upgrade_template\n", ""), 1)

# ---------- 收尾基线（复原之后必须回到 0） ----------
code, out = run_gate(GATE)
log_case("X7-BASE-END", GATE, out)
record("X7-BASE-END", GATE, "收尾基线（全部复原之后）", 0, code, "n/a", "ok", key_lines(out))

print("=" * 78)
print(f"用例 {len(ROWS)} 条 / mismatches = {MISMATCH} / restore 失败 = {RESTORE_BAD}")
for r in ROWS:
    print(f"  {r['id']:12s} expect={r['expect']} got={r['got']} {r['verdict']:8s} hit={r['hit']}")
print("=" * 78)
print("每个被改文件的**逐字节复原**判据 = 上面每条用例 finally 里的 SHA256 复核 + 收尾基线 exit 0")

with open(EVID / "07-扰动矩阵-逐例输出.txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("".join(CASE_OUT))

sys.exit(1 if (MISMATCH or RESTORE_BAD) else 0)
