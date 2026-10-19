"""bg-n10fix2 扰动矩阵（7 用例：①②③④ 各 >=1 + 只改注释仍绿的反向对照）。

铁律：
  * 源码改动 / 复原一律走 Python **bytes**（不碰 PowerShell 的编码）；
  * 每个用例都记录 `exit` 与 `hit`，并**逐字节复原 + SHA256 自证**；
  * 正向 needle 跑在关卡内部的“去注释源码”上，所以“只改注释”必须仍 exit 0。
"""
import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = pathlib.Path(__file__).resolve().parent / "matrix.txt"

CC = "src/main/java/com/hjmmd_8/bettergold/entity/ChaosCoinProjectile.java"
MG = "src/main/java/com/hjmmd_8/bettergold/entity/MoneyGremlin.java"
IM = "src/main/java/com/hjmmd_8/bettergold/material/ImbalanceEffects.java"
AM = "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java"
FD = "src/main/java/com/hjmmd_8/bettergold/fd/FdItems.java"

CASES = [
    ("P01-guard-disabled", "bgn10fix2-coin-pass", CC,
     b"target instanceof MoneyGremlin", b"target instanceof net.minecraft.world.entity.monster.Zombie"),
    ("P02-mold-count-2", "bgn10fix2-mold-count", MG, b"return 1;", b"return 2;"),
    ("P03-power-plus", "bgn10fix2-imbalance", IM,
     b"1.0F - percent / RATE_SCALE", b"1.0F + percent / RATE_SCALE"),
    ("P04-roll-min-2", "bgn10fix2-imbalance", IM,
     b"nextInt(RATE_MAX_PERCENT) + RATE_MIN_PERCENT", b"nextInt(RATE_MAX_PERCENT) + 2"),
    ("P05-knife-range", "bgn10fix2-knife", AM,
     b"knifeAttributesFinal(2.5F, 2.0F)", b"knifeAttributesFinal(1.5F, 2.0F)"),
    ("P06-knife-offset-back", "bgn10fix2-knife", FD,
     b"family.tier.getAttackDamageBonus()", b"0.0F"),
    ("P07-comment-only", None, CC,
     b"public class ChaosCoinProjectile",
     b"// perturb-only-comment bg-n10fix2\npublic class ChaosCoinProjectile"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_validator() -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                          capture_output=True, env=env)
    return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")


def main() -> int:
    lines = []
    all_ok = True
    for name, tag, rel, old, new in CASES:
        path = REPO / rel
        before = path.read_bytes()
        base_sha = sha(before)
        if before.count(old) < 1:
            lines.append(name + " | ANCHOR-MISSING | " + rel)
            all_ok = False
            continue
        path.write_bytes(before.replace(old, new))
        try:
            code, out = run_validator()
        finally:
            path.write_bytes(before)
        restored = sha(path.read_bytes()) == base_sha
        hit = (code == 0) if tag is None else (code == 1 and tag in out)
        ok = restored and hit
        all_ok = all_ok and ok
        lines.append(" | ".join([
            name,
            rel,
            "exit=" + str(code),
            "hit=" + str(hit),
            "restored=" + str(restored),
            "sha=" + base_sha[:16],
            "" if tag is None else ("tag=" + tag),
        ]))
    lines.append("SUMMARY cases=" + str(len(CASES)) + " all_ok=" + str(all_ok))
    text = "\n".join(lines) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
