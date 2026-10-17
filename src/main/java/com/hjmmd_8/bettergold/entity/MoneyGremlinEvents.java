package com.hjmmd_8.bettergold.entity;

import net.minecraft.world.damagesource.DamageTypes;

import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.EntityInvulnerabilityCheckEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;

/**
 * 金钱妖的两条伤害规则（游戏总线，注册在 {@code bettergold} 构造器里）。
 *
 * <ol>
 *   <li><b>免仙人掌伤害</b>（作者原话）：落点 = NeoForge 现成的
 *       {@link EntityInvulnerabilityCheckEvent} —— 与树棘金 / 混沌金器具的「仙人掌免疫」是<b>同款判据</b>
 *       （{@code MetalEvents#onCactusItemImmunity} 用的是同一个事件），<b>不需要 mixin</b>。
 *       {@code Entity#isInvulnerableTo} 已被 NeoForge 改走 {@code CommonHooks}，
 *       而 {@code LivingEntity#hurt} 的第一句就是它 ⇒ 置真即可。</li>
 *   <li><b>受到双倍火焰与岩浆伤害</b>（作者原话）：落点 = {@code LivingDamageEvent.Pre} 的
 *       {@code setNewDamage}。这个事件拿到的是「护甲 / 抗性算完之后真正要扣的数字」，
 *       从这里乘 2 才是玩家理解的「这次伤害翻倍」（与靛海金 / 烈火金 ×2 同一个落点口径）。</li>
 * </ol>
 *
 * <p>判据集合只在 {@link MoneyGremlin#isFireOrLava} 一处（避火 goal 的方块集合与之对齐）；</p>
 */
public final class MoneyGremlinEvents {

    @SubscribeEvent
    public static void onCactusImmunity(EntityInvulnerabilityCheckEvent event) {
        if (!(event.getEntity() instanceof MoneyGremlin)) {
            return;
        }
        if (event.getSource().is(DamageTypes.CACTUS)) {
            event.setInvulnerable(true);
        }
    }

    @SubscribeEvent
    public static void onFireOrLavaDamage(LivingDamageEvent.Pre event) {
        if (!(event.getEntity() instanceof MoneyGremlin)) {
            return;
        }
        if (!MoneyGremlin.isFireOrLava(event.getSource())) {
            return;
        }
        event.setNewDamage(event.getNewDamage() * 2.0F);
    }

    private MoneyGremlinEvents() {
    }
}
