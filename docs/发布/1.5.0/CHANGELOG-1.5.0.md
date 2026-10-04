# Better Gold 1.5.0 Changelog

**TL;DR:** Two new metals - **Indigoseagold** and **Illusiongold** - join the mod, and every metal now has a full weapon line: mace, shield, bow, crossbow and trident. Two new status effects and a batch of fixes come with them.

## Added

### Two new metals

- **Indigoseagold** (signature material: Indigo Ocean Heart) - Sediment on hit, suffocation and drowning armor, faster water movement, no underwater mining penalty.
- **Illusiongold** (signature material: Chorus Cherry Branch) - a 16% chance to Soothe a target for 1 second; its blocks grant Regeneration.

Each metal is a complete line: raw ore, ingot, nugget and an upgrade smithing template; block, bricks, brick stairs, brick slab, brick wall, pillar, door, trapdoor, bars, chain and lantern (11 blocks); sword, axe, pickaxe, shovel and hoe, plus a Farmer's Delight knife; helmet, chestplate, leggings and boots - 24 items and 11 blocks each. Stats match the existing metals (4096 durability, mining speed 14, netherite mining tier, enchantability 24; armor 5/814, 10/1184, 8/1110, 5/962; one piece makes piglins neutral), and both new pillars work as beacon bases.

- **Signature material recipes**: 1 Heart of the Sea + 4 Lapis Blocks -> Indigo Ocean Heart; 1 Chorus Flower + 8 Cherry Saplings -> Chorus Cherry Branch. Raw ore uses the familiar 9-slot recipe with the Golden Cowrie swapped for the metal's signature material.

### Two new status effects

- **Sediment** (Indigoseagold): `level + 1` suffocation damage every second and -1% movement speed per level, stacking without limit; 16 seconds per hit.
- **Soothe** (Illusiongold): the target loses its AI for 1 second. Its original AI state and target come back when the effect ends, is removed early, or the target dies or leaves the world.

### A full weapon line for all six metals (30 weapons)

| Weapon | Values | Special |
|---|---|---|
| Mace | 9 damage, 0.8 attack speed | Final damage x1.2 |
| Shield | Durability 3072 (Sturdygold) / 2048 | See below |
| Bow | Full draw in 16 ticks | Base arrow damage 4.0 (vanilla 2.0) |
| Crossbow | Charge 1 second (20 ticks) | Bolt speed 4.5 |
| Trident | 13 damage, 1.3 attack speed | Throw damage 15 (vanilla 8) |

- Durability and enchantability: **Sturdygold 6144 / 30**, the other five metals **4096 / 24**.
- Every weapon fires its own metal's on-hit effect, and this now works for **ranged and thrown hits too** - arrows and bolts use the bow that fired them, and a thrown trident still counts while it is out of your hand. Metal tridents also have their own in-hand 3D model.
- **Shields**: all six ignore the axe shield-disable; blocking hands the attacker that shield's metal effect; any mod shield in either hand gives +10% knockback resistance (shown in the tooltip).
- **Sturdygold absorption hearts**: a Sturdygold armor piece or shield grants 1 absorption heart (2 points) every 16 seconds, up to 4 points per armor piece plus 4 for the shield - **a maximum of 20**. The **five golden blanks** (Golden Mace / Bow / Crossbow / Trident / Shield Blank) are the crafting bases for the upgrade recipes.

### Armor, tool and block traits

- **Indigoseagold armor**: 25% suffocation and drowning resistance per piece (a full set is immune), a 25% chance per piece to give the attacker Sediment, +25% water movement efficiency and **+25% swim speed** per piece.
- **Indigoseagold tools**: ignore the underwater mining penalty and deal **double damage** to endermen, blazes, snow golems and striders. **Indigoseagold blocks** refill an axolotl's air and hurt those four mobs on contact (4 damage, at most once every 10 ticks).
- **Illusiongold blocks** grant Regeneration (6 seconds) to players and friendly mobs.
- **Two new armor trim materials** (Indigoseagold and Illusiongold) - the mod now ships **7**.

## Changed

- **Voodoo payout**: the damage banked inside the 6-second window now pays out as **36% of the damage taken + 1 damage per effect level**. New config keys `voodooExtractRatio` (0.36) and `voodooFlatPerLevel` (1.0).
- **High Burn lasts 16 seconds** (was 36) from Flamegold weapon hits and armor retaliation.
- **Creative inventory**: still one "Better Gold" page with five banners, now holding **293 items** - 1.5 adds 85 items (87 with Farmer's Delight). Each metal's gear is a 14-piece run: sword, mace, trident, bow, crossbow, axe, pickaxe, shovel, hoe, shield, helmet, chestplate, leggings, boots.

## Fixed

- **Raw ore recipes**: the raw-ore recipes of Flamegold, Voodoogold and Thundergold produced Sturdygold Raw, and an old shapeless recipe duplicated them. Each metal now has exactly one raw-ore recipe, it produces the right item, and it **returns your glass bottle**.
- **Armor trim colors**: every trim material of the mod rendered white in the inventory; each material now uses its own palette index and the trim layers exist in the item atlas.
- **Beacon bases**: Indigoseagold and Illusiongold pillars could not be used as beacon bases; both now can.

## Mod integration (all optional)

- **Farmer's Delight**: the two new knives belong to the Farmer's Delight integration and only exist when it is installed.
- **MoreUpgradeTemplate** (mod id `mut`): with it installed, the five golden blanks and the 30 blank-based upgrade recipes stay hidden and `mut`'s own golden mace / trident / bow / crossbow / shield upgrade into the six metal versions instead. Without it nothing changes - craft the blanks and upgrade them as usual.

**Requirements:** Minecraft 1.21.1 | NeoForge 21.1.228 or newer | Java 21 | mod id `bettergold` | MIT license | by hjmmd_8
