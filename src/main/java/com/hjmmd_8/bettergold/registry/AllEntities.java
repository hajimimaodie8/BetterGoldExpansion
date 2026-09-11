package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.item.ThrownAntique;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 实体注册（新约 1.3）：掷出的"没人要的老古董"。
 */
public class AllEntities {

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, bettergold.MODID);

    public static final DeferredHolder<EntityType<?>, EntityType<ThrownAntique>> THROWN_ANTIQUE =
            ENTITY_TYPES.register("thrown_antique", () -> EntityType.Builder
                    .<ThrownAntique>of(ThrownAntique::new, MobCategory.MISC)
                    .sized(0.25F, 0.25F)
                    .clientTrackingRange(4)
                    .updateInterval(10)
                    .build("thrown_antique"));

    private AllEntities() {
    }
}
