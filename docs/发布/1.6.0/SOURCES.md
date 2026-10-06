# Sources and Evidence (1.6.0 release note)

Every claim in the 1.6.0 documents traces to the items below. Line numbers marked `(spec)` are `docs/1.6-规格.md`
unless another file is named. `(code)` means the cited source file at the cited line.

## 1. Version boundary (1.5.0 -> 1.6.0)

```
$ git tag -l                                     -> (empty: the repository has no tags)
$ (git tag -l | Measure-Object).Count            -> 0

$ git log -L '/mod_version=/,+1:gradle.properties' --format="COMMIT %h %ad %s" --date=iso
COMMIT b99e758 2026-10-04 19:44:12 +0800 bg-15y / bg-15w §九 / 1.5.0 发布文案 / bg-16 1.6.0 全套
+mod_version=1.6.0
COMMIT 16ac37a 2026-10-02 16:58:00 +0800 1.5 完成：两套新金属 + 金制武器体系 + 武器轮收尾（bg-15w / bg-15x）
-mod_version=1.4.0
+mod_version=1.5.0
COMMIT b5f68d3 2026-09-30 20:51:16 +0800 1.4「新约」：三套新金属（烈燃金/巫毒金/结雷金）+ 创造页分区横幅 + 万坚金迁移
-mod_version=1.3.0
+mod_version=1.4.0

$ git log --oneline -3 b99e758        -> b99e758, 051294c, ce10311      # b99e758 的父 = 051294c
$ git log --format="%h %ad %s" --date=iso 051294c..HEAD
4856bb6 2026-10-06 14:35:32 +0800 bg-book §八「装备的强化」9 章（替换「装备的升级」类别）+ 修掉一条真 bug（全套巫毒金免疫中毒）
d4c38cf 2026-10-06 13:59:16 +0800 bg-fix2：六条"未生效"的取证与修复（第 1 条贴图待裁定，未动）
a1c42f2 2026-10-05 21:12:06 +0800 1.6 追加轮（bg-book §七 / bg-fix §八·§九 / bg-ach §七）
0e8eee9 2026-10-05 18:30:17 +0800 1.6 收尾三件：声波击退补全 / 成就英译 / 高燃 1 级不点燃
1e29837 2026-10-05 17:59:07 +0800 1.6 收尾四批：bg-fix 七条修正 + bg-ach 51 个成就 + 手册三章补全 + 幻惑金建材第 8 条
e6d9950 2026-10-04 22:03:27 +0800 bg-book 收尾补记：AGENTS.md 两处红线（UI 自动化建世界 / dev 常驻 Patchouli）与规格 §10.11
8d8341b 2026-10-04 22:01:23 +0800 bg-book 收尾：dev 环境常驻 Patchouli（作者裁定）+ 文档与红线同步
1d3f354 2026-10-04 20:59:50 +0800 bg-17 裁定落实（核心材料免疫仙人掌 / 弩真改 20 tick）+ bg-book 帕秋莉手册
b99e758 2026-10-04 19:44:12 +0800 bg-15y / bg-15w §九 / 1.5.0 发布文案 / bg-16 1.6.0 全套

$ git diff --shortstat 051294c HEAD   -> 681 files changed, 33305 insertions(+), 321 deletions(-)
$ git diff --name-status 051294c HEAD | group
    M = 73, A = 605, D = 3          (src/main/java: M=18 A=4; assets: A=316 M=5; data: A=159 M=30 D=3)
$ git status --porcelain              -> (empty: the working tree matches HEAD)
$ git rev-parse HEAD                  -> 4856bb671770c14c4d428c6288be7a1b9a88b60e
```

**Chosen boundary: `051294c`**, the parent of the version-bump commit `b99e758` (i.e. the last 1.5.0 commit).

Basis: (1) no tag exists, so the boundary comes from `mod_version`; the bump to 1.6.0 happens inside `b99e758`, so the
boundary is its parent. (2) `b99e758` also carries the `bg-15y` / `bg-15w §九` / **1.5.0 release-note** work
(482 files changed), so taking `b99e758` itself would pull 1.5 content into 1.6. (3) Cross-checks: `051294c` **has**
`docs/1.5-规格.md` but **has neither** `docs/发布/1.5.0/` **nor** `docs/1.6-规格.md`
(`git ls-tree -r --name-only 051294c -- <path>` empty for both); and `051294c`'s own message is
"bg-15w §8.3 整节重做：水中游泳速度改用 `neoforge:swim_speed`" - a 1.5 change. Range reviewed = `051294c..HEAD`, **9 commits**,
no uncommitted work.

No tag and no upload action exists anywhere in the range, so all nine commits are unreleased 1.6.0 content.

## 2. 1.5.0 release archive read (source of the "already published" list)

`docs/发布/1.5.0/` - `CHANGELOG-1.5.0.md`, `UPLOAD-METADATA-1.5.0.md`, `MODPAGE-1.5.0.md`, `CHECK-1.4-vs-1.5.md`,
`SOURCES.md`. 23 published claims extracted; see `CHECK-1.5-vs-1.6.md`.

## 3. Build, validators and artifact

```
$ .\gradlew.bat compileJava runData processResources jar --rerun-tasks --console=plain
BUILD SUCCESSFUL in 25s / 8 actionable tasks: 8 executed / exit 0
  (mixin smoke line present:
   [mixin]: Mixing CrossbowChargeDurationMixin from bettergold.mixins.json into net.minecraft.world.item.CrossbowItem)

$ python tools\asset-generator\validate_metal_assets.py   -> exit 0 (595 JSON / 0 problems; 8 families x item=29 block=10 armor=2)
$ python tools\asset-generator\validate_metal_data.py     -> exit 0 (bg-16 / bg-book / bg-append / bg-fix / bg-final / bg-fix2 / bg-book §八 sections all 0 problems)
$ python tools\asset-generator\validate_trim_assets.py    -> exit 0
$ python tools\asset-generator\validate_advancements.py   -> exit 0 (51 advancements / 114 criteria / 6 triggers / 102 lang keys)
$ python tools\asset-generator\check_jar_clean.py         -> exit 0 (0 *Probe* paths / 0 classes with 'halt' bytes / 0 'BG-PROBE' / 2388 files)
$ python tools\asset-generator\check_forced_chunks.py     -> exit 0 (data.Forced = [], length 0)

$ Get-FileHash build\libs\bettergold-1.6.0.jar -Algorithm SHA256
5BC5057F095AF99312DCEE8A6911F9B3C0C910722C17A0588BD4ED3E50272EF1
   size 1,339,929 B (2026-10-06 14:50:15)
```

## 4. Per-claim evidence

| Claim | Evidence |
|---|---|
| Two new metals, ids, names, `mod_version` | `(code)` `src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java:122-152`; `gradle.properties` `mod_version=1.6.0`; `(spec)` §6.1, §6.2 |
| Both metals share the standard stats (no field overridden) | `(spec)` §6.1 first row, §6.2 "两族 Tier" row: `uses=4096 ench=24 speed=14.0 dmgBonus=4.5` (A-level) |
| 11 building blocks each / 10-piece gear run / 4 armor / FD knife | `(code)` `assets/bettergold/blockstates/thornsgold_*.json` = **11** and `echogold_*.json` = **11**; `(code)` `assets/bettergold/models/item/<family>*` = 40 each; `(spec)` §19.2's 14-item forge order; `validate_metal_assets.py` prints `item=29 block=10 armor=2` per family - note that those three numbers count **texture PNGs whose filename contains the family name** (`validate_metal_assets.py:260-264`), not items and not blocks, so they are not interchangeable with the blockstate/model counts |
| Both pillars work as beacon bases | `(spec)` `docs/1.5-规格.md` §18 (the beacon-base fix), and `(spec)` §6.1 records the two new families joining the generator's exhaustive tag list |
| Parasite: level = damage per second, 16 s, 36% heal chance | `(code)` `material/MetalEvents.java:696` `(amplifier + 1) * PARASITE_DAMAGE_PER_LEVEL`, `:699` `nextFloat() < PARASITE_HEAL_CHANCE`; `material/MetalFamily.java:122` `PARASITE_TICKS = 16 * 20`, `:128` `PARASITE_DAMAGE_PER_LEVEL = 1.0F`, `:132` `PARASITE_HEAL_CHANCE = 0.36F` |
| Thornsgold armor 25%/piece cactus resistance, full set immune; 25%/piece Parasite retaliation | `(code)` `material/AllMetals.java:122-130` (`.cactusResist() ... .cactusImmune()`), `material/MetalEvents.java:1745-1748` (`min(pieces,4) * 0.25F`) and `:1759` default counter chance 0.25; `(spec)` §三 item 5, §6.2 "盔甲 25% / 四件 100%" row |
| Sonic Roar: level = damage per second, 6 s, 3x3x3, particles | `(code)` `material/MetalEvents.java:719` `(amplifier + 1) * ECHO_ROAR_DAMAGE_PER_LEVEL`; `material/MetalFamily.java:125` `ECHO_ROAR_TICKS = 6 * 20`, `:130` `ECHO_ROAR_DAMAGE_PER_LEVEL = 1.0F`, `:134` `ECHO_ROAR_RADIUS = 1`; `(spec)` §6.2 "幽咆 3×3×3" row |
| Echogold armor 25%/piece sonic resistance + 25%/piece Sonic Roar retaliation | `(code)` `material/AllMetals.java:145-152` (`.sonicResist() .echoRoarReflect()`), `material/MetalEvents.java:1745-1748`, `:1759` |
| Echogold blocks: 3 sonic damage + knockback away from the block | `(code)` `material/MetalFamily.java:136` `CONTACT_SONIC_DAMAGE = 3.0F`, `:166-170` `CONTACT_SONIC_KNOCKBACK_HORIZONTAL/VERTICAL = 2.5/0.5 * (3.0/10.0)`; `material/MetalEvents.java` `sonicContact` / `applyBlockSonicKnockback`; `(spec)` §16.2 (the derivation) and §16.4 (A-level: K1/K2 `Δdelta` vertical err 0.0000) |
| Alchemy Materials Box: Expert tier, 7 Gift Gold Tickets + 20 XP, max 999, pool = 8 core items | `(code)` `event/VillageTrades.java:70-78` (7 tickets + 20 XP + `MAX_USES` = 999 at `:39`); `(spec)` §6.2 "珍材盒池子" row `alchemy_pool_eight :: 8` |
| Golden Rose Bush: 1 Rose Bush + 8 Gold Nuggets -> 1; -> 2 Yellow Dye | `(code)` `data/bettergold/recipe/golden_rose_bush.json`, `data/bettergold/recipe/yellow_dye_from_golden_rose_bush.json`; `(spec)` §17.2.3 |
| Glittering Vine: 6% + 6%/Fortune, seven special metals only, 65% compost | `(code)` `registry/AllLootModifiers.java:229` `BASE_CHANCE = 0.06F`, `:231` `CHANCE_PER_FORTUNE = 0.06F`, `:279` `family.isSpecialMetal()`; `(code)` `data/neoforge/data_maps/item/compostables.json`; `(spec)` §6.2 (probabilities), §8.1 (compost 0.65, A-level), §18.2.3 |
| Bundled Echo Shard: 8 Echo Shards around a Sculk Vein | `(code)` `data/bettergold/recipe/bundled_echo_shard.json` |
| Buried Treasure in the Treasure Gift Box rotation (12 tables) | `(code)` `item/GiftBoxItem.java:46-54` (12 entries, last = `chest("buried_treasure")`); `(spec)` §6.2 `treasure_tables_twelve :: count=12 hasBuriedTreasure=true` |
| Handbook: craft from 1 Book + 1 Gold Ingot when Patchouli is present | `(code)` `data/bettergold/recipe/alchemy_student_handbook.json` (shapeless + `neoforge:mod_loaded: patchouli`); `(spec)` §11.1 item 1, §11.3 F9 |
| Handbook: 4 categories / 17 entries / 148 pages | `(code)` jar inspection: `assets/bettergold/patchouli_books/alchemy_handbook/{zh_cn,en_us}/entries` = 17 each, `categories` = 4 each, summed `pages` = 148; `(spec)` §19.1 arithmetic (32 + 30 + 86 = 148) and §19.10 A-level `entries=17 pages=148` |
| Handbook content covers 14 items per metal, 2 recipes per page | `(spec)` §19.1, §19.2, §19.3 D1 (7 forge pages x 2 recipes = 14), §19.10 A-level `forge_pages_checked=56` |
| Patchouli optional; book not registered without it | `(spec)` §10.2 (paradigm B), §10.5 `[bgbook-dep-optional]` / `[bgbook-item-guarded]`; `(spec)` §10.9 A-level "not installed" environment; `AGENTS.md` red line 10 |
| 51 advancements, tree shape 5 / 9 / 3-way, no `hidden` | `(code)` `src/main/resources/data/bettergold/advancement/**` = 51 files, jar scan `"hidden"` = 0; `(spec)` §14.1 (tree), §14.5 (shape assertions), §18.2.6 |
| "Craft X" -> "Obtain X", one exception (gift box keeps `villager_trade`) | `(spec)` §17.4 items 2 / 2b / 2c; `(spec)` §18.2.6 (`inventory_changed` 47 advancements / `recipe_crafted` only `root.json`) |
| One challenge advancement; 3 Farmer's Delight advancements, so 48 without FD | `(spec)` §14.4 (`challenge` exactly 1, `fd_achievements_loaded=3/3`, "没装时应为 48") |
| Voodoo payout 36% + 1/level, keys `voodooExtractRatio` / `voodooFlatPerLevel` | `(code)` `config/Config.java:68` (0.36 default); `(spec)` §19.4 row 7 (`VoodooAccumulator#settleDamage` = window damage x ratio + flatPerLevel x level) |
| High Burn and Sediment damage/s = effect level | `(code)` `registry/AllEffects.java:330` `shiftedDamage` = `Math.max(1, amplifier + 1)`; `(spec)` §18.2.5 (A-level 11 / 22 / 33 damage over 11 s at levels 1/2/3) |
| High Burn re-ignites at every level | `(code)` `registry/AllEffects.java:116` (`if (damage > 0.0F) { entity.hurt(...); setRemainingFireTicks(HIGH_BURN_FIRE_TICKS); }`); `(spec)` §18.4 A-level `L1 remainingFireTicks=1`, `onFire=true` |
| 16 new config keys, 25 total, config file is the single source of truth | `(code)` `config/Config.java` (16 new keys); `(spec)` §11.4 (table + formulas) and §11.5 `[bgfix-config-16-keys]` (exactly 25 = 9 + 16); measured `run/config/bettergold-common.toml` = 25 keys |
| `StartupSelfCheck` prints the loaded values | `(spec)` §11.4 last paragraph, §11.6.1 row 7 (`BETTERGOLD-STARTUP bgfix16 ...`) |
| Illusiongold chance keys keep 0.16 / 0.04 | `(spec)` §11.4 table; `(spec)` §19.4 row 10 |
| 16 config-screen entries translated | `(spec)` §17.2.2; measured: 16 added `bettergold.configuration.<key>` entries in `zh_cn.json`, plus 5 pre-existing keys backfilled (21 added i18n keys total) |
| Effect display name "Sonic Roar" (音咆); id and metal name unchanged | `(code)` `assets/bettergold/lang/zh_cn.json` `effect.bettergold.echo_roar` = 音咆, `en_us.json` = `Sonic Roar`; `(spec)` §11.1 item 2, §11.5 `[bgfix-echo-id-unchanged]` / `[bgfix-echo-metal-name-untouched]`; `(spec)` §11.6.1 row 2 A-level |
| Three legacy shapeless raw-ore recipes removed | `git diff --name-status 051294c HEAD -- src/main/resources/data/bettergold/recipe` = `D flamegold_raw.json`, `D thundergold_raw.json`, `D voodoogold_raw.json`; current `raw_flamegold.json` etc. use type `bettergold:raw_sturdygold`; `(spec)` §6.1 lists `flamegold_raw.json / thundergold_raw.json / voodoogold_raw.json` under `b99e758` |
| Golden Bone Meal on hit, 80% per pool entry, Gift Gold Ticket exempt, on-kill drop kept | `(code)` `event/ModEvents.java` `SKELETON_SQUEEZE_RATIO`, `rollGoldLootAgainstSkeleton`, `isSqueezeExempt`; `material/MetalEvents.java` `SKELETON_GOLDEN_BONE_MEAL_CHANCE = 0.8F` in `onLivingDrops`; `(spec)` §18.2.4 (formula + A-level 24/30 and 29/30, ticket exemption, death drop kept) |
| Chorus Cherry Branch: 1 Chorus Flower + 7 Cherry Saplings + 1 Ghast Tear | `(code)` `data/bettergold/recipe/chorus_cherry_branch.json`; `(spec)` §11.1 item 4, §11.6.1 row 1 (old grid no longer matches) |
| Voodoo full-set poison immunity was broken and is fixed | `(spec)` §19.4 row 8, §19.5 (disease course, old code kept verbatim, the two independent guards), §19.10 A-level `10 PASS / 1 FAIL` -> `11 PASS / 0 FAIL`; `(code)` `material/MetalEvents.java#onLivingTick` |
| Sonic Boom sound decoupled from damage | `(spec)` §18.2.2 (judgement + why), §18.3 `[bgfix2-sonic-decoupled]` / `[bgfix2-sonic-decoupled-echo]`, §18.4 A-level brick B 0 -> 16 |
| Sonic knockback magnitude 0.75 / 0.15 | `(spec)` §16.2 (table + `SonicBoom.java:79-83`), §16.4 A-level (vertical err 0.0000, horizontal residual 0.4000 = vanilla's own hit reaction) |
| Glittering Vine tool restriction | `(code)` `registry/AllLootModifiers.java:279`; `(spec)` §11.1 item 3, §18.2.3, §18.4 (7 families true/true, sturdygold false/false) |
| Handbook "Equipment Enhancement" rebuild: 9 chapters / 86 pages / 14 items | `(spec)` §19.1, §19.2, §19.6.1 (the retired 42 pages), §19.10 A-level `gear_total_pages=86` and `entries=17 pages=148` |
| Old worlds need one inventory change (advancement semantics) | `(spec)` §18.2.6 items 1-3 with `InventoryChangeTrigger.java:86 / :91-106 / :108` and `AbstractContainerMenu#broadcastChanges`; `(spec)` §18.6 item 5 (only source-level evidence, no real `ServerPlayer` walk-through) |
| `mut` rough edge in the handbook | `(spec)` §19.3 D2, §19.9 item 4 |
| Jar name / size / SHA256 / entry count | Section 3 above |
| No probe / `halt` / `BG-PROBE` in the jar | `check_jar_clean.py` exit 0 plus an independent byte-level scan of every `.class` in the extracted jar (0 hits for ASCII `halt`, 0 for `BG-PROBE`) |
| Ids / language key names / config key names / datapack paths unchanged | `(spec)` 本轮范围边界 statements (e.g. §11.2 F7, §19.5's "未动" list); `AGENTS.md` red lines 1 / 9; measured: diffing `zh_cn.json` / `en_us.json` between `051294c` and HEAD gives **363 -> 656 keys, 0 values changed, 0 keys removed** in both files (293 additive keys each) |
| The effect display-name rename never overwrote a 1.5.0 string | measured: `effect.bettergold.echo_roar` **does not exist** at `051294c` (the 1.5.0 effect keys are `cold_resistance`, `high_burn`, `voodoo`, `tremble`, `sediment`, `soothe`); the key was created in 1.6 and renamed inside 1.6 by `bg-fix` |
| Raw-ore recipes still return the glass bottle (a 1.5 claim, still true, deliberately not restated) | `(code)` `recipe/RawSturdygoldRecipe.java:141-146` (`getRemainingItems` -> `new ItemStack(Items.GLASS_BOTTLE)`) |
| Platform metadata | `gradle.properties` (`minecraft_version=1.21.1`, `neo_version=21.1.228`, `mod_license=MIT`, `mod_id=bettergold`); `META-INF/neoforge.mods.toml` |

## 5. Judged 1.6 work but deliberately NOT written (insufficient basis)

1. **Whether the mace's x1.2 stacks with Indigoseagold's x2** against the four listed mobs (would be x2.4). Open question
   from 1.5 (`docs/1.5-规格.md` §12.7 no. 4), still unanswered. The 1.6 documents do not claim it.
2. **Whether the metal mace keeps the vanilla smash attack** (`MetalWeapons` extends `MaceItem`, so it is inherited vanilla).
   Treated as unchanged vanilla behaviour, not announced.
3. **The creative-page item count for 1.6** was never measured. The 1.5 figure (293) is not restated and no 1.6 figure is
   claimed. (`docs/1.6-规格.md` has no 1.6 creative-page total.)
4. **The "right-click opens the handbook" click itself was not reproduced** in the last two rounds
   (`docs/1.6-规格.md` §12.7 item 1 and §19.10 both record `screen=null`). The code path was untouched in both rounds and an
   earlier A-level round did record `GuiBookLanding` (§10.9), but since the latest attempts failed to reproduce it, the
   1.6.0 documents describe **what the book contains**, never "right-click to open" as a verified experience.
5. **Old-world advancement migration was never walked end to end with a real `ServerPlayer`** (§18.6 item 5). The public note
   is written strictly from the source-level mechanism, and is phrased as "one inventory change in that slot", not as a
   tested procedure.
6. **Whether the 10-tick Sonic Boom sound is too noisy in real play** is a judgement call (§18.6 item 8); no claim made.
7. **The three "vanilla triggers cannot express this" advancements** (§14.7): the golden-egg criterion is the closest
   semantic fit but was not author-approved; the golden-carrot planting half needs a code change. Only the *player-visible
   outcome* ("obtain X by any means") is announced, and the golden-carrot caveat is not mentioned in the public text.
8. **Immersive Engineering** - unchanged in 1.6; mentioned only as a standing "no new content" note (row 23 of the check).
9. **Golden figurine smelting** - checked and deliberately excluded: `git log --follow` shows it was last touched in `b5f68d3`
   (1.4) and `git diff 051294c HEAD --` on those recipe files is empty, so it is not a 1.6 change.
10. **The `mut` rough edge in the handbook** is stated in the changelog as a known limitation; the changelog does **not**
    claim the pages are broken beyond "can look empty", because that environment was not re-tested this round.
11. **Indigoseagold's trim palette** - stated as still open, with the four exonerated suspects listed; the documents do not
    promise a restoration date or a method.

## 6. Pending author decisions (stated in the documents where relevant, listed here)

1. **Indigoseagold trim palette** - the original file back (A), explicit permission to paint a replacement (B), or accept the
   current greyscale (C). `docs/1.6-规格.md` §18.2.1.
2. **Piglin barter doubling: any one Sturdygold piece, or the full set?** Code says any piece; the handbook says full set.
   §19.4 row 3. The 1.6 documents follow the **handbook wording only where the handbook describes itself**, and the
   changelog does not restate the doubling rule at all.
3. **Handbook with `mut` installed** - the linkage chapter and the first two smithing pages per metal point at
   blank-based recipes that are not loaded. §19.3 D2.
4. **Yellow "fuel" from the Golden Rose Bush** - implemented as `minecraft:yellow_dye` x2 per the request body; the
   follow-up question asks whether it was meant to be a fuel. §17.5 item 2. The changelog says "Yellow Dye", which is what
   the code does.
5. **The handbook's single spotlight icon slot** - "middle-top icon plus a lower icon" cannot be expressed on one Patchouli
   page. §17.5 item 1 / §17.3.2.

## 7. Unverified / human-eye items (never written into the public text)

- The Sonic Boom sound **being audible** depends on the client's "Hostile Creatures" volume slider (§18.6 item 2). The
  changelog claims the sound is *emitted*, not that it is heard.
- Handbook page layout, the 20-tick icon rotation, the advancement tree's fork layout, the banner tooltip's readability,
  the English-client appearance of any of this, and Indigoseagold trims in worn form are all human-eye items
  (§7.2, §10.10, §14.6, §18.6 item 8, §19.10).
- The 80% Golden Bone Meal figure is a 40-sample measurement, not an exact check (§18.6 item 4).
- No `runServer` / `runClient` was executed for this release preparation round; all A-level readings quoted here come from
  the archived rounds under `docs/bg*-证据/`.

## 8. Reproduce

```powershell
cd E:\mc\mcmod\bettergold-template-1.21.1
git rev-parse HEAD
git status --porcelain
git tag -l
git log -L '/mod_version=/,+1:gradle.properties' --format="COMMIT %h %ad %s" --date=iso
git log --format="%h %ad %s" --date=iso 051294c..HEAD
git diff --shortstat 051294c HEAD

.\gradlew.bat compileJava runData processResources jar --rerun-tasks --console=plain
foreach ($s in "validate_metal_assets","validate_metal_data","validate_trim_assets",
                "validate_advancements","check_jar_clean","check_forced_chunks") {
  python "tools\asset-generator\$s.py" }
Get-FileHash build\libs\bettergold-1.6.0.jar -Algorithm SHA256
```
