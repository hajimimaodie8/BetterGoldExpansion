package com.hjmmd_8.bettergold.patchouli;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.item.HandbookItem;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Patchouli（帕秋莉手册）联动模块的装配入口 —— 本项目的「**口径 B**」范式。
 *
 * <h2>口径 B = 没装就不注册（别照抄农夫乐事那一段）</h2>
 * <ul>
 *   <li><b>农夫乐事（fd 包）</b>用的是「**总是注册、功能软依赖**」：刀永远存在，FD 的类靠反射绕开；
 *       那条路允许在字段初始化器里引用对方的类型（靠反射兜住）。</li>
 *   <li><b>本模块</b>按作者 2026-10-04 的裁定取「**没装 Patchouli ⇒ 手册物品不注册**」
 *       （原话「没装手册进不去」= 创造页那一格根本不存在，不是"存在但打不开"）。
 *       ⇒ 这里对类加载的要求完全不同：<b>任何对 Patchouli 类型的静态引用都会在类加载时炸</b>，
 *       {@code isLoaded} 守卫写在字段/构造器里也救不了。</li>
 * </ul>
 * 所以本类<b>不引用任何 Patchouli 类型</b>，唯一的桥是 {@link PatchouliCompat}
 * （它的方法体里才有 Patchouli 的类，且只会在守卫为真时被执行）。
 *
 * <p>判定点：{@link #register} 由 {@code registry/AllItems} 在<b>类初始化期</b>调用，
 * 而那个时刻落在 {@code @Mod} 构造器之内（即 {@code RegisterEvent} 派发之前）——
 * 也就是说"注册期"就已经决定了要不要登记，注册表里的条目数会随环境变化（这是本口径的预期行为）。</p>
 */
public final class HandbookModule {

    /** 手册物品的注册路径（= id 的 path；注册命名空间恒为 bettergold，红线不许改） */
    public static final String ITEM_PATH = "alchemy_student_handbook";

    /** 手册的书 id（Patchouli 的 book 目录名 = `data/bettergold/patchouli_books/<BOOK_PATH>/book.json`） */
    public static final String BOOK_PATH = "alchemy_handbook";

    /** 手册物品的完整 id */
    public static final ResourceLocation ITEM_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, ITEM_PATH);

    /** Patchouli 的书 id（= book.json 所在目录名） */
    public static final ResourceLocation BOOK_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, BOOK_PATH);

    private HandbookModule() {
    }

    /** Patchouli 是否已加载（本模块所有入口的第一道闸） */
    public static boolean isLoaded() {
        return ModList.get().isLoaded("patchouli");
    }

    /**
     * 条件注册手册物品：<b>没装 Patchouli 时返回 {@code null}</b>（物品根本不进注册表），
     * 装了才登记。调用方（{@code AllItems}）把返回值直接存进字段。
     *
     * <p>⚠ 返回 {@code null} 是本口径的<b>预期形状</b>：任何按环境读物品的代码都必须能容忍它
     * （本仓创造页是按 id/位次排的、不是按索引读物品，所以条件注册不会打乱顺序）。</p>
     */
    public static @Nullable DeferredItem<Item> register(DeferredRegister.Items items) {
        if (!isLoaded()) {
            bettergold.LOGGER.info("[bg-book] Patchouli not loaded -> the alchemy handbook item is NOT registered");
            return null;
        }
        bettergold.LOGGER.info("[bg-book] Patchouli loaded -> registering {}", ITEM_ID);
        // 方法引用写在守卫之后：只有装了 Patchouli 才会去解析 PatchouliCompat（以及它体内的 API 调用）。
        return items.register(ITEM_PATH, HandbookModule::createItem);
    }

    /**
     * 手册物品本体：纯功能物品 —— 无属性、无耐久、堆叠 1（书类），模型 {@code item/generated} 单层。
     *
     * <p>不在这里引用 Patchouli 的类型（{@link HandbookItem} 自己也不引用）；本方法只是
     * "被守卫保护的创建入口"。</p>
     */
    private static Item createItem() {
        return new HandbookItem(new Item.Properties().stacksTo(1));
    }
}
