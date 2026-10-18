import sys
sys.stdout.reconfigure(errors="replace")

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
MENU = ROOT + r"\src\main\java\com\hjmmd_8\bettergold\menu\SturdygoldAnvilMenu.java"
BLOCK = ROOT + r"\src\main\java\com\hjmmd_8\bettergold\block\SturdygoldAnvilBlock.java"

s = open(MENU, "rb").read().decode("utf-8")
orig = s


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, "anchor count %d != %d for %r" % (n, count, old[:80])
    s = s.replace(old, new)


# ---- imports ----
rep(
"""import com.hjmmd_8.bettergold.registry.AllMenus;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.entity.player.Inventory;""",
"""import com.hjmmd_8.bettergold.registry.AllMenus;

import javax.annotation.Nullable;

import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.util.StringUtil;
import net.minecraft.world.entity.player.Inventory;""")

# ---- Javadoc: cost line + change list ----
rep(
""" * 等级花费 = used（原版 COST_REPAIR_MATERIAL = 1 每单位材料，第 39 行）</pre>""",
""" * 等级花费 = used（原版 COST_REPAIR_MATERIAL = 1 每单位材料，第 39 行）
 *            + 改名费（原版 COST_RENAME = 1；仅当玩家在名字框里改了名 / 清了名）</pre>""")

rep(
""" *   <li>{@link #mayPickup} / {@link #onTake} / {@link #getCost} → 让上面那条路的花费与消耗生效
 *       （原版这几个方法读的是 {@code AnvilMenu} 的 private {@code cost}，我们读自己的 {@code coinCost}）。</li>""",
""" *   <li>{@link #mayPickup} / {@link #onTake} / {@link #getCost} → 让上面那条路的花费与消耗生效
 *       （原版这几个方法读的是 {@code AnvilMenu} 的 private {@code cost}，我们读自己的 {@code coinCost}）。</li>
 *   <li>{@link #setItemName} → 抄一份原版链路送进来的名字给金币串那条路（{@code AnvilMenu#itemName}
 *       是 private 且没有 getter）。界面侧的名字框 = 原版 {@code EditBox}，见 {@code SturdygoldAnvilScreen}。</li>""")

# ---- field ----
rep(
"""    /** 本次会消耗几个币（只用于 {@link #onTake}，不需要同步） */
    private int coinCount;""",
"""    /** 本次会消耗几个币（只用于 {@link #onTake}，不需要同步） */
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
    private String requestedName;""")

# ---- createResult: drop the old name sync ----
rep(
"""        // ① 名字同步：本界面没有重命名输入框 ⇒ 名字恒等于"输入物品当前的显示名"。
        //    原版 createResult 在 itemName == null 时会把自定义名当成"被清空"抹掉并 +1 级
        //    （第 236-240 行），而原版客户端是靠 AnvilScreen 的名字框 + ServerboundRenameItemPacket
        //    把名字送到服务端的。我们没有那条链路 ⇒ 在两侧都就地同步一次。
        //    ⚠ setItemName 内部会回调 createResult（虚拟派发）⇒ 它返回 true 时本帧直接结束，
        //      真正的计算在那次回调里跑完，不会重入第二遍。
        if (syncNameFromInput()) {
            return;
        }
        // ② 金币串修复这条路：完全由我们算""",
"""        // ① ⚠ 旧口径（bg-n10 轮8，原文留档）：这里原先调 syncNameFromInput()，把 itemName
        //    强行同步成"输入物品当前的显示名"——当时本界面没有名字输入框，不这么做，
        //    原版 createResult 在 itemName == null 时会把自定义名当"被清空"抹掉（第 236-240 行）。
        //    bg-n10anvil 轮（作者要求 GUI 完全照原版砧）加回了原版 EditBox + ServerboundRenameItemPacket，
        //    名字走的就是原版那条链路 ⇒ 再同步就会把玩家刚改的名字立刻抹回去（实测"改名不生效"）
        //    ⇒ 旧口径已作废：只认原版 itemName（本类在 setItemName 里抄一份给金币串那条路用）。
        // ② 金币串修复这条路：完全由我们算（名字也在这一条里按原版语义落到结果上）""")

# ---- remove syncNameFromInput method, leave a pointer ----
rep(
"""    /**
     * 把"输入槽当前显示名"同步进 {@code AnvilMenu#itemName}（没有自定义名 ⇒ 空串，与原版
     * {@code AnvilScreen#onNameChanged} 的约定一致）。
     *
     * @return {@code true} = 名字变了（此时 {@code setItemName} 已经回调过一次 {@code createResult}）
     */
    private boolean syncNameFromInput() {
        ItemStack input = this.inputSlots.getItem(INPUT_SLOT);
        String wanted = !input.isEmpty() && input.has(DataComponents.CUSTOM_NAME)
                ? input.getHoverName().getString()
                : "";
        return super.setItemName(wanted);
    }""",
"""    /**
     * ⚠ 旧口径（bg-n10 轮8）：这里的 {@code syncNameFromInput()} 已整段删除 —— 它把名字强制同步成
     * 输入物品的显示名，会让新加的原版 EditBox 改名立刻被抹回去。现行口径 = 原版链路
     * （{@code AnvilScreen#onNameChanged} → {@code ServerboundRenameItemPacket} → {@link #setItemName}），
     * 见 {@link #requestedName} 与 {@link #tryCoinRepair} 里的名字分支。
     */""")

# ---- setItemName override ----
rep(
"""    /**
     * <b>金币串修复</b>（功能一 + 功能二）。""",
"""    /**
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
     * <b>金币串修复</b>（功能一 + 功能二）。""")

# ---- name branch in tryCoinRepair ----
rep(
"""        result.setDamageValue(remaining);

        // === 不累积惩罚：REPAIR_COST 原样保留（result 是 copy），**不**调用 calculateIncreasedRepairCost ===
        // === 也**不**做 40 级"过于昂贵"门槛（立档 ⑯-c (C)：只豁免这条路）===""",
"""        result.setDamageValue(remaining);

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
        // === 也**不**做 40 级"过于昂贵"门槛（立档 ⑯-c (C)：只豁免这条路）===""")

rep("""        this.coinCost.set(used * COST_PER_COIN);""",
    """        this.coinCost.set(used * COST_PER_COIN + renameCost);""")

assert s != orig
open(MENU, "wb").write(s.encode("utf-8"))
print("menu written", len(s.encode("utf-8")), "B")

# ---------------- block title ----------------
b = open(BLOCK, "rb").read().decode("utf-8")
old = '''    /** 容器标题（与原版砧一样是 {@code container.repair} 的那个键？不 —— 自己的键，见 lang） */
    private static final Component CONTAINER_TITLE = Component.translatable("container.bettergold.sturdygold_anvil");'''
new = '''    /**
     * 容器标题 = <b>原版砧那个键</b>（{@code container.repair}，原版 {@code AnvilBlock.java:44} 逐字相同）。
     *
     * <p>⚠ 旧口径（bg-n10 轮8，原文留档）：原先用本模组自己的键
     * {@code container.bettergold.sturdygold_anvil}（"万坚金砧"）。作者 2026-10-18 要求
     * 「所有 GUI 标识换成和普通铁砧完全一致」⇒ 标题也换成原版那句「修理和命名」。
     * 旧语言键仍保留在 zh/en 里（不删），只是界面不再用它。</p>
     */
    private static final Component CONTAINER_TITLE = Component.translatable("container.repair");'''
assert b.count(old) == 1
b = b.replace(old, new)
open(BLOCK, "wb").write(b.encode("utf-8"))
print("block written", len(b.encode("utf-8")), "B")
