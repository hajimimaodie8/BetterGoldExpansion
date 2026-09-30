package com.hjmmd_8.bettergold.fd;

import java.util.ArrayList;
import java.util.List;

import com.hjmmd_8.bettergold.material.CreativePageSections;
import com.hjmmd_8.bettergold.material.CreativeSections;
import com.hjmmd_8.bettergold.material.CreativeTabSections;

import net.minecraft.world.item.ItemStack;

/**
 * FD（农夫乐事）联动分支在<b>本模组唯一创造页</b>里的「乐事分区」。
 *
 * <p>本模组只有一个创造页（{@link CreativePageSections#PAGE_TAB_ID}），页内共 5 个分区、
 * 每个分区一条横幅；乐事分区用的就是 {@code fd.png}。本类负责把这一分区
 * <b>内部排列规则 + 候选物品</b>打包好，由 {@link FdModule#register} 在 FD 已加载时
 * 登记进 {@link CreativePageSections}（核心代码不认识本类，架构红线见该类的类注释）。</p>
 *
 * <p>乐事分区内部顺序（一个连续列表，不插横幅/空行）：
 * 小刀 → 普通金食物 → 金放置食物 → 万坚金食物 → 万坚金放置食物。</p>
 *
 * <p><b>「小刀」子组内部的先后</b>由 {@link CreativeSections#KNIFE_ORDER} 在唯一真相处
 * （{@code material.CreativeSections}）统一维护：金属小刀按金属出场顺序
 * （烈燃金刀 → 万坚金刀 → 巫毒金刀 → 结雷金刀），非金属小刀（古董刀 → 下界合金古董刀）
 * 排在全部金属小刀之后，同组按物品 id 字典序；本类只负责"哪些是刀"，不另写一套顺序。</p>
 *
 * <p>"放置食物"= 派 / 蛋糕的 BlockItem（{@link FdBlocks} 里注册进 {@link FdItems} 的那些），
 * 靠 {@link CreativeTabSections#isBlockItem} 判定，不枚举具体物品，以后加派/蛋糕不用改这里。</p>
 */
public final class FdTabs {

    /** 乐事分区的内部排列规则（段标签只用于日志/自检，不再画到横幅上） */
    public static final List<CreativeTabSections.Slot> RULES = List.of(
            new CreativeTabSections.Slot("小刀",
                    stack -> CreativeTabSections.pathEndsWith(stack, "_knife"), CreativeSections.KNIFE_ORDER),
            new CreativeTabSections.Slot("普通金食物",
                    stack -> !CreativeTabSections.isSturdygold(stack) && !CreativeTabSections.isBlockItem(stack)),
            new CreativeTabSections.Slot("金放置食物",
                    stack -> CreativeTabSections.isBlockItem(stack) && !CreativeTabSections.isSturdygold(stack)),
            new CreativeTabSections.Slot("万坚金食物",
                    stack -> CreativeTabSections.isSturdygold(stack) && !CreativeTabSections.isBlockItem(stack)),
            new CreativeTabSections.Slot("万坚金放置食物", stack -> true));

    /**
     * 乐事分区：横幅 {@code fd.png}、释词「乐事」，候选物品 = 本模块注册的全部物品
     * （含派/蛋糕的 BlockItem）。order 取 {@link CreativePageSections#CORE_SECTION_COUNT}
     * ⇒ 排在内置 4 个分区（材料/建筑/食物/装备）之后，即页尾。
     */
    public static final CreativePageSections.Section FD_SECTION = new CreativePageSections.Section(
            "fd",
            CreativePageSections.CORE_SECTION_COUNT,
            "乐事",
            CreativePageSections.bannerTexture("fd"),
            RULES,
            FdTabs::candidates);

    /** 乐事分区候选：本模块注册的全部物品，保持注册顺序 */
    private static List<ItemStack> candidates() {
        List<ItemStack> out = new ArrayList<>();
        FdItems.ITEMS.getEntries().forEach(holder -> out.add(holder.get().getDefaultInstance()));
        return out;
    }

    private FdTabs() {
    }
}
