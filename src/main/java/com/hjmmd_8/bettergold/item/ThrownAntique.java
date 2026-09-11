package com.hjmmd_8.bettergold.item;

import com.hjmmd_8.bettergold.registry.AllEntities;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;

/**
 * 掷出的"没人要的老古董"：命中造成 3 点伤害（新约 1.3）。
 */
public class ThrownAntique extends ThrowableItemProjectile {

    /** 命中伤害 */
    public static final float DAMAGE = 3.0F;

    public ThrownAntique(EntityType<? extends ThrownAntique> type, Level level) {
        super(type, level);
    }

    public ThrownAntique(Level level, LivingEntity shooter) {
        super(AllEntities.THROWN_ANTIQUE.get(), shooter, level);
    }

    public ThrownAntique(Level level, double x, double y, double z) {
        super(AllEntities.THROWN_ANTIQUE.get(), x, y, z, level);
    }

    @Override
    protected Item getDefaultItem() {
        return AllItems.UNWANTED_ANTIQUE.get();
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        super.onHitEntity(result);
        Entity target = result.getEntity();
        Entity owner = this.getOwner();
        target.hurt(this.damageSources().thrown(this, owner), DAMAGE);
    }
}
