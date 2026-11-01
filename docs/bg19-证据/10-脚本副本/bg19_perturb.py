import hashlib
import os
import shutil
import subprocess
import sys

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
VMD = os.path.join("tools", "asset-generator", "validate_metal_data.py")
VADV = os.path.join("tools", "asset-generator", "validate_advancements.py")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run(script):
    r = subprocess.run([PY, script], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


CASES = [
    ("P1 R1 摘错 cure（MILK → HONEY）", "src/main/java/com/hjmmd_8/bettergold/registry/BetterGoldMobEffect.java",
     b"cures.remove(EffectCures.MILK);", b"cures.remove(EffectCures.HONEY);",
     VMD, "[bg19-milk-immunity]"),
    ("P2 R2 认错伤害类型（SWEET_BERRY_BUSH → CACTUS）",
     "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java",
     b"source.is(net.minecraft.world.damagesource.DamageTypes.SWEET_BERRY_BUSH)",
     b"source.is(net.minecraft.world.damagesource.DamageTypes.CACTUS)",
     VMD, "[bg19-berry]"),
    ("P3 R5 耐久改回靴 246", "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java",
     b"spec.armorDurability = new int[] { 220, 246, 264, 200 };",
     b"spec.armorDurability = new int[] { 246, 246, 264, 200 };",
     VMD, "[bg19-chaosgold-durability]"),
    ("P4 R6 去掉 25% 系数", "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java",
     b"double keep = 1.0D - Math.min(pieces, 4) * 0.25D;",
     b"double keep = 1.0D;",
     VMD, "[bg19-sonic-knockback]"),
    ("P5 R7-a 判据塞进 doubled 变体",
     "src/main/resources/data/bettergold/advancement/metal/chaosgold/craft.json",
     b'"bettergold:raw_flamegold_chaosgold"', b'"bettergold:raw_flamegold_doubled"',
     VADV, "raw_flamegold_doubled"),
    ("P6 只改注释（在 R6 那段加一行注释）",
     "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java",
     b"// ==================== 1.7 bg19 R6",
     b"// PERTURB-ONLY-COMMENT\n    // ==================== 1.7 bg19 R6",
     VMD, None),
]

print("baseline metal_data:", run(VMD)[0], " advancements:", run(VADV)[0])
hits = 0
for name, rel, old, new, script, needle in CASES:
    p = os.path.join(ROOT, rel)
    before = sha(p)
    bak = p + ".bg19perturb.bak"
    shutil.copyfile(p, bak)
    raw = open(p, "rb").read()
    assert raw.count(old) == 1, (name, raw.count(old))
    open(p, "wb").write(raw.replace(old, new))
    code, out = run(script)
    got = (needle in out) if needle else (code == 0)
    hits += 1 if got else 0
    print("%-44s exit=%d hit=%s (%s)" % (name, code, got, needle or "still green"))
    shutil.copyfile(bak, p)
    os.remove(bak)
    after = sha(p)
    print("    restored=%s sha=%s" % (before == after, after[:16]))
    assert before == after, "复原失败: " + rel
print("cases=%d hits=%d" % (len(CASES), hits))
