package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.worldgen.GoldenPrisonStructure;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 本模组的 StructureType 注册表（第九轮，2026-10-22）。
 *
 * <p>为什么需要它：金之牢狱要"把出入口件搬进空域"，而 jigsaw 装配是**纯几何**的、感知不到空域
 * （见 {@link GoldenPrisonStructure} 的类注释）。所以给它一个**自己的** `type`，
 * 由 Java 在 `Structure#afterPlace` 里做后处理。</p>
 *
 * <p>注册口径：`Registries.STRUCTURE_TYPE` + `() -> CODEC`（`StructureType` 只有一个抽象方法 `codec()`，
 * 见 `StructureType.java:31`）。数据侧 `data/bettergold/worldgen/structure/golden_prison.json`
 * 的 `"type"` 必须写成 `bettergold:golden_prison`（关卡 `[bgp-struct-type]` 钉着）。</p>
 */
public class AllStructures {

    /** StructureType 注册表（在 {@code bettergold#register} 里挂到 mod 总线）。 */
    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_TYPE, bettergold.MODID);

    /** 金之牢狱：jigsaw 装配 + 出入口搬进空域（`bettergold:golden_prison`）。 */
    public static final DeferredHolder<StructureType<?>, StructureType<GoldenPrisonStructure>> GOLDEN_PRISON =
            STRUCTURE_TYPES.register("golden_prison", () -> () -> GoldenPrisonStructure.CODEC);

    private AllStructures() {
    }
}
