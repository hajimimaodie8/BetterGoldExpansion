package com.hjmmd_8.bettergold.block;

import com.hjmmd_8.bettergold.menu.SturdygoldAnvilMenu;
import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AnvilBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * <b>万坚金砧</b>（1.7 {@code bg-n10} 轮8，{@code bettergold:sturdygold_anvil}）。
 *
 * <h2>作者原话（立档 §2.14，逐字）</h2>
 * <ul>
 *   <li>「<b>无法破坏</b>」；</li>
 *   <li>「一样会<b>互斥附魔</b>」；</li>
 *   <li>「主要功能为可以<b>使用混沌金币串修复装备</b>，且以这种方式的修复<b>无法累积惩罚</b>（就是不会出现过于昂贵）」；</li>
 *   <li>「以及<b>下落时根据坠落高度对被砸到的目标造成最多 16% 目标当前生命值的伤害</b>」；</li>
 *   <li>（配方另立，见 {@code data/bettergold/recipe/sturdygold_anvil.json}）</li>
 * </ul>
 *
 * <h2>技术路线（立档 §4 歧义 ⑯-b 未裁 ⇒ 本轮取「继承 {@link AnvilBlock} + 自建 Menu/Screen」）</h2>
 * <p><b>为什么可以两者兼得</b>：{@link AnvilBlock} 只提供「形状 / 四向 facing / 下落方块 / 右键开界面」
 * 这几件与"界面长什么样"无关的东西；界面由 {@code getMenuProvider} 返回的 {@link MenuProvider} 决定。
 * 所以方块照原版继承（形状、朝向、下落行为全部直接复用原版），界面换成自己的
 * {@link SturdygoldAnvilMenu} + {@code client/SturdygoldAnvilScreen}（256×256 贴图、176×166 主面板）。</p>
 *
 * <h2>① 「无法破坏」的精确含义（D15 / 立档 §2.14 可执行口径 1）</h2>
 * <pre>    Properties.ofFullCopy(Blocks.ANVIL).strength(-1.0F, 3600000.0F)</pre>
 * <p>{@code destroyTime = -1.0F} ⇒ <b>生存与创造都挖不掉</b>（客户端 {@code getDestroySpeed} 为负直接不累计挖掘进度，
 * 服务端 {@code Player#blockActionRestricted} 也拦）；{@code explosionResistance = 3,600,000}
 * ＝原版基岩 / 命令方块的写法（硬度 −1、抗爆 360 万）⇒ 抗爆<b>高于</b>原版砧的 1200。口径记在
 * {@code docs/1.7-...md} §17。</p>
 *
 * <h2>② 「无法破坏」与「下落会受损 / 消失」的关系（★ 派单要求写清）</h2>
 * <p>原版砧掉落时有两套"受损"路径，<b>本方块两条都不触发</b>：</p>
 * <ol>
 *   <li><b>砸到实体后自己裂开</b>：{@code FallingBlockEntity#causeFallDamage} 里有一段
 *       {@code if (this.blockState.is(BlockTags.ANVIL) && random < 0.05 + i*0.05) { AnvilBlock.damage(...) }}
 *       —— <b>它的守卫就是 {@code #minecraft:anvil} 这个方块标签</b>。本方块<b>刻意不进该标签</b>
 *       （{@code AnvilMenu#isValidBlock} 已被 {@link SturdygoldAnvilMenu} 覆写，不需要标签），
 *       于是那条随机碎裂 / {@code cancelDrop} <b>根本不会命中</b> ⇒ 砸完实体后照常落地变回方块。</li>
 *   <li><b>用砧时磨损</b>（{@code AnvilMenu#onTake} 里的 {@code breakChance} → {@code AnvilBlock#damage}）：
 *       我们的菜单 {@code onTake} 走自己的分支，<b>不调</b> {@code AnvilBlock.damage} ⇒ 永不磨损。</li>
 * </ol>
 * <p><b>仍然会"消失"的唯一情形</b>＝原版下落方块的通则：落地位置<b>放不下</b>（被占 / 不能存活）时
 * 方块实体碎裂、按 {@code dropItem = true} 掉落<b>方块物品</b>（{@code FallingBlockEntity} 第 200-215 行），
 * 与"能不能被玩家挖掉"是两件不同的事。这条<b>不</b>算"破坏"，也没有物品损失。</p>
 *
 * <h2>③ 下落砸人</h2>
 * <p>见 {@link SturdygoldAnvilFallDamage}（公式的唯一实现）。本类只做一件事：把"
 * 每格 1 点的<b>高度信号</b>"交给原版 {@code FallingBlockEntity}，让它在落地时对箱内的活体
 * 调一次 {@code hurt}（原版路径：{@code causeFallDamage} 第 241-268 行），真正的百分比伤害在
 * {@code LivingDamageEvent.Pre} 里换成「{@code min(16%, 1% × 格数) × 目标当前生命值}」。</p>
 */
public class SturdygoldAnvilBlock extends AnvilBlock {

    /**
     * ⚠ 必须覆写：{@link AnvilBlock#CODEC} 是 {@code simpleCodec(AnvilBlock::new)}，不覆写就会反序列化成原版砧。
     *
     * <p>泛型写 {@code MapCodec<AnvilBlock>}（＝父类 {@code codec()} 的返回类型）而不是
     * {@code MapCodec<SturdygoldAnvilBlock>} —— {@code MapCodec<T>} 是<b>不协变</b>的，
     * 写窄了编译不过（第一版就这样红了）。工厂方法传的仍是本类构造器，所以造出来的实例是本类。</p>
     */
    public static final MapCodec<AnvilBlock> CODEC = simpleCodec(SturdygoldAnvilBlock::new);

    /** 容器标题（与原版砧一样是 {@code container.repair} 的那个键？不 —— 自己的键，见 lang） */
    private static final Component CONTAINER_TITLE = Component.translatable("container.bettergold.sturdygold_anvil");

    /**
     * 方块属性：<b>照原版砧全量复制，只把硬度 / 抗爆换成"不可破坏"</b>。
     *
     * <p>{@code ofFullCopy(Blocks.ANVIL)} 带过来的是 {@code requiresCorrectToolForDrops} + 金属音效 +
     * {@code mapColor}；随后 {@code strength(-1.0F, 3600000.0F)} 覆盖掉原来的 {@code 5.0F / 1200.0F}。
     * 依据：原版基岩 / 命令方块就是 {@code strength(-1.0F, 3600000.0F)}（立档 §8 D15）。</p>
     */
    public SturdygoldAnvilBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    public MapCodec<AnvilBlock> codec() {
        return CODEC;
    }

    /** 默认属性（注册处与 {@link #CODEC} 反序列化共用一处，避免两处不一致） */
    public static BlockBehaviour.Properties defaultProperties() {
        return BlockBehaviour.Properties.ofFullCopy(Blocks.ANVIL)
                .strength(-1.0F, 3600000.0F);
    }

    /**
     * 右键开界面：完全照 {@link AnvilBlock} 的同名方法（{@code level.isClientSide} 早退 + 服务端
     * {@code player.openMenu} + {@code awardStat}），只把 provider 换成自己的。
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        player.openMenu(state.getMenuProvider(level, pos));
        player.awardStat(Stats.INTERACT_WITH_ANVIL);
        return InteractionResult.CONSUME;
    }

    /**
     * 服务端这一侧带 {@link ContainerLevelAccess}（{@code stillValid} 要判"方块还在、玩家没走远"）；
     * 客户端那一侧由 {@code MenuType} 的 2 参构造器造（access = NULL）—— 与原版砧完全同构。
     */
    @Override
    protected MenuProvider getMenuProvider(BlockState state, Level level, BlockPos pos) {
        return new SimpleMenuProvider(
                (containerId, inventory, player) -> new SturdygoldAnvilMenu(containerId, inventory, ContainerLevelAccess.create(level, pos)),
                CONTAINER_TITLE);
    }

    /**
     * 下落方块：交给原版"每格 1 点"的<b>高度信号</b>（不是最终伤害）。
     *
     * <p>原版砧这里是 {@code setHurtsEntities(2.0F, 40)}（每格 2 点、封顶 40）；
     * 我们需要"按目标<b>当前</b>生命值封顶 16%"，这只能逐目标算 ⇒ 原版这条固定数值的路径做不到，
     * 于是把它降级成"信号"：{@code 1.0F} 每格、封顶给足（{@value SturdygoldAnvilFallDamage#SIGNAL_CAP}），
     * 让 {@code f} 恰好等于"格数"，再由 {@code LivingDamageEvent.Pre} 换成百分比。
     * 好处：落地判定、{@code NO_CREATIVE_OR_SPECTATOR} 过滤、AABB 取样全部仍走原版。</p>
     */
    @Override
    protected void falling(FallingBlockEntity fallingEntity) {
        fallingEntity.setHurtsEntities(SturdygoldAnvilFallDamage.SIGNAL_PER_BLOCK, SturdygoldAnvilFallDamage.SIGNAL_CAP);
    }

    // 形状（getShape）、四向 facing（rotate / getStateForPlacement）、落地音效（onLand / onBrokenAfterFall）、
    // 摔落伤害来源（getFallDamageSource = damageSources().anvil(entity)）全部**继承原版、一字未覆写**。
}
