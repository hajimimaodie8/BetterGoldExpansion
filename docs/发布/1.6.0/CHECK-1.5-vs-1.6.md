# 1.5.0 vs 1.6.0 - Re-statement Check

Purpose: prove that nothing already published for 1.5.0 was fed back into the 1.6.0 material.
Left column = every claim found in the 1.5.0 release archive (`docs/发布/1.5.0/` five files).
Right column = whether the 1.6.0 documents re-state it.

Allowed outcomes: **Not re-stated** (nothing in 1.6), or **Re-stated, but flagged as a 1.6 change / fix /
requirement** (the 1.6 text says explicitly that this is what changed in 1.6, or that it is a release-form
field that must appear on every upload).

Sources for the left column - the five 1.5.0 files, read in full:

| File | Lines used |
|---|---|
| `docs/发布/1.5.0/CHANGELOG-1.5.0.md` | Added / Changed / Fixed / Mod-integration sections |
| `docs/发布/1.5.0/UPLOAD-METADATA-1.5.0.md` | Version, Version name, One-line summary, Supported MC, Loader, Dependencies, Upload file, Beta/Release, Known notes |
| `docs/发布/1.5.0/MODPAGE-1.5.0.md` | The four mod-page paragraphs |
| `docs/发布/1.5.0/CHECK-1.4-vs-1.5.md` | 22 published 1.4.0 claims (not used as a source of 1.5.0 claims) |
| `docs/发布/1.5.0/SOURCES.md` | Its evidence table (used to confirm which 1.5.0 statements were public) |

1.5.0 published claims extracted = **23 rows** below.

| # | Published in 1.5.0 | In the 1.6.0 documents |
|---|---|---|
| 1 | **Indigoseagold and Illusiongold**: two new metals, signature materials (Indigo Ocean Heart / Chorus Cherry Branch), full material + building + gear + armor lines, shared stats (4096 / 14 / netherite tier / 24; armor 5/814, 10/1184, 8/1110, 5/962; one piece makes piglins neutral), both pillars work as beacon bases | **Re-stated, but flagged as a 1.6 statement.** The shared shape and the shared stat numbers are asserted about the **1.6** metals, and the sentence is explicitly prefixed with "**Both are built exactly like the rest of the mod**" and "**their stats match the existing metals**" - i.e. it says outright that this is the established pattern, not news. 1.6 never repeats the 1.5 metal names, their materials, their recipes or their traits |
| 2 | **Sediment** (Indigoseagold): `level + 1` suffocation damage every second, -1% movement speed per level, stacking without limit, 16 seconds per hit | **Re-stated, but flagged as a 1.6 change.** Sediment appears **only** inside the 1.6 "Changed" bullet stating that High Burn and Sediment now deal damage equal to the effect's level (one point less per level than the 1.5 figure). The slow, the duration and the stacking rule are not repeated |
| 3 | **Soothe** (Illusiongold): the target loses its AI for 1 second; original AI and target come back on expiry / early removal / death / leaving the world | Not re-stated |
| 4 | **"A full weapon line for all six metals (30 weapons)"** - mace 9/0.8 (x1.2 final damage), shield, bow (16-tick full draw, arrow base damage 4.0), crossbow (charge 1 s = 20 ticks, bolt speed 4.5), trident (13/1.3, throw 15) - with a values table | Not re-stated. The 1.6 text gives no weapon values table and never says "30 weapons". (The crossbow's 20-tick charge is genuinely re-implemented in 1.6 as a `CrossbowItem.getChargeDuration` mixin scoped to this mod's crossbows, but 1.6 does not restate the 20-tick figure either) |
| 5 | Every weapon fires its own metal's on-hit effect, including ranged and thrown hits; metal tridents have their own in-hand 3D model | Not re-stated |
| 6 | **Shields**: all six ignore the axe shield-disable; blocking hands the attacker that shield's metal effect; any mod shield in either hand gives +10% knockback resistance (shown in the tooltip) | Not re-stated |
| 7 | **Armor trim colours**: "every trim material of the mod rendered white in the inventory; each material now uses its own palette index and the trim layers exist in the item atlas" (published as **Fixed**) | **Re-stated, but flagged as a 1.6 fix.** 1.6 says Indigoseagold's palette was rolled back to the vanilla quartz greyscale by a **1.5.0-era** decision, that the author supplied the original artwork, and that it is now **restored byte for byte** while the other eight palettes were never touched. It does **not** re-announce the 1.5 atlas fix and never claims trim colours "work now" |
| 8 | **Raw ore recipes** (published as **Fixed**): the raw-ore recipes of Flamegold, Voodoogold and Thundergold produced Sturdygold Raw, an old shapeless recipe duplicated them, and each metal now has exactly one raw-ore recipe that returns your glass bottle | **Re-stated, but flagged** - and in the **opposite** direction. 1.6 records that **three leftover shapeless raw-ore recipes were still present at the 1.5.0 boundary** and are removed in 1.6, so each metal really has exactly one now. The other half of the 1.5 claim (correct result item, glass bottle returned) **was** true at the boundary - re-checked at `(code)` `recipe/RawSturdygoldRecipe.java:141-146` (`getRemainingItems` returns `Items.GLASS_BOTTLE`) - and is therefore **not** restated. 1.6 describes a removal, not a re-publication of the 1.5 fix |
| 9 | **Voodoo payout**: 36% of the damage taken + 1 damage per effect level; new keys `voodooExtractRatio` (0.36) and `voodooFlatPerLevel` (1.0) | **Not re-stated - deliberately.** The formula and both defaults are **identical** at the 1.5.0 boundary (`(code)` `config/Config.java` at `051294c` already defines `voodooExtractRatio` = 0.36D) and at HEAD (`config/Config.java:68`), so 1.6 changed nothing here. An earlier draft of the 1.6 changelog carried it under "Changed"; it was **removed** for exactly this reason. This is the one place where the check changed the 1.6 text rather than the other way round |
| 10 | **High Burn lasts 16 seconds** (was 36) from Flamegold weapon hits and armor retaliation | Not re-stated as a **duration** claim - the 1.6 text states no High Burn duration at all. High Burn is named only inside the "Changed" bullet about damage per second (row 2), and that bullet's own statement is flagged |
| 11 | **Creative inventory**: one "Better Gold" page with five banners, now holding **293 items** - 1.5 adds 85 items (87 with Farmer's Delight); each metal's gear is a 14-piece run | Not re-stated as 1.5 content (no 293 / 85 / 87 count appears). The "14-piece gear run" phrase is covered by row 1's flag; the 1.6 **Materials-section reorder** is a 1.6-only change and is stated as such |
| 12 | **Beacon bases** (published as **Fixed**): Indigoseagold and Illusiongold pillars could not be used as beacon bases; both now can | **Re-stated, but flagged**: 1.6 says "Both **new pillars** work as beacon bases" inside its own two-metal sentence (row 1's flag). It does not repeat the 1.5 fix wording or the 1.5 metal names |
| 13 | **Farmer's Delight** optional; the two new knives only exist when it is installed | **Re-stated, but flagged as a requirement**: 1.6 lists Farmer's Delight in the dependencies table with the **1.6** content it adds (the Thornsgold and Echogold knives and their smithing recipes, plus the three Farmer's Delight advancements) and never describes the 1.5 knives |
| 14 | **MoreUpgradeTemplate (`mut`)** optional; with it installed the five blanks and the 30 blank-based upgrade recipes stay hidden and `mut`'s own golden mace / trident / bow / crossbow / shield upgrade into the six metal versions instead; without it nothing changes | **Re-stated, but flagged as a requirement / known note**: 1.6 keeps the dependency table row and the behavioural note, and adds a **1.6-specific** rough edge (the handbook's linkage chapter and the first smithing page of each metal point at blank-based recipes that are not loaded under `mut`). The "six metal versions" phrasing is replaced by the 8-metal reality |
| 15 | **Armor/tool/block traits for the two 1.5 metals**: Indigoseagold armor 25% suffocation/drowning resistance per piece + 25% per-piece Sediment retaliation + 25% water movement efficiency + 25% swim speed; Indigoseagold tools ignore the underwater mining penalty and deal double damage to 4 mobs; Indigoseagold blocks refill axolotl air and hurt those 4 mobs (4 damage, <=1 per 10 ticks); Illusiongold blocks grant Regeneration (6 s) | Not re-stated |
| 16 | **Two new armor trim materials**; "the mod now ships 7" | Not re-stated (1.6 does not restate the trim count; it only touches the single Indigoseagold palette, flagged in row 7) |
| 17 | **Golden figurines (creeper / enderman / frog) can be smelted** | Not re-stated, and re-checked at the new HEAD: `git diff --name-only 051294c HEAD -- src/main/resources/data/bettergold/recipe` contains **no** figurine recipe, so 1.6 did not touch them |
| 18 | (1.4-era, repeated into 1.5) **Sturdygold absorption hearts**: 1 absorption heart (2 points) every 16 seconds per armor piece or shield, up to 4 points per armor piece plus 4 for the shield - a maximum of 20; the five golden blanks are the crafting bases for the upgrade recipes | **Re-stated, but flagged.** The absorption mechanic appears only inside the 1.6 bullet about the **new config keys** (`sturdygoldArmorAbilityIntervalMultiplier`), and the five golden blanks appear only in the 1.6 **creative Materials ordering** list (their new positions). Neither the 16-second / 2-point / cap-20 numbers nor the "maximum of 20" claim is repeated |
| 19 | **Version/boundary facts**: version `1.5.0`; the 1.4->1.5 boundary is `b59b892`; jar `bettergold-1.5.0.jar`, **1,089,068 bytes**, built 2026-10-03; "1.5 adds 85 items" | Not re-stated. 1.6 carries its own version, its own boundary (`051294c`), its own jar and its own numbers. (Note: an old `bettergold-1.5.0.jar` - 1,089,906 bytes - is still lying in `build/libs/` as a development leftover; the 1.6 metadata quotes only `bettergold-1.6.0.jar`) |
| 20 | **Platform metadata**: Minecraft 1.21.1 only; NeoForge 21.1.228+, Java 21; MIT; hjmmd_8; one jar for both channels; client/server both required; `modLoader="javafml"`; Beta/Release advice | **Re-stated as release-form metadata** that must appear on every upload. It is not 1.5 content; the 1.5 archive is only the source of the field list. 1.6 gives its own version, name, summary, size and advice |
| 21 | **The 30 blank-based upgrade recipes / `smithing_mut_*` ids** and the note that two recipe ids changed during 1.5 development, so already-unlocked old ids may show as unlocked again | Not re-stated |
| 22 | **Voodoo armor's full-set poison immunity** (1.5.0 mentioned it only via the armor trait list in `SOURCES.md` item "Armor resistance / retaliation"; the mechanic is the one that never worked) | **Re-stated, but flagged as a 1.6 fix**: 1.6 reports that the full-set poison immunity did not work (the check sat behind an unrelated Thundergold early-return) and that it is now an independent check. This is the 1.6 fix statement, not a re-publication of a 1.5 claim |
| 23 | **Immersive Engineering** note: no new content in 1.5.0 | **Re-stated, but flagged as a standing note**: 1.6 carries the same one-line "no new content" note for its own version. It is a standing negative statement about a third-party integration, kept so the upload form is not left ambiguous |

## Machine cross-check: what the language files say about the 1.6 range

Every player-facing string in this mod lives in the language files, so diffing them is an independent
signal for "did 1.6 quietly rewrite 1.5 text?". Comparing the 1.5.0 boundary (`051294c`) against HEAD:

```
zh_cn.json:  keys 363 -> 722   (+359 added)   values CHANGED = 2   keys REMOVED = 0
en_us.json:  keys 363 -> 722   (+359 added)   values CHANGED = 2   keys REMOVED = 0
   added-key breakdown (identical in both files):
     advancements.bettergold.*     102
     bettergold.handbook.*         157
     item.bettergold.*              52
     block.bettergold.*             23
     bettergold.configuration.*     21
     effect.bettergold.*             2
     trim_material.bettergold.*      2
   the only two changed values, in both files:
     item.bettergold.unwanted_antique          (zh 没人要的老古董 -> 没用的老古董;
                                                en Unwanted Old Antique -> Useless Old Antique)
     trim_material.bettergold.unwanted_antique (en Old Antique -> Useless Old Antique)
   zh_cn and en_us key sets are identical at HEAD (722 each).
```

**No 1.5.0 string was silently rewritten.** Out of 363 pre-existing keys, exactly **two** values changed and
both are the deliberate antique rename that the 1.6 changelog announces in its own "Text" bullet; no key
that existed at the boundary was deleted. (Twenty further keys were deleted **inside** the 1.6 range by the
author's own `zh_cn.json` replacement - they were all 1.6-born keys for handbook entries and placeholders
that 1.6 had already retired, and none of them existed at `051294c`.)

The in-range rename of the echo-roar effect (`bettergold:echo_roar` displayed first as 幽咆 / `Echo Roar`,
then as 音咆 / `Sonic Roar`) is likewise **not** in this list, because that key was born in 1.6 - it does not
exist at `051294c`, so nothing 1.5 published was overwritten.

## Verdict

- **Rows re-stating 1.5.0 content as if it were new: 0.**
- **Rows deliberately re-stated, each explicitly labelled as a 1.6 change / fix / requirement: 9** -
  rows **1, 2, 7, 8, 12, 13, 14, 18, 22**.
- **Rows that are release-form metadata or a standing note rather than 1.5.0 content: 2** - rows **20**
  (mandatory upload-form fields, which must appear on every release) and **23** (a standing "no new content"
  note about Immersive Engineering).
- **Rows where 1.5.0 content is silently repeated: 0.**
- **Rows not re-stated at all: 12** - rows **3, 4, 5, 6, 9, 10, 11, 15, 16, 17, 19, 21**.

## Three rows that needed the most care (read these before touching the changelog)

Row 7 - **armor trim colours.** 1.5.0 published this as a fix. 1.6 must not look like it is announcing the
same fix again. The 1.6 text therefore (a) never says "trim colours work now", (b) says the **one**
Indigoseagold palette had been rolled back to the vanilla quartz greyscale by a **1.5.0-era** decision, and
(c) says the author supplied the original artwork and it is **restored byte for byte**, with the other eight
palettes untouched. The underlying cause was never the 1.5 bug.

Row 8 - **raw ore recipes.** 1.5.0 published "each metal now has exactly one raw-ore recipe" as a fix, but the
three legacy shapeless recipes were **still present at the 1.5.0 boundary** (`flamegold_raw.json` /
`thundergold_raw.json` / `voodoogold_raw.json` all existed at `051294c` and were deleted in `b99e758`).
1.6 therefore describes a **removal**, and the 1.5.0 "Fixed" wording is not repeated. This is the one place
where the 1.5.0 archive and the 1.5.0 shipping tree disagree, and the 1.6 documents follow **the tree**.

Row 9 - **Voodoo payout.** 1.5.0 published the 36% + 1/level formula and both config keys. Nothing about it
changed in 1.6, so an earlier draft of the 1.6 changelog that carried it under "Changed" was itself a
re-publication of 1.5.0 content; the bullet has been **deleted** from the changelog. This is the only row
where this check changed the 1.6 text.

Conclusion: the 1.6.0 documents add only 1.6.0 content. Where an already-published 1.5.0 fact had to be
touched (the shared metal shape and stats, the High Burn / Sediment curve, the Indigoseagold trim palette,
the raw-ore recipes, the beacon pillars, the two optional dependencies, the golden blanks and Sturdygold
absorption, the Voodoo poison-immunity fix, and the mandatory release-form fields), the 1.6 text marks it as
what changed, what was fixed or what it is a requirement of - and never re-publishes a 1.5.0 claim as new.
