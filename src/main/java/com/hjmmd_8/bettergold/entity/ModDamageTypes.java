package com.hjmmd_8.bettergold.entity;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;

/**
 * 本模组自己的两个伤害类型（1.7 · 轮6 金钱妖）。
 *
 * <p>为什么不用 {@code damageSources().mobAttack(...)}：原版对<b>玩家</b>受到的伤害会按难度再乘一次
 * （{@code IScalingFunction.DEFAULT}：简单 {@code min(x/2+1, x)}、困难 {@code x*1.5}），
 * 而作者给的是<b>显式查表</b>（近战 4/8/12、弹射物 2/4/6，见立档 §10.1）——
 * 再叠一层原版换算就会变成「简单 3 / 困难 18」。所以这两个伤害类型的 JSON 里
 * {@code "scaling": "never"}，表里的数就是最终数。</p>
 *
 * <p>JSON 落点：{@code data/bettergold/damage_type/{money_gremlin_melee,chaos_coin}.json}；
 * 死亡提示语言键：{@code death.attack.bettergold.<message_id>}。</p>
 */
public final class ModDamageTypes {

    /** 金钱妖的近战（显式难度表 4/8/12） */
    public static final ResourceKey<DamageType> MONEY_GREMLIN_MELEE = key("money_gremlin_melee");
    /** 混沌金币弹射物（显式难度表 2/4/6） */
    public static final ResourceKey<DamageType> CHAOS_COIN = key("chaos_coin");

    /**
     * 巫毒爆发（效果自然到期时的结算伤害）。
     *
     * <p><b>1.7 大轮（2026-10-24，`bgbig`）第 A3 条</b>：作者再次强调「巫毒爆发必须是魔法伤害
     * （不再是物理伤害）」。旧口径用的是原版 {@code minecraft:magic}（它本身就在
     * {@code #minecraft:bypasses_armor} 里，理论上不吃护甲点）；本轮改成<b>自带 damage type</b>
     * {@code bettergold:voodoo_burst}，并在
     * {@code data/minecraft/tags/damage_type/bypasses_armor.json} 里显式登记
     * ⇒ 不依赖原版标签的既有内容，也不会被别的数据包对 {@code minecraft:magic} 的改动波及。</p>
     *
     * <p>JSON 落点：{@code data/bettergold/damage_type/voodoo_burst.json}；
     * {@code message_id = "magic"} ⇒ 死亡提示复用原版 {@code death.attack.magic}，不新增语言键；
     * {@code scaling = "when_caused_by_living_non_player"} 与 {@code minecraft:magic} 逐字同档
     * （伤害数字与旧口径一致，只有类型 id 变了）。</p>
     */
    public static final ResourceKey<DamageType> VOODOO_BURST = key("voodoo_burst");

    private static ResourceKey<DamageType> key(String path) {
        return ResourceKey.create(Registries.DAMAGE_TYPE,
                ResourceLocation.fromNamespaceAndPath(bettergold.MODID, path));
    }

    /**
     * 取一个伤害源；{@code direct} = 直接来源（弹射物本身），{@code causing} = 真正造成者（金钱妖）。
     *
     * <p>两个都允许为 {@code null}（原版 {@code DamageSource} 的构造器就是这么定义的）。</p>
     */
    public static DamageSource source(Level level, ResourceKey<DamageType> damageType,
            @Nullable Entity direct, @Nullable Entity causing) {
        return new DamageSource(
                level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(damageType),
                direct, causing);
    }

    private ModDamageTypes() {
    }
}
