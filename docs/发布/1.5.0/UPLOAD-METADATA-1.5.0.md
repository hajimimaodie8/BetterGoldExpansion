# 1.5.0 Upload Metadata (for the CurseForge / Modrinth forms)

## Version

| Field | Value |
|---|---|
| Version | `1.5.0` |
| Mod id | `bettergold` |
| License | MIT |
| Author | hjmmd_8 |
| Channels | CurseForge / Modrinth (one jar for both) |

## Version name (suggested)

`1.5.0 - Indigoseagold & Illusiongold, plus a Weapon Line for Every Metal`

## One-line summary (first line of the changelog form)

`Two new metals, Indigoseagold and Illusiongold, with two new status effects - and a full weapon line for all six metals: mace, shield, bow, crossbow and trident.`

## Supported Minecraft version

- **1.21.1** only (`minecraft_version_range=[1.21.1]`)

## Loader

| Field | Value |
|---|---|
| Loader | NeoForge (`modLoader="javafml"`) |
| Required NeoForge | **21.1.228 or newer** (`[21.1.228,)`) |
| Java | 21 |
| Client / server | Both required (no side restriction) |

## Dependencies

| Dependency | How it is declared | Effect | When absent |
|---|---|---|---|
| **Farmer's Delight** (>= 1.3.1) | `type="optional"`, `versionRange="[1.3.1,)"`, `ordering="AFTER"` in `neoforge.mods.toml` | Adds the two new metal knives (Indigoseagold, Illusiongold) and their smithing upgrade recipes | Mod loads normally; the two knives are simply not registered |
| **MoreUpgradeTemplate** (mod id `mut`) | **Not** a declared dependency - only datapack conditions (`neoforge:mod_loaded: mut` / `neoforge:not`) on the recipes | Hides the five golden blanks and the 30 blank-based upgrade recipes; `mut`'s own golden mace / trident / bow / crossbow / shield become the upgrade bases instead | Mod loads normally; the five blanks are craftable and are the upgrade bases (nothing is hidden) |

Immersive Engineering: no new content in 1.5.0 (its 1.4-era Metal Press recipe is unchanged and is not part of this release note).

## Upload file

| Field | Value |
|---|---|
| File name | `bettergold-1.5.0.jar` |
| Path | `build/libs/bettergold-1.5.0.jar` |
| Size | **1,089,068 bytes** (last build, 2026-10-03; re-check after the final build) |
| Debug code | No probe / diagnostic classes and no `halt` calls (verified by `tools/asset-generator/check_jar_clean.py`, exit 0) |

## Beta / Release

**Recommended: Release.**
Build and data checks are green (`compileJava`, `runData`, `processResources jar`; five validators exit 0; runtime probes 237 PASS / 0 FAIL for the last round), and no debug code is in the jar.

## Known notes (author only - do not paste into the public changelog)

1. The five golden blanks are hidden **only when `mut` is installed**; if `mut` is absent, the blanks are visible and craftable.
2. Item / block ids, language keys and datapack paths are unchanged from 1.4.0; existing worlds can be loaded.
3. Two recipe ids changed during development (`smithing_<metal>_<weapon>` is now the blank-based recipe, and the MUT variant is `smithing_mut_<metal>_<weapon>`); already-unlocked old ids may show as unlocked again.
4. Indigoseagold's total end-to-end water displacement is the product of two retained effects, not a plain +25% per piece (see `docs/1.5-规格.md` section 17.8).
