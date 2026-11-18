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
 * 1.8（bg25 §B-9）金丝树叶落叶粒子 —— 逐行照搬原版 {@code CherryParticle}
 * （`neoforge-21.1.228-sources` 的 {@code client/particle/CherryParticle.java}）。
 *
 * <p>作者要求「直接照搬樱花树叶」，所以寿命 300、重力 7.5E-4、旋转 ±30°、旋进 ±5°、
 * 末端风速 2.0 的曲线、{@code PARTICLE_SHEET_OPAQUE} 渲染类型都<b>一个数没改</b>；
 * 唯一区别是 sprite 来自我们的 12 帧清单（{@code particles/gold_silk_leaves.json}）。</p>
 */
@OnlyIn(Dist.CLIENT)
public class GoldSilkLeafParticle extends TextureSheetParticle {

    private static final float ACCELERATION_SCALE = 0.0025F;
    private static final int INITIAL_LIFETIME = 300;
    private static final int CURVE_ENDPOINT_TIME = 300;
    private static final float FALL_ACC = 0.25F;
    private static final float WIND_BIG = 2.0F;

    private float rotSpeed;
    private final float particleRandom;
    private final float spinAcceleration;

    protected GoldSilkLeafParticle(ClientLevel level, double x, double y, double z, SpriteSet spriteSet) {
        super(level, x, y, z);
        this.setSprite(spriteSet.get(this.random.nextInt(12), 12));
        this.rotSpeed = (float) Math.toRadians(this.random.nextBoolean() ? -30.0 : 30.0);
        this.particleRandom = this.random.nextFloat();
        this.spinAcceleration = (float) Math.toRadians(this.random.nextBoolean() ? -5.0 : 5.0);
        this.lifetime = INITIAL_LIFETIME;
        this.gravity = 7.5E-4F;
        float f = this.random.nextBoolean() ? 0.05F : 0.075F;
        this.quadSize = f;
        this.setSize(f, f);
        this.friction = 1.0F;
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_OPAQUE;
    }

    @Override
    public void tick() {
        this.xo = this.x;
        this.yo = this.y;
        this.zo = this.z;
        if (this.lifetime-- <= 0) {
            this.remove();
        }
        if (!this.removed) {
            float f = (float) (INITIAL_LIFETIME - this.lifetime);
            float f1 = Math.min(f / (float) CURVE_ENDPOINT_TIME, 1.0F);
            double d0 = Math.cos(Math.toRadians(this.particleRandom * 60.0F)) * WIND_BIG
                    * Math.pow(f1, 1.25D);
            double d1 = Math.sin(Math.toRadians(this.particleRandom * 60.0F)) * WIND_BIG
                    * Math.pow(f1, 1.25D);
            this.xd += d0 * ACCELERATION_SCALE;
            this.zd += d1 * ACCELERATION_SCALE;
            this.yd -= this.gravity;
            this.rotSpeed += this.spinAcceleration / 20.0F;
            this.oRoll = this.roll;
            this.roll += this.rotSpeed / 20.0F;
            this.move(this.xd, this.yd, this.zd);
            if (this.onGround || this.lifetime < INITIAL_LIFETIME - 1 && (this.xd == 0.0D || this.zd == 0.0D)) {
                this.remove();
            }
            if (!this.removed) {
                this.xd *= this.friction;
                this.yd *= this.friction;
                this.zd *= this.friction;
            }
        }
    }

    /** 1.21.1 的 provider 形状：{@code SpriteSet} 由粒子定义里的 12 张图生成 */
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
            return new GoldSilkLeafParticle(level, x, y, z, this.sprites);
        }
    }
}
