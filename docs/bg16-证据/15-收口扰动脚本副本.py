# -*- coding: utf-8 -*-
"""bg-16 closing-round perturbation harness (A: data-map namespace; B: crossbow caliber).

Shape copied from build/bg16-perturb.py (same discipline, see mcmod_experience 3.4):
run the gate after each in-place perturbation, check the exit code AND an expected
stable ASCII assertion id, then restore every touched path -- including the paths
that must NOT exist (an old-namespace data map, a renamed file, a fake data map).

Line endings are handled explicitly (detect dominant ending, normalise to LF for
matching, convert back on write) because Path.read_text/write_text would silently
turn CRLF into LF and the byte-level restore would then fail.

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
DATA = RES / "data"
LOGFILE = REPO / "build" / "bg16close-gate.log"

COMPOST = DATA / "neoforge" / "data_maps" / "item" / "compostables.json"
COMPOST_OLD = DATA / "bettergold" / "data_maps" / "item" / "compostables.json"
COMPOST_RENAMED = COMPOST.with_name("compostables_x.json")
FAKE_MAP = DATA / "bettergold" / "data_maps" / "item" / "whatever.json"
WEAPONS = JAVA / "material" / "MetalWeapons.java"
SPECIAL = JAVA / "material" / "MetalSpecialItems.java"
SPEC15 = REPO / "docs" / "1.5-规格.md"
SPEC16 = REPO / "docs" / "1.6-规格.md"

TARGETS = (COMPOST, WEAPONS, SPECIAL, SPEC15, SPEC16)
GHOSTS = (COMPOST_OLD, COMPOST_RENAMED, FAKE_MAP)


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
    for p in GHOSTS:
        if p.exists():
            p.unlink()
    for d in (DATA / "bettergold" / "data_maps" / "item", DATA / "bettergold" / "data_maps"):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    for p, (text, ending, digest) in ORIGINAL.items():
        save(p, text, ending)
        assert sha(p) == digest, f"restore hash mismatch: {p}"
    for p in GHOSTS:
        assert not p.exists(), f"ghost path survived the restore: {p}"


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


# ---------------- perturbation bodies ----------------
def case_text(path, old, new, all_=False):
    return lambda: perturb(path, old, new, all_)


def case_move_back():
    def _apply():
        data = COMPOST.read_bytes()
        COMPOST_OLD.parent.mkdir(parents=True, exist_ok=True)
        COMPOST_OLD.write_bytes(data)
        COMPOST.unlink()
    return _apply


def case_rename():
    def _apply():
        COMPOST.rename(COMPOST_RENAMED)
    return _apply


def case_fake_namespace_map():
    def _apply():
        FAKE_MAP.parent.mkdir(parents=True, exist_ok=True)
        FAKE_MAP.write_bytes('{\n  "values": {}\n}\n'.encode("utf-8"))
    return _apply


def case_comments_only():
    def _apply():
        # (1) revert the documented path inside a javadoc block comment
        perturb(SPECIAL, "data/neoforge/data_maps/item/compostables.json",
                "data/bettergold/data_maps/item/compostables.json")
        # (2) line comment that mentions the forbidden override name
        perturb(WEAPONS, "        public int getUseDuration(ItemStack stack, LivingEntity entity) {",
                "        // note: releaseUsing(ItemStack, Level, LivingEntity, int) is NOT overridden here\n"
                "        public int getUseDuration(ItemStack stack, LivingEntity entity) {")
    return _apply


CASES = [
    ("A1 data map moved back to data/bettergold/...", case_move_back(),
     1, "[bg16-compost-old-path]"),
    ("A2 data map file renamed (the path IS the id)", case_rename(),
     1, "[bg16-compost-file]"),
    ("A3 chance 0.65 -> 0.5", case_text(COMPOST, '"chance": 0.65', '"chance": 0.5'),
     1, "[bg16-compost-chance]"),
    ("A4 a second data map under the bettergold: namespace", case_fake_namespace_map(),
     1, "[bg16-datamap-namespace]"),
    ("B1 MetalCrossbowItem overrides releaseUsing (a real caliber change)",
     case_text(WEAPONS,
               "        public int getUseDuration(ItemStack stack, LivingEntity entity) {",
               "        public void releaseUsing(ItemStack a, Level b, LivingEntity c, int d) { }\n\n"
               "        public int getUseDuration(ItemStack stack, LivingEntity entity) {"),
     1, "[bg16-crossbow-caliber]"),
    ("B2 the 'held-time cap' +3 changed to +4",
     case_text(WEAPONS, "return chargeDuration(stack, entity) + 3;",
               "return chargeDuration(stack, entity) + 4;"),
     1, "[bg16-crossbow-caliber]"),
    ("B3 seconds->ticks factor changed to 25",
     case_text(WEAPONS, "Mth.floor(f * 20.0F)", "Mth.floor(f * 25.0F)"),
     1, "[bg16-crossbow-caliber]"),
    ("B4 CROSSBOW_CHARGE_SECONDS 1.0F -> 1.25F",
     case_text(WEAPONS, "CROSSBOW_CHARGE_SECONDS = 1.0F", "CROSSBOW_CHARGE_SECONDS = 1.25F"),
     1, "[bg16-crossbow-caliber]"),
    ("B5 docs/1.5 loses the new caliber sentence",
     case_text(SPEC15, "沿用原版的 25 tick 分母", "(removed by perturbation)", True),
     1, "[bg16-crossbow-caliber-doc15]"),
    ("B6 docs/1.6 loses the new caliber sentence",
     case_text(SPEC16, "沿用原版的 25 tick 分母", "(removed by perturbation)", True),
     1, "[bg16-crossbow-caliber-doc16]"),
    ("INVERSE comments only (old path + releaseUsing in comments) must stay GREEN",
     case_comments_only(), 0, ""),
]

mismatches = 0

restore_all()
code, out = run_gate()
print(f"{'OK ' if code == 0 else 'BAD'} baseline validate_metal_data    exit={code}")
if code != 0:
    mismatches += 1
    print(out[-1500:])

for label, apply_, want_code, want_sub in CASES:
    restore_all()
    apply_()
    code, out = run_gate()
    got = code == want_code and (want_sub in out if want_sub else True)
    print(f"{'OK ' if got else 'MISS'} {label}    exit={code} expect={want_code} sub={want_sub!r}")
    if not got:
        mismatches += 1
        print(out[-1500:])

restore_all()
code, out = run_gate()
print(f"{'OK ' if code == 0 else 'BAD'} baseline after restore        exit={code}")
if code != 0:
    mismatches += 1
    print(out[-1500:])

for p, (_, _, digest) in ORIGINAL.items():
    assert sha(p) == digest, f"final hash mismatch: {p}"
print("final SHA256 of all touched sources restored byte-for-byte")
print(f"mismatches = {mismatches}")
sys.exit(1 if mismatches else 0)
