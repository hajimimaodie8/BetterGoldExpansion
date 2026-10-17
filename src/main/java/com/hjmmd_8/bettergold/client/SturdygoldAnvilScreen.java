package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.menu.SturdygoldAnvilMenu;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

/**
 * <b>万坚金砧的界面</b>（1.7 {@code bg-n10} 轮8 —— 本仓<b>第一个</b> {@code AbstractContainerScreen}）。
 *
 * <h2>技术路线判定：<b>自建 {@code AbstractContainerScreen}</b>（不裁切、不裁成 176×166 单张贴图）</h2>
 * <p>依据是<b>贴图的实测像素</b>（不是看感觉）：作者给的 {@code 万坚金砧 gui.png} 是 256×256，
 * 但<b>画出来的内容</b>分三块（逐行 alpha 扫描，见 {@code docs/1.7-...md} §17.2）：</p>
 * <pre>  主面板      x 0..175,   y 0..165     ← 恰好等于原版砧的 176×166，且 9 个槽/背包/快捷栏的
 *                                           格子坐标与 {@code AnvilMenu} 写死的 27/76/134 @47、
 *                                           8/84、8/142 **逐像素重合**
 *     右上装饰    x 176..203, y 0..20      ← 主面板右侧探出的一小块（28×21）
 *     左下两条    x 0..109,   y 166..197   ← 主面板下方两块灰条（110×32）</pre>
 * <p>⇒ <b>不需要裁切</b>：主面板本来就和原版砧同尺寸、同槽位；那两块装饰用两次额外 {@code blit}
 * 贴在面板外侧即可。<b>imageWidth = 176 / imageHeight = 166</b> 保持原版砧的居中与文本基线，
 * 于是 {@code renderLabels} 里"物品栏"三个字仍在 (8,72) —— 与原版砧一致。</p>
 *
 * <h2>⚠ 不许用 {@code blitSprite}（本仓踩过）</h2>
 * <p>1.21.1 的 GUI 图集只扫 {@code assets/<ns>/textures/gui/sprites/}；放在 {@code gui/container/}
 * 的贴图用 {@code blitSprite} 会静默退化成 missing sprite（紫黑格、不报错）——见
 * {@code docs/构建与跑测注意事项.md} §五。这里全部走 {@link GuiGraphics#blit(ResourceLocation,...)}。</p>
 *
 * <h2>空槽幽灵图标</h2>
 * <p>作者素材里的 {@code 空槽中的混沌金币串图标.png}（16×16 灰色三连币）画在<b>输入 2 槽</b>里、
 * 半透明（35%）：提示"这里放混沌金币串"。只在"输入 1 已放可修装备且输入 2 还是空的"时画
 * （判据 {@link SturdygoldAnvilMenu#isCoinRepairCandidate()}），否则满屏提示反而干扰。</p>
 *
 * <h2>花费文字画在哪（★ 与 {@code AnvilScreen} 的差异，记账）</h2>
 * <p>原版 {@code AnvilScreen} 把"花费 X 级 / 过于昂贵"画在 {@code y = 69} 右对齐，因为原版砧贴图那一行是空的。
 * 作者这张贴图<b>在 y 20..35、x 60..170 画了一条 110×16 的红条</b>（原版同一位置是名字输入框），
 * 而 y 69 那一行是金色装饰 —— 所以本界面把花费文字画进<b>红条</b>里（白字居中），
 * 原版那个位置不画。⚠ 观感属"人眼未验证"项（本轮没有跑客户端截屏）。</p>
 */
public class SturdygoldAnvilScreen extends AbstractContainerScreen<SturdygoldAnvilMenu> {

    /** 主面板贴图：贴图坐标 (0,0) 起 176×166 */
    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "textures/gui/container/sturdygold_anvil.png");

    /** 空槽幽灵图标（作者素材「空槽中的混沌金币串图标.png」的字节原样） */
    private static final ResourceLocation GHOST_COIN =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "textures/gui/container/sturdygold_anvil_coin_ghost.png");

    /** 主面板尺寸 = 原版砧（槽位坐标才对得上） */
    public static final int PANEL_WIDTH = 176;
    public static final int PANEL_HEIGHT = 166;
    /** 右上装饰（贴图 u=176,v=0，28×21） */
    private static final int TAB_U = 176;
    private static final int TAB_V = 0;
    private static final int TAB_W = 28;
    private static final int TAB_H = 21;
    /** 左下两条灰条（贴图 u=0,v=166，110×32） */
    private static final int PLATES_U = 0;
    private static final int PLATES_V = 166;
    private static final int PLATES_W = 110;
    private static final int PLATES_H = 32;
    /** 贴图整张大小（blit 的 textureWidth/Height 必须给 256，否则 uv 会按贴图实际大小归一化错） */
    private static final int TEX_W = 256;
    private static final int TEX_H = 256;

    /** 红条（花费文字的背景）：贴图坐标 x 60..169、y 20..35 */
    private static final int COST_BAR_X = 60;
    private static final int COST_BAR_Y = 20;
    private static final int COST_BAR_W = 110;
    private static final int COST_BAR_H = 16;

    /** 输入 2 槽的贴图坐标（{@code AnvilMenu} 写死 76,47） */
    private static final int ADDITIONAL_SLOT_X = 76;
    private static final int ADDITIONAL_SLOT_Y = 47;

    public SturdygoldAnvilScreen(SturdygoldAnvilMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title);
        this.imageWidth = PANEL_WIDTH;
        this.imageHeight = PANEL_HEIGHT;
        // 与原版 AnvilScreen 一致（标题在 x=60），物品栏标签仍落在 (8, 72)
        this.titleLabelX = 60;
    }

    @Override
    protected void renderBg(GuiGraphics guiGraphics, float partialTick, int mouseX, int mouseY) {
        int left = this.leftPos;
        int top = this.topPos;
        // ① 主面板 176×166（贴图 (0,0) 起）
        guiGraphics.blit(TEXTURE, left, top, 0.0F, 0.0F, PANEL_WIDTH, PANEL_HEIGHT, TEX_W, TEX_H);
        // ② 右上装饰（贴在面板右侧）
        guiGraphics.blit(TEXTURE, left + PANEL_WIDTH, top, (float) TAB_U, (float) TAB_V, TAB_W, TAB_H, TEX_W, TEX_H);
        // ③ 左下两条灰条（贴在面板下方）
        guiGraphics.blit(TEXTURE, left, top + PANEL_HEIGHT, (float) PLATES_U, (float) PLATES_V, PLATES_W, PLATES_H, TEX_W, TEX_H);
        // ④ 空槽幽灵图标（半透明，35%）
        if (!this.menu.getSlot(SturdygoldAnvilMenu.ADDITIONAL_SLOT).hasItem()
                && this.menu.isCoinRepairCandidate()) {
            guiGraphics.setColor(1.0F, 1.0F, 1.0F, 0.35F);
            guiGraphics.blit(GHOST_COIN, left + ADDITIONAL_SLOT_X + 1, top + ADDITIONAL_SLOT_Y + 1,
                    0.0F, 0.0F, 16, 16, 16, 16);
            // ⚠ setColor 是 RenderSystem.setShaderColor 的直通，必须显式还原
            guiGraphics.setColor(1.0F, 1.0F, 1.0F, 1.0F);
        }
    }

    @Override
    protected void renderLabels(GuiGraphics guiGraphics, int mouseX, int mouseY) {
        // 标题 + "物品栏"：沿用父类（标题 x=60 / 物品栏 (8,72)，与原版砧一致）
        super.renderLabels(guiGraphics, mouseX, mouseY);
        int cost = this.menu.getCost();
        if (cost <= 0) {
            return;
        }
        Component text = Component.translatable("container.repair.cost", cost);
        int width = this.font.width(text);
        int x = COST_BAR_X + (COST_BAR_W - width) / 2;
        int y = COST_BAR_Y + (COST_BAR_H - 8) / 2;
        // 红条上是白字（贴图自带背景，这里不再画半透明底）
        guiGraphics.drawString(this.font, text, x, y, 0xFFFFFF, false);
    }
}
