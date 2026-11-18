package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 1.8（bg25）专属粒子类型。
 *
 * <ul>
 *   <li>{@link #GOLD_SILK_LEAVES}：金丝树叶落叶，12 帧素材
 *       （{@code 金丝树叶粒子/0..11.png}），行为照搬 {@code CherryParticle}。</li>
 *   <li>{@link #GOLDEN_GROWTH}：金骨粉 / 黄金国浮现之尘的催熟粒子，单帧 8×8 素材
 *       （{@code 金骨粉和黄金国浮现之尘的粒子.png}）。</li>
 * </ul>
 *
 * <p>贴图清单在 {@code assets/bettergold/particles/gold_silk_leaves.json} 与
 * {@code golden_growth.json}，客户端 provider 在
 * {@code bettergoldClient#onRegisterParticleProviders} 注册。</p>
 */
public class AllParticles {

    public static final DeferredRegister<ParticleType<?>> PARTICLE_TYPES =
            DeferredRegister.create(Registries.PARTICLE_TYPE, bettergold.MODID);

    /** 金丝树叶落叶（12 帧） */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> GOLD_SILK_LEAVES =
            PARTICLE_TYPES.register("gold_silk_leaves", () -> new SimpleParticleType(false));

    /** 金骨粉 / 黄金国浮现之尘的催熟粒子（单帧 8×8） */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> GOLDEN_GROWTH =
            PARTICLE_TYPES.register("golden_growth", () -> new SimpleParticleType(false));

    private AllParticles() {
    }
}
