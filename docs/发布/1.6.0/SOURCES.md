# Sources and Evidence (1.6.0 release note)

Every claim in the 1.6.0 documents traces to the items below. Line numbers marked `(spec)` are
`docs/1.6-规格.md` unless another file is named. `(code)` means the cited source file at the cited line.
`(measured)` means a reading taken by hand for this release-note round; everything else is quoted from the
archived verification rounds listed in the spec.

**This round wrote documents only.** No `gradlew` task, no `runServer` / `runClient` and no validator was
executed while preparing the release note; the A-level readings below are the archived ones, and the artifact
figures in section 3 were obtained by inspecting the jar that the last verified build produced.

## 1. Version boundary (1.5.0 -> 1.6.0)

```
$ git rev-parse HEAD        -> da0996e1a4ef321574c8ba35066448f8d595aaf8  (bgfix11, 2026-10-11 15:22:49)
$ git status --porcelain    -> only "?? .incoming_tmp/" (not created by this round)
$ git tag -l                -> (empty: the repository has no tags)

$ git log --oneline -1 b99e758   -> b99e758 ... (the mod_version bump commit)
$ git rev-parse b99e758^         -> 051294ca244845a7c3adeedfa72fd99a10f6c7ad
$ (git log --oneline 051294c..HEAD | Measure-Object).Count   -> 23
$ git diff --shortstat 051294c HEAD  -> 1037 files changed, 94247 insertions(+), 354 deletions(-)
```

**Chosen boundary: `051294c`**, the parent of the version-bump commit `b99e758` (i.e. the last 1.5.0 commit),
exactly as established in the earlier (HEAD `7150071`) release-note round. Basis: no tag exists, so the
boundary comes from `mod_version`; the bump to 1.6.0 happens inside `b99e758`, so the boundary is its parent;
and `b99e758` also carries the `bg-15y` / `bg-15w §九` / **1.5.0 release-note** work, so taking `b99e758`
itself would pull 1.5 content into 1.6.

The range reviewed is therefore **`051294c..HEAD` = 23 commits**. The earlier release-note round stopped at
HEAD `7150071` (9 commits into the range); the additional 14 commits (`0bdeaa4` … `da0996e`) are what this
rewrite adds: `bgfinal3`, `bg-book §九`, `bg-fix3`, `bg-book §九b`, `bg-fix3b`, `bg-book §十`,
`bg-fix3 追加轮 + bg-fix4`, `bgfix5`, `bgfix6`, `bgfix7`, the author's texture update, `bgfix8`, `bgfix9`,
`bgfix10` and `bgfix11`.

## 2. 1.5.0 release archive read (source of the "already published" list)

`docs/发布/1.5.0/` - `CHANGELOG-1.5.0.md`, `UPLOAD-METADATA-1.5.0.md`, `MODPAGE-1.5.0.md`,
`CHECK-1.4-vs-1.5.md`, `SOURCES.md`. 23 published claims extracted; see `CHECK-1.5-vs-1.6.md`.

## 3. Artifact inspected (not rebuilt this round)

```
$ (Get-Item build\libs\bettergold-1.6.0.jar).Length            -> 1,361,212 B  (built 2026-10-11 15:18:29)
$ (Get-FileHash build\libs\bettergold-1.6.0.jar -Algorithm SHA256).Hash
    -> 70094CE269079740CE071968FA5E4E55A87EDA9C16E6ABB0C89C49D9212F6B23
$ zipfile entry count                                          -> 2409
$ entries whose path contains "Probe"/"probe"                   -> 0
$ sha256(jar:assets/bettergold/lang/en_us.json) == sha256(workspace file)  -> True
$ sha256(jar:assets/bettergold/lang/zh_cn.json) == sha256(workspace file)  -> True
   workspace en_us.json = 77,849 B / 07AA2FA07EDD8942FA8CD8BFA441EFEA8BB2740E1532BB1D60143FF27097768F
   workspace zh_cn.json = 73,721 B / 695FA5A5347E1165F431A204D8CA6F1965D9D136DA0F4D560F299E8B3C972810
```

The jar is therefore consistent with HEAD `da0996e`: both language files inside it are byte-identical to the
working tree, and it contains no probe class. The `build/libs/bettergold-1.5.0.jar` (1,089,906 B) next to it
is a development leftover and is **not** part of the upload.

The archived validator readings from the last verified round (`(spec)` §31.10.9, HEAD `da0996e`) were:
`validate_metal_assets.py` exit 0 (595 items checked) · `validate_metal_data.py` exit 0 (307 language keys +
1660 JSON artifacts) · `validate_trim_assets.py` exit 0 (68 items) · `validate_advancements.py` exit 0
(51 advancements / 125 criteria / 102 language keys) · `check_jar_clean.py` exit 0 (2409 entries, `*Probe*` 0,
`'halt'` bytes 0, `'BG-PROBE'` 0) · `check_forced_chunks.py` exit 0 (`data.Forced` empty). Each of the six has
reachable exit-1 and exit-2 paths, proven by the perturbation matrices in `(spec)` §27.4, §28.6, §29.4,
§30.7 and §31.10.4.

## 4. Per-claim evidence

### 4.1 New metals, effects and gear (1.6 features)

| Claim in the changelog | Evidence |
|---|---|
| Two new metals Thornsgold / Echogold; the mod now ships 8 | `(code)` `material/AllMetals.java:122-152` (the two `MetalFamily.register` blocks) plus the eight ids in `(code)` `material/CreativeSections.java:35-44` `METAL_ORDER`; `(spec)` §6.1, §6.2 |
| Parasite: cactus damage every second, damage per second = effect level, 16 s per hit, 36% heal chance, no stack cap | `(code)` `material/MetalEvents.java:692-702` (`level = (amplifier + 1) * PARASITE_DAMAGE_PER_LEVEL`; `nextFloat() < PARASITE_HEAL_CHANCE` → `applier.heal(level)`); `(code)` `material/MetalFamily.java:122` `PARASITE_TICKS = 16 * 20`, `:128` `PARASITE_DAMAGE_PER_LEVEL = 1.0F`, `:132` `PARASITE_HEAL_CHANCE = 0.36F`; `(code)` `material/MetalEvents.java:1019-1024` `stackEffect` caps the amplifier only at 254; `(spec)` §6.2 |
| Sonic Roar: sonic damage every second, damage per second = effect level, 6 s, 3x3x3, particle burst | `(code)` `material/MetalEvents.java:711-735` (`AABB(pos).inflate(ECHO_ROAR_RADIUS)`, `ParticleTypes.SONIC_BOOM`, `level = (amplifier + 1) * ECHO_ROAR_DAMAGE_PER_LEVEL`); `(code)` `material/MetalFamily.java:125` `ECHO_ROAR_TICKS = 6 * 20`, `:130`, `:134` `ECHO_ROAR_RADIUS = 1`; `(spec)` §6.2, §16.4 |
| Thornsgold blocks sting on step-on / brush / break / right-click | `(code)` `material/MetalEvents.java:415-418` (`family.contactCactusThorns` → `hurt(cactus(), 1.0F)` with a per-entity 10-tick cooldown); the four actions: `(code)` `MetalEvents.java:847-849` (break), `:855-857` (right-click), `:862-868` + `:874-888` (player tick) and the entity-tick path, documented at `:881-882` |
| Echogold blocks deal 3 sonic damage and knock the target away from the block | `(code)` `material/MetalFamily.java:136` `CONTACT_SONIC_DAMAGE = 3.0F`, `:166-170` `CONTACT_SONIC_KNOCKBACK_HORIZONTAL/VERTICAL = 2.5/0.5 * (3.0/10.0)`; `(code)` `material/MetalEvents.java:419-422` (`family.contactSonicBoom` → `sonicContact`) and `applyBlockSonicKnockback`; `(spec)` §16.2 (derivation), §16.4 (A-level vertical error 0.0000) |
| Thornsgold armor 25%/piece cactus resistance, full set immune, 25%/piece Parasite retaliation; Echogold armor 25%/piece sonic resistance and 25%/piece Sonic Roar retaliation | `(code)` `material/AllMetals.java:122-130` (`.cactusResist() .cactusImmune()`) and `:145-152` (`.sonicResist() .echoRoarReflect()`); `(code)` `material/MetalEvents.java:1745-1748` (`min(pieces,4) * 0.25F`) and `:1759` (default counter chance 0.25); `(spec)` §三 item 5, §6.2 |
| Raw ore, ingot, nugget, upgrade smithing template; 11 building blocks; 14-piece gear run; Farmer's Delight knife; both pillars work as beacon bases; shared stats 4096 / 14 / netherite tier / 24 and armor 5/814, 10/1184, 8/1110, 5/962 | `(measured)` the handbook's eight building-block pages each list exactly **11** items for their metal (`(code)` `assets/bettergold/patchouli_books/alchemy_handbook/{en_us,zh_cn}/entries/golden_knowledge.json`, pages 3-10); the 14-item order is `(spec)` §19.2; the shared stats and the beacon bases are `(spec)` §6.1 first row, §6.2, and `docs/1.5-规格.md` §18 (the beacon-base generator list); the knife is `(code)` `data/bettergold/recipe/smithing_<family>_knife.json` (8 files, `farmersdelight:golden_knife` base + `mod_loaded` condition) |

### 4.2 New items and drops

| Claim | Evidence |
|---|---|
| Alchemy Materials Box: Expert tier, 7 Gift Gold Tickets + 20 XP, max 999, pool = the 8 signature materials | `(code)` `event/VillageTrades.java:70-78` (7 tickets + 20 XP; `trades.get(4)` = Expert), `:39` `MAX_USES` = 999; `(spec)` §6.2 "珍材盒池子" row `alchemy_pool_eight :: 8`, §21.3 item 12 |
| Golden Rose Bush: 1 Rose Bush + 8 Gold Nuggets → 1; → 2 Yellow Dye | `(code)` `data/bettergold/recipe/golden_rose_bush.json` (`NNN / NRN / NNN` with `minecraft:gold_nugget` and `minecraft:rose_bush`), `data/bettergold/recipe/yellow_dye_from_golden_rose_bush.json`; `(spec)` §17.2.3 |
| Golden Rose Bush can be planted on Gold-Infused Dirt | `(code)` `block/GoldInfusedDirtBlock.java` (`canSustainPlant` = TRUE for the golden rose bush, DEFAULT otherwise); `(code)` `registry/AllBlocks.java:201` registers it; `(spec)` §30.4 (A-level C1/C2/C3a-c: gold-infused dirt OK, farmland OK, plain dirt OK, grass OK, stone refused; wheat seeds still refused on dirt) |
| Glittering Vine: 6% + 6%/Fortune; **any of the eight metals'** tool or weapon; composts at 65% | `(code)` `registry/AllLootModifiers.java:235` `BASE_CHANCE = 0.06F`, `:237` `CHANCE_PER_FORTUNE = 0.06F`, `:286-290` `isOurTool` = `family != null && (isTool || isWeapon)` with the Sturdygold exemption removed (the old line is quoted in the javadoc at `:282`); `(code)` `data/neoforge/data_maps/item/compostables.json`; `(spec)` §8.1 (compost 0.65 A-level), §25.2 (author's 2026-10-08 ruling "all metals, no exemption"), §25.8 table 1 (8 families x 11 classes x 2 block types x 400 = 176 cells, Sturdygold moved from 0/400 to the same band as the other seven) |
| Bundled Echo Shard: 8 Echo Shards around a Sculk Vein | `(code)` `data/bettergold/recipe/bundled_echo_shard.json` |
| Buried Treasure joins the Treasure Gift Box rotation (12 tables) | `(code)` `item/GiftBoxItem.java:46-55` (12 entries, last = `chest("buried_treasure")`); `(spec)` §6.2 `treasure_tables_twelve :: count=12 hasBuriedTreasure=true`, §21.3 item 4 |

### 4.3 Handbook

| Claim | Evidence |
|---|---|
| Crafted from 1 Book + 1 Gold Ingot, only when Patchouli is present | `(code)` `data/bettergold/recipe/alchemy_student_handbook.json` (shapeless + `neoforge:mod_loaded: patchouli`); `(spec)` §11.1 item 1, §11.3 F9 |
| **4 categories / 20 entries / 192 pages** | `(measured)` parsed every entry JSON under `assets/bettergold/patchouli_books/alchemy_handbook/{en_us,zh_cn}/entries/`: **20 files / 192 pages / 4 category files** in each language, identical per-file page counts on both sides (auxiliary_materials 4, core_materials 18, gear_linkage 6, eight gear_* 10 each = 80, golden_knowledge 10, five golden_feast_* 10/10/14/10/10, merchant_intro 3, merchant_gift_box 7, merchant_antique_gear 10 → 4+18+6+80+10+54+20 = 192). Corroborated by `(spec)` §24.10 A-level `book_entries_twenty` / `book_total_pages_190`, §25.5 (+2 pages for the restored Knowledge page) and §29.6.2 A-level `book_pages_unchanged = 192` |
| 9 gear chapters, 14 items per metal, 2 recipes per page | `(spec)` §19.1, §19.2 (the fixed 14-item forge order and the 7 forge pages x 2 recipes), §19.3 D1 (Patchouli's `PageDoubleRecipe` has exactly `recipe` / `recipe2`), §19.10 A-level `gear_total_pages=86` and `forge_pages_checked=56` |
| 5 golden-food chapters and 3 merchant/antique chapters | `(spec)` §24.1 (5 chapters, 10+10+14+10+10 = 54 pages), §24.10 A-level `s10_five_entries_ok` and page counts `10·10·14·10·10`; `(spec)` §21.1 (merchant_intro 3 + merchant_gift_box 7 + merchant_antique_gear 10 = 20 pages), §21.11.2 A-level `s9_three_entries_ok` |
| Patchouli is optional; without it the book and its recipe do not exist and nothing else changes | `(spec)` §10.2 (paradigm B), §10.5 `[bgbook-dep-optional]` / `[bgbook-item-guarded]`, §10.9 A-level "not installed" environment; `AGENTS.md` red line 10 |
| The Knowledge chapter's first page is back, with a caption and body text on both halves | `(spec)` §25.5 (page restored, chapter 3 → 10 pages), §29.2 (right-hand caption present; body text `knowledge_1_right` restored) and §29.6.2 A-level `k3_p1_right_title_resolved` / `k3_p1_right_text_verbatim`; `(code)` `assets/bettergold/lang/zh_cn.json` key `bettergold.handbook.page.knowledge_1_right` |

### 4.4 Advancements

| Claim | Evidence |
|---|---|
| 51 advancements | `(measured)` 51 JSON files under `src/main/resources/data/bettergold/advancement/`; `(spec)` §14.1, §14.5, §31.10.9 validator line "成就 51 个 / criteria 125 条" |
| All visible from the start (no `hidden`) | `(spec)` §14.4 / §14.5 (jar scan `"hidden"` = 0); every JSON has no `"hidden": true` |
| Trunk: root → What Noble Gold Needs I → What Noble Gold Needs II → Treasure of a Thousand-Mile Journey → 9 branches | `(spec)` §22.6 item 3, §23.2 (generator-vs-artifact row-by-row table: `mixed_crystal_pile ← root`, `alchemic_fuel ← alchemy/mixed_crystal_pile`, `any_core_material ← alchemy/alchemic_fuel`, `treasure_parent = treasure/any_core_material` with exactly 9 children); `(measured)` the 51 advancement file list contains `alchemy/mixed_crystal_pile`, `alchemy/alchemic_fuel`, `treasure/any_core_material`, the eight `treasure/*` core-material nodes and `treasure/any_raw_metal` |
| Per metal a four-tier chain (core material → ingot → weapon → armor) | `(spec)` §22.6 item 1 (`armor` parent = `weapon` for all eight); `(spec)` §22.7 A-level `adv_metal_chain_all_eight` = 8/8 |
| Nine challenges (eight armor steps + the Sturdygold skeleton one), 42 normal-frame advancements | `(measured)` grep for `"frame"` across the 51 files returns exactly 9 `"challenge"` (`metal/<family>/armor.json` for all eight families plus `metal/sturdygold/skeleton.json`) and 42 files with no `frame` field; `(spec)` §22.6 item 2 (`bgach-frame-challenge` expectation 1 → 9) |
| Not one advancement checks a crafting action; the root opens on obtaining the handbook | `(measured)` grep for `recipe_crafted` across the 51 files returns **0** hits; `(code)` `data/bettergold/advancement/root.json` trigger = `minecraft:inventory_changed`; `(spec)` §22.5 and `[bgfix3-recipe-crafted-none]`; `(spec)` §22.7 A-level (root unlocks on obtaining the handbook, and no longer unlocks on `RECIPE_CRAFTED`) |
| Trigger types in use | `(measured)` `minecraft:inventory_changed` 119, `minecraft:placed_block` 3, `minecraft:player_hurt_entity` 1, `minecraft:villager_trade` 1, `minecraft:item_used_on_block` 1 |
| Farmer's Delight knives count for the eight weapon/tool advancements | `(spec)` §22.3 (each of the eight gets a `have_knife` criterion pointing at `#bettergold:<family>_knives`, `requirements` = `[["have","have_knife"]]`), §22.3 A-level 142 PASS / 0 FAIL vs 138 / 4 before, and the "not installed" environment (48 advancements, 0 parse errors, `size=0` tags) |
| The two antique advancements accept the Antique Knife and the Netherite Antique Knife | `(spec)` §25.3 (two more `have_knife` criteria over new `required:false` tags), §25.8 table 2 and table 4 (51 with FD / 48 without, 0 parse errors) |
| The eight metal lines always appear in the same order | `(spec)` §26 (`AdvancementNodeChildrenOrderMixin` + `AdvancementTreeOrder`, guarded on the single parent `bettergold:treasure/any_core_material`), §26.4 (the order source is `CreativeSections.METAL_ORDER`), §26.7 A-level (the same build run three times gives the same order 3/3, while the three other sibling groups still differ 3/3) |
| Only the three Farmer's Delight advancements are conditional, so 48 without FD | `(spec)` §14.4 (`challenge` exactly 1 — superseded by §22.6's 9 — and `fd_achievements_loaded=3/3`, "48 without"), §22.3 A-level 48 / 0 parse errors, §25.8 table 4 |

### 4.5 Changed

| Claim | Evidence |
|---|---|
| High Burn and Sediment deal damage equal to the effect's level (1 / 2 / 3), one point less per level than 1.5 | `(code)` `registry/AllEffects.java:330-334` `shiftedDamage(amplifier) = Math.max(1, amplifier + 1)` (the superseded `Math.max(0, amplifier)` is kept in the comment); `(measured)` `git show 051294c:.../registry/AllEffects.java` shows the boundary implementation `entity.hurt(..., amplifier + 2)` for both High Burn and Sediment, i.e. level + 1 points; `(spec)` §18.2.5 (A-level 11 / 22 / 33 damage over 11 s at levels 1/2/3) |
| High Burn lights its target on fire again at every level | `(code)` `registry/AllEffects.java:116-119` (`if (damage > 0.0F) { entity.hurt(...); setRemainingFireTicks(HIGH_BURN_FIRE_TICKS); }` with `shiftedDamage` now always >= 1); `(spec)` §18.4 A-level `L1 remainingFireTicks=1`, `onFire=true`; `(spec)` §16.3 |
| 16 new config keys; 25 in total; the config file is the single source of truth | `(code)` `config/Config.java` (the 16 `<family>{Weapon,Ability}…Chance` / interval keys + the 9 pre-existing ones); `(measured)` `run/config/bettergold-common.toml` lists exactly **25** keys, and the eight metal families appear in the order flamegold, voodoogold, thundergold, indigoseagold, illusiongold, thornsgold, echogold, sturdygold; `(spec)` §11.4 (table + formulas), §11.5 `[bgfix-config-16-keys]` (exactly 25 = 9 + 16), §25.4 (the 16 declarations were reordered to the author's 8-metal order, and the loaded spec — not the TOML file — decides the config-screen order), §29.1.6 (`define` triples 25/25, ranges 18/18, order identical after 14 `.comment` strings changed) |
| Illusiongold keeps 0.16 / 0.04 | `(spec)` §11.4 table, §19.4 row 10; `(spec)` §29.6.1 A-level startup readout `illusiongold[w=0.160 a=0.040]`, `sturdygoldArmorIntervalMultiplier=1.000` |
| The config-screen labels now name the shield on the weapon side and the four armor slots on the armor side; key names / defaults / ranges / order untouched; Sturdygold's two entries unchanged | `(code)` `config/Config.java` (14 `.comment(...)` blocks; lines 198/205/245/252/260/267/275/282/290/297/305/312/320/327 in the post-change file); `(measured)` `assets/bettergold/lang/en_us.json:132-145` reads `<Family> - Weapon/Tool/Shield Buff[ (Sonic Roar)] Chance` and `<Family> - Armor Buff[ (Sonic Roar)] Chance`; `(spec)` §29.1.3-§29.1.6 (`define` triples and ranges identical, only the 14 comment lists changed), §29.6.2b A-level (`cfg_labels_checked_14 = 14/14`, defaults 16/16, Sturdygold's two entries verbatim unchanged), `[bgfix8-config-sturdygold-untouched]` |
| Effect displayed as "Sonic Roar" (音咆); id `bettergold:echo_roar` and the metal name unchanged | `(measured)` `assets/bettergold/lang/en_us.json:453` `"effect.bettergold.echo_roar": "Sonic Roar"`; `(code)` `registry/AllEffects.java:279-291` (registration id `echo_roar`); `(spec)` §11.1 item 2, §11.5 `[bgfix-echo-id-unchanged]` / `[bgfix-echo-metal-name-untouched]`, §11.6.1 row 2 A-level |
| Three leftover shapeless raw-ore recipes removed | `git diff --name-status 051294c HEAD -- src/main/resources/data/bettergold/recipe` = `D flamegold_raw.json`, `D thundergold_raw.json`, `D voodoogold_raw.json`; the current `raw_<family>.json` files use type `bettergold:raw_sturdygold`; `(spec)` §6.1 |
| Golden Bone Meal on hit: 80% per pool entry, Gift Gold Ticket exempt, on-kill drop kept | `(code)` `event/ModEvents.java:132` `SKELETON_SQUEEZE_RATIO = 0.8F`, `:135-136` `isSqueezeExempt` (only `GIFT_GOLD_TICKET`), `:526` uses it; `(code)` `material/MetalEvents.java:1964` `SKELETON_GOLDEN_BONE_MEAL_CHANCE = 0.8F` and `:2034` (the retained on-kill roll); `(spec)` §18.2.4 (formula + A-level 24/30 and 29/30, ticket exemption, death drop kept) |
| Handbook equipment section rebuilt: "Gear Enhancement", 9 chapters, 86 pages, 14 items per metal, the five blank weapons included | `(spec)` §19.1 (arithmetic: 6 + 8x10 = 86), §19.2 (chapter table and the 14-item order), §19.6.1 (the retired two entries and their 42 pages), §19.10 A-level `gear_total_pages=86`, `forge_pages_checked=56`; `(code)` the 9 `gear_*.json` entries exist in both languages (`(measured)`) |
| The retired "Material Chain" and "Upgrade Template" chapters are gone | `(spec)` §22.4 (the two entries `metal_tour` (9 pages) and `upgrade_templates` (5 pages) removed, entries 18 → 16, pages 157 → 143, generator `RETIRED_BY_BGFIX3`), `[bgfix3-old-skeleton-gone]`; `(measured)` neither `metal_tour.json` nor `upgrade_templates.json` exists in either language |
| Creative Materials section: fixed 21-slot prefix in the author's order | `(code)` `material/CreativeTabSections.java` `MATERIAL_PREFIX_ORDER` (21 ids in the author's order, `golden_shield_blank` annotated "待作者确认"); `(spec)` §28.1-§28.3 and §28.5 A-level (`creative_material_prefix_21`, `creative_material_tail_40`, `creative_prefix_differs_from_baseline`, total cells 422 / Materials cells 61 before and after, only the first 21 reordered) |
| Netherite antique tools no longer convert Netherite Blocks or the eight metals' building blocks in place, but the dust still drops (89 blocks) | `(code)` `event/ModEvents.java:376-377` (`conversionExempt` guards the `clear()` / `setDroppedExperience(0)` lines only), `:401-404` `isDustConversionExempt` = `NETHERITE_BLOCK || MetalFamily.of(block) != null`, `:349` `chance = 0.06F + 0.06F * fortune`, `:335-343` (the untouched Ancient Debris → 1-3 scrap path); `(spec)` §21.4 (the full criterion, 8 x 11 + 1 = 89 blocks, and `n = 1 + fortune / 2`), §21.11.1 A-level (netherite block / metal bricks / metal lantern: self-hit every time **and** dust 15·17·13 of 80; stone: 18 dust and **0** self-hits, i.e. conversion still happens) |
| Handbook wording: "any single piece of Sturdygold armor" doubles piglin barter | `(code)` `event/ModEvents.java:576` `wearingAnySturdygoldArmor` (four slots OR'd, no full-set requirement); `(measured)` `assets/bettergold/lang/en_us.json` `bettergold.handbook.page.gear_sturdygold_2_left` now reads "any single piece of"; `(spec)` §20.2 (author's ruling "change the book, not the code"), §21.3 item 3 |
| Text: `Useless Old Antique` rename, the Echogold weapon advancement retitle, two gift-box handbook pages reworded, English handbook no longer showing Chinese | `(measured)` `git diff 051294c HEAD` on the language files shows exactly **2 changed values in each file**: `item.bettergold.unwanted_antique` (zh 没人要的老古董 → 没用的老古董; en `Unwanted Old Antique` → `Useless Old Antique`) and `trim_material.bettergold.unwanted_antique` (en `Old Antique` → `Useless Old Antique`); `assets/bettergold/lang/en_us.json:524` `advancements.bettergold.echogold_weapon.title` = `The Drummer on Stage Sure Packs a Punch` (old: `... about the drummer`); `(spec)` §31.2 (the six changed keys and the new English), §31.10.1 (the `knowledge_1_summary` English), §31.9 A-level 11 PASS / 0 FAIL and §31.10.5 A-level 6 PASS / 0 FAIL reading the values through `I18n` |

### 4.6 Fixed

| Claim | Evidence |
|---|---|
| Voodoo armor's full-set poison immunity did not work and is fixed | `(spec)` §19.4 row 8 and §19.5 (the disease course with the old code kept verbatim, the two independent guards, `[bgbook8-voodoo-poison-independent]`), §19.10 A-level `10 PASS / 1 FAIL` → `11 PASS / 0 FAIL` with the other ten readings identical; `(code)` `material/MetalEvents.java#onLivingTick` |
| Sonic Boom sound decoupled from the damage landing | `(spec)` §18.2.2 (criterion and why), §18.3 `[bgfix2-sonic-decoupled]` / `[bgfix2-sonic-decoupled-echo]`, §18.4 A-level brick B 0 → 16; `(code)` `material/MetalEvents.java:721-735` (`sawVictim` replaces `hitAny`) |
| Echogold block knockback 0.75 / 0.15 | `(spec)` §16.2 (table and the vanilla `SonicBoom.java:79-83` source), §16.4 A-level (vertical error 0.0000; horizontal residual 0.4000 is vanilla's own hit reaction); `(code)` `material/MetalFamily.java:166-170` |
| Glittering Vine now drops for every metal | `(code)` `registry/AllLootModifiers.java:286-290`; `(spec)` §25.2 and §25.8 table 1 (Sturdygold 0/400 → in band; shield cells still 0 because `isWeapon` excludes shields, which `(spec)` §22.2 records as a pre-existing comment/implementation mismatch, not a new defect) |
| Chorus Cherry Branch recipe: 1 Chorus Flower + 7 Cherry Saplings + 1 Ghast Tear | `(code)` `data/bettergold/recipe/chorus_cherry_branch.json`; `(spec)` §11.1 item 4, §11.6.1 row 1 |
| Indigoseagold trim palette restored byte for byte | `(spec)` §20.1.3 (source == drop point == jar entry, all `9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d`, 120 B), §20.1.5 A-level 9 PASS / 0 FAIL (both the item-form and worn-form atlases differ from quartz 4/4 and 36/36), §20.1.4 `[bgfinal3-indigosea-palette-restored]` / `[bgfinal3-indigosea-not-quartz]`; the other eight palettes and `trim_material/indigoseagold.json` were not touched (§20.1.3 "没动的清单") |
| "All Set, Smelt It, Taken!" could never unlock; criterion fixed to "any single raw material" | `(spec)` §30.2 (the `InventoryChangeTrigger` `items.size() == 1` OR vs `!= 1` AND semantics with source lines, the generator fix `c_inv(RAW_MATERIALS)` → `c_inv([RAW_MATERIALS])`), §30.8 A-level A1-A4 (one material: old false / new true; all eight: true both ways); `(measured)` `treasure/any_raw_metal.json` now has one inventory predicate over the eight raw ids |
| "Seeds of Glorious Years" structure gate removed | `(spec)` §30.3 (the `LocationPredicate#matches` structure branch and the conflicting `nether_bridge` loot table source), §30.8 A-level B1/B2; `(measured)` `agriculture/eggplant_seeds.json` no longer carries a `player` condition |
| The planting half of "Tilling My Golden Land" now fires | `(spec)` §20.3 (the vanilla `BlockItem#place` / `ItemUsedOnLocationTrigger` source basis and the added `CriteriaTriggers.PLACED_BLOCK.trigger`), §20.3.4 A-level 9 PASS / 0 FAIL vs 8 / 1 with the three lines removed, plus two negative controls; `(code)` `event/ModEvents.java:797-804` |

### 4.7 Textures

| Claim | Evidence |
|---|---|
| Ten item textures redrawn by the author (eight metal swords, the Gold Door, the Chaos Coin String) | `(measured)` `git show --stat 03e2fe6` = exactly those ten PNGs, all modified, 0 insertions / 0 deletions: `item/{flamegold,sturdygold,thornsgold,echogold,indigoseagold,voodoogold,thundergold,illusiongold}_sword.png`, `item/gold_door.png`, `item/chaos_coin_string.png`; `(measured)` `git diff --name-status 051294c HEAD` on those two paths is `M`, i.e. both existed before 1.6 and were redrawn, not added. Commit date 2026-10-09, message "贴图更新（作者自绘，2026-10-09）" |

### 4.8 Compatibility and requirements

| Claim | Evidence |
|---|---|
| Minecraft 1.21.1 only; NeoForge 21.1.228+; Java 21; mod id `bettergold`; MIT; client and server both required | `(code)` `gradle.properties` (`minecraft_version`, `neo_version`, `mod_license`, `mod_id`), `META-INF/neoforge.mods.toml` |
| Patchouli optional, adds the handbook, absent → book and recipe do not exist | `(spec)` §10.2 (paradigm B), §10.5, §10.9 A-level |
| Farmer's Delight optional, adds the two knives + their smithing recipes + three advancements + the FD golden foods; absent → 48 advancements | `(code)` `data/bettergold/recipe/smithing_<family>_knife.json` (8, `farmersdelight` conditions) and the five FD golden-food handbook entries (`(measured)` present in the book, `(spec)` §24.9 item 6 records that the "not installed" branch for those chapters was not re-tested); advancement counts `(spec)` §14.4, §22.3, §25.8 table 4 |
| `mut` optional, hides the five blanks and their upgrade recipes and uses its own golden weapons as bases | `(code)` `material/CreativeTabSections.java` `materialsCandidates()` excludes the five blanks when `mut` is loaded; the recipe files carry `neoforge:mod_loaded: mut` / `neoforge:not`; `(spec)` §19.4 row 15 |
| JEI needs no update: no JEI dependency is declared and no JEI plugin is shipped | `(code)` `build.gradle:133-138` - the JEI API / runtime lines are all commented out; `(code)` `META-INF/neoforge.mods.toml` declares only `farmersdelight` and `patchouli`; `git diff --name-only 051294c HEAD` contains no JEI-related file. The 1.6 text therefore claims only that nothing is required and nothing changed |
| Immersive Engineering: no new content in 1.6.0 | `git diff 051294c HEAD` touches no IE integration file; standing note carried over from the 1.5.0 metadata |

## 5. Judged 1.6 work but deliberately NOT written (insufficient basis)

1. **Whether the mace's x1.2 stacks with Indigoseagold's x2** against the four listed mobs (would be x2.4).
   Open question from 1.5 (`docs/1.5-规格.md` §12.7 no. 4), still unanswered. Not claimed.
2. **Whether the metal mace keeps the vanilla smash attack** (`MetalWeapons` extends `MaceItem`, so it is
   inherited vanilla). Treated as unchanged vanilla behaviour, not announced.
3. **The creative-page item count for 1.6** was never measured. The 1.5 figure (293) is not restated and no
   1.6 figure is claimed. (The Materials **section** size - 61 cells - is measured, but that is a section, not
   the page.)
4. **"Right-click opens the handbook" as a verified experience.** The last two A-level attempts recorded
   `screen=null` (`(spec)` §12.7 item 1, §19.10); an earlier round did record `GuiBookLanding` (§10.9). The
   changelog therefore describes **what the book contains**, never the click itself.
5. **Old-world advancement migration end to end with a real `ServerPlayer`** (`(spec)` §18.6 item 5). The
   public note is written from the source-level mechanism and phrased as "one inventory change in that slot",
   not as a tested procedure.
6. **Whether the handbook's echo-roar caption sounds right / the 10-tick Sonic Boom sound is too noisy in real
   play** - judgement calls (`(spec)` §18.6 item 8, §29.7 item 1). No claim made.
7. **The positive "inside a bastion remnant" path for Golden Eggplant Seeds after the gate was removed.**
   `(spec)` §30.3 B3 / §30.8 records that the environment never produced a positive structure sample, so the
   changelog only says the gate is gone, never that bastion behaviour was re-tested.
8. **The English-side feel of the new strings** (achievement titles, handbook prose). `I18n` readings prove
   *what the game displays* (`(spec)` §31.9, §31.10.5) - not that the wording reads well.
9. **The handbook's on-screen layout** (caption size, icon rotation, whether the 11-item strips are crowded)
   - `(spec)` §21.12, §24.9 item 5, §25.10 item 6, §29.7 item 10.
10. **The advancement tree's fork layout and toast appearance** - vanilla auto-layout, machine checks only
    cover parents, frames and unlock behaviour (`(spec)` §22.10 item 6, §26.10 item 1, §30.9 item 1).
11. **The restored Indigoseagold trim's actual look** (colours, contrast against the other eight palettes,
    the two armour layers) - `(spec)` §20.1.5 states only "which sprite is drawn and that it differs from
    quartz pixel by pixel".
12. **Whether the config-screen item names render the way the A-level readings suggest.** `ValueSpec
    .getTranslationKey()` is null in NeoForge 21.1.228 and the screen adds its own fallback, so the final
    label source cannot be pinned by a probe (`(spec)` §29.7 item 3). Both the comment line and the language
    value were changed for this reason.
13. **The `mut` / no-Patchouli variants of the new Materials 21-slot prefix** (the prefix table uses ids, so
    missing items are skipped, but neither environment was run) - `(spec)` §28.9 items 3 and 4.
14. **Golden figurine smelting** - checked and deliberately excluded: `git diff 051294c HEAD -- src/main/
    resources/data/bettergold/recipe` contains no figurine file.
15. **Immersive Engineering** - unchanged in 1.6; mentioned only as a standing "no new content" note
    (row 23 of the check).

## 6. Pending author decisions (stated in the documents where relevant, listed here)

1. **Three handbook cells still wait on the author**: the `〔待补〕` chapter name in the gift-box chapter
   (`(spec)` §21.5), the fifth golden-food chapter's cover icon, and the two "(not specified by the author)"
   cells (`(spec)` §24.4). All three are pinned by assertions so they cannot be silently filled in.
2. **Three handbook hunger values cannot be expressed by the code** - 7.5 / 10.5 / 19.5, because
   `FoodProperties.Builder.nutrition` takes an `int` (`(spec)` §24.6). Accept the integer, add a half-point by
   another route, or leave it as documented.
3. **Two handbook effect descriptions do not match the code**: Sturdygold Chocolate Pie (book says
   Regeneration III + Resistance II; code applies Resistance II + Speed II) and the two Alchemical Meat
   Sandwiches (book promises removed negative effects with no matching code branch) - `(spec)` §24.7 items 41
   and 29/37. Book text kept verbatim.
4. **Two handbook recipe pages the book cannot show**: the brewing-stand hot cocoa and the three Farmer's
   Delight cooking-pot dishes are shown as spotlight pages because Patchouli has no page type for those
   stations (`(spec)` §24.3 G1/G2). A custom page type would be needed to show the grids.
5. **The "Gold Door" reading of the author's 金门** in the Materials ordering - the id is uniquely determined
   by set equality, but the wording differs from the language key (`(spec)` §28.2, three names flagged
   "待作者确认").
6. **The building-block order inside the Knowledge chapter's body text** still follows the author's original
   sentence (bars / door / trapdoor / chain / lantern), while the display strip now uses the newer order
   (door / trapdoor / bars) - `(spec)` §25.6 note, restated in §31.10.8 item 2. Both are recorded, neither was
   changed.
7. **The Yellow Dye question** - the Golden Rose Bush crafts down into `minecraft:yellow_dye` x2 per the
   request body; the follow-up asking whether it was meant to be a fuel is unresolved (`(spec)` §17.5 item 2).
8. **The `trim_material` suffix question** was answered "no change needed" by the author for 1.6
   (`(spec)` §31.10), so `Useless Old Antique` stays without a `Material` suffix.

## 7. Unverified / human-eye items (never written into the public text)

- The Sonic Boom sound **being audible** depends on the client's "Hostile Creatures" volume slider
  (`(spec)` §18.6 item 2). The changelog claims the sound is *emitted*, not that it is heard.
- Handbook page layout, the icon rotation, the advancement tree's fork layout, the banner tooltip's
  readability, the English-client appearance of the handbook, and the restored Indigoseagold trims in worn
  form are all human-eye items (§7.2, §10.10, §14.6, §20.1.5, §21.12, §24.9, §25.10, §26.10, §29.7, §30.9).
- The 80% Golden Bone Meal figure is a sampled measurement, not an exact count (`(spec)` §18.6 item 4).
- The five Farmer's Delight golden-food handbook chapters were never tested with Farmer's Delight absent
  (`(spec)` §24.9 item 6).
- No `runServer` / `runClient` and no validator was executed for this release-preparation round; all A-level
  readings quoted here come from the archived rounds under `docs/bg*-证据/`.

## 8. Reproduce

```powershell
cd E:\mc\mcmod\bettergold-template-1.21.1
git rev-parse HEAD                       # da0996e1a4ef321574c8ba35066448f8d595aaf8
git status --porcelain
git tag -l
git log --oneline 051294c..HEAD
git diff --shortstat 051294c HEAD
git show --stat 03e2fe6                  # the ten redrawn textures

# artifact currently on disk (not rebuilt for this round)
(Get-Item build\libs\bettergold-1.6.0.jar).Length
(Get-FileHash build\libs\bettergold-1.6.0.jar -Algorithm SHA256).Hash

# handbook shape (20 entries / 192 pages / 4 categories, both languages)
#   parse every assets/bettergold/patchouli_books/alchemy_handbook/{en_us,zh_cn}/entries/*.json
#   and sum len(pages)

# language-file diff against the 1.5.0 boundary
git show 051294c:src/main/resources/assets/bettergold/lang/zh_cn.json
git show 051294c:src/main/resources/assets/bettergold/lang/en_us.json
#   -> keys 363 -> 722, 0 removed, exactly 2 values changed in each file

# if a full re-verification is wanted (NOT run for this release note):
.\gradlew.bat compileJava runData processResources jar --rerun-tasks --console=plain
foreach ($s in "validate_metal_assets","validate_metal_data","validate_trim_assets",
                "validate_advancements","check_jar_clean","check_forced_chunks") {
  python "tools\asset-generator\$s.py" }
```
