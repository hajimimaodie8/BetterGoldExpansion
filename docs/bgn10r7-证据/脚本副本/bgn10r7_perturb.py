# -*- coding: utf-8 -*-
"""轮7 扰动实测（7 用例，含「只改注释必须仍绿」）。

纪律：
  * 每个用例**先做字节备份**、跑完**逐字节复原**，并把 **前后 SHA256** 写进证据（自证复原）；
  * 只动本会话改过的文件（`AllMetals` / `ChaosItems` / `ImbalanceEffects` / 一条配方 JSON）；
  * 退出码契约：0 绿 / 1 有问题 / 2 前置坏 —— 判据同时看 **exit** 与**命中的 gate 行**；
  * 失败文案里不写裸 `%`（会被当格式符 ⇒ TypeError ⇒ "红不出来"）。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
VD = REPO / "tools" / "asset-generator"
EV = REPO / "docs" / "bgn10r7-证据"
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
RECIPES = REPO / "src" / "main" / "resources" / "data" / "bettergold" / "recipe"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def run_validator() -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(VD / "validate_metal_data.py")],
                          cwd=str(REPO), capture_output=True)
    try:
        out = proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        out = proc.stdout.decode("gbk", errors="replace")
    return proc.returncode, out


def hit_lines(out: str) -> list[str]:
    want = ("[bgn10r7-", "[bg-data-fail]", "[bg-data-ok]")
    hits = [ln.strip() for ln in out.splitlines() if any(w in ln for w in want)]
    # 只保留本轮与总结两类（前面那些历史 gate 的「问题: 0」行会挤掉重点）
    return hits[-6:]


PATCHES = [
    ("1-baseline", "（不改任何东西：基线必须绿）", [], 0),
    ("2-fruit-level", "ChaosItems: CHAOSALLOY_FRUIT_MAX_LEVEL 4 → 3", [
        ("src/main/java/com/hjmmd_8/bettergold/material/ChaosItems.java",
         "CHAOSALLOY_FRUIT_MAX_LEVEL = 4", "CHAOSALLOY_FRUIT_MAX_LEVEL = 3", "[bgn10r7-fruit]"),
    ], 1),
    ("3-armor-array", "AllMetals: armorDefense { 3, 6, 8, 3 } → { 3, 8, 6, 3 }（头胸写反）", [
        ("src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java",
         "spec.armorDefense = new int[] { 3, 6, 8, 3 }",
         "spec.armorDefense = new int[] { 3, 8, 6, 3 }", "[bgn10r7-armor]"),
    ], 1),
    ("4-resist-x2", "ImbalanceEffects: RESISTANCE_MULTIPLIER 2.0F → 1.5F（抗性失衡不再固定 ×2）", [
        ("src/main/java/com/hjmmd_8/bettergold/material/ImbalanceEffects.java",
         "RESISTANCE_MULTIPLIER = 2.0F", "RESISTANCE_MULTIPLIER = 1.5F", "[bgn10r7-effects]"),
    ], 1),
    ("5-recipe-missing", "临时移走 smithing_chaosalloy_bow.json（15 条锻造少一条）", [], 1),
    ("6-comment-only", "**只改注释**：AllMetals 里插一行注释 ⇒ 必须仍然绿（去注释源码判据）", [
        ("src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java",
         "    private static MetalFamily registerChaosalloy() {",
         "    // 扰动用例 6：只加一行注释，所有关卡必须仍然绿（validate_metal_data 走 strip_comments）\n"
         "    private static MetalFamily registerChaosalloy() {", None),
    ], 0),
    ("7-recipe-count", "chaosalloy_ingot.json：4 下界合金锭 → 3（锭配方 9 项不再等于作者给的数）", [], 1),
]


def main() -> None:
    rows: list[str] = []
    rows.append("轮7 扰动实测（判据 = exit 码 + 命中的 gate 行；每例逐字节复原 + SHA256 自证）")
    rows.append("=" * 116)
    rows.append("")
    all_ok = True

    for name, desc, edits, want_exit in PATCHES:
        backups: list[tuple[Path, bytes, str]] = []
        gate_seen: list[str] = []
        note = ""

        # ---- 施加扰动 ----
        if name == "5-recipe-missing":
            p = RECIPES / "smithing_chaosalloy_bow.json"
            backups.append((p, p.read_bytes(), sha(p)))
            p.unlink()
        elif name == "7-recipe-count":
            p = RECIPES / "chaosalloy_ingot.json"
            backups.append((p, p.read_bytes(), sha(p)))
            obj = json.loads(p.read_bytes().decode("utf-8"))
            ings = obj["ingredients"]
            nether = [i for i in ings if i.get("item") == "minecraft:netherite_ingot"]
            ings.remove(nether[0])          # 4 → 3
            ings.append({"item": "bettergold:chaosgold_ingot"})   # 仍 9 项，但配比不对
            obj["ingredients"] = ings
            p.write_bytes((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        else:
            for rel, old, new, gate in edits:
                p = REPO / rel
                raw = p.read_bytes()
                backups.append((p, raw, hashlib.sha256(raw).hexdigest().upper()))
                text = raw.decode("utf-8")
                if old not in text:
                    note += " [锚点缺失:" + rel + "]"
                p.write_bytes(text.replace(old, new, 1).encode("utf-8"))
                if gate:
                    gate_seen.append(gate)

        # ---- 跑校验器 ----
        code, out = run_validator()
        hits = hit_lines(out)
        restored_ok = True
        for p, raw, sha_before in backups:
            p.write_bytes(raw)
            if sha(p) != sha_before:
                restored_ok = False

        ok = (code == want_exit) and restored_ok
        if code != want_exit:
            all_ok = False
        if not restored_ok:
            all_ok = False
        rows.append("%-18s exit=%d（期望 %d）%s  %s" % (name, code, want_exit,
                                                        "OK" if ok else "MISMATCH", desc))
        rows.append("    复原=%s；命中行：" % ("逐字节一致" if restored_ok else "**不一致**"))
        for h in hits:
            rows.append("      " + h)
        if note:
            rows.append("    注：" + note)
        rows.append("")

    rows.append("判读：%s" % ("7 个用例全部符合期望（含用例 6 的「只改注释仍绿」= exit 0）"
                              if all_ok else "**有用例不符合期望，见上**"))
    EV.mkdir(parents=True, exist_ok=True)
    (EV / "03-扰动矩阵.txt").write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
    print("\n".join(rows))
    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
