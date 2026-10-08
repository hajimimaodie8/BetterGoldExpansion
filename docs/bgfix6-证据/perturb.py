# -*- coding: utf-8 -*-
"""bgfix6 关卡扰动矩阵（可复算 / 逐字节复原）。

口径（每个用例五步）：
  ① 记录目标文件（或目录）的 SHA256
  ② 施加**最小**改动，并显式报出「改动真的生效了吗」（hit / occ=N）—— §3.11：
     扰动矩阵必须能区分「关卡漏了」与「扰动没生效」；目标串不唯一就**判用例失效**（不谎报命中）
  ③ 跑关卡（stdout+stderr 落**文件**，不走管道 —— 避开本机沙箱对 pipe 的限制），记**退出码**与关键行
  ④ **逐字节复原**（从原始 `bytes` 写回，不是文本往返 ⇒ 不会有 BOM / 行尾漂移）
  ⑤ 复核 SHA256 与改前**完全相同**

退出码契约：0 绿 / 1 有「问题」 / 2 前置坏。
⚠ 本脚本**不碰** `run\\` 目录（forceload 用例只用 `%TEMP%` 里的复制品与伪造件）、
  **不碰任何贴图**、**不 commit**。
用法: python perturb.py
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "tools" / "asset-generator"
EVID = Path(__file__).resolve().parent
TMP = Path(tempfile.gettempdir())

ROWS: list[dict] = []
MISMATCH = 0
RESTORE_BAD = 0
CASE_OUT: list[str] = []


class _Tee:
    """同时写「UTF-8 证据文件」与「控制台」。

    Windows 控制台是 GBK：非 GBK 字符（U+21D2 之类）会让 print 直接抛 UnicodeEncodeError
    —— 这正是本仓六个校验器都写了兜底的那一条（`docs/构建与跑测注意事项.md` §三）。
    而证据文件必须是 UTF-8（否则 `Get-Content -Encoding utf8` 读出来是乱码）。
    """

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


sys.stdout = _Tee(EVID / "17-扰动矩阵.txt")

KEY_RE = re.compile(
    r"FAIL|\[[a-z0-9-]*(?:ok|fail|anti-vacuum|crash|missing|unreadable|key-absent|residual)\]"
    r"|问题合计|问题: [1-9]|为 0 =|关卡自身出错")


def sha256_of(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_gate(script: str, extra: tuple = ()) -> tuple[int, str]:
    fd, tmp = tempfile.mkstemp(prefix="bgfix6-out-", suffix=".txt")
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
    return " | ".join(hits[:4])


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
    """每个用例的关卡原始输出逐例留档（自证用；不进控制台）。"""
    CASE_OUT.append(f"\n########## {cid}  {gate}  ##########\n{out.rstrip()}\n")


def file_case(cid, gate, rel, mode, expect, old=None, new=None, extra=()):
    """字节改动 ⇒ 跑关卡 ⇒ 逐字节复原。"""
    path = REPO / rel
    orig = path.read_bytes()
    sha0 = hashlib.sha256(orig).hexdigest()
    hit = "n/a"
    try:
        if mode == "replace":
            text = orig.decode("utf-8")
            occ = text.count(old)
            hit = f"occ={occ}"
            if occ != 1:
                raise RuntimeError(f"扰动目标不唯一（occ={occ}）—— 用例本身失效（§3.11）")
            path.write_bytes(text.replace(old, new).encode("utf-8"))
        elif mode == "append":
            path.write_bytes(orig + ("\r\n" + (new or "")).encode("utf-8"))
            hit = "appended"
        else:
            raise RuntimeError(f"未知 mode {mode}")
        code, out = run_gate(gate, extra)
        log_case(cid, gate, out)
        record(cid, gate, f"{mode}@{rel}", expect, code, hit, "ok", key_lines(out))
    except Exception as exc:  # noqa: BLE001
        record(cid, gate, f"{mode}@{rel}", expect, -1, f"ERROR {exc!r}", "ok", "用例自身失效（§3.11）")
    finally:
        path.write_bytes(orig)
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha0:
            print(f"[RESTORE-FAIL] {cid} 复原后哈希不符")
            globals()["RESTORE_BAD"] += 1


def rename_case(cid, gate, rel, expect, extra=()):
    """前置缺失（目录/文件改名搬走）⇒ 期望 exit 2；finally 一定搬回来。"""
    path = REPO / rel
    bak = path.with_name(path.name + ".bgfix6bak")
    is_dir = path.is_dir()
    sha0 = None if is_dir else hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        path.rename(bak)
        code, out = run_gate(gate, extra)
        log_case(cid, gate, out)
        record(cid, gate, f"rename-away@{rel}", expect, code, "moved", "ok", key_lines(out))
    except Exception as exc:  # noqa: BLE001
        record(cid, gate, f"rename-away@{rel}", expect, -1, f"ERROR {exc!r}", "ok", "用例自身失效（§3.11）")
    finally:
        if bak.exists():
            bak.rename(path)
        if not path.exists():
            print(f"[RESTORE-FAIL] {cid} 没复原")
            globals()["RESTORE_BAD"] += 1
        elif sha0 is not None and hashlib.sha256(path.read_bytes()).hexdigest() != sha0:
            print(f"[RESTORE-FAIL] {cid} 复原后哈希不符")
            globals()["RESTORE_BAD"] += 1


M = "src\\main\\resources\\assets\\bettergold\\models\\item\\flamegold_ingot.json"
ZH = "src\\main\\resources\\assets\\bettergold\\lang\\zh_cn.json"
TRIM = "src\\main\\resources\\data\\bettergold\\trim_material\\illusiongold.json"
ROOT = "src\\main\\resources\\data\\bettergold\\advancement\\root.json"

print("=" * 78)
print("bgfix6 扰动矩阵：弄脏 ⇒ exit 1 / 前置缺失 ⇒ exit 2 / 只加空白 ⇒ exit 0")
print("=" * 78)

# ============ 1. validate_metal_assets.py ============
file_case("MA-D1", "validate_metal_assets.py", M, "replace", 1,
          old='"bettergold:item/flamegold_ingot"', new='"bettergold:item/flamegold_ingot_NOPE"')
rename_case("MA-T1", "validate_metal_assets.py", "src\\main\\resources\\assets\\bettergold", 2)
file_case("MA-W1", "validate_metal_assets.py", M, "append", 0, new="")

# ============ 2. validate_metal_data.py ============
file_case("MD-D1", "validate_metal_data.py", ZH, "replace", 1,
          old='"item.bettergold.flamegold_ingot"', new='"item.bettergoldXXX.flamegold_ingot"')
rename_case("MD-T1", "validate_metal_data.py", "src\\main\\resources\\assets\\bettergold\\lang", 2)
file_case("MD-W1", "validate_metal_data.py", ZH, "append", 0, new="   ")

# ============ 3. validate_trim_assets.py ============
file_case("TR-D1", "validate_trim_assets.py", TRIM, "replace", 1,
          old='"item_model_index": 0.07', new='"item_model_index": 0.1')
_no_jar = TMP / "bgfix6-no-such-client.jar"
code, out = run_gate("validate_trim_assets.py", (str(_no_jar),))
log_case("TR-T1", "validate_trim_assets.py", out)
record("TR-T1", "validate_trim_assets.py", "argv=不存在的原版 client jar", 2, code, "n/a", "ok", key_lines(out))
file_case("TR-W1", "validate_trim_assets.py", TRIM, "append", 0, new="")

# ============ 4. validate_advancements.py ============
file_case("AD-D1", "validate_advancements.py", ROOT, "replace", 1,
          old='"trigger": "minecraft:inventory_changed"', new='"trigger": "minecraft:inventory_changedXX"')
rename_case("AD-T1", "validate_advancements.py", "tools\\asset-generator\\advancement_manifest.json", 2)
file_case("AD-W1", "validate_advancements.py", ROOT, "append", 0, new="")

# ============ 5. check_jar_clean.py ============
# 弄脏 jar 的 JC-D1 需要「带假 Probe 类的一次构建」⇒ 由 dirty-jar-case.ps1/python 单独跑（见 18-*）
rename_case("JC-T1", "check_jar_clean.py", "build\\libs\\bettergold-1.6.0.jar", 2)
file_case("JC-W1", "check_jar_clean.py",
          "src\\main\\java\\com\\hjmmd_8\\bettergold\\material\\MetalFamily.java", "append", 0,
          new="// bgfix6 反向对照：只加注释必须仍绿（jar 内容不变）")

# ============ 6. check_forced_chunks.py ============
real = REPO / "run" / "world" / "data" / "chunks.dat"
if real.is_file():
    copy = TMP / "bgfix6-chunks-copy.dat"
    shutil.copyfile(real, copy)
    code, out = run_gate("check_forced_chunks.py", (str(copy),))
    log_case("FC-W1", "check_forced_chunks.py", out)
    record("FC-W1", "check_forced_chunks.py", "argv=真实 chunks.dat 的副本（原件零改动）", 0,
           code, "copy", "ok", key_lines(out))
    dirty = TMP / "bgfix6-chunks-dirty.dat"
    subprocess.run([sys.executable, str(EVID / "make-dirty-chunks.py"), str(dirty)], check=True)
    code, out = run_gate("check_forced_chunks.py", (str(dirty),))
    log_case("FC-D1", "check_forced_chunks.py", out)
    record("FC-D1", "check_forced_chunks.py", "argv=伪造 Forced=[0] 的 chunks.dat", 1,
           code, "crafted", "ok", key_lines(out))
else:
    print("[SKIP] run\\world\\data\\chunks.dat 不存在 ⇒ FC-W1 / FC-D1 跳过")
code, out = run_gate("check_forced_chunks.py", (str(TMP / "bgfix6-no-such-chunks.dat"),))
log_case("FC-T1", "check_forced_chunks.py", out)
record("FC-T1", "check_forced_chunks.py", "argv=不存在的路径", 2, code, "n/a", "ok", key_lines(out))

print("")
print("=" * 78)
print(f"{'id':7s} {'gate':26s} {'op':46s} {'exp':>3s} {'got':>3s} {'hit':12s} restore")
for r in ROWS:
    print(f"{r['id']:7s} {r['gate']:26s} {r['op']:46s} {r['expect']:>3d} {r['got']:>3d} {r['hit']:12s} {r['restore']}")
print(f"mismatches = {MISMATCH} / {len(ROWS)} 个用例；restore 失败 = {RESTORE_BAD}")
print(f"[bgfix6-perturb-{'ok' if (MISMATCH == 0 and RESTORE_BAD == 0) else 'fail'}]")
(EVID / "17-扰动矩阵-逐例输出.txt").write_text("".join(CASE_OUT), encoding="utf-8")
sys.stdout.flush()
sys.exit(0 if (MISMATCH == 0 and RESTORE_BAD == 0) else 1)
