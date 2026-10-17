package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.entity.ChaosCoinProjectile;
import com.hjmmd_8.bettergold.entity.MoneyGremlin;
import com.hjmmd_8.bettergold.item.ThrownAntique;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 实体注册：新约 1.3 的投掷物「没人要的老古董」+ 1.7 轮6 的<b>本仓第一个活体生物</b>（金钱妖）
 * 与它的弹射物（混沌金币）。
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

    /**
     * 金钱妖（1.7 · 轮6，作者：金钱妖）。
     *
     * <p>这是本模组<b>第一个活体生物</b>：属性在 {@code EntityAttributeCreationEvent} 里创建
     * （{@code MoneyGremlin#createAttributes}）、渲染器在 {@code bettergoldClient} 注册、
     * 生成蛋在 {@code AllItems} 注册、自然生成规则在 {@code RegisterSpawnPlacementsEvent} +
     * {@code data/bettergold/neoforge/biome_modifier/add_money_gremlin.json}。</p>
     *
     * <p>命中箱 1.2 × 1.2 是工作值：模型最宽处是圆环直径 26.8 px ≈ 1.675 格、最高处 ≈ 1.375 格
     * （见 {@code MoneyGremlinModel}），取 1.2 让近战判定与视觉尺寸都不离谱。</p>
     */
    public static final DeferredHolder<EntityType<?>, EntityType<MoneyGremlin>> MONEY_GREMLIN =
            ENTITY_TYPES.register("money_gremlin", () -> EntityType.Builder
                    .of(MoneyGremlin::new, MobCategory.MONSTER)
                    .sized(1.2F, 1.2F)
                    .clientTrackingRange(10)
                    .updateInterval(3)
                    .build("money_gremlin"));

    /**
     * 混沌金币（弹射物，1.7 · 轮6）：与物品 {@code chaos_coin} 同名 —— 实体与物品是两个注册表，
     * 立档 §2.0 的命名表就是这么定的。投掷物模板照 {@link #THROWN_ANTIQUE}。
     */
    public static final DeferredHolder<EntityType<?>, EntityType<ChaosCoinProjectile>> CHAOS_COIN =
            ENTITY_TYPES.register("chaos_coin", () -> EntityType.Builder
                    .<ChaosCoinProjectile>of(ChaosCoinProjectile::new, MobCategory.MISC)
                    .sized(0.25F, 0.25F)
                    .clientTrackingRange(4)
                    .updateInterval(10)
                    .build("chaos_coin"));

    private AllEntities() {
    }
}
