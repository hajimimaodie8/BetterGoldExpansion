package com.hjmmd_8.bettergold.patchouli;

import net.minecraft.server.level.ServerPlayer;
import vazkii.patchouli.api.PatchouliAPI;
import vazkii.patchouli.common.base.PatchouliSounds;

/**
 * <b>本项目唯一允许引用 Patchouli 类型的类</b>（bg-book §3.1.2 的「编译期隔离」落点）。
 *
 * <h2>铁律（违反任意一条都会在「没装 Patchouli」时炸）</h2>
 * <ul>
 *   <li>对 Patchouli 类型的引用<b>只许出现在方法体内</b>，而且这些方法<b>只许在
 *       {@code ModList.get().isLoaded("patchouli")} 为真时被调用</b>；</li>
 *   <li><b>绝不许</b>出现在字段类型、构造器签名、静态初始化块里 —— 那些位置在<b>类加载时</b>
 *       就要解析，守卫根本没机会执行（这就是「静态引用第三方类 = 类加载即炸」那条教训）；</li>
 *   <li>Patchouli 在构建里是 {@code compileOnly}（<b>故意没有 localRuntime</b>，见
 *       {@code gradle.properties}），所以开发环境默认就是"没装"这一档。</li>
 * </ul>
 *
 * <p>类加载本身<b>不会</b>解析方法体里引用的类（JVM 惰性解析），所以本类被加载是安全的；
 * 真正会把 Patchouli 的类拖进来的是<b>执行</b>那几行 —— 而那几行前面都有早退。</p>
 */
public final class PatchouliCompat {

    private PatchouliCompat() {
    }

    /**
     * 右键手册：打开 {@link HandbookModule#BOOK_ID} 这本书；没装 Patchouli 时直接返回。
     *
     * <p>与 Patchouli 自带 {@code ItemModBook#use} 走的是<b>同一条路径</b>
     * （{@code PatchouliAPI.get().openBookGUI(ServerPlayer, ResourceLocation)} + 开书音效），
     * 区别只在于它从堆叠上的 {@code patchouli:book} 数据组件取书 id，而本模组的手册固定指向
     * 自己那一本 —— 也正因为如此，我们的物品<b>不需要</b>那个组件。</p>
     */
    public static void openBookIfLoaded(ServerPlayer player) {
        if (!HandbookModule.isLoaded()) {
            // 正常情况下走不到这里（物品压根没注册）；留着是为了"路径先早退"这条纪律本身。
            return;
        }
        PatchouliAPI.get().openBookGUI(player, HandbookModule.BOOK_ID);
        player.playSound(PatchouliSounds.BOOK_OPEN, 1.0F, 1.0F);
    }
}
