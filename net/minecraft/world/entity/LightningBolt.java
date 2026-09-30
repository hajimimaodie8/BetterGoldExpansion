package net.minecraft.world.entity;

import com.google.common.collect.Sets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import javax.annotation.Nullable;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseFireBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightningRodBlock;
import net.minecraft.world.level.block.WeatheringCopper;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

public class LightningBolt extends Entity {
    private static final int START_LIFE = 2;
    private static final double DAMAGE_RADIUS = 3.0;
    private static final double DETECTION_RADIUS = 15.0;
    private int life;
    public long seed;
    private int flashes;
    private boolean visualOnly;
    @Nullable
    private ServerPlayer cause;
    private final Set<Entity> hitEntities = Sets.newHashSet();
    private int blocksSetOnFire;
    private float damage = 5.0F;

    public LightningBolt(EntityType<? extends LightningBolt> entityType, Level level) {
        super(entityType, level);
        this.noCulling = true;
        this.life = 2;
        this.seed = this.random.nextLong();
        this.flashes = this.random.nextInt(3) + 1;
    }

    public void setVisualOnly(boolean visualOnly) {
        this.visualOnly = visualOnly;
    }

    @Override
    public SoundSource getSoundSource() {
        return SoundSource.WEATHER;
    }

    @Nullable
    public ServerPlayer getCause() {
        return this.cause;
    }

    public void setCause(@Nullable ServerPlayer cause) {
        this.cause = cause;
    }

    private void powerLightningRod() {
        BlockPos blockpos = this.getStrikePosition();
        BlockState blockstate = this.level().getBlockState(blockpos);
        // Neo: support custom LightningRodBlocks
        if (blockstate.getBlock() instanceof LightningRodBlock) {
            ((LightningRodBlock)blockstate.getBlock()).onLightningStrike(blockstate, this.level(), blockpos);
        }
    }

    public void setDamage(float damage) {
        this.damage = damage;
    }

    public float getDamage() {
        return this.damage;
    }

    @Override
    public void tick() {
        super.tick();
        if (this.life == 2) {
            if (this.level().isClientSide()) {
                this.level()
                    .playLocalSound(
                        this.getX(),
                        this.getY(),
                        this.getZ(),
                        SoundEvents.LIGHTNING_BOLT_THUNDER,
                        SoundSource.WEATHER,
                        10000.0F,
                        0.8F + this.random.nextFloat() * 0.2F,
                        false
                    );
                this.level()
                    .playLocalSound(
                        this.getX(),
                        this.getY(),
                        this.getZ(),
                        SoundEvents.LIGHTNING_BOLT_IMPACT,
                        SoundSource.WEATHER,
                        2.0F,
                        0.5F + this.random.nextFloat() * 0.2F,
                        false
                    );
            } else {
                Difficulty difficulty = this.level().getDifficulty();
                if (difficulty == Difficulty.NORMAL || difficulty == Difficulty.HARD) {
                    this.spawnFire(4);
                }

                this.powerLightningRod();
                clearCopperOnLightningStrike(this.level(), this.getStrikePosition());
                this.gameEvent(GameEvent.LIGHTNING_STRIKE);
            }
        }

        this.life--;
        if (this.life < 0) {
            if (this.flashes == 0) {
                if (this.level() instanceof ServerLevel) {
                    List<Entity> list = this.level()
                        .getEntities(
                            this,
                            new AABB(
                                this.getX() - 15.0, this.getY() - 15.0, this.getZ() - 15.0, this.getX() + 15.0, this.getY() + 6.0 + 15.0, this.getZ() + 15.0
                            ),
                            p_147140_ -> p_147140_.isAlive() && !this.hitEntities.contains(p_147140_)
                        );

                    for (ServerPlayer serverplayer : ((ServerLevel)this.level()).getPlayers(p_325666_ -> p_325666_.distanceTo(this) < 256.0F)) {
                        CriteriaTriggers.LIGHTNING_STRIKE.trigger(serverplayer, this, list);
                    }
                }

                this.discard();
            } else if (this.life < -this.random.nextInt(10)) {
                this.flashes--;
                this.life = 1;
                this.seed = this.random.nextLong();
                this.spawnFire(0);
            }
        }

        if (this.life >= 0) {
            if (!(this.level() instanceof ServerLevel)) {
                this.level().setSkyFlashTime(2);
            } else if (!this.visualOnly) {
                List<Entity> list1 = this.level()
                    .getEntities(
                        this,
                        new AABB(this.getX() - 3.0, this.getY() - 3.0, this.getZ() - 3.0, this.getX() + 3.0, this.getY() + 6.0 + 3.0, this.getZ() + 3.0),
                        Entity::isAlive
                    );

                for (Entity entity : list1) {
                    if (!net.neoforged.neoforge.event.EventHooks.onEntityStruckByLightning(entity, this))
                    entity.thunderHit((ServerLevel)this.level(), this);
                }

                this.hitEntities.addAll(list1);
                if (this.cause != null) {
                    CriteriaTriggers.CHANNELED_LIGHTNING.trigger(this.cause, list1);
                }
            }
        }
    }

    private BlockPos getStrikePosition() {
        Vec3 vec3 = this.position();
        return BlockPos.containing(vec3.x, vec3.y - 1.0E-6, vec3.z);
    }

    private void spawnFire(int extraIgnitions) {
        if (!this.visualOnly && !this.level().isClientSide && this.level().getGameRules().getBoolean(GameRules.RULE_DOFIRETICK)) {
            BlockPos blockpos = this.blockPosition();
            BlockState blockstate = BaseFireBlock.getState(this.level(), blockpos);
            if (this.level().getBlockState(blockpos).isAir() && blockstate.canSurvive(this.level(), blockpos)) {
                this.level().setBlockAndUpdate(blockpos, blockstate);
                this.blocksSetOnFire++;
            }

            for (int i = 0; i < extraIgnitions; i++) {
                BlockPos blockpos1 = blockpos.offset(this.random.nextInt(3) - 1, this.random.nextInt(3) - 1, this.random.nextInt(3) - 1);
                blockstate = BaseFireBlock.getState(this.level(), blockpos1);
                if (this.level().getBlockState(blockpos1).isAir() && blockstate.canSurvive(this.level(), blockpos1)) {
                    this.level().setBlockAndUpdate(blockpos1, blockstate);
                    this.blocksSetOnFire++;
                }
            }
        }
    }

    private static void clearCopperOnLightningStrike(Level level, BlockPos pos) {
        BlockState blockstate = level.getBlockState(pos);
        BlockPos blockpos;
        BlockState blockstate1;
        // Neo: support custom LightningRodBlocks
        if (blockstate.getBlock() instanceof LightningRodBlock) {
            blockpos = pos.relative(blockstate.getValue(LightningRodBlock.FACING).getOpposite());
            blockstate1 = level.getBlockState(blockpos);
        } else {
            blockpos = pos;
            blockstate1 = blockstate;
        }

        if (blockstate1.getBlock() instanceof WeatheringCopper) {
            level.setBlockAndUpdate(blockpos, WeatheringCopper.getFirst(level.getBlockState(blockpos)));
            BlockPos.MutableBlockPos blockpos$mutableblockpos = pos.mutable();
            int i = level.random.nextInt(3) + 3;

            for (int j = 0; j < i; j++) {
                int k = level.random.nextInt(8) + 1;
                randomWalkCleaningCopper(level, blockpos, blockpos$mutableblockpos, k);
            }
        }
    }

    private static void randomWalkCleaningCopper(Level level, BlockPos pos, BlockPos.MutableBlockPos mutable, int steps) {
        mutable.set(pos);

        for (int i = 0; i < steps; i++) {
            Optional<BlockPos> optional = randomStepCleaningCopper(level, mutable);
            if (optional.isEmpty()) {
                break;
            }

            mutable.set(optional.get());
        }
    }

    private static Optional<BlockPos> randomStepCleaningCopper(Level level, BlockPos pos) {
        for (BlockPos blockpos : BlockPos.randomInCube(level.random, 10, pos, 1)) {
            BlockState blockstate = level.getBlockState(blockpos);
            if (blockstate.getBlock() instanceof WeatheringCopper) {
                WeatheringCopper.getPrevious(blockstate).ifPresent(p_147144_ -> level.setBlockAndUpdate(blockpos, p_147144_));
                level.levelEvent(3002, blockpos, -1);
                return Optional.of(blockpos);
            }
        }

        return Optional.empty();
    }

    /**
     * Checks if the entity is in range to render.
     */
    @Override
    public boolean shouldRenderAtSqrDistance(double distance) {
        double d0 = 64.0 * getViewScale();
        return distance < d0 * d0;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
    }

    /**
     * (abstract) Protected helper method to read subclass entity data from NBT.
     */
    @Override
    protected void readAdditionalSaveData(CompoundTag compound) {
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag compound) {
    }

    public int getBlocksSetOnFire() {
        return this.blocksSetOnFire;
    }

    public Stream<Entity> getHitEntities() {
        return this.hitEntities.stream().filter(Entity::isAlive);
    }
}
