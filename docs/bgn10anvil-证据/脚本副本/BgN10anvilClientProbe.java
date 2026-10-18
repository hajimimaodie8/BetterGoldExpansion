package com.hjmmd_8.bettergold.probe;

import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllBlocks;
import com.hjmmd_8.bettergold.registry.AllMenus;
import com.mojang.blaze3d.platform.NativeImage;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.renderer.texture.AbstractTexture;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/**
 * 临时客户端探针（bg-n10anvil：万坚金砧的 blockstate → model → 5 张 texture + GUI 贴图）—— 收尾整块删除。
 *
 * <p>只做启动探针：标题界面出现后，从客户端**真正挂载**的模型/贴图/资源包里读数，
 * **不进任何世界**，然后 {@link Minecraft#stop()} 只调一次。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class BgN10anvilClientProbe {

    private static final String TAG = "BGN10ANVILCLIENT";
    private static final String SWITCH = "bgn10anvil-client.enabled";

    private static boolean done;
    private static int passes;
    private static int fails;

    private BgN10anvilClientProbe() {
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
        mc.stop(); // 只调一次
    }

    private static void run(Minecraft mc) throws Exception {
        check("client_title_screen", mc.screen instanceof TitleScreen,
                "screen=" + mc.screen.getClass().getName());

        // ① 自定义 Screen 工厂（原版那张 MenuScreens 表）
        check("screen_factory_present",
                MenuScreens.getScreenFactory(AllMenus.STURDYGOLD_ANVIL.get()).isPresent(),
                "MenuScreens.getScreenFactory(bettergold:sturdygold_anvil) present");

        // ② blockstate → baked model：21 个面全部解析，且没有任何 missing sprite
        BlockState state = AllBlocks.STURDYGOLD_ANVIL.get().defaultBlockState();
        BakedModel model = mc.getModelManager().getBlockModelShaper().getBlockModel(state);
        check("model_not_missing", model != mc.getModelManager().getMissingModel(),
                "baked model class=" + model.getClass().getName());
        Set<String> sprites = new HashSet<>();
        int quads = 0;
        for (int i = -1; i < 6; i++) {
            Direction dir = i < 0 ? null : Direction.values()[i];
            for (var quad : model.getQuads(state, dir, RandomSource.create(42L))) {
                quads++;
                TextureAtlasSprite sprite = quad.getSprite();
                sprites.add(sprite.contents().name().toString());
            }
        }
        check("model_quads_21", quads == 21, "quads=" + quads + "（4 个 element 共 21 个面）");
        boolean missing = sprites.contains(MissingTextureAtlasSprite.getLocation().toString());
        check("model_no_missing_sprite", !missing, "sprites=" + sprites + " missing=" + missing);
        for (String want : new String[] {
                "bettergold:block/sturdygold_anvil_top",
                "bettergold:block/sturdygold_anvil_ns",
                "bettergold:block/sturdygold_anvil_ew",
                "bettergold:block/sturdygold_anvil_base_top",
                "bettergold:block/sturdygold_anvil_base_bottom" }) {
            check("model_sprite_" + want.substring(want.lastIndexOf('/') + 1),
                    sprites.contains(want), "want=" + want);
        }

        // ③ GUI 贴图：客户端资源包里在 + TextureManager 真的读到了（不是 missing 回退）
        ResourceLocation gui = ResourceLocation.fromNamespaceAndPath(bettergold.MODID,
                "textures/gui/container/sturdygold_anvil.png");
        var res = mc.getResourceManager().getResource(gui);
        check("gui_resource_present", res.isPresent(), "resource=" + gui);
        int w = -1;
        int h = -1;
        if (res.isPresent()) {
            try (InputStream in = res.get().open(); NativeImage img = NativeImage.read(in)) {
                w = img.getWidth();
                h = img.getHeight();
            }
        }
        check("gui_png_256x256", w == 256 && h == 256, "size=" + w + "x" + h);
        AbstractTexture tex = mc.getTextureManager().getTexture(gui);
        check("gui_texture_loaded", tex != MissingTextureAtlasSprite.getTexture(),
                "texture class=" + tex.getClass().getName() + "（!= missing 回退）");
    }
}
