# 1.4.0 vs 1.5.0 - Re-statement Check

Purpose: prove that nothing already published for 1.4.0 was fed back into the 1.5.0 material.
Left column = every claim found in the 1.4.0 release archive (`docs/发布/1.4-*.md`).
Right column = whether the 1.5.0 documents re-state it.

Allowed outcomes: **Not re-stated** (nothing in 1.5), or **Re-stated, but flagged as a 1.5 change / fix**
(the 1.5 text says explicitly that this is what changed in 1.5).

| # | Published in 1.4.0 | In the 1.5.0 documents |
|---|---|---|
| 1 | Three new metals: Flamegold, Voodoogold, Thundergold, with signature materials Blazing Rod / Voodoo Feather / Amethyst Energy Dust | **Re-stated, but flagged**: the three names appear only as the subject of two 1.5 changes (raw-ore recipe fix, High Burn duration). Their materials, stats and traits are not described |
| 2 | Each 1.4 metal = 24 items + 11 blocks, complete material / building / tool / armor line | Not re-stated |
| 3 | 1.4 adds 78 items; items 128 -> 206, blocks 43 -> 76 | Not re-stated (1.5 gives its own 85 items and 293-item total) |
| 4 | Shared tool stats: 4096 durability, mining speed 14, netherite tier, enchantability 24, repaired with own ingot, fireproof | Not re-stated |
| 5 | Tool damage / attack speed table: 10/1.8, 12/1.2, 8/1.4, 8.5/1.2, 7/4.2, knife 7.5/2.2 | Not re-stated |
| 6 | Armor values 5/814, 10/1184, 8/1110, 5/962; enchantability 24, toughness 6, 15% knockback resistance; one piece -> piglins neutral | Not re-stated |
| 7 | Three status effects: High Burn, Voodoo, Tremble, with their 1.4 numbers (36s, stored x (1 + 0.8 x level), etc.) | **Partly re-stated, but flagged**: the Voodoo payout change and the High Burn 36s -> 16s change are declared as 1.5 changes. Tremble is only used in the generic phrase "that shield's metal effect"; its 1.4 numbers are not repeated |
| 8 | Config keys `voodooStoreRatio` / `voodooReleasePerLevel` (0.8 / 0.8) | Not re-stated (only the two new key names appear) |
| 9 | Building-block contact effects, 6s: Flamegold fire / Voodoogold Poison I / Thundergold Weakness I, no refresh | Not re-stated (1.5 describes only the two new blocks' effects) |
| 10 | Flamegold auto-smelting; Thundergold visual lightning 3x3, 6 extra damage + Tremble; three thunder-sound modes | Not re-stated |
| 11 | Armor resistance / retaliation table, 25% per piece, full set immune + 100% retaliation | Not re-stated (the 25%-per-piece language in 1.5 belongs to the new Indigoseagold armor and is a new rule, not the 1.4 table) |
| 12 | Armor trim materials flamegold / voodoogold / thundergold; "the mod ships 5 trim materials" | **Re-stated, but flagged**: 1.5 says the mod now ships 7 and that trim colours were broken before; the 1.4 material names are not listed |
| 13 | Signature-material recipes: Blazing Rod (1 gunpowder + 8 blaze rods), Voodoo Feather (witch 36%, duplication), Amethyst Energy Dust (4+4+1) | Not re-stated |
| 14 | Creative inventory merged into one page with 5 banners; 206 items with FD / 175 without; per-section counts | **Re-stated, but flagged**: 1.5 gives the new total (293) and the new 14-piece gear order; the 1.4 section counts are not repeated |
| 15 | SturdyGold migrated onto the shared metal framework, stats unchanged (6144 / 10 / 30) | Not re-stated as a change; Sturdygold appears only in 1.5's own weapon values (6144 / 30) |
| 16 | Golden figurines (creeper / enderman / frog) can be smelted | Not re-stated |
| 17 | Language files: 101 new entries, 261 keys each | Not re-stated |
| 18 | Fixes: metal-knife traits, Voodoogold block poison, Flamegold sword texture, witch voodoo-feather loot injection | Not re-stated |
| 19 | Farmer's Delight optional: Farmer's Delight creative section (31 items), 4 metal knives, smithing recipes, knife tags | **Re-stated only as a requirement**: the two knives added in 1.5 need Farmer's Delight. The 1.4 FD content is not described |
| 20 | Immersive Engineering optional: Metal Press recipe (4 Golden Cowries + Gear Mold -> Mold, 3200 FE) | Not re-stated (the 1.5 upload metadata explicitly says IE added nothing in 1.5) |
| 21 | Platform metadata: Minecraft 1.21.1, NeoForge 21.1.228+, Java 21, MIT, hjmmd_8, one jar for both channels | **Re-stated**: release-form metadata that must appear on every upload. It is not 1.4 content; the 1.4 archive is only the source of the field list |
| 22 | 1.4 artifacts: `bettergold-1.4.0.jar`, 782,850 bytes, 1306 entries, 1.4 display name, 1.4 TL;DR, Beta/Release advice | Not re-stated (1.5 carries its own name, jar and numbers) |

## Verdict

- **Rows re-stating 1.4 content as if it were new: 0.**
- Rows deliberately re-stated and each explicitly labelled as a 1.5 change or a 1.5 fix: **6** (rows 1, 7, 12, 14, 19, 21) - every one of them is either a change/fix statement, a requirement statement, or mandatory release-form metadata.
- Rows where 1.4 content is silently repeated: **0**.

Conclusion: the five 1.5.0 documents add only 1.5.0 content; where an already-published 1.4.0 fact had to be touched (Voodoo formula, High Burn duration, trim count, creative-page size, Farmer's Delight requirement, release form fields), the 1.5 text marks it as what changed in 1.5 rather than re-publishing it as new.
