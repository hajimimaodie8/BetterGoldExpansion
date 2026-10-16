#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[bgn10-perturb] 扰动实测（1.7 bg-n10 轮1 后半 + 轮2）。

⚠ 为什么用 Python 而不是 PowerShell：第一版 PS 脚本在 **PowerShell 5.1** 下把 .ps1 当 ANSI 读
   ⇒ 中文路径变乱码、`Get-Content | WriteAllLines` 把 Java 文件的中文注释**双重编码写坏**
   （实测教训：MetalFamily.java 被写坏后只能用 `git checkout` 复原重做）。
   本脚本全程 bytes 级操作 + `shutil.copyfile` 复原 ⇒ 不经过任何文本代码页转换。

跑法：py -3 docs\\bgn10-证据\\脚本副本\\bgn10_perturb.py
每个用例：byte 备份 → 改 → 跑关卡 → 记 exit → **bytes 复原** → SHA256 自证。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = Path(__file__).resolve().parents[3]
EV = REPO / "docs" / "bgn10-证据"
TOOLS = REPO / "tools" / "asset-generator"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_validator(name: str) -> tuple[int, str]:
    cp = subprocess.run([sys.executable, str(TOOLS / f"{name}.py")], cwd=REPO,
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = [ln for ln in (cp.stdout or "").splitlines() if ln.strip()][-1:]
    return cp.returncode, (tail[0][:150] if tail else "")


def case(title: str, target: Path, mutate, validator: str, expect: int, log: list) -> None:
    bak = EV / ("_bak_" + target.name)
    shutil.copyfile(target, bak)
    h0 = sha(target)
    mutate()
    code, tail = run_validator(validator)
    ok = "OK" if code == expect else "!!"
    log.append(f"[{ok}] {title}: {validator} => exit {code}（期望 {expect}）| {tail}")
    shutil.copyfile(bak, target)
    log.append(f"      restore: sha256_equal={sha(target) == h0}")
    if code != expect:
        log.append("      ^^ 期望与实测不一致 —— 必须人工看")


def main() -> None:
    log: list[str] = []

    # ---------- 用例 1：只改注释必须仍绿（Java；断言读的是去注释源码） ----------
    mf = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "MetalFamily.java"

    def m1() -> None:
        with mf.open("ab") as fh:
            fh.write(b"\r\n// [bgn10-perturb] comment-only control (validator reads comment-stripped source)\r\n")

    case("CASE1 comment-only", mf, m1, "validate_metal_data", 0, log)

    # ---------- 用例 2：Python 侧的形态声明加回 bricks（Java ↔ Python 不一致） ----------
    pyf = TOOLS / "metal_forms.py"
    old = b'"chaosalloy": ["ingot", "block", "upgrade_template"],'
    new = b'"chaosalloy": ["ingot", "block", "upgrade_template", "bricks"],'

    def m2() -> None:
        pyf.write_bytes(pyf.read_bytes().replace(old, new))

    case("CASE2 dirty(Python forms != Java)", pyf, m2, "validate_metal_data", 1, log)

    # ---------- 用例 3：前置缺失（metal_forms.py 抽走）⇒ exit 2 ----------
    bak_name = pyf.with_suffix(".py.off")
    shutil.copyfile(pyf, bak_name)
    h0 = sha(pyf)
    pyf.unlink()
    code, tail = run_validator("validate_metal_data")
    log.append(f"[{'OK' if code == 2 else '!!'}] CASE3 missing-prereq(metal_forms.py): "
               f"validate_metal_data => exit {code}（期望 2）| {tail}")
    shutil.copyfile(bak_name, pyf)
    bak_name.unlink()
    log.append(f"      restore: sha256_equal={sha(pyf) == h0}")

    # ---------- 用例 4：数据侧脏（信标基座标签里删掉 chaosalloy_block） ----------
    bc = REPO / "src" / "main" / "resources" / "data" / "minecraft" / "tags" / "block" / "beacon_base_blocks.json"

    def m4() -> None:
        obj = json.loads(bc.read_text(encoding="utf-8"))
        obj["values"] = [v for v in obj["values"] if v != "bettergold:chaosalloy_block"]
        bc.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    case("CASE4 dirty(beacon tag)", bc, m4, "validate_metal_data", 1, log)

    # ---------- 用例 5：资产侧脏（删掉 chaosgold_block 的 blockstate） ----------
    bs = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "blockstates" / "chaosgold_block.json"

    def m5() -> None:
        bs.unlink()

    case("CASE5 dirty(missing blockstate)", bs, m5, "validate_metal_assets", 1, log)

    out = EV / "17-扰动实测.log"
    out.write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    bad = [x for x in log if x.startswith("[!!")]
    print(f"\n[bgn10-perturb] 用例 {len([x for x in log if x.startswith('[')])} 条，"
          f"不符合预期的 {len(bad)} 条")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
