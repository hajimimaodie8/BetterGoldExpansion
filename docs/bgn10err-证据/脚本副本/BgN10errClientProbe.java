package com.hjmmd_8.bettergold.probe;

import java.io.InputStream;

import com.hjmmd_8.bettergold.bettergold;
import com.mojang.blaze3d.platform.NativeImage;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.resources.ResourceLocation;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/**
 * 临时客户端启动探针（bg-n10err：万坚金砧的 error 精灵变体）—— 收尾整块删除。
 *
 * <p>只做启动探针：标题界面出现后，从客户端<b>真正挂载</b>的 GUI 图集 / 资源包里读数，
 * <b>不进任何世界</b>，然后 {@link Minecraft#stop()} 只调一次。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class BgN10errClientProbe {

    private static final String TAG = "BGN10ERRCLIENT";
    private static final String SWITCH = "bgn10err-client.enabled";

    private static final ResourceLocation OURS =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "container/sturdygold_anvil/error");
    private static final ResourceLocation VANILLA =
            ResourceLocation.withDefaultNamespace("container/anvil/error");
    private static final ResourceLocation GUI_ATLAS =
            ResourceLocation.withDefaultNamespace("textures/atlas/gui.png");

    private static boolean done;
    private static int passes;
    private static int fails;

    private BgN10errClientProbe() {
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            passes++;
            bettergold.LOGGER.info("{} PASS {} :: {}", TAG, name, detail);
        } else {
            fails++;
            bettergold.LOGGER.error("{} FAIL {} :: {}", TAG, name, detail);
        }
    }

    @SubscribeEvent
    public static void onClientTick(ClientTickEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        if (done || mc.screen == null) {
            return;
        }
        if (!java.nio.file.Files.exists(java.nio.file.Path.of(System.getProperty("user.dir"), SWITCH))) {
            return;
        }
        done = true;
        try {
            run(mc);
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} EXCEPTION", TAG, t);
            fails++;
        }
        bettergold.LOGGER.info("{} SUMMARY pass={} fail={} (没有进世界)", TAG, passes, fails);
        mc.stop();
    }

    private static void run(Minecraft mc) throws Exception {
        check("client_title_screen", mc.screen instanceof TitleScreen,
                "screen=" + mc.screen.getClass().getName());

        // ① GUI 图集里的精灵本体：解析到 + 不是 missing + 尺寸 28x21
        TextureAtlasSprite ours = mc.getGuiSprites().getSprite(OURS);
        boolean oursMissing = ours == null
                || ours.contents().name().equals(MissingTextureAtlasSprite.getLocation());
        check("sprite_present", !oursMissing, "sprite=" + (ours == null ? "null" : ours.contents().name()));
        check("sprite_not_missing", !oursMissing, "missing=" + oursMissing + "（missing 必须 = 0）");
        check("sprite_28x21", ours != null && ours.contents().width() == 28 && ours.contents().height() == 21,
                "size=" + (ours == null ? "n/a"
                        : ours.contents().width() + "x" + ours.contents().height()));
        // 原版那一张做对照：证明"查表本身是有效的"（否则 ours 也可能是查不到才 missing）
        TextureAtlasSprite vanilla = mc.getGuiSprites().getSprite(VANILLA);
        check("vanilla_control_present", vanilla != null
                        && !vanilla.contents().name().equals(MissingTextureAtlasSprite.getLocation()),
                "vanilla=" + (vanilla == null ? "null" : vanilla.contents().name())
                        + " size=" + (vanilla == null ? "n/a"
                        : vanilla.contents().width() + "x" + vanilla.contents().height()));
        // 图集纹理本身在 TextureManager 里（不是 missing 回退）
        check("gui_atlas_texture_loaded",
                mc.getTextureManager().getTexture(GUI_ATLAS) != MissingTextureAtlasSprite.getTexture(),
                "texture=" + mc.getTextureManager().getTexture(GUI_ATLAS).getClass().getName());

        // ② 客户端资源包里那 414 B 的 PNG：能读、28x21、像素对得上（A 级：真的读到了像素）
        ResourceLocation png = ResourceLocation.fromNamespaceAndPath(bettergold.MODID,
                "textures/gui/sprites/container/sturdygold_anvil/error.png");
        var res = mc.getResourceManager().getResource(png);
        check("png_resource_present", res.isPresent(), "resource=" + png);
        int w = -1;
        int h = -1;
        int p00 = 0;
        int p1310 = 0;
        int p2720 = 0;
        if (res.isPresent()) {
            try (InputStream in = res.get().open(); NativeImage img = NativeImage.read(in)) {
                w = img.getWidth();
                h = img.getHeight();
                p00 = img.getPixelRGBA(0, 0);
                p1310 = img.getPixelRGBA(13, 10);
                p2720 = img.getPixelRGBA(27, 20);
            }
        }
        check("png_28x21", w == 28 && h == 21, "size=" + w + "x" + h);
        // ⚠ NativeImage#getPixelRGBA 的原生字节序是 **ABGR 打包进 int**（RGBA 的 4 个字节按小端读回）：
        //   作者 (99,45) #D89106 ⇒ 0xFF0691D8；原版红叉 #BA370F ⇒ 0xFF0F37BA；作者 (126,65) #FCDB40 ⇒ 0xFF40DBFC
        check("pixel_00_from_author", Integer.toHexString(p00).equalsIgnoreCase("ff0691d8"),
                "pixel(0,0)=" + Integer.toHexString(p00) + "（ABGR；期望 ff0691d8 = 作者贴图 (99,45) #D89106）");
        check("pixel_13_10_is_red", Integer.toHexString(p1310).equalsIgnoreCase("ff0f37ba"),
                "pixel(13,10)=" + Integer.toHexString(p1310) + "（ABGR；期望 ff0f37ba = 原版红叉 #BA370F）");
        check("pixel_27_20_from_author", Integer.toHexString(p2720).equalsIgnoreCase("ff40dbfc"),
                "pixel(27,20)=" + Integer.toHexString(p2720) + "（ABGR；期望 ff40dbfc = 作者贴图 (126,65) #FCDB40）");

        // ③ 原版对照：它也是 28x21（说明"尺寸读法"本身没读错）
        check("vanilla_28x21", vanilla != null && vanilla.contents().width() == 28
                        && vanilla.contents().height() == 21,
                "vanilla size=" + (vanilla == null ? "n/a"
                        : vanilla.contents().width() + "x" + vanilla.contents().height()));
        // ④ 图集给这张精灵登记的名字里确实带这条路径（不是落到别的 id 上）
        check("sprite_id_contains_path",
                ours != null && ours.contents().name().getPath().contains("container/sturdygold_anvil/error"),
                "name=" + (ours == null ? "null" : ours.contents().name().toString()));
    }
}
