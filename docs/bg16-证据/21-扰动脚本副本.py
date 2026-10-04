# -*- coding: utf-8 -*-
"""bg-17 ruling-round perturbation harness (task 1: cactus coreItem; task 2: crossbow 20 ticks).

Shape copied from build/bg16close-perturb.py / docs/bg16-证据/15 (same discipline, mcmod_experience 3.4):
run the gate after each in-place perturbation, check the exit code AND the expected stable ASCII
assertion id, then restore every touched path byte-for-byte (byte-level read/write + SHA256 self-check,
because Path.read_text/write_text would silently turn CRLF into LF).

Gate output goes to a FILE (no piped stdio).
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold"
RES = REPO / "src" / "main" / "resources"
LOGFILE = REPO / "build" / "bg17-gate.log"

FAMILY = JAVA / "material" / "MetalFamily.java"
EVENTS = JAVA / "material" / "MetalEvents.java"
ALLMETALS = JAVA / "material" / "AllMetals.java"
WEAPONS = JAVA / "material" / "MetalWeapons.java"
MIXIN = JAVA / "mixin" / "CrossbowChargeDurationMixin.java"
MIXINS_JSON = RES / "bettergold.mixins.json"
SPEC15 = REPO / "docs" / "1.5-规格.md"
SPEC16 = REPO / "docs" / "1.6-规格.md"

TARGETS = (FAMILY, EVENTS, ALLMETALS, WEAPONS, MIXIN, MIXINS_JSON, SPEC15, SPEC16)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    raw = path.read_bytes().decode("utf-8")
    ending = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), ending


def save(path: Path, text_lf: str, ending: str) -> None:
    path.write_bytes(text_lf.replace("\n", ending).encode("utf-8"))


ORIGINAL = {p: (*load(p), sha(p)) for p in TARGETS}


def restore_all() -> None:
    for p, (text, ending, digest) in ORIGINAL.items():
        save(p, text, ending)
        assert sha(p) == digest, f"restore hash mismatch: {p}"


def run_gate():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    with open(LOGFILE, "wb") as fh:
        cp = subprocess.run([sys.executable, str(GATE)], stdout=fh,
                            stderr=subprocess.STDOUT, env=env)
    out = LOGFILE.read_bytes().decode("utf-8", "replace")
    return cp.returncode, out


def perturb(path: Path, old: str, new: str, all_: bool = False) -> None:
    text, ending = load(path)
    assert old in text, f"perturbation text not found in {path.name}: {old[:70]!r}"
    save(path, text.replace(old, new) if all_ else text.replace(old, new, 1), ending)


def case_text(path, old, new, all_=False):
    return lambda: perturb(path, old, new, all_)


CORE_BRANCH = "        return coreItemOwner(item) != null;"
GUARD = "        if (stack == null || !(stack.getItem() instanceof MetalWeapons.MetalCrossbowItem)) {"
RETURN_20 = "        return MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter);"
DESCRIPTOR = ('"getChargeDuration(Lnet/minecraft/world/item/ItemStack;'
              'Lnet/minecraft/world/entity/LivingEntity;)I"')


def case_guard_after_conversion():
    def _apply():
        body = (GUARD + "\n"
                "            return original;\n"
                "        }\n"
                + RETURN_20)
        replacement = ("        int probe = MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter);\n"
                       + GUARD + "\n"
                       "            return original;\n"
                       "        }\n"
                       + RETURN_20)
        perturb(MIXIN, body, replacement)
    return _apply


def case_comment_feeds_positive_assertion():
    """comments must NOT feed the positive assertion: the real call is replaced by the old pattern
    while a comment still mentions MetalFamily.isCactusImmune( -> the gate must stay RED."""
    def _apply():
        perturb(EVENTS,
                "        if (MetalFamily.isCactusImmune(itemEntity.getItem().getItem())) {",
                "        // note: MetalFamily.isCactusImmune(itemEntity.getItem().getItem()) is the new predicate\n"
                "        MetalFamily family = MetalFamily.of(itemEntity.getItem());\n"
                "        if (family != null && family.cactusImmune) {")
    return _apply


def case_comments_only():
    def _apply():
        # (1) a comment that mentions the forbidden override name inside MetalCrossbowItem
        perturb(WEAPONS, "        public int getUseDuration(ItemStack stack, LivingEntity entity) {",
                "        // note: releaseUsing(ItemStack, Level, LivingEntity, int) is NOT overridden here\n"
                "        public int getUseDuration(ItemStack stack, LivingEntity entity) {")
        # (2) a comment mentioning the converted value ABOVE the instanceof guard
        perturb(MIXIN, GUARD,
                "        // note: MetalWeapons.MetalCrossbowItem.chargeDuration(stack, shooter) is what we return\n"
                + GUARD)
        # (3) a comment inside the item-immunity handler that mentions an old-style judgement
        perturb(EVENTS, "        if (!isCactus(event.getSource())) {",
                "        // note: family.cactusImmune is still read by the armour-durability half\n"
                "        if (!isCactus(event.getSource())) {")
    return _apply


CASES = [
    ("C1 coreItem branch removed from isCactusImmune (the required 'remove the coreItem predicate' case)",
     case_text(FAMILY, CORE_BRANCH, "        return false;"),
     1, "[bg16-cactus-coreitem-predicate]"),
    ("C2 coreItem branch inverted (blanket rule broken)",
     case_text(FAMILY, CORE_BRANCH, "        return coreItemOwner(item) == null;"),
     1, "[bg16-cactus-coreitem-blanket]"),
    ("C3 onCactusItemImmunity reverted to the old family-only pattern",
     case_text(EVENTS, "        if (MetalFamily.isCactusImmune(itemEntity.getItem().getItem())) {",
               "        MetalFamily family = MetalFamily.of(itemEntity.getItem());\n"
               "        if (family != null && family.cactusImmune) {"),
     1, "[bg16-cactus-coreitem-event]"),
    ("C4 one family loses its coreItem declaration (7 of 8)",
     case_text(ALLMETALS, ".coreItem(() -> MetalSpecialItems.BLAZING_ROD.get())",
               ".specFieldRemovedByPerturbation()"),
     1, "[bg16-cactus-coreitem-anti-vacuum]"),
    ("C5 a COMMENT mentions the new predicate while the real call is gone -> must still be RED",
     case_comment_feeds_positive_assertion(), 1, "[bg16-cactus-coreitem-event]"),
    ("X1 instanceof guard removed (would touch vanilla / third-party crossbows)",
     case_text(MIXIN, GUARD, "        if (stack == null) {"),
     1, "[bg16-crossbow-mixin-guard]"),
    ("X2 guard moved AFTER the conversion (order broken)",
     case_guard_after_conversion(), 1, "[bg16-crossbow-mixin-guard-first]"),
    ("X3 require = 1 -> require = 0 (silent-failure protection removed)",
     case_text(MIXIN, "require = 1,", "require = 0,"),
     1, "[bg16-crossbow-mixin-require]"),
    ("X4 target descriptor loses the return type",
     case_text(MIXIN, DESCRIPTOR, '"getChargeDuration"'),
     1, "[bg16-crossbow-mixin-descriptor]"),
    ("X5 mixin dropped from the mixins.json 'mixins' list (silently not loaded)",
     case_text(MIXINS_JSON, '  "mixins": [\n    "CrossbowChargeDurationMixin"\n  ],', '  "mixins": [],'),
     1, "[bg16-crossbow-mixin-listed]"),
    ("X5b the real trap: the entry moved to a bogus 'common' key (Mixin silently ignores it)",
     case_text(MIXINS_JSON, '  "mixins": [\n    "CrossbowChargeDurationMixin"\n  ],',
               '  "common": [\n    "CrossbowChargeDurationMixin"\n  ],'),
     1, "[bg16-crossbow-mixin-listed]"),
    ("X6 mixin also registered on the client list (wrong side)",
     case_text(MIXINS_JSON, '  "client": [\n    "ItemRendererTridentMixin"\n  ],',
               '  "client": [\n    "ItemRendererTridentMixin",\n    "CrossbowChargeDurationMixin"\n  ],'),
     1, "[bg16-crossbow-mixin-side]"),
    ("X7 docs/1.6 loses the new caliber sentence",
     case_text(SPEC16, "已被本裁定取代", "(removed by perturbation)", True),
     1, "[bg16-crossbow-caliber-doc16-new]"),
    ("X8 docs/1.5 loses the new caliber sentence",
     case_text(SPEC15, "已被本裁定取代", "(removed by perturbation)", True),
     1, "[bg16-crossbow-caliber-doc15-new]"),
    ("X9 seconds->ticks factor changed to 25",
     case_text(WEAPONS, "Mth.floor(f * 20.0F)", "Mth.floor(f * 25.0F)"),
     1, "[bg16-crossbow-caliber]"),
    ("X10 MetalCrossbowItem really overrides releaseUsing (the other landing spot)",
     case_text(WEAPONS, "        public int getUseDuration(ItemStack stack, LivingEntity entity) {",
               "        public void releaseUsing(ItemStack a, Level b, LivingEntity c, int d) { }\n\n"
               "        public int getUseDuration(ItemStack stack, LivingEntity entity) {"),
     1, "[bg16-crossbow-caliber]"),
    ("INVERSE comments only (releaseUsing / chargeDuration / cactusImmune mentioned in comments) must stay GREEN",
     case_comments_only(), 0, ""),
]

mismatches = 0

restore_all()
code, out = run_gate()
print(f"{'OK ' if code == 0 else 'BAD'} baseline validate_metal_data    exit={code}")
if code != 0:
    mismatches += 1
    print(out[-2500:])

for label, apply_, want_code, want_sub in CASES:
    restore_all()
    apply_()
    code, out = run_gate()
    got = code == want_code and (want_sub in out if want_sub else True)
    print(f"{'OK ' if got else 'MISS'} {label}    exit={code} expect={want_code} sub={want_sub!r}")
    if not got:
        mismatches += 1
        print(out[-2500:])

restore_all()
code, out = run_gate()
print(f"{'OK ' if code == 0 else 'BAD'} baseline after restore        exit={code}")
if code != 0:
    mismatches += 1
    print(out[-2500:])

for p, (_, _, digest) in ORIGINAL.items():
    assert sha(p) == digest, f"final hash mismatch: {p}"
print("final SHA256 of all touched sources restored byte-for-byte")
print(f"mismatches = {mismatches}")
sys.exit(1 if mismatches else 0)
