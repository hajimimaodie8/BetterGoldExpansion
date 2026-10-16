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
| **Patchouli** (>= 1.21.1-93) | `type="optional"`, `versionRange="[1.21.1-93,)"`, `ordering="AFTER"` in `neoforge.mods.toml` | Adds the **Alchemy Student's Handbook** (**4 categories / 20 entries / 192 pages**) and its crafting recipe | Mod loads normally; the book item **and** its recipe simply do not exist. Every reference to a Patchouli type sits behind an `isLoaded` guard in a method body, so nothing is touched at class-load time |
| **Farmer's Delight** (>= 1.3.1) | `type="optional"`, `versionRange="[1.3.1,)"`, `ordering="AFTER"` | Adds the Thornsgold and Echogold knives and their smithing recipes, the three Farmer's Delight advancements, the antique knives, and the five Farmer's Delight golden-food chapters of the handbook | Mod loads normally; the knives, the three advancements and those chapters' items are not registered (**48** advancements instead of 51) |
| **MoreUpgradeTemplate** (mod id `mut`) | **Not** a declared dependency - only datapack conditions (`neoforge:mod_loaded: mut` / `neoforge:not`) on the recipes and on the creative-tab candidate list | Hides the five golden blanks and the blank-based upgrade recipes; `mut`'s own golden mace / trident / bow / crossbow / shield become the upgrade bases | Mod loads normally; the five blanks are craftable and are the upgrade bases (nothing is hidden) |
| **JEI** | Runtime only (ships in `run/mods` for development) | Recipe viewing, unchanged in 1.6.0 | Mod loads normally |

Immersive Engineering: no new content in 1.6.0 (its 1.4-era Metal Press recipe is unchanged and is not part of this release note).

## Upload file

| Field | Value |
|---|---|
| File name | `bettergold-1.6.0.jar` |
| Path | `build/libs/bettergold-1.6.0.jar` |
| Size | **1,361,212 bytes** (built 2026-10-11 15:18:29) |
| SHA256 | `70094CE269079740CE071968FA5E4E55A87EDA9C16E6ABB0C89C49D9212F6B23` |
| Entries | 2,409 files |
| Consistency | Both language files **inside the jar** are byte-identical to HEAD `da0996e` (`en_us.json` = `07AA2FA0…F27097768F`, `zh_cn.json` = `695FA5A5…8B3C972810`), and the jar contains no `*Probe*` path |
| Debug code | No probe / diagnostic classes, no `halt` calls and no `BG-PROBE` marker (verified by `tools/asset-generator/check_jar_clean.py` on the last verified build, exit 0 with `*Probe*` 0 / `'halt'` bytes 0 / `'BG-PROBE'` 0) |

⚠ The old `build/libs/bettergold-1.5.0.jar` (1,089,906 B) sitting next to it is a development leftover and is **not** part of the upload.

## Beta / Release

**Recommended: Release.**
Build and data checks are green on the last verified build (`compileJava`, `runData`, `processResources jar --rerun-tasks`: `BUILD SUCCESSFUL`; six validators all exit 0 **and** each validator's exit-1 / exit-2 paths were proven by perturbation matrices; no debug code in the jar). The release note for this round was written from the repository as it stands at HEAD `da0996e` and did not rebuild anything.

## Known notes (author only - do not paste into the public changelog)

1. The five golden blanks are hidden **only when `mut` is installed**; if `mut` is absent, the blanks are visible and craftable. With `mut` installed, the handbook's linkage chapter and the first smithing page of each metal reference blank-based recipes that are not loaded, so those pages can look empty.
2. With Farmer's Delight absent, the handbook's last two golden-food chapters have no items or recipes to resolve (5 of the 20 entries).
3. Three handbook cells still wait on the author: the `〔待补〕` chapter name (gift-box chapter), the fifth golden-food chapter's cover icon, and the two "(not specified by the author)" cells.
4. Three handbook hunger values (7.5 / 10.5 / 19.5) cannot be expressed by the code because `FoodProperties.Builder.nutrition` takes an `int`; the book text is kept verbatim and the difference is recorded.
5. Two handbook effect descriptions do not match the code (Sturdygold Chocolate Pie; the two Alchemical Meat Sandwiches). Book text unchanged.
6. Five handbook pages show a spotlight icon instead of a recipe grid, because Patchouli cannot express the brewing stand or the Farmer's Delight cooking pot.
7. **Player-visible rename in this release**: the antique is now 没用的老古董 / `Useless Old Antique` (was 没人要的老古董 / `Unwanted Old Antique`; the trim-material display name was `Old Antique`). Across the whole 1.6 range these are the **only two** language values that changed relative to the 1.5.0 boundary - 0 keys were removed and 359 were added in each file.
8. **Advancement progress in an existing world does not re-evaluate itself after the update.** Items already in the inventory need one inventory change in that slot; new worlds are unaffected. The advancement tree's order is now pinned for the eight metal lines only - the root, the Sturdygold weapon group and the Gold-Infused Dirt group still appear in a launch-dependent order.
9. The 80% Golden Bone Meal figure is a sampled measurement, not an exact count.
10. Mod ids, block and item ids, language key **names**, config key **names** and datapack paths are unchanged from 1.5.0; existing worlds can be loaded. `mod_version` moved from 1.5.0 to 1.6.0 in the first 1.6 commit (`b99e758`).
11. The old "Equipment Upgrades" handbook category is retired; the retired "Material Chain" and "Upgrade Template" chapters are retired as well. Their language keys were deleted by the author's own `zh_cn.json` replacement late in the range; the archived text of every retired page is kept in `docs/1.6-规格.md`, not in the language files.
12. Sixteen new config keys were added; the config file now holds **25** keys (9 pre-existing + 16 new). Existing config files pick up the new keys with their defaults on first launch, but NeoForge does **not** reorder keys already present in an existing TOML file - the config **screen** order comes from the loaded spec, so it is correct either way.
13. The `.bak` files under `run/config/` are development leftovers and are **not** part of the upload.
