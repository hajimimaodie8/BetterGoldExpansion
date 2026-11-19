package com.hjmmd_8.bettergold.spear;

/**
 * <b>标记接口：本模组的长矛</b>（1.8 §G）。
 *
 * <p>为什么需要它、而不直接 {@code instanceof MetalSpearItem}：长矛的类
 * （{@link MetalSpearItem}）继承的是<b>外部库</b> SpearCore 的 {@code ConfiguredSpearItem}，
 * 没装那个库时该类<b>根本加载不了</b>。而「这件物品要不要进创造页的装备分区」这条判断
 * （{@code AllItems#isGearTab}）在<b>没装</b>的档里也会被调用 —— 若那里写
 * {@code instanceof MetalSpearItem}，就会走到类解析、抛 {@code NoClassDefFoundError}。</p>
 *
 * <p>这个接口本身<b>不带任何 SpearCore 类型</b>，所以两种环境都能安全加载；
 * 实现它的类只在装了库时才存在（此时才可能被 {@code instanceof} 命中）。</p>
 */
public interface SpearGear {
}
