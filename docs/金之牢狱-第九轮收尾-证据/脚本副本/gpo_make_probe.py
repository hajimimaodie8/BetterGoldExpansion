# -*- coding: utf-8 -*-
"""第十轮（2026-10-23）：由归档 GpnProbe.java.txt 生成 GpoProbe.java。

做的事（全部替换都断言"恰好命中一次"，命中不了就报错退出）：
  1) 类名 / 输出目录 / 日志前缀：Gpn -> Gpo；
  2) **洪泛换位集实现、不封顶**（旧口径 reachAir=200000 / parentFlood=40000 都是封顶值，
     会把"走得通"读成"到不了"——本轮 4 个 NG 里就可能有这种假阴性）；
  3) 每个出入口新增读数：外门口 3×3（空气/可达）、旧外门口、旧 45 格通道、父件模板、离其它件的最小空隙；
  4) 每座结构新增 pieceBboxes（件 bbox 全表，用于复核"相邻禁止"）。

跑法（工作区自带 Python）：<dsh python> probe\\gpo\\gpo_make_probe.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVID = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据")
SRC = os.path.join(ROOT, "docs", "金之牢狱-第九轮收尾-证据", "GpnProbe.java.txt")

t = open(SRC, encoding="utf-8").read()


def sub(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, "命中 %d 次（期望 %d）：%r" % (n, count, old[:90])
    t = t.replace(old, new)
    print("  ok  %-60s -> %d 处" % (old.strip().splitlines()[0][:60], count))


# ---- 1) 类名 / 路径 / 前缀
sub("GpnProbe", "GpoProbe", t.count("GpnProbe"))
sub('Path.of("probe", "gpn")', 'Path.of("probe", "gpo")')
sub("[gpn]", "[gpo]", t.count("[gpn]"))
sub("probe/gpm/report.json", "probe/gpo/report.json")

# ---- 2) 常数：去掉两个封顶
sub("""    private static final int SCAN_RADIUS = 20;      // 41×41 区块
    private static final int MAX_STRUCTURES = 8;
    private static final int MAX_FLOOD = 200_000;
    private static final int FORCE_PAD = 32;        // 新出入口最多搬 24 格 ⇒ 32 够
    private static final int REGION_PAD = 64;       // 洪泛区域 = start bbox + 64
    private static final int PARENT_FLOOD = 40_000;
    private static final int GAP_FLOOD = 120_000;""",
    """    private static final int SCAN_RADIUS = 20;      // 41×41 区块
    private static final int MAX_STRUCTURES = 8;
    private static final int FORCE_PAD = 32;        // 新出入口最多搬 24 格 ⇒ 32 够
    private static final int REGION_PAD = 64;       // 洪泛区域 = start bbox + 64（+96 会多生成上百个区块）
    // ★ 2026-10-23：reachAir / parentFlood **不再封顶**（旧值 20 万 / 4 万都真的打满了）。
    //   位集洪泛 ~1200 万格只要 1.5 MB；封顶会把"走得通"读成"到不了"（假阴性）。
    private static final int GAP_FLOOD = 400_000;   // 只有"确实到不了"时才跑的穿墙 BFS（诊断用）""")

# ---- 3) 洪泛：位集 + 最小 int 队列
OLD_FLOOD = """    private static Set<Long> flood(List<BlockPos> seeds, BoundingBox region, int max, boolean airOnly) {
        Set<Long> seen = new HashSet<>();
        ArrayDeque<BlockPos> q = new ArrayDeque<>();
        for (BlockPos s : seeds) {
            if (s == null || !region.isInside(s) || lvl.isOutsideBuildHeight(s)) {
                continue;
            }
            if (!passable(s, airOnly)) {
                continue;
            }
            long k = key(s);
            if (seen.add(k)) {
                q.add(s);
            }
        }
        while (!q.isEmpty() && seen.size() < max) {
            BlockPos p = q.poll();
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                long k = key(n);
                if (seen.contains(k) || !region.isInside(n) || lvl.isOutsideBuildHeight(n)) {
                    continue;
                }
                if (!passable(n, airOnly)) {
                    continue;
                }
                seen.add(k);
                q.add(n);
            }
        }
        return seen;
    }
"""
NEW_FLOOD = """    /** air-only / 非固体 洪泛（**位集、不封顶**：封顶会把"走得通"读成"到不了"）。 */
    private static Flood flood(List<BlockPos> seeds, BoundingBox region, boolean airOnly) {
        Flood f = new Flood(region);
        IntQueue q = new IntQueue();
        for (BlockPos s : seeds) {
            if (s == null || !region.isInside(s) || lvl.isOutsideBuildHeight(s)) {
                continue;
            }
            if (!passable(s, airOnly)) {
                continue;
            }
            if (f.mark(s)) {
                q.add(f.index(s));
            }
        }
        while (!q.isEmpty()) {
            BlockPos p = f.pos(q.poll());
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                if (!region.isInside(n) || lvl.isOutsideBuildHeight(n)) {
                    continue;
                }
                if (!passable(n, airOnly)) {
                    continue;
                }
                if (f.mark(n)) {
                    q.add(f.index(n));
                }
            }
        }
        return f;
    }

    /** 位集洪泛结果（区域 ~1200 万格 ⇒ 1.5 MB；同规模 HashSet<Long> 要 100 MB+ 且慢）。 */
    private static final class Flood {
        final BoundingBox region;
        final int sx;
        final int sz;
        final java.util.BitSet bits = new java.util.BitSet();
        int n;

        Flood(BoundingBox region) {
            this.region = region;
            this.sx = region.maxX() - region.minX() + 1;
            this.sz = region.maxZ() - region.minZ() + 1;
        }

        int index(BlockPos p) {
            return ((p.getY() - region.minY()) * sz + (p.getZ() - region.minZ())) * sx + (p.getX() - region.minX());
        }

        BlockPos pos(int i) {
            int x = i % sx;
            int r = i / sx;
            int z = r % sz;
            int y = r / sz;
            return new BlockPos(region.minX() + x, region.minY() + y, region.minZ() + z);
        }

        boolean mark(BlockPos p) {
            int i = index(p);
            if (bits.get(i)) {
                return false;
            }
            bits.set(i);
            n++;
            return true;
        }

        boolean contains(BlockPos p) {
            return p != null && region.isInside(p) && bits.get(index(p));
        }

        int size() {
            return n;
        }
    }

    /** 最小 int FIFO（避免 Integer 装箱；区域级洪泛会入队百万级）。 */
    private static final class IntQueue {
        int[] a = new int[1 << 16];
        int head;
        int tail;

        void add(int v) {
            if (tail == a.length) {
                if (head > a.length / 2) {
                    System.arraycopy(a, head, a, 0, tail - head);
                    tail -= head;
                    head = 0;
                } else {
                    a = java.util.Arrays.copyOf(a, a.length * 2);
                }
            }
            a[tail++] = v;
        }

        int poll() {
            return a[head++];
        }

        boolean isEmpty() {
            return head == tail;
        }
    }
"""
sub(OLD_FLOOD, NEW_FLOOD)

# ---- 4) 调用点：类型 / contains / size
sub("Set<Long> reachAir = flood(seedsAir, region, MAX_FLOOD, true);", "Flood reachAir = flood(seedsAir, region, true);")
sub("Set<Long> reachNonSolid = flood(seeds, region, MAX_FLOOD, false);", "Flood reachNonSolid = flood(seeds, region, false);")
sub("Set<Long> fromParent = flood(List.of(oldParent), region, PARENT_FLOOD, true);",
    "Flood fromParent = flood(List.of(oldParent), region, true);")
sub("boolean reachable = mouth != null && reachAir.contains(key(mouth));",
    "boolean reachable = mouth != null && reachAir.contains(mouth);")
sub("boolean reachableNs = mouth != null && reachNonSolid.contains(key(mouth));",
    "boolean reachableNs = mouth != null && reachNonSolid.contains(mouth);")
sub("if (fromParent.contains(key(p))) {", "if (fromParent.contains(p)) {")
sub("reachedFromOldParent = mouth != null && fromParent.contains(key(mouth));",
    "reachedFromOldParent = mouth != null && fromParent.contains(mouth);")
sub("private static Map<String, Object> measureExit(PoolElementStructurePiece pep, int idx,\n"
    "            Set<Long> reachAir, Set<Long> reachNonSolid, BoundingBox region, List<StructurePiece> pieces) {",
    "private static Map<String, Object> measureExit(PoolElementStructurePiece pep, int idx,\n"
    "            Flood reachAir, Flood reachNonSolid, BoundingBox region, List<StructurePiece> pieces) {")
sub("    private static List<BlockPos> gapPath(BlockPos seed, Set<Long> target, BoundingBox region, int max, int[] stat) {",
    "    private static List<BlockPos> gapPath(BlockPos seed, Flood target, BoundingBox region, int max, int[] stat) {")
sub("                if (target.contains(k)) {", "                if (target.contains(n)) {")

# ---- 5) 每座结构：pieceBboxes
sub("""        row.put("treasure", treasure);
        row.put("cross", cross);
        row.put("fingerprint", String.join(">", tpl));""",
    """        row.put("treasure", treasure);
        row.put("cross", cross);
        row.put("fingerprint", String.join(">", tpl));
        List<Object> pbs = new ArrayList<>();
        for (StructurePiece sp : pieces) {
            if (sp instanceof PoolElementStructurePiece pep2) {
                BoundingBox b = sp.getBoundingBox();
                Map<String, Object> pb = new LinkedHashMap<>();
                pb.put("tpl", tplOf(pep2));
                pb.put("bbox", List.of(b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ()));
                pbs.add(pb);
            }
        }
        row.put("pieceBboxes", pbs);""")

# ---- 6) 每个出入口：gapToPieces
sub("""        m.put("bbox", List.of(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ()));
        m.put("cells", cells.size());""",
    """        m.put("bbox", List.of(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ()));
        int gapToPieces = 999;
        for (StructurePiece sp : pieces) {
            if (sp == pep) {
                continue;
            }
            BoundingBox b = sp.getBoundingBox();
            int gx = Math.max(0, Math.max(b.minX() - box.maxX(), box.minX() - b.maxX()));
            int gy = Math.max(0, Math.max(b.minY() - box.maxY(), box.minY() - b.maxY()));
            int gz = Math.max(0, Math.max(b.minZ() - box.maxZ(), box.minZ() - b.maxZ()));
            gapToPieces = Math.min(gapToPieces, Math.max(gx, Math.max(gy, gz)));
        }
        m.put("gapToPieces", gapToPieces);
        m.put("cells", cells.size());""")

# ---- 7) 父件模板（当前口位 / 旧口位）
sub("""            m.put("parentState", blockId(lvl.getBlockState(parent)));""",
    """            m.put("parentState", blockId(lvl.getBlockState(parent)));
            String parentTpl = "natural";
            List<Integer> parentBbox = null;
            for (StructurePiece sp : pieces) {
                if (sp != pep && sp.getBoundingBox().isInside(parent)) {
                    parentTpl = sp instanceof PoolElementStructurePiece p2 ? tplOf(p2) : sp.getClass().getSimpleName();
                    BoundingBox pb = sp.getBoundingBox();
                    parentBbox = List.of(pb.minX(), pb.minY(), pb.minZ(), pb.maxX(), pb.maxY(), pb.maxZ());
                    break;
                }
            }
            m.put("parentTpl", parentTpl);
            m.put("parentBbox", parentBbox);""")
sub("""            m.put("oldParentState", blockId(lvl.getBlockState(oldParent)));
            m.put("parentFlood", fromParent.size());""",
    """            m.put("oldParentState", blockId(lvl.getBlockState(oldParent)));
            m.put("oldParentTpl", pieceAt(oldParent, pieces));
            m.put("parentFlood", fromParent.size());""")

# ---- 8) 外门口 / 旧外门口 / 旧 45 格通道
sub("""        m.put("oldOrigin", vec(oldOrigin));
        m.put("oldMouth", vec(oldMouth));""",
    """        m.put("oldOrigin", vec(oldOrigin));
        m.put("oldMouth", vec(oldMouth));

        // ★ 本轮关键读数：口位面（jigsaw 那一面 = 这个件**唯一**的开口）外侧的空气/可达
        int doorCells = 0;
        int doorFaceAirN = 0;
        int doorFaceReachN = 0;
        int frontAirN = 0;
        int frontReachN = 0;
        if (mouth != null) {
            frontAirN = lvl.getBlockState(mouth.relative(front)).isAir() ? 1 : 0;
            frontReachN = reachAir.contains(mouth.relative(front)) ? 1 : 0;
        }
        for (Cell c : cells) {
            if (!c.air) {
                continue;
            }
            BlockPos w = rel(settings, c.local, pep.getPosition());
            if (!box.isInside(w.relative(front))) {
                doorCells++;
                BlockPos out = w.relative(front);
                if (lvl.getBlockState(out).isAir()) {
                    doorFaceAirN++;
                }
                if (reachAir.contains(out)) {
                    doorFaceReachN++;
                }
            }
        }
        m.put("doorwayCells", doorCells);
        m.put("doorwayAir", doorFaceAirN);
        m.put("doorwayReach", doorFaceReachN);
        m.put("frontAir", frontAirN);
        m.put("frontReach", frontReachN);
        m.put("oldMouthReach", oldMouth != null && reachAir.contains(oldMouth));
        // 旧位置的口位面（玩家从牢狱走进旧 3×3 房间的那一面）
        BoundingBox oldBoxP = box;
        if (rec != null && rec.oldMin != null && rec.oldMax != null) {
            oldBoxP = new BoundingBox(rec.oldMin.getX(), rec.oldMin.getY(), rec.oldMin.getZ(),
                    rec.oldMax.getX(), rec.oldMax.getY(), rec.oldMax.getZ());
        }
        int oldDoorAir = 0;
        int oldDoorReach = 0;
        for (Cell c : cells) {
            if (!c.air) {
                continue;
            }
            BlockPos w = rel(settings, c.local, oldOrigin);
            if (!oldBoxP.isInside(w.relative(front))) {
                BlockPos out = w.relative(front);
                if (lvl.getBlockState(out).isAir()) {
                    oldDoorAir++;
                }
                if (reachAir.contains(out)) {
                    oldDoorReach++;
                }
            }
        }
        m.put("oldDoorFaceAir", oldDoorAir);
        m.put("oldDoorFaceReach", oldDoorReach);
        // 旧位置的**整条 3×3 通道**（模板 44 个空气格 + 口位格 M；旧位置恢复只恢复实心格）
        int oldTunnelCells = 0;
        int oldTunnelAir = 0;
        for (Cell c : cells) {
            if (!c.air) {
                continue;
            }
            oldTunnelCells++;
            if (lvl.getBlockState(rel(settings, c.local, oldOrigin)).isAir()) {
                oldTunnelAir++;
            }
        }
        m.put("oldTunnelCells", oldTunnelCells);
        m.put("oldTunnelAir", oldTunnelAir);""")

open(os.path.join(EVID, "GpoProbe.java.txt"), "w", encoding="utf-8", newline="\n").write(t)
out = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "GpoProbe.java")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", os.path.join(EVID, "GpoProbe.java.txt"), len(t))
print("wrote", out, len(t))
assert "Gpn" not in t, "还有 Gpn 残留"
assert "probe\", \"gpn" not in t
