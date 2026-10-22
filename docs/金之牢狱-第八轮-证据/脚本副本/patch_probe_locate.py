# -*- coding: utf-8 -*-
"""把 GpjProbe 的 locate() 换成「玄武岩里 ourStarts==0 / 对照 fortress>0」的版本（bytes 级）。"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'src\main\java\com\hjmmd_8\bettergold\probe\GpjProbe.java'
txt = open(P, 'rb').read().decode('utf-8')

OLD = '''    // ------------------------------------------------------------------ ③ locate
    private static Map<String, Object> locate(Holder<Structure> holder) {
        Map<String, Object> out = new LinkedHashMap<>();
        ChunkGenerator gen = lvl.getChunkSource().getGenerator();
        HolderSet<Structure> set = HolderSet.direct(holder);
        Registry<Structure> reg = srv.registryAccess().registryOrThrow(Registries.STRUCTURE);
        Holder<Structure> fortress = reg.getHolder(ResourceKey.create(
                Registries.STRUCTURE, ResourceLocation.fromNamespaceAndPath("minecraft", "fortress"))).orElse(null);
        for (String biome : WANT_BIOMES) {
            BlockPos spot = findBiome(biome);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("spot", spot == null ? null : List.of(spot.getX(), spot.getY(), spot.getZ()));
            if (spot == null) {
                row.put("found", "no-biome-spot");
                out.put(biome, row);
                continue;
            }
            Pair<BlockPos, Holder<Structure>> found = gen.findNearestMapStructure(lvl, set, spot, 100, false);
            row.put("found", found == null ? null
                    : List.of(found.getFirst().getX(), found.getFirst().getY(), found.getFirst().getZ()));
            if (fortress != null && biome.equals("minecraft:basalt_deltas")) {
                Pair<BlockPos, Holder<Structure>> ctl =
                        gen.findNearestMapStructure(lvl, HolderSet.direct(fortress), spot, 100, false);
                row.put("controlFortress", ctl == null ? null
                        : List.of(ctl.getFirst().getX(), ctl.getFirst().getY(), ctl.getFirst().getZ()));
            }
            out.put(biome, row);
            LOG.info("[gpj] locate {} spot={} found={}", biome, spot, row.get("found"));
        }
        return out;
    }

    private static BlockPos findBiome(String biome) {
        for (int r = 0; r <= 4096; r += 256) {
            for (int gx = -r; gx <= r; gx += 256) {
                for (int gz = -r; gz <= r; gz += 256) {
                    BlockPos p = new BlockPos(gx, 64, gz);
                    if (biome.equals(biomeAt(p))) {
                        return p;
                    }
                }
            }
        }
        return null;
    }
'''

NEW = '''    // ------------------------------------------------------------------ ③ 玄武岩里没有 start
    private static Map<String, Object> locate(Holder<Structure> holder) {
        Map<String, Object> out = new LinkedHashMap<>();
        Registry<Structure> reg = srv.registryAccess().registryOrThrow(Registries.STRUCTURE);
        Holder<Structure> fortress = reg.getHolder(ResourceKey.create(
                Registries.STRUCTURE, ResourceLocation.fromNamespaceAndPath("minecraft", "fortress"))).orElse(null);
        for (String biome : WANT_BIOMES) {
            BlockPos spot = findBiomeRegion(biome);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("spot", spot == null ? null : List.of(spot.getX(), spot.getY(), spot.getZ()));
            if (spot == null) {
                row.put("note", "no 3x3-chunk region of this biome found");
                out.put(biome, row);
                continue;
            }
            int chunks = 0;
            int basaltChunks = 0;
            int ours = 0;
            int forts = 0;
            List<String> ourStartBiomes = new ArrayList<>();
            int ccx = spot.getX() >> 4;
            int ccz = spot.getZ() >> 4;
            for (int cx = ccx - 12; cx <= ccx + 12; cx++) {
                for (int cz = ccz - 12; cz <= ccz + 12; cz++) {
                    chunks++;
                    BlockPos mid = new BlockPos(cx * 16 + 8, 64, cz * 16 + 8);
                    if ("minecraft:basalt_deltas".equals(biomeAt(mid))) {
                        basaltChunks++;
                    }
                    StructureStart a = findStartLoose(mid, holder.value());
                    if (a != null && a.isValid()) {
                        ours++;
                        ourStartBiomes.add(biomeAt(new BlockPos(a.getChunkPos().getMinBlockX() + 8,
                                40, a.getChunkPos().getMinBlockZ() + 8)));
                    }
                    if (fortress != null) {
                        StructureStart b = findStartLoose(mid, fortress.value());
                        if (b != null && b.isValid()) {
                            forts++;
                        }
                    }
                }
            }
            row.put("chunks", chunks);
            row.put("basaltChunks", basaltChunks);
            row.put("ourStarts", ours);
            row.put("ourStartBiomes", new LinkedHashSet<>(ourStartBiomes));
            row.put("fortressStarts", forts);
            out.put(biome, row);
            LOG.info("[gpj] locate {} spot={} chunks={} basaltChunks={} ourStarts={} fortStarts={}",
                    biome, spot, chunks, basaltChunks, ours, forts);
        }
        return out;
    }

    /** 在一块 3×3 区块全部是该群系的窗口里找一个中心（避开边界混群系）。 */
    private static BlockPos findBiomeRegion(String biome) {
        for (int r = 0; r <= 6144; r += 384) {
            for (int gx = -r; gx <= r; gx += 384) {
                for (int gz = -r; gz <= r; gz += 384) {
                    BlockPos p = new BlockPos(gx, 64, gz);
                    boolean all = true;
                    for (int dx = -1; dx <= 1 && all; dx++) {
                        for (int dz = -1; dz <= 1; dz++) {
                            if (!biome.equals(biomeAt(p.offset(dx * 16, 0, dz * 16)))) {
                                all = false;
                                break;
                            }
                        }
                    }
                    if (all) {
                        return p;
                    }
                }
            }
        }
        return null;
    }

    private static StructureStart findStartLoose(BlockPos mid, Structure structure) {
        for (int y = 32; y <= 64; y += 8) {
            StructureStart s = lvl.structureManager().getStructureAt(
                    new BlockPos(mid.getX(), y, mid.getZ()), structure);
            if (s.isValid()) {
                return s;
            }
        }
        return null;
    }
'''

if NEW.split('\n')[1] in txt:
    print('already patched')
    sys.exit(0)
if OLD not in txt:
    print('OLD not found')
    sys.exit(1)
open(P, 'wb').write(txt.replace(OLD, NEW, 1).encode('utf-8'))
print('patched locate()')
