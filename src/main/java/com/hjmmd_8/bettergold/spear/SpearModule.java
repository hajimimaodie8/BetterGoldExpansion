package com.hjmmd_8.bettergold.spear;

import java.util.List;

import javax.annotation.Nullable;

import net.minecraft.world.item.Item;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * <b>长矛模块的门面（1.8 §G）—— 这个类不引用任何 SpearCore 类型，两种环境都能加载。</b>
 *
 * <h2>为什么要分成「门面 + 注册器」两个类</h2>
 * <p>实测教训（本轮踩到）：把「{@code new MetalSpearItem(...)} 的供应商 lambda」和
 * {@link #isLoaded()} 放在<b>同一个类</b>里时，<b>没装 SpearCore</b> 的档会在
 * {@code bettergold} 构造器里抛</p>
 * <pre>java.lang.NoClassDefFoundError: net/minecraft/spearcore/item/ConfiguredSpearItem</pre>
 * <p>—— 因为 JVM 定义那个类时就会去解析 lambda 体里 {@code new} 的目标类（= 我们的
 * {@code MetalSpearItem}），而它的父类正是库里的类。AGENTS.md 第 10 条那条
 * 「paradigm B：引用只许在方法体内、且在早退之后」在这里<b>还不够</b>：连「方法体内的 new」
 * 都不能和判定放在同一个类里。</p>
 *
 * <p>⇒ 现行结构：</p>
 * <ul>
 *   <li><b>本类</b>（门面）：只放 {@link #isLoaded()} / 查询 / 派发，<b>零</b> spearcore 引用；</li>
 *   <li>{@link SpearRegistration}（注册器）：所有 {@code SpearStats} / {@code SpearItem} /
 *       {@code MetalSpearItem} 的引用都在这里，<b>只有装了库才会被加载</b>。</li>
 * </ul>
 */
public final class SpearModule {

    /** 外部库的 modid（依赖判定与关卡断言都读这一个字符串） */
    public static final String LIB_MODID = "spearcore";

    /** 长矛物品 id 的统一后缀（创造页 {@code GEAR_SLOT} 用它定位） */
    public static final String SUFFIX = "spear";

    private static @Nullable DeferredItem<Item> antique;
    private static List<DeferredItem<Item>> all = List.of();
    private static boolean registered;

    private SpearModule() {
    }

    /** SpearCore 装了吗（**唯一的**依赖判定入口） */
    public static boolean isLoaded() {
        return ModList.get().isLoaded(LIB_MODID);
    }

    /**
     * 装配：装了库才加载 {@link SpearRegistration} 并注册 14 件矛 + 一个
     * {@code FMLCommonSetupEvent} 监听（把「矛 → 家族」登记进各族）。
     *
     * <p>调用点：{@code bettergold} 的构造器。<b>没装时本方法只做一次字符串判定</b>，
     * 注册器那个类一个字节都不会被加载。</p>
     */
    public static void init(IEventBus modEventBus) {
        if (!isLoaded()) {
            return;
        }
        SpearRegistration.register(modEventBus);
        registered = true;
    }

    /** 注册器在注册完成后回填（{@link SpearRegistration} 调用） */
    static void publish(@Nullable DeferredItem<Item> antiqueSpear, List<DeferredItem<Item>> spears) {
        antique = antiqueSpear;
        all = List.copyOf(spears);
    }

    /** 古董长矛（给「珍品古董盒」的开奖池用；没装库时返回 null） */
    public static @Nullable DeferredItem<Item> antiqueSpear() {
        return antique;
    }

    /** 14 件矛的注册顺序表（没装库 = 空表） */
    public static List<DeferredItem<Item>> all() {
        return all;
    }

    /** 本模块是否真的装配过（= 装了库且 init 跑过） */
    public static boolean isRegistered() {
        return registered;
    }
}
