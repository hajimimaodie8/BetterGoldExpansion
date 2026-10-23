package com.hjmmd_8.bettergold.worldgen;

import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.WeakHashMap;

import com.hjmmd_8.bettergold.registry.AllStructures;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.JigsawBlock;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import net.minecraft.world.level.levelgen.heightproviders.HeightProvider;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.PiecesContainer;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasBinding;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;
import net.minecraft.world.phys.AABB;

import org.slf4j.Logger;

/**
 * 金之牢狱的 Structure 类型（第九轮，2026-10-22）：**把出入口件搬进空域**。
 *
 * <h2>为什么需要自定义 StructureType（纯数据做不到）</h2>
 * 作者四图：黄色（牢狱的走廊）要**不断延伸至空域**，再把蓝色（出入口）**整块架在空域里**；
 * 而不是把蓝色半嵌在红色岩体里、还把周围清空一圈。
 * <p>jigsaw 装配是**纯几何**的：它只知道"件与口"，**感知不到空域**（哪一格是空气只有地形知道），
 * 而装配期（{@code STRUCTURE_STARTS} 状态）区块**还没有地形** ⇒ 只能等**件已落地之后**再判断。
 * 唯一的那个钩子 =
 * {@link Structure#afterPlace(net.minecraft.world.level.WorldGenLevel, StructureManager, ChunkGenerator,
 * RandomSource, BoundingBox, ChunkPos, PiecesContainer)}（`Structure.java:133`），
 * 它由 `StructureStart.java:90-96` 在**逐件 postProcess 放完方块之后**调用。
 *
 * <h2>口径（每条都有源码依据，见 docs\金之牢狱-实现记录.md §15）</h2>
 * <ol>
 *   <li><b>判据</b>：把出入口件（5×8×5）搬到一个**整块都是空气**的位置 ⇒ 它每一块实心方块的落点
 *       「原本就是空气」⇒ {@code overwroteNatural == 0}（= 作者说的"不要顶掉红色区域"）。</li>
 *   <li><b>只准动出入口</b>：全类里 {@code setBlock} 只出现一次（在 {@link #write} 里），
 *       每次写都断言 {@code pos ∈ 允许集}（旧 footprint ∪ 新 footprint），越界**拒写**并计数。</li>
 *   <li><b>恢复只碰自己的方块</b>：填旧 footprint 前逐格比对「当前格 == 该格模板期望方块」，
 *       不等就跳过（别的件/别的东西一格都不碰）。</li>
 *   <li><b>连通性前置</b>（父代理 2026-10-22 追加，2026-10-23 收紧）：以**出入口自己的口位格 M**
 *       为种子做 air-only 洪泛，**必须能到新位置的口位格 M'** 才搬；到不了就不搬（记账 {@code notConnected}）。
 *       宁可退化，**也不许挖洞**。洪泛的障碍集 = ① 旧位置里**放置后仍是实心**的格（会被恢复成原地形；
 *       模板空气格 + M 搬迁后仍是空气，是玩家走进旧 3×3 房间的路，**不许挡**）；
 *       ② `PiecesContainer` 里**每一个件**（含父件与本件）的**模板实心格** —— 件是"先算 bbox、再逐区块
 *       postProcess"的，现在还没放的件最终一定会放；按模板逐格当墙后"生成期连通"才等于"最终世界连通"。
 *       ⚠ 不能把整箱 bbox 当墙：bbox 里也有件内的走廊/门道（模板 air），整箱挡会把洪泛关死在旧件里
 *       （A 级实测 33 个出入口 0 次搬迁）。</li>
 *   <li><b>出入口的真实几何（2026-10-23 按 exit.nbt 逐格核）</b>：5×8×5、174 条 blocks =
 *       129 实心 + 1 jigsaw + 44 air；44 air = 3×3×3 房间 27 + 3×3 口位面 9（其中 6 air + 2 实心柱 +
 *       jigsaw）+ 顶部通风角 8。**jigsaw 在 z=0 那一面，其余五面是实心壳 ⇒ 这个件只有一个开口
 *       （朝父件的口位面）**。所以"搬家后玩家能不能走到新口位"等价于"最终世界里新口位面那一侧
 *       是否与牢狱空气连通"，判据就是 `reach2.contains(M')`；旧代码查的 `newMouth.relative(front)`
 *       正是 M' 的外侧一格（语义重复），没有"另一面的大门"可查。</li>
 *   <li><b>口位不补实</b>：口位格（父件 `final_state = minecraft:air` + 出入口自己的口位格）
 *       **保持空气** —— 那是"走廊通往空域的门道"。补实会把玩家锁死在牢狱里（与第 4 条直接冲突）。
 *       世界口径的"落单口" = 口位外侧**是实心**且没有配对件；这里口位外侧是空气 ⇒ 是门道、不是洞。</li>
 *   <li><b>恢复只恢复实心格（第十轮修正）</b>：旧 footprint 里**模板写的是空气**的格
 *       （3×3×3 内腔 27 + 3×3 门口 9 + 顶部开口 8）一律**保持空气**，只把实心格恢复成原地形。
 *       旧口径只留口位格 M（1 格）⇒ 玩家只能钻 1×1 洞；现口径 = 整条 3×3×3 通道保留
 *       （读数见 docs\金之牢狱-实现记录.md §16；模板几何见 exit.nbt：5×8×5 / 44 air / 1 jigsaw）。</li>
 * </ol>
 *
 * <h2>为什么不能 {@code extends JigsawStructure}</h2>
 * `JigsawStructure.java:26` 是 **{@code public final class}** ⇒ 不能继承。所以这里 {@code extends Structure}
 * 并**逐参照抄**它：codec 字段集（`JigsawStructure.java:32-50`）、`findGenerationPoint`（`:139-157`）。
 * 装配算法一个字都没重写 —— 仍然走原版 {@link JigsawPlacement#addPieces}。
 *
 * <h2>写入窗口（为什么实际搜索半径小于 24）</h2>
 * `WorldGenRegion.java:244-272` 的 {@code ensureCanWrite} 只允许**当前区块 ±1 区块**
 * （`ChunkPyramid.java:35-41` 的 FEATURES 步 {@code blockStateWriteRadius(1)}）；
 * `WorldGenRegion.java:113-144` 的 {@code getChunk} 超出依赖范围会**直接抛异常**（= 崩服）。
 * 所以探测与写入一律限制在 ±1 区块（48×48）窗口内。
 */
public class GoldenPrisonStructure extends Structure {

    private static final Logger LOGGER = LogUtils.getLogger();

    /** 出入口模板（唯一被搬迁的件）。 */
    public static final ResourceLocation EXIT_TEMPLATE =
            ResourceLocation.fromNamespaceAndPath("bettergold", "golden_prison/exit");

    /** 最大搜索距离（格）。实际会被 ±1 区块窗口裁短，见类注释。 */
    static final int MAX_SEARCH = 24;

    /** 已处理过的件（afterPlace 每个区块调一次 ⇒ 必须幂等）。WeakHashMap 不用手动清。 */
    private static final Map<StructurePiece, Boolean> DONE =
            Collections.synchronizedMap(new WeakHashMap<>());

    /** 诊断环（给 A 级探针读；最多 256 条）。 */
    private static final List<RelocationRecord> RECORDS = Collections.synchronizedList(new ArrayList<>());
    private static final int MAX_RECORDS = 256;

    /** 洪泛上限（防御性；正常一片洞穴远小于它）。2026-10-23：28 → 40 万格
     *  （诚实洪泛会走进旧门口外的空域，可能远大于旧口径的"父件那 28 格"；截断只会少搬、不会假通）。 */
    private static final int MAX_FLOOD_CELLS = 400_000;

    // ------------------------------------------------------------------ codec（照抄 JigsawStructure.java:32-50）
    public static final MapCodec<GoldenPrisonStructure> CODEC = RecordCodecBuilder.<GoldenPrisonStructure>mapCodec(
                    i -> i.group(
                                    settingsCodec(i),
                                    StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
                                    ResourceLocation.CODEC.optionalFieldOf("start_jigsaw_name").forGetter(s -> s.startJigsawName),
                                    Codec.intRange(0, 20).fieldOf("size").forGetter(s -> s.maxDepth),
                                    HeightProvider.CODEC.fieldOf("start_height").forGetter(s -> s.startHeight),
                                    Codec.BOOL.fieldOf("use_expansion_hack").forGetter(s -> s.useExpansionHack),
                                    Heightmap.Types.CODEC.optionalFieldOf("project_start_to_heightmap").forGetter(s -> s.projectStartToHeightmap),
                                    Codec.intRange(1, 128).fieldOf("max_distance_from_center").forGetter(s -> s.maxDistanceFromCenter),
                                    Codec.list(PoolAliasBinding.CODEC).optionalFieldOf("pool_aliases", List.of()).forGetter(s -> s.poolAliases),
                                    DimensionPadding.CODEC
                                            .optionalFieldOf("dimension_padding", JigsawStructure.DEFAULT_DIMENSION_PADDING)
                                            .forGetter(s -> s.dimensionPadding),
                                    LiquidSettings.CODEC
                                            .optionalFieldOf("liquid_settings", JigsawStructure.DEFAULT_LIQUID_SETTINGS)
                                            .forGetter(s -> s.liquidSettings))
                            .apply(i, GoldenPrisonStructure::new))
            .validate(GoldenPrisonStructure::verifyRange);

    private final Holder<StructureTemplatePool> startPool;
    private final Optional<ResourceLocation> startJigsawName;
    private final int maxDepth;
    private final HeightProvider startHeight;
    private final boolean useExpansionHack;
    private final Optional<Heightmap.Types> projectStartToHeightmap;
    private final int maxDistanceFromCenter;
    private final List<PoolAliasBinding> poolAliases;
    private final DimensionPadding dimensionPadding;
    private final LiquidSettings liquidSettings;

    /** 装配期顺手记下的模板管理器（afterPlace 的参数里没有它）。 */
    private static volatile StructureTemplateManager cachedTemplates;

    public GoldenPrisonStructure(
            Structure.StructureSettings settings,
            Holder<StructureTemplatePool> startPool,
            Optional<ResourceLocation> startJigsawName,
            int maxDepth,
            HeightProvider startHeight,
            boolean useExpansionHack,
            Optional<Heightmap.Types> projectStartToHeightmap,
            int maxDistanceFromCenter,
            List<PoolAliasBinding> poolAliases,
            DimensionPadding dimensionPadding,
            LiquidSettings liquidSettings) {
        super(settings);
        this.startPool = startPool;
        this.startJigsawName = startJigsawName;
        this.maxDepth = maxDepth;
        this.startHeight = startHeight;
        this.useExpansionHack = useExpansionHack;
        this.projectStartToHeightmap = projectStartToHeightmap;
        this.maxDistanceFromCenter = maxDistanceFromCenter;
        this.poolAliases = poolAliases;
        this.dimensionPadding = dimensionPadding;
        this.liquidSettings = liquidSettings;
    }

    /** 同 `JigsawStructure.java:62-70`：bury 的 12 格 padding 顶着 128 上限。 */
    private static DataResult<GoldenPrisonStructure> verifyRange(GoldenPrisonStructure structure) {
        int i = switch (structure.terrainAdaptation()) {
            case NONE -> 0;
            case BURY, BEARD_THIN, BEARD_BOX, ENCAPSULATE -> 12;
        };
        return structure.maxDistanceFromCenter + i > 128
                ? DataResult.error(() -> "Structure size including terrain adaptation must not exceed 128")
                : DataResult.success(structure);
    }

    @Override
    public StructureType<?> type() {
        return AllStructures.GOLDEN_PRISON.get();
    }

    // ------------------------------------------------------------------ 装配（照抄 JigsawStructure.java:139-157）
    @Override
    public Optional<Structure.GenerationStub> findGenerationPoint(Structure.GenerationContext context) {
        cachedTemplates = context.structureTemplateManager();
        ChunkPos chunkpos = context.chunkPos();
        int i = this.startHeight.sample(context.random(), new WorldGenerationContext(context.chunkGenerator(), context.heightAccessor()));
        BlockPos blockpos = new BlockPos(chunkpos.getMinBlockX(), i, chunkpos.getMinBlockZ());
        return JigsawPlacement.addPieces(
                context,
                this.startPool,
                this.startJigsawName,
                this.maxDepth,
                blockpos,
                this.useExpansionHack,
                this.projectStartToHeightmap,
                this.maxDistanceFromCenter,
                PoolAliasLookup.create(this.poolAliases, blockpos, context.seed()),
                this.dimensionPadding,
                this.liquidSettings);
    }

    // ------------------------------------------------------------------ 钩子
    @Override
    public void afterPlace(
            WorldGenLevel level,
            StructureManager structureManager,
            ChunkGenerator generator,
            RandomSource random,
            BoundingBox chunkBox,
            ChunkPos chunkPos,
            PiecesContainer pieces) {
        try {
            relocateAll(level, structureManager, generator, random, chunkBox, chunkPos, pieces);
        } catch (Throwable t) {
            LOGGER.error("[bgp-exit] 出入口搬迁失败（chunk {}）—— 该件保持原位", chunkPos, t);
            publish(RelocationRecord.failure(chunkPos, t));
        }
    }

    private static synchronized void relocateAll(
            WorldGenLevel level,
            StructureManager structureManager,
            ChunkGenerator generator,
            RandomSource random,
            BoundingBox chunkBox,
            ChunkPos chunkPos,
            PiecesContainer pieces) {
        List<StructurePiece> all = pieces.pieces();
        if (all.isEmpty()) {
            return;
        }
        StructureTemplateManager mgr = templateManager(level);
        if (mgr == null) {
            LOGGER.warn("[bgp-exit] 拿不到 StructureTemplateManager，跳过（chunk {}）", chunkPos);
            return;
        }
        StructureTemplate exitTemplate = mgr.getOrCreate(EXIT_TEMPLATE);
        if (exitTemplate.getSize().equals(Vec3i.ZERO)) {
            LOGGER.warn("[bgp-exit] 出入口模板 {} 为空，跳过", EXIT_TEMPLATE);
            return;
        }
        BoundingBox window = windowOf(chunkPos);
        for (StructurePiece sp : all) {
            if (!(sp instanceof PoolElementStructurePiece pep)) {
                continue;
            }
            if (DONE.containsKey(pep)) {
                continue;
            }
            if (!isExitPiece(pep, mgr, exitTemplate)) {
                continue;
            }
            // 只处理"压在当前区块上"的那一件；别的区块的 afterPlace 会处理它自己
            if (!pep.getBoundingBox().intersects(chunkBox)) {
                continue;
            }
            // 整块旧 footprint 必须落在 ±1 区块窗口内，否则等管得着它的那个区块
            if (!inside(pep.getBoundingBox(), window)) {
                continue;
            }
            // ★ 第十轮修正：件是**逐区块** postProcess 的 ⇒ 旧 bbox 覆盖的别的区块可能还没放。
            //   必须等它们都到 FEATURES（整件已落地）再搬；否则旧位置只有"当前区块那一片"是真的，
            //   3×3×3 内腔在别的区块里仍是地形（A 级实测：一个跨区块的出入口只恢复 20/129 格、
            //   内腔 2/27）。不标 DONE ⇒ 最后一个 bbox 区块的 afterPlace 会再来一次。
            if (!fullyPlaced(level, pep.getBoundingBox(), chunkPos)) {
                continue;
            }
            DONE.put(pep, Boolean.TRUE);
            RelocationRecord rec = relocateOne(level, structureManager, generator, random, pieces, pep, mgr, exitTemplate, window, chunkBox, chunkPos);
            if (rec != null) {
                publish(rec);
            }
        }
    }

    // ------------------------------------------------------------------ 单件搬迁
    private static RelocationRecord relocateOne(
            WorldGenLevel level,
            StructureManager structureManager,
            ChunkGenerator generator,
            RandomSource random,
            PiecesContainer pieces,
            PoolElementStructurePiece pep,
            StructureTemplateManager mgr,
            StructureTemplate exitTemplate,
            BoundingBox window,
            BoundingBox chunkBox,
            ChunkPos chunkPos) {
        RelocationRecord rec = new RelocationRecord();
        rec.chunk = chunkPos.x + "," + chunkPos.z;
        rec.element = String.valueOf(pep.getElement());
        rec.rotation = pep.getRotation().getSerializedName();

        StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(pep.getRotation());
        BlockPos origin = pep.getPosition();
        List<TemplateCell> cells = templateCells(exitTemplate);
        if (cells.isEmpty()) {
            rec.outcome = "noCells";
            return rec;
        }
        List<PlacedCell> oldCells = place(cells, settings, origin);
        BoundingBox oldBox = pep.getBoundingBox();
        rec.oldMin = new BlockPos(oldBox.minX(), oldBox.minY(), oldBox.minZ());
        rec.oldMax = new BlockPos(oldBox.maxX(), oldBox.maxY(), oldBox.maxZ());
        rec.cells = oldCells.size();

        // ---- 幂等/有效校验：只看**压在当前区块里**的那批格子（afterPlace 逐区块调，
        //      别的区块的格子这时还没放；用全量匹配会把自己误判成 stale）
        int matched = 0;
        int solid = 0;
        for (PlacedCell c : oldCells) {
            if (c.cell.air() || !chunkBox.isInside(c.pos)) {
                continue;
            }
            solid++;
            if (blockId(level.getBlockState(c.pos)).equals(c.cell.placedBlockId())) {
                matched++;
            }
        }
        rec.matched = matched;
        rec.solidCells = solid;
        if (solid == 0) {
            // 这件在本区块里没有实心格 ⇒ 让"管得着它的那个区块"去处理
            return null;
        }
        if (matched * 2 < solid) {
            rec.outcome = "stale"; // 已经不在原位（或一开始就被别的东西顶掉）⇒ 什么都不做
            return rec;
        }

        // ---- 出入口自己的口位格（M）与父件口位格（P）
        Mouth mouth = mouthOf(cells, settings, origin);
        if (mouth == null) {
            rec.outcome = "noMouth";
            return rec;
        }
        rec.mouth = mouth.exitCell;
        rec.parentCell = mouth.parentCell;
        BlockPos seed = mouth.exitCell; // 「父件口位外侧那一格」= 出入口自己的口位格

        // ---- ★ 墙集：PiecesContainer 里**每一个件**（含父件与本件）的**模板实心格**整格当墙。
        //   件是"先算 bbox、再逐区块 postProcess"的 ⇒ 现在还没放的件最终一定会放；把每个件的
        //   **实心格**（不是整箱 bbox —— bbox 会把件内的走廊/门道也当墙，实测把洪泛关死在旧件里、
        //   33 个出入口 0 次搬迁）当墙后，"生成期看到的连通" = "最终世界的连通"。
        //   父件同样只挡实心格：它的口位格/走廊是空气 ⇒ 洪泛能走进牢狱；它的墙照样挡。
        //   模板里的 air 格是**会被放置成空气**的（模板 blocks 里就有 air），structure_void 格
        //   不进模板（= 地形原样），两边都不当墙 —— 与最终世界逐格一致。
        PieceWalls walls = new PieceWalls(window);
        int wallPieces = 0;
        for (StructurePiece other : pieces.pieces()) {
            if (!(other instanceof PoolElementStructurePiece opep)) {
                walls.addBox(other.getBoundingBox());
                wallPieces++;
                continue;
            }
            StructureTemplate otherTpl = templateOf(opep, mgr);
            if (otherTpl == null) {
                // 拿不到模板（本结构 7 个池全是 single_pool_element，理论上不会）⇒ 退回整箱当墙（保守）
                walls.addBox(opep.getBoundingBox());
                wallPieces++;
                continue;
            }
            StructurePlaceSettings otherSettings = new StructurePlaceSettings().setRotation(opep.getRotation());
            for (PlacedCell c : place(templateCells(otherTpl), otherSettings, opep.getPosition())) {
                if ("minecraft:air".equals(c.cell.placedBlockId())) {
                    walls.addAir(c.pos);
                } else {
                    walls.addCell(c.pos);
                }
            }
            wallPieces++;
        }
        rec.wallPieces = wallPieces;

        // ---- 连通性：以 M 为种子的 air-only 洪泛。
        //   ★ 旧位置里**只有"放置后仍是实心"的格**才是障碍（恢复逻辑会把它们变回原地形）；
        //     模板空气格 + 口位格 M 搬迁后**保持空气**（见类注释第 6 条）⇒ 它们是"旧 3×3 通道"，
        //     是玩家走出旧位置的必经之路。旧口径把 44 个模板空气格也挡住 ⇒ 洪泛被关在旧件里
        //     （A 级实测只剩 28 格、0 次搬迁），这是 §16 那 9 个"到不了"的根因。
        Set<Long> oldBlocked = new HashSet<>();
        for (PlacedCell c : oldCells) {
            if (!"minecraft:air".equals(c.cell.placedBlockId())) {
                oldBlocked.add(pack(c.pos));
            }
        }
        Set<Long> reachable = floodAir(level, window, seed, oldBlocked, MAX_FLOOD_CELLS, walls);
        rec.reachable = reachable.size();

        // ---- 别的出入口的"门道"格要保护：一件 5×8×5，搬 4 件时很容易把前一件的口盖掉
        Set<Long> protectedCells = new HashSet<>();
        for (StructurePiece other : pieces.pieces()) {
            if (other == pep || !(other instanceof PoolElementStructurePiece opep)) {
                continue;
            }
            if (!isExitPiece(opep, mgr, exitTemplate)) {
                continue;
            }
            Mouth om = mouthOf(cells, settings, opep.getPosition());
            if (om != null) {
                protectedCells.add(pack(om.exitCell));
                protectedCells.add(pack(om.parentCell));
            }
        }
        rec.protectedCells = protectedCells.size();

        // ---- 别的件的 bbox：目的地必须在**整个牢狱之外**（否则后生成的件会把门口压掉）
        List<BoundingBox> otherBoxes = new ArrayList<>();
        for (StructurePiece other : pieces.pieces()) {
            if (other != pep) {
                otherBoxes.add(other.getBoundingBox());
            }
        }

        // ---- 找目的地：在"从口位洪泛可达的空气"里**穷举**所有放得下出入口 bbox 的位置
        //   （只沿 6 条轴射线试是不够的：空腔往往斜着错开，实测 0 命中）
        Destination dest = searchDestination(level, window, oldBox, reachable, seed, oldBlocked, cells, settings, mouth, origin,
                protectedCells, otherBoxes, walls, rec);
        if (dest == null) {
            rec.outcome = reachable.size() <= 1 ? "noAir" : "notConnected";
            return rec;
        }
        rec.dist = dest.dist;
        rec.dir = dest.dir == null ? "" : dest.dir.getName();
        rec.strict = dest.strict;
        rec.newMin = new BlockPos(dest.box.minX(), dest.box.minY(), dest.box.minZ());
        rec.newMax = new BlockPos(dest.box.maxX(), dest.box.maxY(), dest.box.maxZ());

        // ---- 目的地再核一次（写之前）：每一块实心落点原本确实是空气 ⇒ overwroteNatural
        int overwrote = 0;
        Set<Long> allowed = new HashSet<>();
        for (PlacedCell c : dest.cells) {
            allowed.add(pack(c.pos));
            if (!c.cell.air() && !level.getBlockState(c.pos).isAir()) {
                overwrote++;
            }
        }
        for (PlacedCell c : oldCells) {
            allowed.add(pack(c.pos));
        }
        rec.overwroteNatural = overwrote;
        rec.allowedCells = allowed;
        if (overwrote != 0) {
            rec.outcome = "overwriteGuard"; // 理论上不可能（洪泛已筛过）；留作保险
            return rec;
        }

        // ---- 旧位置的实体（出入口自己放的展示框）先撤掉，免得留在石头里
        rec.entitiesRemoved = discardEntities(level, oldBox);

        // ---- ① 在新位置重放同一个 element（与原放置同一条代码路径）
        BlockPos pivot = pivotOf(pieces);
        pep.move(dest.origin.getX() - origin.getX(), dest.origin.getY() - origin.getY(), dest.origin.getZ() - origin.getZ());
        pep.place(level, structureManager, generator, random, dest.box, pivot, false);
        // 放完再逐格回读：实心格必须都变成了出入口自己的方块（= 真的放下了）
        int matchedNew = 0;
        int solidNew = 0;
        for (PlacedCell c : dest.cells) {
            if (c.cell.air()) {
                continue;
            }
            solidNew++;
            if (blockId(level.getBlockState(c.pos)).equals(c.cell.placedBlockId())) {
                matchedNew++;
            }
        }
        rec.matchedNew = matchedNew;
        rec.solidNew = solidNew;
        rec.placed = solidNew > 0 && matchedNew == solidNew;

        // ---- ② 恢复旧 footprint（只碰"当前格 == 出入口自己的方块"的**实心**格；
        //      模板空气格 + 口位格 M 一律保持空气 = 整条 3×3×3 通道）
        Set<Long> destinationCells = new HashSet<>();
        for (PlacedCell c : dest.cells) {
            destinationCells.add(pack(c.pos));
        }
        int restored = 0;
        int skipped = 0;
        int doorway = 0;
        int keptAir = 0;
        Map<String, Integer> materials = new LinkedHashMap<>();
        for (PlacedCell c : oldCells) {
            if (c.cell.air() || c.pos.equals(seed)) {
                // 门道：模板空气格（3×3×3 内腔 27 + 3×3 门口 9 + 顶部开口 8）与口位格保持空气。
                // 旧口径只留 M 一格 ⇒ 玩家只能钻 1×1 洞（第十轮修正，见类注释第 6 条）。
                if (c.cell.air()) {
                    keptAir++;
                }
                doorway++;
                continue;
            }
            if (destinationCells.contains(pack(c.pos))) {
                continue; // 新旧 footprint 重叠：以新位置为准
            }
            BlockState cur = level.getBlockState(c.pos);
            if (!blockId(cur).equals(c.cell.placedBlockId())) {
                skipped++; // 不是自己的方块 ⇒ 一格都不碰
                continue;
            }
            BlockState natural = naturalBelow(level, c.pos, oldBox);
            materials.merge(blockId(natural), 1, Integer::sum);
            if (write(level, c.pos, natural, rec)) {
                restored++;
            } else {
                skipped++;
            }
        }
        rec.restored = restored;
        rec.skipped = skipped;
        rec.doorway = doorway;
        rec.keptAir = keptAir;
        rec.restoreMaterials = materials;

        // ---- ③ 实体卫生：同一格只留一个（件可能因跨区块被重放一次）
        rec.entityDupesRemoved = dedupeEntities(level, dest.box);

        rec.cap = "kept-3x3x3"; // 口位 + 整个 3×3×3 内腔保持空气（见类注释第 5、6 条）
        rec.outcome = "relocated";
        return rec;
    }

    // ------------------------------------------------------------------ 目的地搜索
    /** 搜索时 y 方向放宽多少（格）。 */
    private static final int SEARCH_Y = 40;

    /**
     * 在"从口位洪泛可达的空气"里**穷举**所有放得下出入口 bbox 的位置。
     *
     * <p>做法：把窗口内每一格"是不是可达空气"做成 3D 前缀和 ⇒ 任取一个 bbox 都能 O(1) 判
     * 「整块都是可达空气」（= 判据 overwroteNatural == 0 + 连通性前置**同时**满足），
     * 再按"离原位多远"从近到远挑，最后过一道"把新出入口实心格挡上再洪泛"的闸门。</p>
     *
     * <p>⚠ 为什么不用"沿 6 条轴射线各试 1..24 格"：那是第一版的写法，A 级实测 25 个出入口
     * **0 命中** —— 空腔基本都是斜着错开的，纯轴位移扫不到（见 §15 的读数）。</p>
     */
    private static Destination searchDestination(
            WorldGenLevel level,
            BoundingBox window,
            BoundingBox oldBox,
            Set<Long> reachable,
            BlockPos seed,
            Set<Long> oldBlocked,
            List<TemplateCell> cells,
            StructurePlaceSettings settings,
            Mouth mouth,
            BlockPos origin,
            Set<Long> protectedCells,
            List<BoundingBox> otherBoxes,
            PieceWalls walls,
            RelocationRecord rec) {
        int minX = window.minX();
        int maxX = window.maxX();
        int minZ = window.minZ();
        int maxZ = window.maxZ();
        int minY = Math.max(level.getMinBuildHeight(), oldBox.minY() - SEARCH_Y);
        int maxY = Math.min(level.getMaxBuildHeight() - 1, oldBox.maxY() + SEARCH_Y);
        int sx = maxX - minX + 1;
        int sy = maxY - minY + 1;
        int sz = maxZ - minZ + 1;
        int strideY = sz + 1;
        int strideX = (sy + 1) * (sz + 1);
        int[] pre = new int[(sx + 1) * (sy + 1) * (sz + 1)];
        for (int i = 0; i < sx; i++) {
            for (int j = 0; j < sy; j++) {
                for (int k = 0; k < sz; k++) {
                    int v = reachable.contains(BlockPos.asLong(minX + i, minY + j, minZ + k)) ? 1 : 0;
                    pre[(i + 1) * strideX + (j + 1) * strideY + (k + 1)] = v
                            + pre[i * strideX + (j + 1) * strideY + (k + 1)]
                            + pre[(i + 1) * strideX + j * strideY + (k + 1)]
                            + pre[(i + 1) * strideX + (j + 1) * strideY + k]
                            - pre[i * strideX + j * strideY + (k + 1)]
                            - pre[i * strideX + (j + 1) * strideY + k]
                            - pre[(i + 1) * strideX + j * strideY + k]
                            + pre[i * strideX + j * strideY + k];
                }
            }
        }
        int w = oldBox.maxX() - oldBox.minX() + 1;
        int h = oldBox.maxY() - oldBox.minY() + 1;
        int dep = oldBox.maxZ() - oldBox.minZ() + 1;
        int vol = w * h * dep;
        int volShell = (w + 2) * (h + 2) * (dep + 2);
        int dxMin = -(oldBox.minX() - minX);
        int dxMax = maxX - oldBox.maxX();
        int dyMin = -(oldBox.minY() - minY);
        int dyMax = maxY - oldBox.maxY();
        int dzMin = -(oldBox.minZ() - minZ);
        int dzMax = maxZ - oldBox.maxZ();
        List<int[]> hits = new ArrayList<>(); // {dx, dy, dz, strict, score}
        for (int dy = dyMin; dy <= dyMax; dy++) {
            for (int dz = dzMin; dz <= dzMax; dz++) {
                for (int dx = dxMin; dx <= dxMax; dx++) {
                    if (dx == 0 && dy == 0 && dz == 0) {
                        continue;
                    }
                    int cheb = Math.max(Math.abs(dx), Math.max(Math.abs(dy), Math.abs(dz)));
                    if (cheb > MAX_SEARCH) {
                        continue;
                    }
                    int i1 = oldBox.minX() + dx - minX;
                    int j1 = oldBox.minY() + dy - minY;
                    int k1 = oldBox.minZ() + dz - minZ;
                    int i2 = i1 + w - 1;
                    int j2 = j1 + h - 1;
                    int k2 = k1 + dep - 1;
                    if (boxSum(pre, strideX, strideY, i1, j1, k1, i2, j2, k2) != vol) {
                        continue;
                    }
                    boolean strict = i1 > 0 && j1 > 0 && k1 > 0 && i2 < sx - 1 && j2 < sy - 1 && k2 < sz - 1
                            && boxSum(pre, strideX, strideY, i1 - 1, j1 - 1, k1 - 1, i2 + 1, j2 + 1, k2 + 1) == volShell;
                    int score = Math.abs(dx) + Math.abs(dy) + Math.abs(dz) + (strict ? 0 : 1000);
                    hits.add(new int[] {dx, dy, dz, strict ? 1 : 0, score, cheb});
                }
            }
        }
        rec.candidates = hits.size();
        if (hits.isEmpty()) {
            rec.strictTier = 0;
            rec.lenientTier = 0;
            return null;
        }
        hits.sort((a, b) -> Integer.compare(a[4], b[4]));
        int strictHits = 0;
        int lenientHits = 0;
        int attempts = 0;
        for (int[] hit : hits) {
            if (hit[3] == 1) {
                strictHits++;
            } else {
                lenientHits++;
            }
            if (attempts >= 48) {
                continue;
            }
            attempts++;
            BlockPos candOrigin = origin.offset(hit[0], hit[1], hit[2]);
            // 目的地实心格不许压到别的出入口的门道格
            boolean hitsProtected = false;
            for (PlacedCell c : place(cells, settings, candOrigin)) {
                if (!"minecraft:air".equals(c.cell.placedBlockId()) && protectedCells.contains(pack(c.pos))) {
                    hitsProtected = true;
                    break;
                }
            }
            if (hitsProtected) {
                rec.protectedBlocked++;
                continue;
            }
            BoundingBox candBox = oldBox.moved(hit[0], hit[1], hit[2]);
            boolean outside = true;
            for (BoundingBox ob : otherBoxes) {
                // ★ 不相交**也不相邻**：inflatedBy(1) 把"贴脸一格"也算相交（≥1 格空隙），
                //   否则后放的件会正好把新门口糊住（父代理 2026-10-23 裁定）。
                if (ob.intersects(candBox.inflatedBy(1))) {
                    outside = false;
                    break;
                }
            }
            if (!outside) {
                rec.insideStructure++;
                continue;
            }
            List<PlacedCell> newCells = place(cells, settings, candOrigin);
            BoundingBox newBox = oldBox.moved(hit[0], hit[1], hit[2]);
            BlockPos newMouth = mouthAt(cells, settings, candOrigin);
            Set<Long> block2 = new HashSet<>(oldBlocked);
            for (PlacedCell c : newCells) {
                // 只挡"放置后是实心"的格；jigsaw 的 final_state = air ⇒ 口位格必须是空的
                if (!"minecraft:air".equals(c.cell.placedBlockId())) {
                    block2.add(pack(c.pos));
                }
            }
            Set<Long> reach2 = floodAir(level, window, seed, block2, MAX_FLOOD_CELLS, walls);
            if (newMouth == null || !reach2.contains(pack(newMouth))) {
                rec.pathBlocked++;
                continue;
            }
            // 口位格 M' 是整个件**唯一**的开口（exit.nbt：jigsaw 在 z=0 面，其余 5 面是实心壳；
            // 模板 44 个 air 全在 z=0..3 的 3×3 竖井里）。所以「M' 在洪泛集里」= 玩家能从新位置
            // 的开口走进这个件；不需要再单独查某一面（旧代码查 jigsaw 外侧一格，语义上就是 M' 自己）。
            rec.strictTier = strictHits;
            rec.lenientTier = lenientHits;
            return new Destination(candOrigin, newBox, newCells, hit[3] == 1, hit[5], null);
        }
        rec.strictTier = strictHits;
        rec.lenientTier = lenientHits;
        return null;
    }

    /** 3D 前缀和求盒内 1 的个数（0-based 局部坐标，含端点）。 */
    private static int boxSum(int[] pre, int strideX, int strideY, int i1, int j1, int k1, int i2, int j2, int k2) {
        return pv(pre, strideX, strideY, i2, j2, k2)
                - pv(pre, strideX, strideY, i1 - 1, j2, k2)
                - pv(pre, strideX, strideY, i2, j1 - 1, k2)
                - pv(pre, strideX, strideY, i2, j2, k1 - 1)
                + pv(pre, strideX, strideY, i1 - 1, j1 - 1, k2)
                + pv(pre, strideX, strideY, i1 - 1, j2, k1 - 1)
                + pv(pre, strideX, strideY, i2, j1 - 1, k1 - 1)
                - pv(pre, strideX, strideY, i1 - 1, j1 - 1, k1 - 1);
    }

    private static int pv(int[] pre, int strideX, int strideY, int i, int j, int k) {
        if (i < 0 || j < 0 || k < 0) {
            return 0;
        }
        return pre[(i + 1) * strideX + (j + 1) * strideY + (k + 1)];
    }

    // ------------------------------------------------------------------ 写入（全类唯一的 setBlock）
    /**
     * 唯一写入口：断言 {@code pos} 落在允许集里（旧 footprint ∪ 新 footprint），否则拒写并计数。
     */
    private static boolean write(WorldGenLevel level, BlockPos pos, BlockState state, RelocationRecord rec) {
        if (rec.allowedCells == null || !rec.allowedCells.contains(pack(pos))) {
            rec.violations++;
            LOGGER.error("[bgp-exit] 越界写入被拒：{}", pos);
            return false;
        }
        if (level.isOutsideBuildHeight(pos)) {
            rec.outOfWorld++;
            return false;
        }
        rec.writes++;
        return level.setBlock(pos, state, 2 | 16);
    }

    // ------------------------------------------------------------------ 工具
    private static StructureTemplateManager templateManager(WorldGenLevel level) {
        StructureTemplateManager mgr = cachedTemplates;
        if (mgr != null) {
            return mgr;
        }
        try {
            return level.getLevel().getStructureManager();
        } catch (Throwable t) {
            return null;
        }
    }

    /** ±1 区块窗口（可读 + 可写，见类注释）。y 放开，靠 isOutsideBuildHeight 兜。 */
    static BoundingBox windowOf(ChunkPos pos) {
        return new BoundingBox((pos.x - 1) * 16, -256, (pos.z - 1) * 16, (pos.x + 1) * 16 + 15, 511, (pos.z + 1) * 16 + 15);
    }

    private static boolean inside(BoundingBox box, BoundingBox window) {
        return box.minX() >= window.minX() && box.maxX() <= window.maxX()
                && box.minZ() >= window.minZ() && box.maxZ() <= window.maxZ();
    }

    /**
     * 旧 bbox 覆盖的所有区块是否都已经是 FEATURES（= 这个件的**所有切片**都放完了）。
     *
     * <p>件是逐区块 `postProcess` 的；`afterPlace` 每区块调一次。当前区块的切片在调用前已放，
     * 所以跳过它；其余区块用 `getChunk(cx,cz)`（EMPTY，3×3 依赖区内安全）读持久状态。
     * 拿不到/状态不够 ⇒ 返回 false（**不标 DONE**，等最后一个 bbox 区块再来）。
     */
    private static boolean fullyPlaced(WorldGenLevel level, BoundingBox box, ChunkPos current) {
        try {
            for (int cx = box.minX() >> 4; cx <= box.maxX() >> 4; cx++) {
                for (int cz = box.minZ() >> 4; cz <= box.maxZ() >> 4; cz++) {
                    if (cx == current.x && cz == current.z) {
                        continue;
                    }
                    ChunkAccess chunk = level.getChunk(cx, cz);
                    if (chunk == null || !chunk.getPersistedStatus().isOrAfter(ChunkStatus.FEATURES)) {
                        return false;
                    }
                }
            }
            return true;
        } catch (Throwable t) {
            return false;
        }
    }

    /** 出入口件识别：尺寸与 exit 模板一致 + **恰好 1 个口且 target = empty**（26 件里只有 exit 这样）。 */
    private static boolean isExitPiece(PoolElementStructurePiece pep, StructureTemplateManager mgr, StructureTemplate exitTemplate) {
        Vec3i size;
        try {
            size = pep.getElement().getSize(mgr, pep.getRotation());
        } catch (Throwable t) {
            return false;
        }
        if (!size.equals(exitTemplate.getSize(pep.getRotation()))) {
            return false;
        }
        try {
            List<StructureTemplate.StructureBlockInfo> jigs = pep.getElement()
                    .getShuffledJigsawBlocks(mgr, pep.getPosition(), pep.getRotation(), RandomSource.create(0L));
            if (jigs.size() != 1) {
                return false;
            }
            CompoundTag nbt = jigs.get(0).nbt();
            return nbt != null && "empty".equals(nbt.getString("target"));
        } catch (Throwable t) {
            return false;
        }
    }

    /** 从模板 `save()` 的 NBT 里读出"这个模板写了哪些格、每格是 air 还是实心"。 */
    static List<TemplateCell> templateCells(StructureTemplate template) {
        List<TemplateCell> out = new ArrayList<>();
        CompoundTag tag = template.save(new CompoundTag());
        ListTag palette;
        if (tag.contains("palette")) {
            palette = tag.getList("palette", Tag.TAG_COMPOUND);
        } else if (tag.contains("palettes")) {
            ListTag all = tag.getList("palettes", Tag.TAG_LIST);
            palette = all.isEmpty() ? new ListTag() : all.getList(0);
        } else {
            return out;
        }
        ListTag blocks = tag.getList("blocks", Tag.TAG_COMPOUND);
        for (int i = 0; i < blocks.size(); i++) {
            CompoundTag b = blocks.getCompound(i);
            ListTag posTag = b.getList("pos", Tag.TAG_INT);
            if (posTag.size() != 3) {
                continue;
            }
            int id = b.getInt("state");
            if (id < 0 || id >= palette.size()) {
                continue;
            }
            CompoundTag state = palette.getCompound(id);
            String name = state.getString("Name");
            CompoundTag nbt = b.contains("nbt") ? b.getCompound("nbt") : null;
            out.add(new TemplateCell(new Vec3i(posTag.getInt(0), posTag.getInt(1), posTag.getInt(2)), name, state, nbt));
        }
        return out;
    }

    private static List<PlacedCell> place(List<TemplateCell> cells, StructurePlaceSettings settings, BlockPos origin) {
        List<PlacedCell> out = new ArrayList<>(cells.size());
        for (TemplateCell c : cells) {
            BlockPos world = StructureTemplate.calculateRelativePosition(settings, new BlockPos(c.local)).offset(origin);
            out.add(new PlacedCell(world, c));
        }
        return out;
    }

    private static BlockPos mouthAt(List<TemplateCell> cells, StructurePlaceSettings settings, BlockPos origin) {
        for (TemplateCell c : cells) {
            if (c.jigsaw()) {
                return StructureTemplate.calculateRelativePosition(settings, new BlockPos(c.local)).offset(origin);
            }
        }
        return null;
    }

    private static String blockId(BlockState state) {
        return state.getBlock().builtInRegistryHolder().key().location().toString();
    }

    private static long pack(BlockPos p) {
        return BlockPos.asLong(p.getX(), p.getY(), p.getZ());
    }

    /** air-only 洪泛（只走"现在是 air 且不在 blocked 里"的格），限制在窗口内。 */
    private static Set<Long> floodAir(WorldGenLevel level, BoundingBox window, BlockPos seed, Set<Long> blocked,
            int maxCells, PieceWalls walls) {
        Set<Long> seen = new HashSet<>();
        if (level.isOutsideBuildHeight(seed) || !window.isInside(seed) || !level.getBlockState(seed).isAir()) {
            return seen;
        }
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(seed);
        seen.add(pack(seed));
        while (!queue.isEmpty() && seen.size() < maxCells) {
            BlockPos p = queue.poll();
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                long key = pack(n);
                if (seen.contains(key) || blocked.contains(key)) {
                    continue;
                }
                // ★ 其它件的 bbox 整箱当墙（除 exit 自身与父件）：这些件最终一定会放，
                //   现在是不是空气都不许走 —— 这是"生成期连通 = 最终世界连通"的关键。
                if (walls != null && walls.blocked(n)) {
                    continue;
                }
                if (!window.isInside(n) || level.isOutsideBuildHeight(n)) {
                    continue;
                }
                // 最终世界是空气：现在就是空气，或者这一格是某个件的**模板 air 格**
                // （件还没放时地形可能还是岩体，但模板会把这一格写成空气）。
                if (!level.getBlockState(n).isAir() && (walls == null || !walls.air(n))) {
                    continue;
                }
                seen.add(key);
                queue.add(n);
            }
        }
        return seen;
    }

    /**
     * 其它件的**模板格**：实心格 = 墙；air 格 = "最终世界一定是空气"（件还没放时地形可能是岩体，
     * 但模板会把这一格写成空气）。两类都是 O(1) 查询。拿不到模板时退回**整箱当墙**（保守）。
     */
    private static final class PieceWalls {
        private final int minX;
        private final int minY;
        private final int minZ;
        private final int maxX;
        private final int maxY;
        private final int maxZ;
        private final int sx;
        private final int sy;
        private final int sz;
        private final boolean[] solidBits;
        private final boolean[] airBits;

        PieceWalls(BoundingBox region) {
            this.minX = region.minX();
            this.minY = region.minY();
            this.minZ = region.minZ();
            this.maxX = region.maxX();
            this.maxY = region.maxY();
            this.maxZ = region.maxZ();
            this.sx = maxX - minX + 1;
            this.sy = maxY - minY + 1;
            this.sz = maxZ - minZ + 1;
            this.solidBits = new boolean[sx * sy * sz];
            this.airBits = new boolean[sx * sy * sz];
        }

        void addBox(BoundingBox b) {
            int x1 = Math.max(b.minX(), minX);
            int y1 = Math.max(b.minY(), minY);
            int z1 = Math.max(b.minZ(), minZ);
            int x2 = Math.min(b.maxX(), maxX);
            int y2 = Math.min(b.maxY(), maxY);
            int z2 = Math.min(b.maxZ(), maxZ);
            for (int y = y1; y <= y2; y++) {
                for (int z = z1; z <= z2; z++) {
                    int base = ((y - minY) * sz + (z - minZ)) * sx;
                    for (int x = x1; x <= x2; x++) {
                        solidBits[base + (x - minX)] = true;
                    }
                }
            }
        }

        void addCell(BlockPos p) {
            int i = index(p);
            if (i >= 0) {
                solidBits[i] = true;
            }
        }

        void addAir(BlockPos p) {
            int i = index(p);
            if (i >= 0) {
                airBits[i] = true;
            }
        }

        /** 模板 air 格 ⇒ 最终世界一定可走（即使现在还没放、地形还是岩体）。 */
        boolean air(BlockPos p) {
            int i = index(p);
            return i >= 0 && airBits[i];
        }

        boolean blocked(BlockPos p) {
            int i = index(p);
            return i >= 0 && solidBits[i];
        }

        private int index(BlockPos p) {
            int x = p.getX() - minX;
            int y = p.getY() - minY;
            int z = p.getZ() - minZ;
            if (x < 0 || y < 0 || z < 0 || x >= sx || y >= sy || z >= sz) {
                return -1;
            }
            return (y * sz + z) * sx + x;
        }
    }

    /**
     * 取件的模板。本结构 7 个池全是 {@code minecraft:single_pool_element} ⇒
     * {@code SinglePoolElement#toString()} = {@code Single[Left[<location>]]}，从中解析 location。
     * 解析失败/不是单模板件 ⇒ 返回 null（调用方退回整箱当墙）。
     */
    private static StructureTemplate templateOf(StructurePiece sp, StructureTemplateManager mgr) {
        if (!(sp instanceof PoolElementStructurePiece pep)) {
            return null;
        }
        try {
            String s = String.valueOf(pep.getElement());
            int a = s.indexOf("Left[");
            int b = a < 0 ? -1 : s.indexOf(']', a);
            if (a < 0 || b < 0) {
                return null;
            }
            ResourceLocation loc = ResourceLocation.tryParse(s.substring(a + 5, b));
            if (loc == null) {
                return null;
            }
            StructureTemplate tpl = mgr.getOrCreate(loc);
            return tpl.getSize().equals(Vec3i.ZERO) ? null : tpl;
        } catch (Throwable t) {
            return null;
        }
    }

    /**
     * 原地形：沿该列往下找第一个"像地形"的方块（不是空气/流体/带方块实体/不是本结构的方块）。
     * 找不到就往上找；都没有 ⇒ 下界岩兜底（读数里会记到 materials 上）。
     */
    static BlockState naturalBelow(WorldGenLevel level, BlockPos pos, BoundingBox oldBox) {
        for (int y = pos.getY() - 1; y >= pos.getY() - 13; y--) {
            BlockState s = stateAt(level, pos.getX(), y, pos.getZ());
            if (s != null && usableTerrain(s)) {
                return s;
            }
        }
        for (int y = oldBox.maxY() + 1; y <= oldBox.maxY() + 13; y++) {
            BlockState s = stateAt(level, pos.getX(), y, pos.getZ());
            if (s != null && usableTerrain(s)) {
                return s;
            }
        }
        return Blocks.NETHERRACK.defaultBlockState();
    }

    private static BlockState stateAt(WorldGenLevel level, int x, int y, int z) {
        if (level.isOutsideBuildHeight(y)) {
            return null;
        }
        return level.getBlockState(new BlockPos(x, y, z));
    }

    static boolean usableTerrain(BlockState s) {
        if (s.isAir() || !s.getFluidState().isEmpty() || s.hasBlockEntity()) {
            return false;
        }
        String id = blockId(s);
        if (id.startsWith("bettergold:") || "minecraft:jigsaw".equals(id)) {
            return false;
        }
        return !s.is(Blocks.STRUCTURE_VOID) && !s.is(Blocks.BARRIER) && !s.is(Blocks.LIGHT);
    }

    /** 复刻 `StructureStart.placeInChunk` 的 `blockpos1`（第一件的 bbox 中心、取 minY）。 */
    private static BlockPos pivotOf(PiecesContainer pieces) {
        List<StructurePiece> list = pieces.pieces();
        BoundingBox b0 = list.get(0).getBoundingBox();
        BlockPos center = b0.getCenter();
        return new BlockPos(center.getX(), b0.minY(), center.getZ());
    }

    private static int discardEntities(WorldGenLevel level, BoundingBox box) {
        int n = 0;
        try {
            AABB aabb = new AABB(box.minX(), box.minY(), box.minZ(), box.maxX() + 1.0, box.maxY() + 1.0, box.maxZ() + 1.0);
            for (Entity e : level.getEntitiesOfClass(Entity.class, aabb, e -> true)) {
                e.discard();
                n++;
            }
        } catch (Throwable t) {
            LOGGER.warn("[bgp-exit] 撤销旧位置实体时出错", t);
        }
        return n;
    }

    private static int dedupeEntities(WorldGenLevel level, BoundingBox box) {
        int n = 0;
        try {
            AABB aabb = new AABB(box.minX(), box.minY(), box.minZ(), box.maxX() + 1.0, box.maxY() + 1.0, box.maxZ() + 1.0);
            Set<Long> seen = new HashSet<>();
            for (Entity e : level.getEntitiesOfClass(Entity.class, aabb, e -> true)) {
                if (!seen.add(BlockPos.asLong(e.getBlockX(), e.getBlockY(), e.getBlockZ()))) {
                    e.discard();
                    n++;
                }
            }
        } catch (Throwable t) {
            LOGGER.warn("[bgp-exit] 实体去重时出错", t);
        }
        return n;
    }

    // ------------------------------------------------------------------ 记账
    private static void publish(RelocationRecord rec) {
        synchronized (RECORDS) {
            if (RECORDS.size() >= MAX_RECORDS) {
                RECORDS.remove(0);
            }
            RECORDS.add(rec);
        }
        LOGGER.info("[bgp-exit] {}", rec.line());
    }

    /** 给 A 级探针读的只读视图。 */
    public static List<RelocationRecord> records() {
        synchronized (RECORDS) {
            return List.copyOf(RECORDS);
        }
    }

    /** 探针用：清空诊断环。 */
    public static void clearRecords() {
        synchronized (RECORDS) {
            RECORDS.clear();
        }
    }

    // ------------------------------------------------------------------ 内部类型
    static final class TemplateCell {
        final Vec3i local;
        final String blockId;
        final CompoundTag stateTag;
        final CompoundTag nbt;
        private BlockState state;

        TemplateCell(Vec3i local, String blockId, CompoundTag stateTag, CompoundTag nbt) {
            this.local = local;
            this.blockId = blockId;
            this.stateTag = stateTag;
            this.nbt = nbt;
        }

        boolean air() {
            return "minecraft:air".equals(blockId) || "minecraft:cave_air".equals(blockId) || "minecraft:void_air".equals(blockId);
        }

        boolean jigsaw() {
            return "minecraft:jigsaw".equals(blockId);
        }

        BlockState state() {
            if (state == null) {
                try {
                    state = NbtUtils.readBlockState(BuiltInRegistries.BLOCK.asLookup(), stateTag);
                } catch (Throwable t) {
                    state = Blocks.AIR.defaultBlockState();
                }
            }
            return state;
        }

        /** 放置后这一格应该是什么方块（jigsaw 会被 JigsawReplacementProcessor 换成 final_state）。 */
        String placedBlockId() {
            if (!jigsaw()) {
                return blockId;
            }
            String fs = nbt == null ? "" : nbt.getString("final_state");
            if (fs == null || fs.isEmpty()) {
                return "minecraft:air";
            }
            int i = fs.indexOf('[');
            return i < 0 ? fs : fs.substring(0, i);
        }
    }

    static final class PlacedCell {
        final BlockPos pos;
        final TemplateCell cell;

        PlacedCell(BlockPos pos, TemplateCell cell) {
            this.pos = pos;
            this.cell = cell;
        }
    }

    private static final class Mouth {
        final BlockPos exitCell;
        final BlockPos parentCell;
        final Direction front;

        Mouth(BlockPos exitCell, BlockPos parentCell, Direction front) {
            this.exitCell = exitCell;
            this.parentCell = parentCell;
            this.front = front;
        }
    }

    /** 出入口自己的口位格 + 它朝向父件的那一面（jigsaw 的 front 指向父件）。 */
    private static Mouth mouthOf(List<TemplateCell> cells, StructurePlaceSettings settings, BlockPos origin) {
        for (TemplateCell c : cells) {
            if (!c.jigsaw()) {
                continue;
            }
            BlockPos world = StructureTemplate.calculateRelativePosition(settings, new BlockPos(c.local)).offset(origin);
            Direction front;
            try {
                front = JigsawBlock.getFrontFacing(c.state().rotate(settings.getRotation()));
            } catch (Throwable t) {
                front = Direction.NORTH;
            }
            return new Mouth(world, world.relative(front), front);
        }
        return null;
    }

    private static final class Destination {
        final BlockPos origin;
        final BoundingBox box;
        final List<PlacedCell> cells;
        final boolean strict;
        final int dist;
        final Direction dir;

        Destination(BlockPos origin, BoundingBox box, List<PlacedCell> cells, boolean strict, int dist, Direction dir) {
            this.origin = origin;
            this.box = box;
            this.cells = cells;
            this.strict = strict;
            this.dist = dist;
            this.dir = dir;
        }
    }

    /** 一条搬迁记录（同时进日志与诊断环）。 */
    public static final class RelocationRecord {
        public String chunk = "";
        public String element = "";
        public String rotation = "";
        public String outcome = "?";
        public BlockPos oldMin;
        public BlockPos oldMax;
        public BlockPos newMin;
        public BlockPos newMax;
        public BlockPos mouth;
        public BlockPos parentCell;
        public int cells;
        public int solidCells;
        public int matched;
        public int reachable;
        public int dist = -1;
        public String dir = "";
        public boolean strict;
        public int strictTier;
        public int lenientTier;
        public int candidates;
        public int protectedCells;
        public int protectedBlocked;
        public int insideStructure;
        public int pathBlocked;
        public int overwroteNatural = -1;
        public int restored;
        public int skipped;
        public int doorway;
        public int keptAir;
        public int wallPieces;
        public int entitiesRemoved;
        public int entityDupesRemoved;
        public boolean placed;
        public int matchedNew;
        public int solidNew;
        public String cap = "";
        public int writes;
        public int violations;
        public int outOfWorld;
        public Map<String, Integer> restoreMaterials = Map.of();
        Set<Long> allowedCells;

        static RelocationRecord failure(ChunkPos pos, Throwable t) {
            RelocationRecord r = new RelocationRecord();
            r.chunk = pos.x + "," + pos.z;
            r.outcome = "error:" + t.getClass().getSimpleName();
            return r;
        }

        public String line() {
            return "chunk=" + chunk
                    + " outcome=" + outcome
                    + " rot=" + rotation
                    + " dist=" + dist + (dir.isEmpty() ? "" : "(" + dir + ")")
                    + " strict=" + strict
                    + " tiers=" + strictTier + "/" + lenientTier + " cand=" + candidates
                    + " prot=" + protectedCells + "/" + protectedBlocked
                    + " inStruct=" + insideStructure
                    + " pathBlocked=" + pathBlocked
                    + " reachable=" + reachable
                    + " overwroteNatural=" + overwroteNatural
                    + " old=" + oldMin + ".." + oldMax
                    + " new=" + newMin + ".." + newMax
                    + " placed=" + placed + "(" + matchedNew + "/" + solidNew + ")"
                    + " restored=" + restored + " skipped=" + skipped + " doorway=" + doorway
                    + " keptAir=" + keptAir
                    + " walls=" + wallPieces
                    + " cap=" + cap
                    + " entsRemoved=" + entitiesRemoved + " entDupes=" + entityDupesRemoved
                    + " writes=" + writes + " violations=" + violations + " oob=" + outOfWorld
                    + " materials=" + restoreMaterials;
        }

        public Map<String, Object> toMap() {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("chunk", chunk);
            m.put("outcome", outcome);
            m.put("rotation", rotation);
            m.put("dist", dist);
            m.put("dir", dir);
            m.put("strict", strict);
            m.put("strictTier", strictTier);
            m.put("lenientTier", lenientTier);
            m.put("candidates", candidates);
            m.put("protectedCells", protectedCells);
            m.put("protectedBlocked", protectedBlocked);
            m.put("insideStructure", insideStructure);
            m.put("pathBlocked", pathBlocked);
            m.put("reachable", reachable);
            m.put("overwroteNatural", overwroteNatural);
            m.put("oldMin", vec(oldMin));
            m.put("oldMax", vec(oldMax));
            m.put("newMin", vec(newMin));
            m.put("newMax", vec(newMax));
            m.put("mouth", vec(mouth));
            m.put("parentCell", vec(parentCell));
            m.put("cells", cells);
            m.put("solidCells", solidCells);
            m.put("matched", matched);
            m.put("placed", placed);
            m.put("matchedNew", matchedNew);
            m.put("solidNew", solidNew);
            m.put("restored", restored);
            m.put("skipped", skipped);
            m.put("doorway", doorway);
            m.put("keptAir", keptAir);
            m.put("wallPieces", wallPieces);
            m.put("cap", cap);
            m.put("entitiesRemoved", entitiesRemoved);
            m.put("entityDupesRemoved", entityDupesRemoved);
            m.put("writes", writes);
            m.put("violations", violations);
            m.put("outOfWorld", outOfWorld);
            m.put("restoreMaterials", restoreMaterials);
            m.put("element", element);
            return m;
        }

        private static List<Integer> vec(BlockPos p) {
            return p == null ? null : List.of(p.getX(), p.getY(), p.getZ());
        }
    }
}
