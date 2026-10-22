package com.hjmmd_8.bettergold.registry;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 模组自定义音效（第八轮，2026-10-22：金钱妖音效）。
 *
 * <p>作者原话：「补充一下金钱妖的音效（因为人家是<b>浮空</b>的所以<b>不需要什么走路音效</b>，
 * 所以之前用的<b>僵尸音效请给它毙掉</b>）」「这个<code>E:\mc\mc资料\金钱妖声音.zip</code> 这个地方是
 * 金钱妖的声音，还有就是金桥。这些声音发生的时候，如果<b>开了声音字幕，最好在声音字幕那里显示</b>」。</p>
 *
 * <h2>素材来源与转码（只读，绝不改原始 zip）</h2>
 * <ul>
 *   <li>zip 里 3 个文件（文件名 <b>.mp3</b>，实际容器 = <b>MP4</b>：HEVC 视频流 + AAC 音轨）：
 *       <code>金钱妖：刷刷响.mp3</code> 2.07 s / <code>金钱妖：受伤.mp3</code> 0.98 s /
 *       <code>金钱妖：死亡.mp3</code> 1.73 s。</li>
 *   <li>接入只取<b>音轨</b>（<code>-vn -map 0:a:0</code>）转 <b>ogg vorbis 单声道 44.1 kHz</b>
 *       （3D 定位音必须单声道，否则原版会当成"环境音"不做方位衰减）。</li>
 *   <li>清单与哈希：<code>docs\金钱妖声音-素材清单\素材清单.tsv</code>（含原 zip 的 SHA256）。</li>
 * </ul>
 *
 * <h2>字幕（<code>subtitles.*</code>）</h2>
 * <p>每个事件在 <code>assets/bettergold/sounds.json</code> 里都登记了 <code>subtitle</code> 键，
 * 语言键见 <code>assets/bettergold/lang/zh_cn.json</code> / <code>en_us.json</code> 的
 * <code>subtitles.bettergold.money_gremlin_*</code>。⚠ 没有 <code>subtitle</code> 的 sound event
 * 在"声音字幕"开时<b>不会显示任何文字</b>——这正是作者要求的"要在字幕里显示"。</p>
 *
 * <p>★ <b>「金桥」</b>：本 zip 里 <b>没有</b>任何名字含「桥 / bridge / 金桥」的文件（3 个文件全是金钱妖的
 * ambient / hurt / death）⇒ 本仓<b>没有接入金桥音效</b>，已按任务书"不要自己猜着接"回报作者。</p>
 */
public class AllSounds {

    /** 音效注册表（<code>bettergold:*</code>；在 {@code bettergold#register} 里挂到 mod 总线） */
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(Registries.SOUND_EVENT, bettergold.MODID);

    /** 金钱妖：刷刷响（作者文件名「金钱妖：刷刷响」，2.07 s）——环境音（ambient） */
    public static final DeferredHolder<SoundEvent, SoundEvent> MONEY_GREMLIN_AMBIENT =
            register("money_gremlin_ambient");

    /** 金钱妖：受伤（0.98 s）——受击音（hurt） */
    public static final DeferredHolder<SoundEvent, SoundEvent> MONEY_GREMLIN_HURT =
            register("money_gremlin_hurt");

    /** 金钱妖：死亡（1.73 s）——死亡音（death） */
    public static final DeferredHolder<SoundEvent, SoundEvent> MONEY_GREMLIN_DEATH =
            register("money_gremlin_death");

    /**
     * 注册一个 sound event。位置可变范围（{@code createVariableRangeEvent} = 16 格衰减）——
     * 生物音效就该是可变范围的；固定范围（{@code createFixedRangeEvent}）只用于玩家自己的界面音。
     */
    private static DeferredHolder<SoundEvent, SoundEvent> register(String name) {
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(
                ResourceLocation.fromNamespaceAndPath(bettergold.MODID, name)));
    }

    private AllSounds() {
    }
}
