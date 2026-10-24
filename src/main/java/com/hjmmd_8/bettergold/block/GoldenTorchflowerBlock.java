package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.registry.AllBlocks;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.item.component.SuspiciousStewEffects;

/**
 * 金火把花（成熟方块，1.7 轮5，会话标记 {@code bg-n10r5}）。
 *
 * <p><b>作者原话</b>：「金火把花不仅能提供 <b>16 点</b>的亮度（顺带也兼容一下<b>花盆</b>样式）
 * 还能在<b>酿造台</b>上以炼金燃油为基、以金火把花为引即可酿制成高精度炼金油」。</p>
 *
 * <h2>亮度：作者给 16，落实现值 = 15（差 1 点，原因写在下面，A 级有读数）</h2>
 * <p>原版方块光照上限就是 <b>15</b>：{@code LightEngine.MAX_LEVEL = 15}；
 * 光照位图 {@code DataLayer} 每方块只有 <b>4 bit</b>，写入时是
 * {@code int l = (value & 15) << 4 * j}（{@code DataLayer#set(int,int)}）——
 * 也就是说把 <b>16</b> 直接交给引擎会被<b>掩成 0</b>（不是 15），方块会一点都不亮。
 * ⇒ 所以这里用 {@link #AUTHOR_LIGHT} 保留作者原数（= 16，供记账与文档引用），
 * 真正喂给 {@code BlockBehaviour.Properties#lightLevel} 的是 {@link #ENGINE_LIGHT} = {@code min(15, 16)} = <b>15</b>
 * ＝"原版能表达的最大亮度"，与作者"满亮"的意图一致。A 级实测读数见
 * {@code docs/bgn10r5-证据/01-A级读数.txt}（{@code getLightEmission = 15} / 方块光 = 15）。</p>
 *
 * <h2>花盆</h2>
 * <p>花盆兼容在 1.21.1 是<b>三件事</b>：① 本方块要能被 {@code FlowerPotBlock} 认成"可入盆的花"
 * （由 {@code AllBlocks#POTTED_GOLDEN_TORCHFLOWER} 的构造调用 {@code FlowerPotBlock#addPlant} 完成）；
 * ② 要有 {@code potted_*} 方块；③ 要进 {@code #minecraft:flower_pots}（数据标签）。
 * 渲染不额外画图：{@code models/block/potted_golden_torchflower.json} 直接继承
 * {@code minecraft:block/flower_pot_cross}，花盆体与泥土都取原版贴图，只把 {@code #plant}
 * 指向本方块贴图 ⇒ <b>零新增手绘像素</b>。</p>
 *
 * <h2>为什么还要覆写 {@code mayPlaceOn}</h2>
 * <p>{@link FlowerBlock} 继承 {@code BushBlock}，其默认判据是
 * 「下方 ∈ {@code #minecraft:dirt} 或 是原版耕地」。而金染耕地
 * （{@code GoldInfusedFarmlandBlock}）既不在 dirt 标签里、也<b>不是</b> {@code FarmBlock} 子类
 * ⇒ 不覆写的话，作物长成的花会在下一次邻接更新的 {@code canSurvive} 里<b>当场掉落</b>
 * （不报错、静默消失）。这里取「原版判据 ∪ 金染耕地」：既保住"花可以像普通花一样种在土上"
 * 的原版行为，也让金染耕地上长出来的那一朵站得住。</p>
 *
 * <p>⚠ <b>上面那句「∪ 金染耕地」是 1.7 轮5 的旧口径，原文保留不删</b>：作者 2026-10-24 第 ① 条
 * 追加了<b>金染土</b>⇒ 现行是「原版判据 ∪ 金染耕地 ∪ 金染土」（见下面 {@link #mayPlaceOn}）。</p>
 */
public class GoldenTorchflowerBlock extends FlowerBlock {

    /** 作者原话给的亮度（= 16）。⚠ 原版引擎上限 15，见类注释 */
    public static final int AUTHOR_LIGHT = 16;

    /** 真正喂给光照引擎的值 = {@code min(15, AUTHOR_LIGHT)} = 15 */
    public static final int ENGINE_LIGHT = Math.min(15, AUTHOR_LIGHT);

    /**
     * 迷之炖菜的**伤害吸收**时长：作者 2026-10-18 原话「**16 秒的伤害吸收三**」⇒ 16 × 20 = <b>320 tick</b>。
     *
     * <p>⚠ 1.21.1 的 {@code SuspiciousStewEffects.Entry} 只有 {@code (effect, duration)}、<b>没有 amplifier</b>
     * （读 `neoforge-21.1.228-sources` 确认），所以这里能声明的是「absorption / 320 tick」，
     * III 级（amplifier 2）由 {@code ModEvents#onGoldenTorchflowerStew} 在喝下那一刻补上；
     * 这个常量是两处**唯一共用**的时长真源（关卡钉住两边都引用它、不各写一份 320）。</p>
     */
    public static final int STEW_TICKS = 16 * 20;

    public GoldenTorchflowerBlock(BlockBehaviour.Properties properties) {
        // 1.7 `bg-n10fix` ③（作者 2026-10-18）：「金火把花可以作为迷之炖菜用 ⇒ 16 秒的伤害吸收三」
        // ⚠ 旧口径（原文保留）：「作者没提"可疑的炖菜"效果 ⇒ 用 EMPTY（零效果），不发明炖菜 buff」
        //   —— 已被作者本轮推翻；现行 = absorption / 16 秒（III 级在饮用时补齐，见 STEW_TICKS 注释）。
        super(net.minecraft.world.effect.MobEffects.ABSORPTION, STEW_TICKS / 20.0F, properties);
    }

    /**
     * 原版 {@code BushBlock} 的判据 ∪ 金染耕地 ∪ <b>金染土</b>（理由见类注释末段）。
     *
     * <p><b>1.7 作者 2026-10-24 第 ① 条（{@code gpt} 轮）</b>：「长成的金火把花能放在<b>金染土</b>上」
     * —— 旧口径只有「原版判据 ∪ 金染耕地」，金染土上放不上去（{@code canSustainPlant} 对花方块返回
     * {@code TriState.DEFAULT} ⇒ 回落到这里的 {@code mayPlaceOn}，而金染土不在 {@code #minecraft:dirt}
     * 里、也不是 {@code FarmBlock} ⇒ 拒）。现行口径 = 再并上 {@code gold_infused_dirt} 这一件方块。</p>
     *
     * <p>⚠ <b>没有动金染土那一侧的白名单</b>（{@link GoldInfusedDirtBlock#canSustainPlant} 仍然只放行
     * 金玫瑰丛）：本方法属于「花自己愿意长在哪」，与「土愿意养什么」是两个方向；
     * 在那里放行金火把花会顺带影响所有走 {@code canSustainPlant} 的路径，范围更大、没有必要。</p>
     *
     * <p>⚠ <b>负向保持</b>：普通耕地 / 普通土 / 石头仍然不可（{@code super.mayPlaceOn} 的原版判据 ∪
     * 上述两块，没有别的入口）；金染耕地仍然可（既有那条一个字节没动）。
     * <b>花盆</b>不受影响：{@code FlowerPotBlock} 走的是
     * {@code FlowerPotBlock#addPlant} 的白名单（{@code AllBlocks#POTTED_GOLDEN_TORCHFLOWER}），
     * 与本方法无关。</p>
     */
    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        // 1.7 第 ① 条：金染土（gold_infused_dirt）也允许
        return state.is(AllBlocks.GOLD_INFUSED_DIRT.get())
                || state.getBlock() instanceof GoldInfusedFarmlandBlock
                || super.mayPlaceOn(state, level, pos);
    }

    /** 显式暴露一次，便于探针 / 关卡读"这个方块声明了多少亮度"（返回 15，见类注释） */
    @Override
    public int getLightEmission(BlockState state, BlockGetter level, BlockPos pos) {
        return ENGINE_LIGHT;
    }
}
