package com.hjmmd_8.bettergold.material;

import java.util.List;
import java.util.function.Supplier;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.registry.AllSounds;

import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.damagesource.DamageTypes;

/**
 * 1.8 阶段 3 · 段 C（§I-36~40）：<b>12 枚转化之戒</b>的唯一真源表。
 *
 * <h2>id 与族的一一对应（§Z-5 已核定）</h2>
 * <p>{@code <族>_ring}：烈火→{@code flamegold}、点金→{@code sturdygold}、风起→{@code windgold}、
 * 木棘→{@code thornsgold}、幽爆→{@code echogold}、冰霜→{@code frostgold}、
 * 水压→{@code indigoseagold}、毒腺→{@code voodoogold}、雷波→{@code thundergold}、
 * 幻奏→{@code illusiongold}、混源稳定→{@code chaosgold}、分崩离析→{@code chaosalloy}。</p>
 *
 * <h2>「转化类型」只有 9 枚（不是 12）</h2>
 * <p>§I-38 表里 <b>幻奏 / 混源稳定 / 分崩离析</b> 三枚的「转化类型」一栏是 <b>—</b>：它们没有两种模式、
 * 也不改伤害类型 ⇒ 本枚举里这三枚的 {@link #convertedType} 是 {@code null}，
 * {@link #hasModes()} = false。**关卡按 12 行映射判**（9 个类型 + 3 个 none）。</p>
 *
 * <h2>音效（§I-38 那一列）</h2>
 * <p>全是<b>原版</b>音效，只有雷波是作者 zip 里的 <code>mp3</code>（转 ogg，见 {@link AllSounds#THUNDER_RING}）。
 * 点金那一栏写的是「原攻击音效」⇒ 本表 null = 不额外播放。</p>
 */
public enum RingType {

    /** 烈火：火焰（音效 = 火焰弹呼啸，{@code item.firecharge.use}） */
    FLAME("flamegold", DamageTypes.ON_FIRE, () -> SoundEvents.FIRECHARGE_USE, true),
    /** 点金：物理（原攻击音效 ⇒ 不额外播） */
    GILD("sturdygold", DamageTypes.GENERIC, null, true),
    /** 风起：风弹（音效 = 风弹爆裂） */
    WIND("windgold", DamageTypes.WIND_CHARGE, () -> SoundEvents.WIND_CHARGE_BURST.value(), true),
    /** 木棘：仙人掌（音效 = 甜浆果丛） */
    THORNS("thornsgold", DamageTypes.CACTUS, () -> SoundEvents.PLAYER_HURT_SWEET_BERRY_BUSH, true),
    /** 幽爆：监守者音波（音效 = 幽匿感测体颤动） */
    ECHO("echogold", DamageTypes.SONIC_BOOM, () -> SoundEvents.SCULK_CLICKING, true),
    /** 冰霜：冰冻（音效 = 玩家冻伤） */
    FROST("frostgold", DamageTypes.FREEZE, () -> SoundEvents.PLAYER_HURT_FREEZE, true),
    /** 水压：窒息（音效 = 玩家溺水） */
    PRESSURE("indigoseagold", DamageTypes.IN_WALL, () -> SoundEvents.PLAYER_HURT_DROWN, true),
    /** 毒腺：魔法（音效 = 玻璃瓶倒空） */
    VENOM("voodoogold", DamageTypes.MAGIC, () -> SoundEvents.BOTTLE_EMPTY, true),
    /** 雷波：闪电束（音效 = 作者 zip 里那个 mp3 转的 ogg） */
    THUNDER("thundergold", DamageTypes.LIGHTNING_BOLT, () -> AllSounds.THUNDER_RING.get(), true),
    /** 幻奏：无转化类型、无两种模式；攻击 100% 附带 3 分钟安抚二式 */
    PHANTOM("illusiongold", null, null, false),
    /** 混源稳定：无转化类型、无两种模式；混沌金/崩乱合金数值强制最大 + 耐久 64 */
    CHAOS_STABLE("chaosgold", null, null, false),
    /** 分崩离析：混源稳定的升级款（无耐久 + 双失衡 100%） */
    DISINTEGRATE("chaosalloy", null, null, false);

    /** 族 id（= 物品 id 前缀，与 {@code MetalFamily#byId} 对得上） */
    public final String metalId;
    /** 转化后的伤害类型；{@code null} = 不转化（幻奏 / 混源稳定 / 分崩离析） */
    public final @Nullable ResourceKey<DamageType> convertedType;
    /** 转化 / 使用时播放的音效；{@code null} = 不额外播 */
    public final @Nullable Supplier<SoundEvent> sound;
    /** 有没有「仅物理 / 全部」两种模式 */
    public final boolean modes;

    RingType(String metalId, @Nullable ResourceKey<DamageType> convertedType,
            @Nullable Supplier<SoundEvent> sound, boolean modes) {
        this.metalId = metalId;
        this.convertedType = convertedType;
        this.sound = sound;
        this.modes = modes;
    }

    /** 物品注册名（{@code <族>_ring}） */
    public String itemId() {
        return this.metalId + "_ring";
    }

    /** 物品语言键 */
    public String descriptionId() {
        return "item.bettergold." + itemId();
    }

    public boolean hasModes() {
        return this.modes;
    }

    /** 全部 12 枚（顺序固定 = §I-38 表序 + 三枚无类型的尾巴） */
    public static List<RingType> all() {
        return List.of(values());
    }

    /** 按族 id 反查（没有 = null） */
    public static @Nullable RingType byMetalId(String metalId) {
        for (RingType type : values()) {
            if (type.metalId.equals(metalId)) {
                return type;
            }
        }
        return null;
    }
}
