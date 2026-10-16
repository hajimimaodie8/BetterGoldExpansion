# Better Gold 1.6.0 Changelog

**TL;DR:** Two new metals - **Thornsgold** and **Echogold** - join the mod, which now ships **8 metals**. The mod also gets its first **in-game handbook** and **51 advancements**, plus two new status effects, a handful of loose items and a batch of fixes.

## Highlights

- **Two new metals** - Thornsgold and Echogold - each a complete line: material chain, **11 building blocks**, a **14-piece** upgrade run and a Farmer's Delight knife.
- **Two new status effects**: **Parasite** (cactus damage that pays part of it back to whoever applied it) and **Sonic Roar** (a warden-style sonic burst that catches everything in a 3x3x3 cube).
- **The mod's first in-game handbook** - the Alchemy Student's Handbook: **4 categories, 20 entries, 192 pages** (needs Patchouli).
- **51 advancements**, all visible from the start, on a rebuilt tree whose eight metal lines always appear in the same order.
- **16 new config keys** make the config file the single source of truth for every metal's on-hit and armor chances - and the config screen now labels them correctly.
- **The creative inventory's "Materials" section was reordered** into the order the author dictated (its first 21 slots).
- **Antique tools no longer turn Netherite Blocks or this mod's metal building blocks into Netherite Dust on the spot** - the dust still drops.
- **Ten item textures were redrawn** by the author: the eight metal swords, the Gold Door and the Chaos Coin String.

## New metals

- **Thornsgold** (signature material: **Glittering Vine**) - weapons and tools inflict **Parasite**: **cactus damage every second for 16 seconds, with the damage per second equal to the effect's level**; each tick has a **36% chance** to heal the attacker the same number of points back. Its blocks sting anything that steps on them, brushes against them, breaks them or right-clicks them. Its armor takes **25% less cactus damage per piece**, a full set is **immune to cactus damage**, and each worn piece has a **25% chance** to hand the attacker Parasite.
- **Echogold** (signature material: **Bundled Echo Shard**) - weapons and tools inflict **Sonic Roar**: **sonic-boom damage every second for 6 seconds, with the damage per second equal to the effect's level**, hitting **everything in a 3x3x3 around the target** with a sonic-boom particle burst. Its blocks hit anything that touches them for **3 sonic damage and knock it away from the block**. Its armor takes **25% less sonic-boom damage per piece**, and each worn piece has a **25% chance** to hand the attacker Sonic Roar.
- Both are built exactly like the rest of the mod: raw ore, ingot, nugget and an upgrade smithing template; the **11 building blocks** (block, bricks, brick stairs, brick slab, brick wall, pillar, door, trapdoor, bars, chain, lantern); the **14-piece gear run** (sword, mace, trident, bow, crossbow, axe, pickaxe, shovel, hoe, shield, helmet, chestplate, leggings, boots); and a Farmer's Delight knife. Both new pillars work as beacon bases, and their stats match the existing metals (4096 durability, mining speed 14, netherite mining tier, enchantability 24; armor 5/814, 10/1184, 8/1110, 5/962).

## New items and drops

- **Alchemy Materials Box** - the Gold Trader's fourth (Expert) tier sells one for **7 Gift Gold Tickets + 20 XP**, up to 999 times. Opening it always yields exactly one of the eight metals' signature materials.
- **Golden Rose Bush** - a two-block-tall flower. 1 Rose Bush ringed by 8 Gold Nuggets makes one; the bush crafts down into **2 Yellow Dye**. It can now also be planted on **Gold-Infused Dirt**, not only on farmland.
- **Glittering Vine** - drops from leaves and vines at **6% base, plus 6% per level of Fortune**, when you break them with **any of the eight metals'** tool or weapon. It also composts at **65%**.
- **Bundled Echo Shard** - 8 Echo Shards arranged around a Sculk Vein.
- **Buried Treasure** joins the Treasure Gift Box loot rotation (**12 tables** now, up from 11).

## The handbook (needs Patchouli)

- **Alchemy Student's Handbook** - craft it from 1 Book + 1 Gold Ingot. With Patchouli installed it is a real book: **4 categories, 20 entries and 192 pages**.
- It covers the alchemy chain and the core materials; every metal's gear (**9 chapters** - one for cross-mod links and the golden blanks, plus one per metal, **14 items per metal**, 2 recipes per page); golden food across **5 chapters** (crops, golden foods, Sturdygold foods, and the two Farmer's Delight chapters); and the Gold Trader and the antiques across **3 chapters**.
- Patchouli is an **optional** dependency. Without it the book is simply not registered and its crafting recipe does not exist - **nothing else changes**, and the mod loads and plays exactly as before.

## Advancements

- **51 advancements**, all visible from the start - none of them are hidden.
- Per metal the tree is a **four-tier chain** (core material -> ingot -> weapon or tool -> armor), hanging off one shared trunk: **Heir to the Old Alchemy** -> **What Noble Gold Needs I** -> **What Noble Gold Needs II** -> **Treasure of a Thousand-Mile Journey** -> **9 branches** (the eight metal lines plus *All Set, Smelt It, Taken!*).
- **Nine of them are challenges** - the eight armor steps plus the Sturdygold-on-a-skeleton one; the remaining 42 use the normal frame.
- **The requirement is "obtain X" by any means** - pick it up, trade for it, get it as a drop or craft it, all count. **Not one advancement checks a crafting action any more**, including the root, which now opens on *obtaining* the handbook rather than crafting it.
- **Farmer's Delight knives count**: the eight "obtain any kind of this metal's weapon or tool" advancements accept that metal's knife, and the two antique advancements accept the Antique Knife and the Netherite Antique Knife.
- **The eight metal lines always appear in the same top-to-bottom order** in the advancement screen (flamegold, sturdygold, thornsgold, echogold, indigoseagold, voodoogold, thundergold, illusiongold) instead of being reshuffled at every launch.
- The three Farmer's Delight advancements only load when Farmer's Delight is installed, so **48** normally and **51** with it.

## Changed

- **High Burn and Sediment now deal damage equal to the effect's level** - **1 point per second at level 1, 2 at level 2, 3 at level 3** - one point less per level than before. High Burn lights its target on fire again at every level.
- **Sixteen new config keys** - two per metal, eight metals - now drive the on-hit buff chances and the armor counterattack chances (plus Sturdygold's absorption interval multiplier). The old hard-coded values no longer decide anything at runtime. Illusiongold's chance keys keep their existing values (0.16 weapon / 0.04 armor per piece).
- **The config screen's labels were corrected**: the weapon-side entry now names the **shield** as well (`<metal> - Weapon/Tool/Shield Buff Chance`), and the armor-side entry states that it is a per-piece chance for the **four armor slots only** (`<metal> - Armor Buff Chance`). Key names, defaults, ranges and order are untouched, and Sturdygold's two entries keep their original wording.
- **The sonic-roar effect is displayed as "Sonic Roar"** (Chinese: 音咆). Its **id is unchanged** (`bettergold:echo_roar`) and the metal is still Echogold / 幽咆金 - only the display name changed.
- **Three leftover shapeless raw-ore recipes are gone** (Flamegold, Thundergold and Voodoogold). Each metal now has exactly one raw-ore recipe instead of two.
- **Golden Bone Meal now drops on hit, not only on kill.** Hitting a skeleton, stray, wither skeleton or bogged with a Sturdygold tool or weapon has an **80% chance to replace each entry** of that hit's gold-loot pool with Golden Bone Meal - so the meal turns up about 80% of the time. **Gift Gold Tickets are exempt** and are never replaced. The original on-kill drop is still there.
- **The handbook's equipment section was rebuilt**: the old "Equipment Upgrades" category (two entries, 42 pages, 6 tools and 4 armor pieces) is replaced by "**Gear Enhancement**" - one linkage chapter plus one chapter per metal, **9 chapters, 86 pages, 14 items per metal** - and the five blank weapons (mace, trident, bow, crossbow, shield) are in the book now too. The retired "Material Chain" and "Upgrade Template" chapters are gone; the Knowledge chapter's first page is back, with a caption and body text on both halves.
- **The creative inventory's "Materials" section opens with a fixed 21-slot prefix**: the handbook, Mixed Crystal Pile, Alchemic Fuel, Golden Bone Meal, Chaos Coin String, the five golden blanks, Useless Old Antique, the Netherite Antique Upgrade Smithing Template, Netherite Dust, Small Netherite Scrap, Golden Cowrie Mold, Gift Gold Ticket, Treasure Gift Box, Curio Box, Golden Idol Box, Gourmet Box and Alchemical Materials Box. Everything after that is untouched.
- **Netherite antique tools no longer convert in place**: mining a Netherite Block or any of the eight metals' building blocks (89 blocks in all) with a Netherite Antique axe, pickaxe, shovel or hoe now leaves the block dropping itself, and the **Netherite Dust still drops on top** at the usual 6% + 6% per Fortune level (1 + Fortune / 2 items). Stone and everything else behave exactly as before, and the pickaxe's Ancient Debris -> 1-3 Netherite Scrap conversion is unaffected.
- **The handbook now says "any single piece of Sturdygold armor" doubles what you get from bartering with piglins**, which is what the code has always done.
- **Text**: the Useless Old Antique is now 没用的老古董 in Chinese (English stays `Useless Old Antique`), the Echogold weapon advancement is now 台上这鼓手有力气 / `The Drummer on Stage Sure Packs a Punch`, two gift-box handbook pages were reworded, and the English handbook no longer shows a Chinese sentence on the first page of "Knowledge of Noble Gold".

## Fixed

- **Voodoo armor's full-set poison immunity did not work.** Wearing all four Voodoogold armor pieces was supposed to make you immune to Poison, but the check sat behind an unrelated early-return for the Thundergold set, so it only ran if you *also* wore four Thundergold pieces. The two immunities are now independent checks - and you still need all four pieces of the relevant set for either one.
- **The Sonic Boom sound did not play.** It was gated on the damage actually landing, which made it stay silent for exactly the people most likely to test it - creative-mode players (whose `hurt` returns false), targets inside their invulnerability frames, and anything immune to that damage type. The sound is now tied to "a valid target was in range", not to the damage landing.
- **Echogold's blocks did not actually knock targets back.** The handbook promised "3 points of warden sonic boom damage and knock the target back", and only the damage existed. The knockback is now there: **0.75 horizontal / 0.15 vertical**, scaled from vanilla's warden sonic boom by this mod's 3 damage, reduced by the target's knockback resistance, and only applied when the damage lands.
- **Glittering Vine only dropped for seven of the eight metals.** It now drops for **every** metal, Sturdygold included.
- **The Chorus Cherry Branch recipe** now takes 1 Chorus Flower + **7 Cherry Saplings + 1 Ghast Tear** instead of 8 Cherry Saplings.
- **Indigoseagold trims render in colour again.** A 1.5.0-era decision had rolled that one palette back to the vanilla quartz greyscale, so Indigoseagold trims showed up white/grey. The author supplied the original artwork and it is restored byte for byte; the other eight palettes were never touched.
- **"All Set, Smelt It, Taken!" could never be unlocked.** Its criterion asked you to hold all eight raw materials at once instead of any one of them, so neither picking one up nor crafting one worked; it now unlocks as soon as a single raw material reaches your inventory.
- **"Seeds of Glorious Years" only unlocked inside a bastion remnant.** The structure condition is gone, so any way of getting Golden Eggplant Seeds counts.
- **The planting half of "Tilling My Golden Land" never fired.** Golden Carrots are planted through a custom event that bypasses vanilla's placement path, so the vanilla `placed_block` trigger never ran; it is now fired explicitly, and planting a golden crop on Gold-Infused Farmland unlocks the advancement.

## Compatibility & Requirements

| Component | Requirement / effect |
|---|---|
| Minecraft | **1.21.1** only |
| Loader | **NeoForge 21.1.228 or newer**, Java 21, client and server both required |
| Mod id / license | `bettergold` / MIT, by hjmmd_8 |
| **Patchouli** (optional) | Adds the **Alchemy Student's Handbook** (4 categories / 20 entries / 192 pages) and its recipe. Without it the book item and its recipe simply do not exist; nothing else changes. |
| **Farmer's Delight** (optional) | Adds the Thornsgold and Echogold knives and their smithing recipes, plus the three Farmer's Delight advancements. Without it: **48** advancements instead of 51. Its golden foods (5 of the handbook's chapters) come from it too. |
| **More Upgrade Templates** (mod id `mut`, optional) | With it installed, the five golden blanks and their upgrade recipes stay hidden and `mut`'s own golden mace / trident / bow / crossbow / shield become the upgrade bases. Without it, nothing is hidden. |
| **JEI** (optional) | Not required and not declared; the mod ships no JEI plugin, and 1.6.0 adds no JEI-specific content. |
| Immersive Engineering | No new content in 1.6.0. |

## Known notes / not in this release

- **Old worlds and advancements.** Advancement progress lives in your world; a datapack update replaces the *definitions* and does not re-evaluate what you already did. New worlds and new players unlock everything normally. In an old world, an item already sitting in your inventory will not re-trigger on its own - any single inventory change to that slot (move it, drop it and pick it back up, get another one) unlocks it immediately. "All advancements visible" is a definition-side setting and works in old worlds straight away.
- **Custom recipes the handbook cannot show.** Five handbook pages (the brewed hot cocoa on the brewing stand, and the Farmer's Delight cooking-pot dishes) show the finished item instead of a recipe grid, because Patchouli's recipe pages cannot express either station. The body text on those pages still describes the ingredients.
- **Two handbook cells are still placeholders** waiting on the author: one page holds a `〔待补〕` marker where a chapter name should be, and the fifth golden-food chapter uses a stand-in cover icon and has two cells reading "(not specified by the author)".
- **Three handbook nutrition numbers cannot be expressed by the code.** The book lists 7.5 / 10.5 / 19.5 hunger for three foods, but `nutrition` is an integer, so the code uses 7 / 10 / 19. The matching saturation values agree (one of them is 0.1 short). The book text is kept verbatim and the difference is recorded rather than silently rounded.
- **Two handbook effect descriptions do not match the code**: Sturdygold Chocolate Pie (the book lists Regeneration III + Resistance II, the code applies Resistance II + Speed II, matching its non-Sturdygold sibling), and the two Alchemical Meat Sandwiches (the book promises removed negative effects that no code branch applies). The book text is unchanged.
- **With `mut` installed**, the handbook's linkage chapter and the first smithing page of each metal reference blank-based recipes that are not loaded, so those pages can look empty. Without `mut` nothing is affected.
- **Three other sibling groups in the advancement tree** (the root, the Sturdygold weapon group and the Gold-Infused Dirt group) still appear in a launch-dependent order. Only the eight metal lines were pinned.
- **Human-eye items not verified by machine checks**: whether the Sonic Boom is comfortably audible at its volume level, the handbook's on-screen layout and icon rotation, the advancement tree's fork layout, and how the restored Indigoseagold trim palette looks in item form and worn.
- The 80% Golden Bone Meal figure is a sampled measurement, not an exact count.
- **Mod ids, block and item ids, language key names, config key names and datapack paths are unchanged from 1.5.0**, so existing worlds load normally. The one player-visible rename is the antique's display name noted above.

**Requirements:** Minecraft 1.21.1 | NeoForge 21.1.228 or newer | Java 21 | mod id `bettergold` | MIT license | by hjmmd_8
