# Better Gold 1.6.0 Changelog

**TL;DR:** Two new metals - **Thornsgold** and **Echogold** - join the mod, the mod gets its first in-game **handbook**, and **51 advancements** arrive with it. Two new status effects, a handful of loose items, and a batch of fixes come with them. The mod now ships **8 metals**.

## Added

### Two new metals

- **Thornsgold** (signature material: Glittering Vine) - weapons and tools inflict **Parasite** (寄生): **1 to 3 cactus damage every second for 16 seconds**, and the attacker has a **36% chance to heal the same number of points back**. Its blocks answer anything that steps on them, brushes against them, breaks them or right-clicks them. Its armor takes **25% less cactus damage per piece** and a full set is **immune to cactus damage**; each piece worn also has a **25% chance** to hand the attacker Parasite.
- **Echogold** (signature material: Bundled Echo Shard) - weapons and tools inflict **Sonic Roar** (音咆): **1 to 3 sonic-boom damage every second for 6 seconds**, hitting **everything in a 3x3x3 around the target**, with a sonic-boom particle burst. Its blocks hit anything that touches them for **3 sonic damage and knock it away from the block**. Its armor takes **25% less sonic-boom damage per piece** and each piece has a **25% chance** to hand the attacker Sonic Roar.

Both are built exactly like the rest of the mod: raw ore, ingot, nugget and an upgrade smithing template; **11 building blocks** (block, bricks, brick stairs, brick slab, brick wall, pillar, door, trapdoor, bars, chain, lantern); the **10-piece gear run** (sword, mace, trident, bow, crossbow, axe, pickaxe, shovel, hoe, shield); four armor pieces; and a Farmer's Delight knife. Both new pillars work as beacon bases. Their stats match the existing metals (4096 durability, mining speed 14, netherite mining tier, enchantability 24; armor 5/814, 10/1184, 8/1110, 5/962).

### The loose pieces

- **Alchemy Materials Box** - the Gold Trader's fourth (Expert) tier sells one for **7 Gift Gold Tickets + 20 XP**, up to 999 times. Opening it always yields exactly one of the eight metals' signature materials.
- **Golden Rose Bush** - a two-block-tall flower. 1 Rose Bush ringed by 8 Gold Nuggets makes one; the bush crafts down into **2 Yellow Dye**.
- **Glittering Vine** - drops from leaves and vines at **6% base, plus 6% per level of Fortune**, but only when you break them with a *special* metal tool or weapon (any of the seven; **Sturdygold does not qualify**). It also composts at **65%**.
- **Bundled Echo Shard** - 8 Echo Shards arranged around a Sculk Vein.
- **Buried Treasure** joins the Treasure Gift Box loot rotation (**12 tables** now, up from 11).

### A handbook (needs Patchouli)

- **Alchemy Student's Handbook** - craft it from 1 Book + 1 Gold Ingot. With Patchouli installed it is a real book: **4 categories, 17 entries and 148 pages**, covering the alchemy chain, the core materials, every metal's equipment (the 14-piece smithing run, 2 recipes per page), golden food, and the trader and antiques.
- Patchouli is an **optional** dependency. Without it the book is simply not registered and the handbook recipe does not exist - **nothing else changes**, and the mod loads and plays exactly as before.

### 51 advancements

- A full tree grew out of the alchemy theme: **5 branches** off the root, **9** off "Treasures of a Thousand Miles", and one **three-way split** on the Sturdygold line.
- **All of them are visible from the start** - no hidden advancements.
- Wherever the wording used to say "craft X", the requirement is now "**obtain X**" **by any means** - pick it up, trade for it, get it as a drop, or craft it. The single exception is the gift-box advancement, which still asks for a trade.
- **One challenge** advancement (hit a skeleton with Sturdygold gear). The three Farmer's Delight ones only load when Farmer's Delight is installed, so **48** normally and **51** with it.

## Changed

- **Voodoo payout** is now **36% of the damage banked in the 6-second window + 1 damage per effect level** (config keys `voodooExtractRatio` = 0.36 and `voodooFlatPerLevel` = 1.0).
- **High Burn and Sediment damage per second now equals the effect's level**: level 1 = 1, level 2 = 2, level 3 = 3. (Somewhere in the 1.6 development line this had been shifted down one level; that is reverted.) High Burn lights its target on fire again at every level.
- **Sixteen new config keys** - two per metal, eight metals - now drive the on-hit buff chances, the armor counterattack chances and Sturdygold's absorption interval multiplier. The old hard-coded values **no longer decide anything at runtime**: the config file is the single source of truth, and the mod prints the values it actually loaded at startup. Illusiongold's chance keys keep their existing values (0.16 weapon / 0.04 armor per piece). The 16 new config-screen entries are translated into Chinese and English.
- **The sonic-roar effect is displayed as "Sonic Roar"** (Chinese: 音咆). The effect's **id is unchanged** (`bettergold:echo_roar`), and the **metal is still Echogold / 幽咆金** - only the display name changed.
- **Three leftover shapeless raw-ore recipes are gone** (Flamegold, Thundergold, Voodoo gold). Each metal now has exactly one raw-ore recipe instead of two.
- **Golden Bone Meal now drops on hit, not only on kill.** Hitting a skeleton (skeleton, stray, wither skeleton or bogged) with a Sturdygold tool or weapon has an **80% chance to replace each entry** of that hit's gold-loot pool with Golden Bone Meal - so the meal turns up about 80% of the time, and **Gift Gold Tickets are exempt** and never replaced. The original on-kill drop is still there: it was always "not only".
- **The handbook's equipment section was rebuilt.** The old "Equipment Upgrades" category (two entries, 42 pages, covering 6 tools and 4 armor pieces) is replaced by "**Equipment Enhancement**": one linkage / golden-blanks chapter plus one chapter per metal - **9 chapters, 86 pages, 14 items per metal** - and the five blank weapons (mace, trident, bow, crossbow, shield) are in the book now too.

## Fixed

- **Voodoo armor's full-set poison immunity did not work.** Wearing all four Voodoo gold armor pieces was supposed to make you immune to Poison. The check sat behind an unrelated early-return for the Thundergold set, so it only ran if you *also* wore four Thundergold pieces. The two immunities are now independent checks - and you still need all four pieces of the relevant set for either one.
- **The Sonic Boom sound did not play.** It was gated on the damage actually landing, which made it stay silent for exactly the people most likely to test it - creative-mode players (whose `hurt` returns false), targets inside their invulnerability frames, and anything immune to that damage type. The sound is now tied to "a valid target was in range", not to the damage landing.
- **Echogold's blocks did not actually knock targets back.** The handbook promised "3 points of warden sonic boom damage and knock the target back", and only the damage existed. The knockback is now there: **0.75 horizontal / 0.15 vertical**, scaled from vanilla's warden sonic boom (2.5 / 0.5 at 10 damage) by this mod's 3 damage, reduced by the target's knockback resistance, and only applied when the damage lands.
- **Glittering Vine dropped for the wrong tools.** It was dropping for every metal including Sturdygold. It now requires a *special* metal tool or weapon (the seven non-Sturdygold metals).
- **The Chorus Cherry Branch recipe** now takes 1 Chorus Flower + **7 Cherry Saplings + 1 Ghast Tear** instead of 8 Cherry Saplings.
- **Indigoseagold's trim palette is still open.** A 1.5.0-era decision rolled that one palette back to the vanilla quartz greyscale, so Indigoseagold trims currently render white/grey. The cause is pinned down - every other suspect (trim atlas, model indices, the runtime trim model layer, file format) checked out - but restoring it needs either the original palette file back or an explicit go-ahead to paint a replacement.

## Notes

- **Old worlds and advancements:** advancement progress lives in your world (`<world>/advancements/<uuid>.json`), and a datapack update replaces the *definitions* - it does not re-evaluate what you have already done. **New worlds and new players unlock everything normally.** In an **old world**, an item that is already sitting in your inventory will not re-trigger on its own, but any single inventory change to that slot (move it, drop it and pick it back up, get another one) unlocks it immediately. "All advancements visible" is a definition-side setting and works in old worlds straight away.
- **With MoreUpgradeTemplate (`mut`) installed**, the five golden blanks and their upgrade recipes stay hidden as before, and `mut`'s own golden mace / trident / bow / crossbow / shield become the upgrade bases. One rough edge: the handbook's linkage chapter and the first two smithing pages of each metal still point at the blank-based recipes, which are not loaded in that environment, so those pages can look empty. Without `mut` nothing is affected.
- The mod's item and block ids, language key **names**, config key **names** and datapack paths are unchanged from 1.5.0, so existing worlds load normally.

**Requirements:** Minecraft 1.21.1 | NeoForge 21.1.228 or newer | Java 21 | mod id `bettergold` | MIT license | by hjmmd_8
