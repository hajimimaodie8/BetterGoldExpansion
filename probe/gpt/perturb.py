# -*- coding: utf-8 -*-
"""gpt 轮扰动矩阵：九条各 1 用例 + 1 个「只改注释仍绿」的反向对照。

每个用例：
  ① 记录目标文件改前 SHA256；
  ② 按**字节**替换（Python read_bytes/write_bytes，绝不走 PowerShell 文本转码）；
  ③ 跑 `validate_metal_data.py`（本轮的关卡），记录 exit 与是否命中**期望的稳定 ASCII tag**；
  ④ 逐字节复原并复核 SHA256 == 改前（不一致 = 用例坏了，exit 2）。
判据：
  · 命中 = exit 1 且输出里出现期望 tag；
  · 未命中 = 其它组合（含 exit 0 = 关卡漏了；exit 2 = 脚本自身坏了，不算命中）；
  · 只改注释那一例：必须 exit 0（证明"注释里写一句"喂不饱断言）。

跑法（工作区自带 Python；禁用 py -3）：
    <dsh python> probe\\gpt\\perturb.py
输出：docs\\gpt-证据\\04-扰动矩阵.txt
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = sys.executable
GATE = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
EVID = os.path.join(ROOT, "docs", "gpt-证据")
J = "src/main/java/com/hjmmd_8/bettergold/"
R = "src/main/resources/data/bettergold/recipe/"

CASES = [
    ("①金火把花-去掉金染土那一支", J + "block/GoldenTorchflowerBlock.java",
     "state.is(AllBlocks.GOLD_INFUSED_DIRT.get())", "false",
     "gpt1-torchflower-dirt"),
    ("②混沌金-韧性改回旧值 3.0", J + "material/AllMetals.java",
     "spec.armorToughness = 2.0F", "spec.armorToughness = 3.0F",
     "gpt2-chaosgold-values"),
    ("③金钱茄模具配方-类型改成金锭版", R + "golden_cowrie_from_mold_money_eggplant.json",
     '"bettergold:golden_cowrie_mold_money_eggplant"', '"bettergold:golden_cowrie_mold"',
     "gpt3-cowrie-mold-eggplant"),
    ("④新手交易-24 改成 23", J + "event/VillageTrades.java",
     "AllItems.GOLDEN_EGG.get(), 24", "AllItems.GOLDEN_EGG.get(), 23",
     "gpt4-gold-trader-egg"),
    ("⑤金火把花种子-100% 改成 50%", J + "event/ModEvents.java",
     "GOLDEN_TORCHFLOWER_SEED_EGG_CHANCE = 1.0F", "GOLDEN_TORCHFLOWER_SEED_EGG_CHANCE = 0.5F",
     "gpt5-chicken-golden-egg"),
    ("⑥巫毒结算-退回无 owner 的 magic()", J + "material/MetalEvents.java",
     "entity.hurt(voodooSettleSource(entity), (float) damage)",
     "entity.hurt(entity.damageSources().magic(), (float) damage)",
     "gpt6-voodoo-magic"),
    ("⑦金玫瑰产量-3 改成 2", J + "registry/AllItems.java",
     "GOLDEN_ROSE_PRODUCE = 3", "GOLDEN_ROSE_PRODUCE = 2",
     "gpt7-golden-rose-bonemeal"),
    ("⑧mixin 登记-从 mixins 列表摘掉", "src/main/resources/bettergold.mixins.json",
     ',\n    "AbstractArrowWaterInertiaMixin"', "",
     "gpt8-indigosea-water-inertia"),
    ("⑨盾牌配方-中心苹果换成锭", R + "chaosgold_shield.json",
     '"XAX"', '"XXX"',
     "gpt9-shape"),
    ("反向对照-只改注释（必须仍绿）", J + "block/GoldenTorchflowerBlock.java",
     "public class GoldenTorchflowerBlock extends FlowerBlock {",
     "// gpt 扰动：只加这一行注释（不改任何代码）\npublic class GoldenTorchflowerBlock extends FlowerBlock {",
     None),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def gate():
    out = os.path.join(ROOT, "build", "gpt_perturb_gate.log")
    with open(out, "wb") as f:
        p = subprocess.run([PY, GATE], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        f.flush()
    text = open(out, "rb").read().decode("utf-8", "replace")
    return p.returncode, text


def main():
    os.makedirs(EVID, exist_ok=True)
    lines = ["gpt 轮扰动矩阵（2026-10-24；关卡 = tools/asset-generator/validate_metal_data.py）",
             "判据：exit=1 且命中期望 tag = 命中；exit=0 = 关卡漏了；exit=2 = 用例坏了（不算命中）",
             ""]
    rows = []
    for name, rel, old, new, tag in CASES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        raw = open(path, "rb").read()
        before = hashlib.sha256(raw).hexdigest().upper()
        text = raw.decode("utf-8")
        n = text.count(old)
        if n != 1:
            rows.append((name, rel, "CASE-BROKEN", "命中 %d 次（期望 1）" % n, "?", "?"))
            lines.append("[CASE-BROKEN] %s :: %s 命中 %d 次（期望 1）" % (name, rel, n))
            continue
        open(path, "wb").write(text.replace(old, new).encode("utf-8"))
        rc, out = gate()
        hit = tag is not None and tag in out
        if tag is None:
            ok = rc == 0
            verdict = "命中（仍绿）" if ok else "未命中"
        else:
            ok = rc == 1 and hit
            verdict = "命中" if ok else ("未命中(exit=%d,tag=%s)" % (rc, hit))
        # 逐字节复原
        open(path, "wb").write(raw)
        after = sha(path)
        restored = after == before
        rows.append((name, rel, verdict, tag or "（无，期望 exit 0）", "exit=%d" % rc,
                     "%s %s" % (after[:16], "OK" if restored else "MISMATCH")))
        lines.append("[%s] %s" % ("HIT" if ok else "MISS", name))
        lines.append("   文件=%s" % rel)
        lines.append("   变更=%r -> %r" % (old[:60], new[:60]))
        lines.append("   关卡 exit=%d；期望 tag=%s；tag 命中=%s" % (rc, tag, hit))
        lines.append("   复原 SHA256=%s（改前 %s）/ %s" % (after, before, "一致" if restored else "不一致!!"))
        if not restored:
            lines.append("   !! 复原失败 = 用例坏了（exit 2）")
            write(lines)
            return 2
    hits = sum(1 for r in rows if r[2].startswith("命中"))
    lines.append("")
    lines.append("矩阵：%d 用例 / %d 命中 / 复原 %d/%d 逐字节一致" % (
        len(rows), hits, sum(1 for r in rows if r[5].endswith("OK")), len(rows)))
    write(lines)
    print("矩阵：%d 用例 / %d 命中 / 复原全部一致? %s" % (
        len(rows), hits, all(r[5].endswith("OK") for r in rows)))
    return 0 if hits == len(rows) else 1


def write(lines):
    io.open(os.path.join(EVID, "04-扰动矩阵.txt"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")


sys.exit(main())
