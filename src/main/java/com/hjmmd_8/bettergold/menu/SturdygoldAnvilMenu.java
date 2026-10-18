package com.hjmmd_8.bettergold.menu;

import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllItems;
import com.hjmmd_8.bettergold.registry.AllMenus;

import javax.annotation.Nullable;

import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.util.StringUtil;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AnvilMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.DataSlot;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;

/**
 * <b>万坚金砧的容器</b>（1.7 {@code bg-n10} 轮8 —— 本仓<b>第一个</b>自定义 {@code MenuType} / Menu）。
 *
 * <h2>技术路线：<b>继承</b> {@link AnvilMenu}，只改三处「作者点名的差异」</h2>
 * <p>立档 §4 歧义 ⑯-b 给了两个选项（(A) 继承原版 {@code AnvilBlock} + 复用 {@code AnvilMenu}；
 * (B) 自己写 Block + 自建 MenuType/Screen）。派单又要求「<b>直接复用 {@code AnvilMenu} 的合并逻辑，
 * 不要自己重写附魔合并</b>」。两者看似冲突（原版 {@code AnvilMenu} 的构造器把
 * {@code MenuType.ANVIL} 写死，服务端 {@code ServerPlayer#openMenu} 发的
 * {@code ClientboundOpenScreenPacket} 用的就是 {@code menu.getType()} ⇒ 不换 type，客户端永远只会造出
 * 原版 {@code AnvilMenu} + 原版 {@code AnvilScreen}）。</p>
 *
 * <p><b>解法（源码依据）</b>：{@code AbstractContainerMenu#getType()} 是
 * <b>{@code public} 且非 {@code final}</b>（1.21.1 {@code AbstractContainerMenu.java:76-81}）⇒
 * 子类<b>覆写 {@link #getType()}</b> 就能让自己上报成自己的 {@code MenuType}，
 * 而构造器里那个 {@code private final MenuType<?> menuType} 字段只被崩溃报告用到（同文件 :302）。
 * 于是：<b>附魔合并 / 互斥 / 修复材料判定 / 名字 / repairCost 全部是原版 {@code AnvilMenu#createResult}
 * 那一份代码</b>（我们<b>一行都没抄</b>），只有"金币串修复"这一条新路是我们写的。</p>
 *
 * <p>⚠ 记录（旧口径就地标注）：派单提到的 {@code RegisterMenuTypes} 是 <b>Forge</b> 时代的事件，
 * NeoForge 21.1 <b>没有</b>它 —— {@code MenuType} 就是普通的注册表条目（{@code Registries.MENU}），
 * 用 {@code DeferredRegister} 注册；客户端 Screen 才走事件
 * {@code RegisterMenuScreensEvent}（见 {@code bettergoldClient}）。</p>
 *
 * <h2>改动清单（相对原版砧）</h2>
 * <ol>
 *   <li>{@link #isValidBlock} → 认自己的方块（原版认 {@code #minecraft:anvil} 标签）；</li>
 *   <li>{@link #createResult} → <b>金币串修复</b>这一条新路（其余<b>原样交给</b> {@code super}）；</li>
 *   <li>{@link #mayPickup} / {@link #onTake} / {@link #getCost} → 让上面那条路的花费与消耗生效
 *       （原版这几个方法读的是 {@code AnvilMenu} 的 private {@code cost}，我们读自己的 {@code coinCost}）。</li>
 *   <li>{@link #setItemName} → 抄一份原版链路送进来的名字给金币串那条路（{@code AnvilMenu#itemName}
 *       是 private 且没有 getter）。界面侧的名字框 = 原版 {@code EditBox}，见 {@code SturdygoldAnvilScreen}。</li>
 * </ol>
 *
 * <h2>★ 功能一：用混沌金币串修复（作者原话 → 唯一实现）</h2>
 * <pre>perCoin = maxDamage / 4                       // 原版 AnvilMenu#createResult 第 138 行的公式
 * 每次消耗 1 个混沌金币串，修掉 min(剩余损伤, perCoin)
 * 消耗币数 used = ceil(damage / perCoin)（受输入槽里的币数上限约束）
 * 等级花费 = used（原版 COST_REPAIR_MATERIAL = 1 每单位材料，第 39 行）
 *            + 改名费（原版 COST_RENAME = 1；仅当玩家在名字框里改了名 / 清了名）</pre>
 * <p>⚠ 派单提到的 {@code AnvilMenu#getDamageChance} 在 1.21.1 <b>不存在</b>（旧版本才有）；
 * 1.21.1 的等价口径就是上面那条 {@code Math.min(getDamageValue(), getMaxDamage() / 4)}。
 * 原版砧的"用砧会磨损"（{@code breakChance} → {@code AnvilBlock.damage}）在这条路上<b>不做</b>：
 * 作者要的是<b>无法破坏</b>。</p>
 *
 * <h2>★ 功能二：不累积惩罚（立档 ⑯-c，本轮取 <b>(C) 只豁免这条路</b>）</h2>
 * <p>原版在 {@code createResult} 末尾会 {@code REPAIR_COST = calculateIncreasedRepairCost(old)}
 * （{@code old * 2 + 1}，第 279-281 行），累积到一定值后 {@code cost >= 40} ⇒ 输出清空 = 「过于昂贵」。
 * 本菜单的金币串修复<b>不碰 {@code REPAIR_COST}</b>（结果 = 输入栈的 copy，组件原样带过去）
 * ⇒ 修多少次都不涨、也永远不进入"过于昂贵"分支。
 * <b>其它路（合并附魔 / 合并同名物品 / 铁砧自带修复材料）仍走原版</b>：{@code super.createResult()}
 * 会照常把 {@code REPAIR_COST} ×2+1、照常受 40 级门槛约束 —— 这就是 ⑯-c (C) 的"只豁免一条路"。</p>
 *
 * <h2>功能三：互斥附魔</h2>
 * <p>合并走原版 {@code AnvilMenu#createResult} 的附魔段（含 {@code Enchantment.areCompatible}
 * 互斥判定与 {@code itemstack.supportsEnchantment}）——<b>本类没有第二份合并代码</b>（关卡钉"全仓只有一处"）。</p>
 */
public class SturdygoldAnvilMenu extends AnvilMenu {

    /** 输入 1：待修装备（槽位索引与原版砧逐字相同，贴图坐标才对得上） */
    public static final int INPUT_SLOT = 0;
    /** 输入 2：混沌金币串 */
    public static final int ADDITIONAL_SLOT = 1;
    /** 输出槽 */
    public static final int RESULT_SLOT = 2;

    /**
     * 每个混沌金币串能修掉的耐久 = {@code maxDamage / 4}。
     * 原版 {@code AnvilMenu#createResult} 第 138 行就是 {@code Math.min(damage, getMaxDamage() / 4)}
     * —— 这个 4 是原版砧"一份材料修四分之一"的那个 4，逐字沿用。
     */
    public static final int COIN_REPAIR_DIVISOR = 4;

    /** 每次修复消耗 1 个币时的等级花费（原版 {@code COST_REPAIR_MATERIAL = 1}） */
    public static final int COST_PER_COIN = 1;

    /** 金币串这条路的等级花费（DataSlot = 会同步到客户端，客户端 Screen 才能显示） */
    private final DataSlot coinCost = DataSlot.standalone();

    /** 当前 {@code resultSlots} 里的东西是不是"金币串修复"的产物（服务端与客户端各自算，结果一致） */
    private boolean coinRepair;

    /** 本次会消耗几个币（只用于 {@link #onTake}，不需要同步） */
    private int coinCount;

    /**
     * 原版链路（{@code AnvilScreen} 的 EditBox → {@code ServerboundRenameItemPacket} → {@link #setItemName}）
     * 送进来的名字。
     *
     * <p>{@code AnvilMenu#itemName} 是 <b>private 且没有 getter</b>（1.21.1 {@code AnvilMenu.java:34}）
     * ⇒ 在 {@link #setItemName} 里抄一份，金币串那条路才能按原版语义把名字落到结果上。
     * {@code null} = 还没有人送过名字（与原版 {@code itemName} 的初始值同义）。</p>
     */
    @Nullable
    private String requestedName;

    public SturdygoldAnvilMenu(int containerId, Inventory playerInventory) {
        this(containerId, playerInventory, ContainerLevelAccess.NULL);
    }

    public SturdygoldAnvilMenu(int containerId, Inventory playerInventory, ContainerLevelAccess access) {
        super(containerId, playerInventory, access);
        // ⚠ 必须在 super(...) 之后：原版构造器已经 addDataSlot 了它自己的 cost（索引 0），
        //    我们的 coinCost 顺位是索引 1 —— 两个都靠 ClientboundContainerSetDataPacket 同步。
        this.addDataSlot(this.coinCost);
    }

    /**
     * ★ 让本菜单上报成<b>自己的</b> {@code MenuType}（理由见类注释）。
     *
     * <p>{@code ServerPlayer#openMenu} 用 {@code menu.getType()} 填
     * {@code ClientboundOpenScreenPacket}（{@code ServerPlayer.java:1188}），客户端再按这个 type 找
     * {@code MenuScreens} 里注册过的 Screen 工厂 ⇒ 这一处覆写就是"自定义界面能开出来"的总开关。</p>
     */
    @Override
    public MenuType<?> getType() {
        return AllMenus.STURDYGOLD_ANVIL.get();
    }

    /** 只认万坚金砧（原版认 {@code BlockTags.ANVIL}；我们<b>刻意不进</b>那个标签，见方块类注释） */
    @Override
    protected boolean isValidBlock(BlockState state) {
        return state.is(AllBlocks.STURDYGOLD_ANVIL.get());
    }

    // ==================== createResult：金币串修复 + 其余全交原版 ====================

    @Override
    public void createResult() {
        // ① ⚠ 旧口径（bg-n10 轮8，原文留档）：这里原先调 syncNameFromInput()，把 itemName
        //    强行同步成"输入物品当前的显示名"——当时本界面没有名字输入框，不这么做，
        //    原版 createResult 在 itemName == null 时会把自定义名当"被清空"抹掉（第 236-240 行）。
        //    bg-n10anvil 轮（作者要求 GUI 完全照原版砧）加回了原版 EditBox + ServerboundRenameItemPacket，
        //    名字走的就是原版那条链路 ⇒ 再同步就会把玩家刚改的名字立刻抹回去（实测"改名不生效"）
        //    ⇒ 旧口径已作废：只认原版 itemName（本类在 setItemName 里抄一份给金币串那条路用）。
        // ② 金币串修复这条路：完全由我们算（名字也在这一条里按原版语义落到结果上）
        if (tryCoinRepair()) {
            return;
        }
        // ③ 其余一切（附魔合并 / 互斥 / 同名合并 / 铁砧自带材料修复 / 名字 / repairCost）→ 原版
        this.coinRepair = false;
        this.coinCount = 0;
        this.coinCost.set(0);
        super.createResult();
    }

    /**
     * ⚠ 旧口径（bg-n10 轮8）：这里的 {@code syncNameFromInput()} 已整段删除 —— 它把名字强制同步成
     * 输入物品的显示名，会让新加的原版 EditBox 改名立刻被抹回去。现行口径 = 原版链路
     * （{@code AnvilScreen#onNameChanged} → {@code ServerboundRenameItemPacket} → {@link #setItemName}），
     * 见 {@link #requestedName} 与 {@link #tryCoinRepair} 里的名字分支。
     */

    /**
     * 原版链路送进来的名字：先抄进 {@link #requestedName}，再交回 {@code AnvilMenu#setItemName}。
     *
     * <p>⚠ 必须先写字段再调 {@code super}：{@code AnvilMenu#setItemName} 内部会虚派发到本类
     * {@link #createResult}，金币串那条路要立刻读到新名字（否则会拿上一帧的旧名字算花费）。</p>
     */
    @Override
    public boolean setItemName(String itemName) {
        this.requestedName = itemName;
        return super.setItemName(itemName);
    }

    /**
     * <b>金币串修复</b>（功能一 + 功能二）。
     *
     * @return {@code true} = 这条路接下了（{@code resultSlots} 已写好）；{@code false} = 让原版去算
     */
    private boolean tryCoinRepair() {
        ItemStack toRepair = this.inputSlots.getItem(INPUT_SLOT);
        ItemStack material = this.inputSlots.getItem(ADDITIONAL_SLOT);
        if (toRepair.isEmpty() || material.isEmpty()) {
            return false;
        }
        // 只认"输入 2 = 混沌金币串"（既有物品 bettergold:chaos_coin_string）
        if (!material.is(AllItems.CHAOS_COIN_STRING.get())) {
            return false;
        }
        // 目标必须是可损坏物品（装备 / 工具）；不可损坏的东西没有"修复"可言 ⇒ 交回原版（会给出空结果）
        if (!toRepair.isDamageableItem()) {
            return false;
        }
        int maxDamage = toRepair.getMaxDamage();
        int damage = toRepair.getDamageValue();
        int perCoin = maxDamage / COIN_REPAIR_DIVISOR;
        if (damage <= 0 || perCoin <= 0) {
            // 满耐久 / 数据异常：无结果（与原版砧"材料用不上"时一样是空输出）
            return false;
        }

        // === 原版砧的修复公式，逐币推进（AnvilMenu#createResult 第 145-153 行的等价写法）===
        ItemStack result = toRepair.copy();
        int remaining = damage;
        int used = 0;
        while (remaining > 0 && used < material.getCount()) {
            remaining -= Math.min(remaining, perCoin);
            used++;
        }
        result.setDamageValue(remaining);

        // === 名字：完全照原版 AnvilMenu#createResult 第 230-240 行的语义 ===
        //     有名字且与"输入物品当前显示名"不同 ⇒ 写到结果上、+1 级；
        //     名字为空 / 没送过、而输入物品带自定义名 ⇒ 抹掉自定义名、+1 级。
        //     （旧 §17.3"等级花费 = used"只描述修理本身；改名这一级是原版砧本来的规则。）
        int renameCost = 0;
        if (this.requestedName != null && !StringUtil.isBlank(this.requestedName)) {
            if (!this.requestedName.equals(toRepair.getHoverName().getString())) {
                renameCost = 1;
                result.set(DataComponents.CUSTOM_NAME, Component.literal(this.requestedName));
            }
        } else if (toRepair.has(DataComponents.CUSTOM_NAME)) {
            renameCost = 1;
            result.remove(DataComponents.CUSTOM_NAME);
        }

        // === 不累积惩罚：REPAIR_COST 原样保留（result 是 copy），**不**调用 calculateIncreasedRepairCost ===
        // === 也**不**做 40 级"过于昂贵"门槛（立档 ⑯-c (C)：只豁免这条路）===

        this.resultSlots.setItem(0, result);
        this.coinRepair = true;
        this.coinCount = used;
        this.coinCost.set(used * COST_PER_COIN + renameCost);
        // 原版那条 cost 在我们这条路上没有意义（本来可能留着上一次算出来的值）⇒ 清掉
        this.setMaximumCost(0);
        this.broadcastChanges();
        return true;
    }

    // ==================== 取件 / 花费 ====================

    @Override
    protected boolean mayPickup(Player player, boolean hasStack) {
        if (this.coinRepair) {
            // 与原版同构：创造模式无视等级；否则要够扣
            return hasStack && (player.hasInfiniteMaterials() || player.experienceLevel >= this.coinCost.get());
        }
        return super.mayPickup(player, hasStack);
    }

    @Override
    protected void onTake(Player player, ItemStack stack) {
        if (!this.coinRepair) {
            super.onTake(player, stack);
            return;
        }
        // ★ 先把"本次要消耗几个币"抄成局部变量再动输入槽 —— A 级首跑抓到的真 bug：
        //   `inputSlots.setItem(0, EMPTY)` 会触发 setChanged → slotsChanged → createResult 重入，
        //   而重入时 input0 已空 ⇒ 走不到金币串那条路 ⇒ `coinCount` 被清成 0 ⇒ 币一个都不消耗
        //   （读数：等级扣了、币没少）。原版 AnvilMenu 用的是 `repairItemCountCost`，它只在
        //   "input0 非空" 的分支里被重置，所以恰好没这个问题 —— 我们照它的**语义**，把值先取出来。
        final int used = this.coinCount;
        final int cost = this.coinCost.get();
        if (!player.getAbilities().instabuild) {
            player.giveExperienceLevels(-cost);
        }
        this.inputSlots.setItem(INPUT_SLOT, ItemStack.EMPTY);
        ItemStack material = this.inputSlots.getItem(ADDITIONAL_SLOT);
        if (!material.isEmpty() && used > 0) {
            ItemStack left = material.copy();
            left.shrink(Math.min(used, left.getCount()));
            this.inputSlots.setItem(ADDITIONAL_SLOT, left.isEmpty() ? ItemStack.EMPTY : left);
        }
        this.coinCount = 0;
        this.coinCost.set(0);
        this.coinRepair = false;
        this.setMaximumCost(0);
        // 原版取件时的"用法音效"（levelEvent 1030）；⚠ 这里**不**调 AnvilBlock#damage ⇒ 永不磨损
        this.access.execute((level, pos) -> level.levelEvent(1030, pos, 0));
    }

    /** 客户端界面读这一条显示花费（金币串这条路读我们的 DataSlot，其余读原版） */
    @Override
    public int getCost() {
        return this.coinRepair ? this.coinCost.get() : super.getCost();
    }

    /** 当前结果是否来自"金币串修复"（界面 / 探针用；不影响逻辑） */
    public boolean isCoinRepair() {
        return this.coinRepair;
    }

    /** 本次会消耗的币数（界面 / 探针用；只在 {@code createResult} 之后有效） */
    public int getCoinCount() {
        return this.coinCount;
    }

    /** 输入 2 是不是混沌金币串（界面画"幽灵图标"用） */
    public boolean isCoinRepairCandidate() {
        ItemStack toRepair = this.inputSlots.getItem(INPUT_SLOT);
        ItemStack material = this.inputSlots.getItem(ADDITIONAL_SLOT);
        return !toRepair.isEmpty()
                && toRepair.isDamageableItem()
                && toRepair.getDamageValue() > 0
                && (material.isEmpty() || material.is(AllItems.CHAOS_COIN_STRING.get()));
    }

    /** 输出槽的 Slot（原版 {@code ItemCombinerMenu} 里 resultSlotIndex 是私有的 ⇒ 这里给个稳定入口） */
    public Slot resultSlot() {
        return this.getSlot(RESULT_SLOT);
    }
}
