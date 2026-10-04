# -*- coding: utf-8 -*-
"""bg-16 perturbation harness (ASCII-only source).

Runs tools/asset-generator/validate_metal_data.py after each in-place source/data
perturbation, checks exit code + an expected assertion id, then restores every
touched file byte-for-byte (SHA256 verified).

Line endings are handled explicitly (detect dominant ending, normalise to LF for
matching, convert back on write) - Path.read_text/write_text would silently turn
CRLF into LF and the byte-level restore would then fail.
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

BANNERS = JAVA / "client" / "CreativeSectionBanners.java"
EVENTS = JAVA / "material" / "MetalEvents.java"
SOOTHE = JAVA / "material" / "SootheState.java"
ALLMETALS = JAVA / "material" / "AllMetals.java"
CREATIVE = JAVA / "material" / "CreativeSections.java"
FAMILY = JAVA / "material" / "MetalFamily.java"
GIFT = JAVA / "item" / "GiftBoxItem.java"
GLM_JAVA = JAVA / "registry" / "AllLootModifiers.java"
GLOBAL_GLM = RES / "data" / "neoforge" / "loot_modifiers" / "global_loot_modifiers.json"
COMPOST = RES / "data" / "bettergold" / "data_maps" / "item" / "compostables.json"
BUNDLED = RES / "data" / "bettergold" / "recipe" / "bundled_echo_shard.json"
MIXINS = RES / "bettergold.mixins.json"
ROSE_LOOT = RES / "data" / "bettergold" / "loot_table" / "blocks" / "golden_rose_bush.json"

TARGETS = (BANNERS, EVENTS, SOOTHE, ALLMETALS, CREATIVE, FAMILY, GIFT, GLM_JAVA,
           GLOBAL_GLM, COMPOST, BUNDLED, MIXINS, ROSE_LOOT)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> tuple[str, str]:
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


def run_gate() -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    cp = subprocess.run([sys.executable, str(GATE)], capture_output=True, env=env)
    out = cp.stdout.decode("utf-8", "replace") + cp.stderr.decode("utf-8", "replace")
    return cp.returncode, out


def perturb(path: Path, old: str, new: str, all_: bool = False) -> None:
    text, ending = load(path)
    assert old in text, f"perturbation text not found in {path.name}: {old[:70]!r}"
    save(path, text.replace(old, new) if all_ else text.replace(old, new, 1), ending)


CASES = [
    # ---------------- §5.2 banner ----------------
    ("A  banner: Foreground -> Background event",
     BANNERS, "ContainerScreenEvent.Render.Foreground event", "ContainerScreenEvent.Render.Background event",
     1, "ContainerScreenEvent.Render.Foreground", False),
    ("B  banner: container-relative x no longer exact",
     BANNERS, "int left = ITEM_AREA_X;", "int left = ITEM_AREA_X + 1;",
     1, "[bg16-banner-relative-coords]", False),
    ("C  banner: absolute coords (guiLeft) reintroduced",
     BANNERS, "int top = ITEM_AREA_Y;",
     "int top = ITEM_AREA_Y;\n        int _legacyLeft = screen.getGuiLeft();",
     1, "[bg16-banner-no-absolute-coords]", False),
    ("D  banner: the OLD hook used as real code",
     BANNERS, "int left = ITEM_AREA_X;",
     "Class<?> _legacy = ScreenEvent.Render.Post.class;\n        int left = ITEM_AREA_X;",
     1, "[bg16-banner-old-event]", False),
    # ---------------- §5.1 soothe ----------------
    ("E  soothe: JUMP_STRENGTH line removed",
     EVENTS, "        sootheFreeze(player, net.minecraft.world.entity.ai.attributes.Attributes.JUMP_STRENGTH,\n                SOOTHE_FREEZE_JUMP_ID, soothing);\n", "",
     1, "JUMP_STRENGTH", False),
    ("F  soothe: ADD_MULTIPLIED_TOTAL -> ADD_VALUE",
     EVENTS, "AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));", "AttributeModifier.Operation.ADD_VALUE));",
     1, "ADD_MULTIPLIED_TOTAL", False),
    ("G  soothe: a right-key handler loses setCanceled",
     EVENTS, "    public static void onSootheRightClickItem(\n            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickItem event) {\n        if (isSoothed(event.getEntity())) {\n            event.setCanceled(true);\n            event.setCancellationResult(net.minecraft.world.InteractionResult.FAIL);\n        }\n    }",
     "    public static void onSootheRightClickItem(\n            net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickItem event) {\n        if (isSoothed(event.getEntity())) {\n            return;\n        }\n    }",
     1, "onSootheRightClickItem", False),
    ("H  soothe: persistent data written in the player branch",
     EVENTS, "        boolean soothing = player.hasEffect(AllEffects.SOOTHE);",
     "        player.getPersistentData();\n        boolean soothing = player.hasEffect(AllEffects.SOOTHE);",
     1, "[bg16-soothe-player-no-persistent-data]", False),
    ("I  soothe: modifier id literal renamed",
     EVENTS, '"soothe_freeze_speed"', '"soothe_freeze_speed_x"',
     1, "soothe_freeze_speed", False),
    ("J  SootheState: both non-Mob guards broken",
     SOOTHE, "!(entity instanceof Mob mob)", "entity instanceof Mob",
     1, "[bg16-soothe-state-untouched]", True),
    # ---------------- batch 1: two metals ----------------
    ("K  spec: numeric field override sneaks back in",
     ALLMETALS, 'new MetalFamily.Spec("thornsgold", "树棘金")\n                    .contactCactusThorns()',
     'new MetalFamily.Spec("thornsgold", "树棘金")\n                    .contactCactusThorns()\n                    .durability(4096)',
     1, "[bg16-spec-no-numeric-override]", False),
    ("L  spec: a trait call removed",
     ALLMETALS, ".cactusImmune()\n", "",
     1, "[bg16-spec-traits]", False),
    ("M  METAL_ORDER: echogold dropped",
     CREATIVE, '            "echogold",       // 幽咆金（1.6 新增）\n', "",
     1, "[bg16-metal-order", False),
    ("N  METAL_ORDER: thornsgold moved after indigoseagold",
     CREATIVE, '            "thornsgold",     // 树棘金（1.6 新增，作者裁定：在万坚金与靛海金之间、树棘金在前）\n            "echogold",       // 幽咆金（1.6 新增）\n            "indigoseagold",  // 靛海金（1.5，作者指定：在万坚金与巫毒金之间）',
     '            "indigoseagold",  // 靛海金（1.5，作者指定：在万坚金与巫毒金之间）\n            "thornsgold",     // 树棘金\n            "echogold",       // 幽咆金',
     1, "[bg16-metal-order-position]", False),
    ("O  GLM: not registered in global_loot_modifiers (silent no-op)",
     GLOBAL_GLM, ',\n    "bettergold:leaves_glittering_vine"', "",
     1, "[bg16-glm-registered]", False),
    ("P  GLM: base chance 6% -> 7%",
     GLM_JAVA, "BASE_CHANCE = 0.06F", "BASE_CHANCE = 0.07F",
     1, "[bg16-glm-chance]", False),
    ("Q  GLM: fortune lookup removed",
     GLM_JAVA, "Enchantments.FORTUNE", "Enchantments.SHARPNESS",
     1, "[bg16-glm-fortune-lookup]", False),
    ("R  compostable: 0.65 -> 0.5",
     COMPOST, '"chance": 0.65', '"chance": 0.5',
     1, "[bg16-compost-chance]", False),
    ("S  bundled echo shard: pattern broken",
     BUNDLED, '"EEE",\n    "EVE",', '"EEE",\n    "EEE",',
     1, "[bg16-recipe-pattern]", False),
    ("T  cactus immunity: ArmorHurt handler renamed away",
     EVENTS, "onArmorHurtCactusImmunity", "onArmorHurtSomethingElse",
     1, "[bg16-cactus-armor]", False),
    ("U  mixin file gains a cactus mixin",
     MIXINS, '"client": [', '"cactus": [],\n  "client": [',
     1, "[bg16-no-mixin]", False),
    ("V  Spec default flips to true (would hit every family)",
     FAMILY, "public boolean cactusImmune = false;", "public boolean cactusImmune = true;",
     1, "[bg16-spec-default]", False),
    ("W  Spec -> family copy removed",
     FAMILY, "this.cactusImmune = spec.cactusImmune;\n", "",
     1, "[bg16-family-copy]", False),
    # ---------------- batch 2: spare parts ----------------
    ("X  rose bush loot table loses the half=lower condition",
     ROSE_LOOT, '"properties": { "half": "lower" }', '"properties": {}',
     1, "[bg16-rose-loot-condition]", False),
    ("Y  treasure tables: buried_treasure renamed away",
     GIFT, 'chest("buried_treasure")', 'chest("buried_treasure_x")',
     1, "[bg16-treasure-buried]", False),
    ("Z  alchemy box pool hardcoded instead of family-driven",
     GIFT, "for (var family : com.hjmmd_8.bettergold.material.MetalFamily.all()) {",
     "for (var family : java.util.List.of(com.hjmmd_8.bettergold.material.MetalFamily.byId(\"sturdygold\"))) {",
     1, "[bg16-box-pool]", False),
    # ---------------- reverse control: comment only, must stay GREEN ----------------
    ("AA INVERSE: a comment mentioning forbidden names must stay green",
     EVENTS, "    // ==================== 1.6（bg-16）：两套新金属的 trait ====================",
     "    // ==================== 1.6（bg-16）：两套新金属的 trait ====================\n    // note: cactusImmune / ArmorHurtEvent / EntityInvulnerabilityCheckEvent live below",
     0, "", False),
]

mismatches = 0
code, out = run_gate()
ok = code == 0
print(f"{'OK ' if ok else 'BAD'} baseline validate_metal_data    exit={code}")
if not ok:
    mismatches += 1
    print(out[-1500:])

for label, path, old, new, want_code, want_sub, all_ in CASES:
    restore_all()
    perturb(path, old, new, all_)
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
