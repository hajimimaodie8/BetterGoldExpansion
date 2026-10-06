# 1.5.0 vs 1.6.0 - Re-statement Check

Purpose: prove that nothing already published for 1.5.0 was fed back into the 1.6.0 material.
Left column = every claim found in the 1.5.0 release archive (`docs/发布/1.5.0/` five files).
Right column = whether the 1.6.0 documents re-state it.

Allowed outcomes: **Not re-stated** (nothing in 1.6), or **Re-stated, but flagged as a 1.6 change / fix / requirement**
(the 1.6 text says explicitly that this is what changed in 1.6, or that it is a release-form field that must appear on every upload).

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
| 1 | **Indigoseagold and Illusiongold**: two new metals, signature materials (Indigo Ocean Heart / Chorus Cherry Branch), full material + building + gear + armor lines, shared stats (4096 / 14 / netherite tier / 24; armor 5/814, 10/1184, 8/1110, 5/962; one piece makes piglins neutral), both pillars work as beacon bases | Not re-stated. 1.6 states the shared stats **for its own two metals only** ("their stats match the existing metals"), and never repeats the 1.5 names, materials, recipes or traits |
| 2 | **Sediment** (Indigoseagold): `level + 1` suffocation damage every second, -1% movement speed per level, stacking without limit, 16 seconds per hit | Not re-stated as new. Sediment appears **only** inside the 1.6 "Changed" statement that High Burn and Sediment damage now equals the effect's level - i.e. explicitly flagged as what changed in 1.6 |
| 3 | **Soothe** (Illusiongold): the target loses its AI for 1 second; original AI and target come back on expiry / early removal / death / leaving the world | Not re-stated |
| 4 | **"A full weapon line for all six metals (30 weapons)"** - mace 9/0.8 (x1.2 final damage), shield, bow (16-tick full draw, arrow base damage 4.0), crossbow (charge 1 s = 20 ticks, bolt speed 4.5), trident (13/1.3, throw 15) - with a values table | Not re-stated as 1.5 content. The **crossbow's 20-tick charge** is genuinely re-implemented in 1.6 (a `CrossbowItem.getChargeDuration` mixin scoped to this mod's crossbows), but 1.6 does **not** restate the 20-tick claim as news either - the 1.5 statement stays a 1.5 fact |
| 5 | Every weapon fires its own metal's on-hit effect, including ranged and thrown hits; metal tridents have their own in-hand 3D model | Not re-stated |
| 6 | **Shields**: all six ignore the axe shield-disable; blocking hands the attacker that shield's metal effect; any mod shield in either hand gives +10% knockback resistance (shown in the tooltip) | Not re-stated |
| 7 | **Armor trim colours**: "every trim material of the mod rendered white in the inventory; each material now uses its own palette index and the trim layers exist in the item atlas" (published as **Fixed**) | **Re-stated, but flagged** - and flagged as *still open*. 1.6 says Indigoseagold's palette is **currently** the vanilla quartz greyscale because a 1.5.0-era rollback touched that one file, that every other suspect checked out, and that restoring it needs the original file back or an explicit go-ahead. It does **not** claim the 1.5.0 fix was undone or redone |
| 8 | **Raw ore recipes** (published as **Fixed**): the raw-ore recipes of Flamegold, Voodoogold and Thundergold produced Sturdygold Raw, an old shapeless recipe duplicated them, and each metal now has exactly one raw-ore recipe that returns your glass bottle | **Re-stated, but flagged** - and in the **opposite** direction. 1.6 records that **three leftover shapeless raw-ore recipes were still present at the 1.5.0 boundary** and are removed in 1.6, so each metal really has exactly one now. The other half of the 1.5 claim (correct result item, glass bottle returned) **was** true at the boundary - checked at `(code)` `recipe/RawSturdygoldRecipe.java:130-146` (`getRemainingItems` returns `Items.GLASS_BOTTLE`) - and is therefore **not** restated. 1.6 describes a removal, not a re-publication of the 1.5 fix |
| 9 | **Voodoo payout**: 36% of the damage taken + 1 damage per effect level; new keys `voodooExtractRatio` (0.36) and `voodooFlatPerLevel` (1.0) | **Re-stated, but flagged**: 1.6 lists it under "Changed". Verified against the code that the formula and defaults are the same, so this is a **change notice for 1.6**, not a re-publication |
| 10 | **High Burn lasts 16 seconds** (was 36) from Flamegold weapon hits and armor retaliation | Not re-stated as a duration claim. High Burn appears **only** inside the 1.6 "Changed" bullet about damage-per-second equalling the effect level - a different axis |
| 11 | **Creative inventory**: one "Better Gold" page with five banners, now holding **293 items** - 1.5 adds 85 items (87 with Farmer's Delight); each metal's gear is a 14-piece run | Not re-stated (1.6 gives its own item list and never repeats the 293 / 85 / 87 counts) |
| 12 | **Beacon bases** (published as **Fixed**): Indigoseagold and Illusiongold pillars could not be used as beacon bases; both now can | **Re-stated, but flagged**: 1.6 says "Both **new pillars** work as beacon bases" while describing its own two new metals. It is a statement about 1.6 content, and it does not repeat the 1.5 fix wording or the 1.5 metal names as a fix |
| 13 | **Farmer's Delight** optional; the two new knives only exist when it is installed | **Re-stated, but flagged as a requirement**: 1.6 lists Farmer's Delight in the optional-dependency table with the **1.6** content it adds (the Thornsgold and Echogold knives and their smithing recipes) and never describes the 1.5 knives |
| 14 | **MoreUpgradeTemplate (`mut`)** optional; with it installed the five blanks and the 30 blank-based upgrade recipes stay hidden and `mut`'s own golden mace / trident / bow / crossbow / shield upgrade into the six metal versions instead; without it nothing changes | **Re-stated, but flagged as a requirement / known note**: 1.6 keeps the dependency table row and the behavioural note, and adds a **1.6-specific** rough edge (the handbook's linkage chapter and the first two smithing pages of each metal point at blank-based recipes that are not loaded under `mut`). The "six metal versions" phrasing is replaced by the 8-metal reality |
| 15 | **Armor/tool/block traits for the two 1.5 metals**: Indigoseagold armor 25% suffocation/drowning resistance per piece + 25% per-piece Sediment retaliation + 25% water movement efficiency + 25% swim speed; Indigoseagold tools ignore the underwater mining penalty and deal double damage to 4 mobs; Indigoseagold blocks refill axolotl air and hurt those 4 mobs (4 damage, ≤1 per 10 ticks); Illusiongold blocks grant Regeneration (6 s) | Not re-stated |
| 16 | **Two new armor trim materials**; "the mod now ships 7" | Not re-stated (1.6 does not restate the trim count; it only touches the single Indigoseagold palette, flagged in row 7) |
| 17 | **Golden figurines (creeper / enderman / frog) can be smelted** | Not re-stated, and checked: `git log --follow -- .../golden_creeper_figurine_smelting.json` returns only `b5f68d3` (1.4) and `git diff 051294c HEAD -- <that file>` is empty, so 1.6 did not touch it |
| 18 | (1.4-era, repeated into 1.5) **Sturdygold absorption hearts**: 1 absorption heart (2 points) every 16 seconds per armor piece or shield, up to 4 points per armor piece plus 4 for the shield - a maximum of 20; the five golden blanks are the crafting bases for the upgrade recipes | Not re-stated as 1.5 content. The **blanks** appear in 1.6 only via the `mut` dependency row and the new handbook chapter; the **absorption** mechanic appears only inside the 1.6 "Changed" bullet about the new config keys (`sturdygoldArmorAbilityIntervalMultiplier`). Neither the 16-second/2-point/cap-20 numbers nor the "maximum of 20" claim is repeated |
| 19 | **Version/boundary facts**: version `1.5.0`; the 1.4→1.5 boundary is `b59b892`; jar `bettergold-1.5.0.jar`, **1,089,068 bytes**, built 2026-10-03; "1.5 adds 85 items" | Not re-stated. 1.6 carries its own version, its own boundary, its own jar and its own numbers. (Note: an old `bettergold-1.5.0.jar` - 1,089,906 bytes - is still lying in `build/libs/` as a development leftover; the 1.6 metadata quotes only `bettergold-1.6.0.jar`) |
| 20 | **Platform metadata**: Minecraft 1.21.1 only; NeoForge 21.1.228+, Java 21; MIT; hjmmd_8; one jar for both channels; client/server both required; `modLoader="javafml"`; Beta/Release advice | **Re-stated**: release-form metadata that must appear on every upload. It is not 1.5 content; the 1.5 archive is only the source of the field list. 1.6 gives its own version, name, summary, size and advice |
| 21 | **The 30 blank-based upgrade recipes / `smithing_mut_*` ids** and the note that two recipe ids changed during 1.5 development, so already-unlocked old ids may show as unlocked again | Not re-stated |
| 22 | **Voodoo armor's full-set poison immunity** (1.5.0 mentioned it only via the armor trait list in `SOURCES.md` item "Armor resistance / retaliation"; the mechanic is the one that never worked) | **Re-stated, but flagged as a 1.6 fix**: 1.6 reports that the full-set poison immunity did not work (the check sat behind an unrelated Thundergold early-return) and that it is now an independent check. This is the 1.6 fix statement, not a re-publication of a 1.5 claim |
| 23 | **Immersive Engineering** note: no new content in 1.5.0 | **Re-stated, but flagged**: 1.6 carries the same one-line "no new content" note for its own version. It is a standing negative statement about a third-party integration, kept so the upload form is not left ambiguous |

## Machine cross-check: the 1.6 language files are purely additive

A useful independent signal for "did 1.6 quietly rewrite 1.5 text?" is the language files, because every
player-facing string in this mod lives there. Comparing the 1.5.0 boundary (`051294c`) against HEAD:

```
zh_cn.json:  keys 363 -> 656   (293 added)   values CHANGED = 0   keys REMOVED = 0
en_us.json:  keys 363 -> 656   (293 added)   values CHANGED = 0   keys REMOVED = 0
   added-key breakdown (zh):  advancements.bettergold.* 102
                              bettergold.handbook.*      91
                              item.bettergold.*          52
                              block.bettergold.*         23
                              bettergold.configuration.* 21
                              trim_material.bettergold.*  2
                              effect.bettergold.*         2
```

**No 1.5.0 string was edited or deleted anywhere in the 1.6 range.** Everything the 1.6 documents say about changed text
is therefore about **newly added** keys plus exactly one in-1.6 rename (the new `effect.bettergold.echo_roar` key was born
in 1.6 as 幽咆 / `Echo Roar` and was renamed to 音咆 / `Sonic Roar` inside 1.6 by the `bg-fix` round - it never existed in
1.5.0, so nothing 1.5 published was overwritten).

## Verdict

- **Rows re-stating 1.5.0 content as if it were new: 0.**
- **Rows deliberately re-stated, each explicitly labelled as a 1.6 change / fix / requirement: 7** -
  rows **7, 8, 9, 12, 13, 14, 22**.
- **Rows that are release-form metadata or a standing note rather than 1.5.0 content: 2** - rows **20** (mandatory upload-form
  fields, which must appear on every release) and **23** (a standing "no new content" note about Immersive Engineering).
  Both are labelled as such in the right-hand column.
- **Rows where 1.5.0 content is silently repeated: 0.**

## Two rows that needed the most care (read these before touching the changelog)

Row 7 - **armor trim colours.** 1.5.0 published this as a fix. 1.6 must not look like it is announcing the same fix again.
The 1.6 text therefore (a) never says "trim colours work now", (b) says the **one** Indigoseagold palette is currently the
vanilla quartz greyscale, and (c) marks it as **open / pending a decision**. The underlying cause is _not_ the 1.5 bug.

Row 8 - **raw ore recipes.** 1.5.0 published "each metal now has exactly one raw-ore recipe" as a fix, but the three legacy
shapeless recipes were **still present at the 1.5.0 boundary** (`flamegold_raw.json` / `thundergold_raw.json` /
`voodoogold_raw.json` all existed at `051294c` and were deleted in `b99e758`). 1.6 therefore describes a **removal**, and the
1.5.0 "Fixed" wording is not repeated. This is the one place where the 1.5.0 archive and the 1.5.0 shipping tree disagree, and
the 1.6 documents follow **the tree**.

Conclusion: the five 1.6.0 documents add only 1.6.0 content. Where an already-published 1.5.0 fact had to be touched
(Voodoo payout, the High Burn / Sediment curve, the Indigoseagold trim palette, the beacon pillars, the two optional
dependencies, the Voodoo poison-immunity fix, and the mandatory release-form fields), the 1.6 text marks it as what changed,
what was fixed, or what is still open in 1.6 - and never re-publishes a 1.5.0 claim as new.
