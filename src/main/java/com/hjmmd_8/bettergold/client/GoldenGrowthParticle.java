package com.hjmmd_8.bettergold.client;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;

/**
 * 1.8（bg25 §C-12）金骨粉 / 黄金国浮现之尘的专属催熟粒子。
 *
 * <p>素材 = {@code 金骨粉和黄金国浮现之尘的粒子.png}（8×8，单帧）。形态取原版
 * {@code HappyVillagerParticle} 的「向上飘 + 随机散开」手感（作者要的是「催熟粒子」，
 * 不是落叶），但贴图用自己的。单帧纹理清单见 {@code particles/golden_growth.json}。</p>
 */
@OnlyIn(Dist.CLIENT)
public class GoldenGrowthParticle extends TextureSheetParticle {

    protected GoldenGrowthParticle(ClientLevel level, double x, double y, double z,
                                   double xSpeed, double ySpeed, double zSpeed, SpriteSet sprites) {
        super(level, x, y, z, 0.0D, 0.0D, 0.0D);
        this.setSprite(sprites.get(this.random));
        this.lifetime = 16 + this.random.nextInt(8);
        this.quadSize = 0.18F + this.random.nextFloat() * 0.12F;
        this.setSize(this.quadSize, this.quadSize);
        this.gravity = -0.02F;
        this.friction = 0.96F;
        this.xd = xSpeed + (this.random.nextDouble() - 0.5D) * 0.12D;
        this.yd = ySpeed + this.random.nextDouble() * 0.12D;
        this.zd = zSpeed + (this.random.nextDouble() - 0.5D) * 0.12D;
        this.roll = (float) (Math.PI * this.random.nextFloat());
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    @Override
    public void tick() {
        this.oRoll = this.roll;
        this.roll += 0.12F;
        super.tick();
        this.xd *= 0.98D;
        this.zd *= 0.98D;
    }

    @OnlyIn(Dist.CLIENT)
    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public net.minecraft.client.particle.Particle createParticle(SimpleParticleType type,
                                                                     ClientLevel level,
                                                                     double x, double y, double z,
                                                                     double xSpeed, double ySpeed, double zSpeed) {
            return new GoldenGrowthParticle(level, x, y, z, xSpeed, ySpeed, zSpeed, this.sprites);
        }
    }
}
