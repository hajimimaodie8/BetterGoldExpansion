# Sources and Evidence (1.5.0 release note)

Every claim in the 1.5.0 documents traces to the items below.

## 1. Version boundary (1.4.0 -> 1.5.0)

```
$ git tag -l                                  -> (empty: the repository has no tags)

$ git log --format="%h %ad %s" --date=iso -8
051294c 2026-10-02 20:25 bg-15w 8.3 rebuilt: swim speed now uses neoforge:swim_speed
ce10311 2026-10-02 18:28 bg-15w section 8 round 2: gear order re-pinned + real swim speed
16ac37a 2026-10-02 16:58 1.5 complete: two new metals + gold weapon system + weapon round
b59b892 2026-10-01 17:25 1.4 fix: building order, FD knife traits, no poison refresh, sword texture
9a9f417 2026-09-30 21:10 IE integration: Immersive Engineering Metal Press recipe
b5f68d3 2026-09-30 20:51 1.4 "new covenant": three new metals + banner sections + SturdyGold migration

$ git log --format="COMMIT %h %ad %s" --date=short -p -- gradle.properties | Select-String "COMMIT |mod_version"
COMMIT 16ac37a 2026-10-02   -mod_version=1.4.0  +mod_version=1.5.0
COMMIT b5f68d3 2026-09-30   -mod_version=1.3.0  +mod_version=1.4.0

$ git log --oneline b59b892..HEAD        -> 051294c, ce10311, 16ac37a
$ git diff --shortstat b59b892..HEAD     -> 662 files changed, 22083 insertions(+), 250 deletions(-)  (26 .java)
$ git status --porcelain                 -> 12 entries, uncommitted 1.5 work (sections 18 / 19):
     modified: AGENTS.md, docs/1.5-规格.md, AllMetals.java, CreativeSections.java, MetalEvents.java,
               MetalFamily.java, beacon_base_blocks.json, generate_metal_tags.py, validate_metal_data.py
     deleted:  data/bettergold/recipe/{flamegold,thundergold,voodoogold}_raw.json
     untracked: docs/bg15y-证据/, docs/bg9-证据/
$ git ls-tree -r --name-only b59b892 | docs/*   -> 0 files
$ git log --oneline --diff-filter=A -- docs/发布/ -> 16ac37a
```

**Chosen boundary: `b59b892`**, the parent of the version-bump commit `16ac37a` (the last 1.4.0 commit).

Basis: (1) no tag exists, so the boundary comes from `mod_version` - the bump to 1.5.0 happens *inside* `16ac37a`, which is itself the first 1.5 commit, so the boundary is its parent; `git log 16ac37a..HEAD` would return only 2 commits and hide the whole 1.5 body of work. (2) `b59b892` is exactly what the 1.4.0 release archive describes: its content maps one-for-one onto the "Fixed" section of `docs/发布/1.4-变更日志.*`, and the commit before it (`9a9f417`) matches the Immersive Engineering recipe in the same archive. (3) Cross-check: the 1.4 upload metadata records a jar built 2026-10-01 12:50 from a tree last modified 12:46 with no uncommitted changes; `b59b892` was committed that day at 17:25 carrying that tree. (4) The whole `docs/` tree did not exist at `b59b892` (0 files).

Range reviewed = `b59b892..HEAD` **plus the 12 uncommitted working-tree files** (sections 18 / 19), since those belong to 1.5.0.

## 2. 1.4.0 release archive read (source of the "already published" list)

`docs/发布/1.4-上传元信息.md` (1-83), `docs/发布/1.4-变更日志.zh_cn.md` (1-131), `docs/发布/1.4-变更日志.en_us.md` (1-131), `docs/发布/1.4-模组页新增段落.md` (1-31). 22 published claims extracted; see `CHECK-1.4-vs-1.5.md`.

## 3. 1.5 evidence

| Claim | Evidence |
|---|---|
| Two new metals, ids, names, version | `docs/1.5-规格.md` (spec) sections 1-2; `material/AllMetals.java:63,92`; `lang/en_us.json`; `gradle.properties` `mod_version=1.5.0` |
| 24 items + 11 blocks each, tool/armor values, single-piece piglin neutrality | spec 2.1 / 2.2, 11.2 (measured); `material/MetalFamily.java` spec defaults |
| Signature materials and their recipes | spec 2.1 / 2.2, section 7 no. 5; lang keys `indigo_ocean_heart`, `chorus_cherry_branch` |
| Sediment / Soothe | spec 3.1, 3.2, 11.3 (measured: 2.0 / 4.0 damage per second, NoAI restore on 4 paths); `registry/AllEffects.java:124,162` |
| Voodoo formula + config keys | spec 4.3, 4.4, 10.2 (measured A=17.4, A2=5.0); `material/VoodooAccumulator.java:26,54-57,92-93,101`; `config/Config.java:75,90` |
| High Burn 16 s | spec 13.2 (320 ticks measured); `material/MetalFamily.java:116` |
| 30 weapons, stats, blanks | spec 12.1, 12.2, 12.8 re-check (mace 9.0/0.8, bow `powerForTime(16)=1.0`, crossbow `chargeDuration=20`, trident 13.0/1.3 + throw 15.0, shield 3072/2048, arrow `baseDamage=4.0`, bolt 4.4994); `material/MetalWeapons.java:45,51,61,89,190,244,268`; 5 `golden_*_blank.json` |
| Ranged / thrown dispatch, trident 3D + thrown texture | spec 12.4(1)/(1b), 14.2, 16.6 |
| Shield disable immunity, block retaliation, +10% knockback resistance | spec 16.2 (measured 0.4000 -> 0.3600, tooltip rows), 16.3 (Sturdygold red -> all six green) |
| Absorption 16 s / 2 points / cap 4 x pieces + 4 | spec 12.3, 13.6, 14.3 (4 pieces + shield = 20.0); `material/MetalFamily.java:164-182` |
| Creative page 293 items, 14-piece gear order | spec 12.8 re-check; spec 19.1 (measured order, 6/6); `material/CreativeSections.java:143-156` |
| Indigoseagold armor / tools / blocks | spec 2.1, 11.4, 13.3 (axolotl air 10 -> 6000), 13.4 (8.0 vs 4.0), 13.5 + 17.8 (water movement efficiency / swim speed, 1.25-2.00 layer ratio), 19.3 (mining 14.0 vs 2.8) |
| Illusiongold blocks grant Regeneration | spec 2.2, 11.4 (120 ticks; hostile mob negative control) |
| 7 trim materials + trim colour fix | spec 13.7; `data/bettergold/trim_material/*.json` = 7 files, `item_model_index` 0.01-0.07 |
| Beacon pillars | spec 18.1-18.5 (4 PASS/4 FAIL -> 8 PASS/0 FAIL); `beacon_base_blocks.json` = 20 members incl. both new pillars |
| Raw-ore recipe fix + 3 duplicate recipes deleted | spec 10.1, 11.1, 19.2; `raw_flamegold.json` now has `exchange`/`result`; the three legacy `*_raw.json` are gone |
| Farmer's Delight optional | `neoforge.mods.toml:100-103` (optional, `[1.3.1,)`); `data/farmersdelight/tags/item/tools/knives.json` = 8 members |
| MUT (`mut`) optional, blanks hidden only when installed | spec 16.5 (both environments); 30 `smithing_mut_*.json` with `neoforge:mod_loaded: mut`; blank recipes with `neoforge:not` |
| Jar name and clean jar | `build/libs/bettergold-1.5.0.jar`, 1,089,068 bytes, 2026-10-03 09:32; spec 19.4 (`check_jar_clean.py` exit 0) |
| "1.5 adds 85 items (87 with FD)" | Arithmetic on two measured points: creative page 206 items (published for 1.4) -> 293 items (spec 12.8); 293 - 206 = 87, of which 2 are the new Farmer's Delight knives |

## 4. Judged 1.5 work but deliberately NOT written (insufficient basis)

1. Whether the mace's x1.2 stacks with Indigoseagold's x2 against the four listed mobs (would be x2.4) - open question, spec 12.7 no. 4, never answered. Both rules are stated separately; the interaction is not claimed.
2. Whether the metal mace keeps the vanilla smash attack (`MetalWeapons.java:61` extends `MaceItem`, so it is inherited vanilla; spec 12.7 no. 8 unanswered) - treated as unchanged vanilla behaviour, not announced.
3. The creative-page item count with `mut` installed (five blanks hidden) - only the no-`mut` figure (293) is measured.
4. Illusiongold armor retaliation chance (4% per piece -> 16% full set) - our arithmetic, not author-confirmed (spec 2.2 and section 7).
5. The trim `description.color` (`#E8B93A`) - out of scope, untouched (spec 17.2).
6. Client-side visibility of the shield knockback modifier - original-game behaviour, no player-facing claim (spec 16.2).
7. Beacon beam tinting by pillars - impossible with a plain pillar block; recorded as a limitation (spec 18.8).
8. Immersive Engineering / Metal Press - unchanged in 1.5; mentioning it would re-publish 1.4 content.

## 5. Pending author confirmation (stated in the documents, flagged here)

1. Indigoseagold block contact damage: 4 damage, at most once per 10 ticks - implemented and measured, but the number is our inference (spec section 7 no. 1).
2. Sediment slow: -1% movement speed per level (spec section 7 no. 2).
3. "Friendly mobs" for Illusiongold blocks = `!(entity instanceof Enemy)` (spec section 7 no. 4).
4. Soothe: 1 second, no stacking, duration takes the max (spec section 7 no. 8).
