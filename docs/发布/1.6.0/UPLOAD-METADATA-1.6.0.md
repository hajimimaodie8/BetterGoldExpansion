# 1.6.0 Upload Metadata (for the CurseForge / Modrinth forms)

## Version

| Field | Value |
|---|---|
| Version | `1.6.0` |
| Mod id | `bettergold` |
| License | MIT |
| Author | hjmmd_8 |
| Channels | CurseForge / Modrinth (one jar for both) |

## Version name (suggested)

`1.6.0 - Thornsgold & Echogold, an In-Game Handbook, and 51 Advancements`

## One-line summary (first line of the changelog form)

`Two new metals, Thornsgold and Echogold, with two new status effects - plus the mod's first in-game handbook and 51 advancements.`

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
| **Patchouli** (>= 1.21.1-93) | `type="optional"`, `versionRange="[1.21.1-93,)"`, `ordering="AFTER"` in `neoforge.mods.toml` | Adds the **Alchemy Student's Handbook** (4 categories / 17 entries / 148 pages) and its crafting recipe | Mod loads normally; the book item **and** its recipe simply do not exist. Every reference to a Patchouli type sits behind an `isLoaded` guard in a method body, so nothing is touched at class-load time |
| **Farmer's Delight** (>= 1.3.1) | `type="optional"`, `versionRange="[1.3.1,)"`, `ordering="AFTER"` | Adds the Thornsgold and Echogold knives and their smithing recipes, plus the three Farmer's Delight advancements | Mod loads normally; the two knives and the three advancements are not registered (48 advancements instead of 51) |
| **MoreUpgradeTemplate** (mod id `mut`) | **Not** a declared dependency - only datapack conditions (`neoforge:mod_loaded: mut` / `neoforge:not`) on the recipes | Hides the five golden blanks and the blank-based upgrade recipes; `mut`'s own golden mace / trident / bow / crossbow / shield become the upgrade bases | Mod loads normally; the five blanks are craftable and are the upgrade bases (nothing is hidden) |

Immersive Engineering: no new content in 1.6.0 (its 1.4-era Metal Press recipe is unchanged and is not part of this release note).

## Upload file

| Field | Value |
|---|---|
| File name | `bettergold-1.6.0.jar` |
| Path | `build/libs/bettergold-1.6.0.jar` |
| Size | **1,339,929 bytes** (built 2026-10-06 14:50:15 from HEAD `4856bb6`, clean working tree) |
| SHA256 | `5BC5057F095AF99312DCEE8A6911F9B3C0C910722C17A0588BD4ED3E50272EF1` |
| Entries | 2,388 files (2,289 files + 99 directories when unzipped) |
| Debug code | No probe / diagnostic classes, no `halt` calls and no `BG-PROBE` marker (verified by `tools/asset-generator/check_jar_clean.py`, exit 0) |

## Beta / Release

**Recommended: Release.**
Build and data checks are green (`compileJava`, `runData`, `processResources jar --rerun-tasks`: `BUILD SUCCESSFUL`; six validators all exit 0; no debug code in the jar).

## Known notes (author only - do not paste into the public changelog)

1. The five golden blanks are hidden **only when `mut` is installed**; if `mut` is absent, the blanks are visible and craftable.
2. Item / block ids, language key **names**, config key **names** and datapack paths are unchanged from 1.5.0; existing worlds can be loaded. `mod_version` moved from 1.5.0 to 1.6.0 in the first 1.6 commit (`b99e758`).
3. The old "Equipment Upgrades" handbook category is retired; its two entries no longer exist in either language, but the language keys are kept in the files for history. Its replacement lives in the same category id (`gear_upgrade`), whose display name is now "Equipment Enhancement".
4. **Indigoseagold's trim palette is still an open item** - see the changelog note. It needs the original palette file or an explicit go-ahead to paint a replacement.
5. Sixteen new config keys were added; the config file now holds **25** keys (9 pre-existing + 16 new). Existing config files pick up the new keys with their defaults on first launch.
6. Advancement progress in an existing world does not re-evaluate itself after the update. Items already in the inventory need one inventory change in that slot; new worlds are unaffected.
7. The `.bak` files under `run/config/` and the old `bettergold-1.5.0.jar` in `build/libs/` are development leftovers and are **not** part of the upload.
