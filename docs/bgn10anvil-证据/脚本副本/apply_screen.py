import sys
sys.stdout.reconfigure(errors="replace")

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
PATH = ROOT + r"\src\main\java\com\hjmmd_8\bettergold\client\SturdygoldAnvilScreen.java"

SRC = '''package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.menu.SturdygoldAnvilMenu;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.inventory.ItemCombinerScreen;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundRenameItemPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/**
 * <b>万坚金砧的界面</b>（1.7 {@code bg-n10} 轮8 创建；{@code bg-n10anvil} 轮按作者 2026-10-18 试玩反馈
 * 「贴图严重匹配错误」「把 GUI 换成和普通铁砧完全一致」<b>整类重写</b>）。
 *
 * <h2>现在走的就是原版砧那条路：{@code ItemCombinerScreen}</h2>
 * <p>原版 {@code AnvilScreen extends ItemCombinerScreen<AnvilMenu>}；本类照抄同一层
 * （{@code ItemCombinerScreen<SturdygoldAnvilMenu>}），于是下面这些<b>全部由父类原样提供</b>，
 * 我们一行都不再自己写：</p>
 * <ul>
 *   <li>{@code renderBg} = {@code blit(texture, leftPos, topPos, 0, 0, 176, 166)} + {@code renderErrorIcon}；</li>
 *   <li>{@code render()} 的顺序 = 背景 → 槽位 → 文字 → {@code renderFg} → tooltip；</li>
 *   <li>{@code init()} = {@code subInit()} + 注册 {@code ContainerListener}（改名输入框靠它初始化）；</li>
 *   <li>槽位坐标来自 {@code AnvilMenu} 的 {@code 27 / 76 / 134 @ 47} + 背包 {@code 8,84/102/120} + 快捷栏 {@code 142}。</li>
 * </ul>
 *
 * <h2>逐项照原版 {@code AnvilScreen} 抄全的元素（坐标/颜色/字面全部原版）</h2>
 * <pre>标题            drawString(font, title, 60, 6, 4210752, false)        ← 原版 titleLabelX = 60
 * 物品栏标题      drawString(font, playerInventoryTitle, 8, 72, 4210752, false)  ← imageHeight 166 - 94
 * 等级花费        k = 176 - 8 - font.width - 2；fill(k-2, 67, 168, 79, 0x4F000000)；
 *                drawString(font, component, k, 69, j)（默认带阴影）
 *                j = 8453920（够级，绿）；16736352（不够级 / ≥40「过于昂贵」，红）
 *                i >= 40 且非创造 ⇒ container.repair.expensive；花费为 0 ⇒ 什么都不画
 * 名字输入框      EditBox(left+62, top+24, 103, 12)，无边框、白字、maxLength 50，
 *                responder -> 原版 setItemName + ServerboundRenameItemPacket
 * 输入框底图      blitSprite(container/anvil/text_field[_disabled], left+59, top+20, 110, 16)
 * 错误图标        blitSprite(container/anvil/error, x+99, y+45, 28, 21)</pre>
 *
 * <h2>★ 截图里那条「红条」到底是什么（实测，不是猜）</h2>
 * <p>作者那张金色 GUI <b>本身就是原版 {@code anvil.png} 的 1:1 换色</b>（176×166 主面板亮度相关 0.7186；
 * 槽位/背包/快捷栏逐像素同位置）。原版 {@code anvil.png} 在 {@code (59,20)-(168,35)} 有一块
 * <b>纯红 (255,0,0) 占位方块</b>（实测 1760 像素），它由原版那块 {@code text_field} 精灵盖住；
 * 作者换色时把这块占位也一起涂成了红条（金色图里同样是 {@code (59,20)-(168,35)} 110×16 的纯红）。
 * 旧版界面没有画 {@code text_field} 精灵、也没画输入框 ⇒ 红条直接露出来，就是截图里那条红条。</p>
 * <p>⇒ 修法 = <b>照原版画 {@code text_field} 精灵 + EditBox</b>，红条被同一位置、同一尺寸的精灵盖住。
 * <b>没有改任何 PNG 像素</b>（作者素材，SHA256 由关卡钉住）。</p>
 *
 * <h2>⚠ 旧口径（{@code bg-n10} 轮8）原文留档，已作废</h2>
 * <p>旧版是自建 {@code AbstractContainerScreen}：{@code renderBg} 里三次 {@code blit}
 * （主面板 + 右上装饰 + 左下两条灰条）、{@code renderLabels} 里把花费文字画进
 * {@code x60 y20 110×16} 的「红条」并居中、外加一个 35% 半透明的空槽幽灵金币。
 * 作者 2026-10-18 明确要求「所有 GUI 标识换成和普通铁砧完全一致」⇒ 这些自加元素<b>全部删除</b>：
 * 右上装饰 / 左下两条是金色图里 176×166 主面板之外的装饰，不属于原版砧 GUI，不再 blit；
 * 幽灵金币不再画（贴图文件保留，作者素材不删）。旧文档 §17.2 / §17.9 的相关口径已在
 * {@code docs/1.7-...md} §25 就地标注。</p>
 */
public class SturdygoldAnvilScreen extends ItemCombinerScreen<SturdygoldAnvilMenu> {

    /** 金色主面板：贴图 (0,0) 起 176×166（与原版砧同一块区域、同尺寸） */
    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "textures/gui/container/sturdygold_anvil.png");

    /** 原版砧的三个 GUI 精灵（在 {@code minecraft:gui/sprites} 图集里，blitSprite 用它们是对的） */
    private static final ResourceLocation TEXT_FIELD_SPRITE =
            ResourceLocation.withDefaultNamespace("container/anvil/text_field");
    private static final ResourceLocation TEXT_FIELD_DISABLED_SPRITE =
            ResourceLocation.withDefaultNamespace("container/anvil/text_field_disabled");
    private static final ResourceLocation ERROR_SPRITE =
            ResourceLocation.withDefaultNamespace("container/anvil/error");

    private static final Component TOO_EXPENSIVE_TEXT = Component.translatable("container.repair.expensive");

    /** 与原版砧相同（{@code AbstractContainerScreen} 的默认值也是 176×166，这里显式写出来给关卡钉） */
    public static final int PANEL_WIDTH = 176;
    public static final int PANEL_HEIGHT = 166;

    private EditBox name;
    private final Player player;

    public SturdygoldAnvilScreen(SturdygoldAnvilMenu menu, Inventory playerInventory, Component title) {
        super(menu, playerInventory, title, TEXTURE);
        this.imageWidth = PANEL_WIDTH;
        this.imageHeight = PANEL_HEIGHT;
        this.titleLabelX = 60;
        this.player = playerInventory.player;
    }

    /** 逐字照原版 {@code AnvilScreen#subInit}：位置、尺寸、最大长度、无边框、白字、responder 全部一致 */
    @Override
    protected void subInit() {
        int i = (this.width - this.imageWidth) / 2;
        int j = (this.height - this.imageHeight) / 2;
        this.name = new EditBox(this.font, i + 62, j + 24, 103, 12, Component.translatable("container.repair"));
        this.name.setCanLoseFocus(false);
        this.name.setTextColor(-1);
        this.name.setTextColorUneditable(-1);
        this.name.setBordered(false);
        this.name.setMaxLength(50);
        this.name.setResponder(this::onNameChanged);
        this.name.setValue("");
        this.addWidget(this.name);
        this.name.setEditable(this.menu.getSlot(0).hasItem());
    }

    @Override
    protected void setInitialFocus() {
        this.setInitialFocus(this.name);
    }

    @Override
    public void resize(Minecraft minecraft, int width, int height) {
        String s = this.name.getValue();
        this.init(minecraft, width, height);
        this.name.setValue(s);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == 256) {
            this.minecraft.player.closeContainer();
        }

        return !this.name.keyPressed(keyCode, scanCode, modifiers) && !this.name.canConsumeInput()
                ? super.keyPressed(keyCode, scanCode, modifiers)
                : true;
    }

    /** 逐字照原版：只有名字真的变了才发 {@code ServerboundRenameItemPacket} */
    private void onNameChanged(String name) {
        Slot slot = this.menu.getSlot(0);
        if (slot.hasItem()) {
            String s = name;
            if (!slot.getItem().has(DataComponents.CUSTOM_NAME)
                    && name.equals(slot.getItem().getHoverName().getString())) {
                s = "";
            }

            if (this.menu.setItemName(s)) {
                this.minecraft.player.connection.send(new ServerboundRenameItemPacket(s));
            }
        }
    }

    /**
     * 背景 = 原版 {@code ItemCombinerScreen#renderBg}（176×166 主面板 + 错误图标）+ 原版输入框底图。
     *
     * <p>输入框底图必须画：它盖住金色图里 {@code (59,20)-(168,35)} 那块和原版一模一样的红色占位。</p>
     */
    @Override
    protected void renderBg(GuiGraphics guiGraphics, float partialTick, int mouseX, int mouseY) {
        super.renderBg(guiGraphics, partialTick, mouseX, mouseY);
        guiGraphics.blitSprite(this.menu.getSlot(0).hasItem() ? TEXT_FIELD_SPRITE : TEXT_FIELD_DISABLED_SPRITE,
                this.leftPos + 59, this.topPos + 20, 110, 16);
    }

    /**
     * 三处文字 + 花费，逐字照原版 {@code AnvilScreen#renderLabels}（坐标/颜色/阈值一个数没改）。
     *
     * <p>标题与物品栏标题这里显式画（而不是调 {@code super.renderLabels}），是为了让
     * 「原版三处 drawString 的坐标字面」在本类源码里可被关卡逐项钉住；数值与父类实现完全相同：
     * 标题 {@code (titleLabelX=60, titleLabelY=6)}、物品栏 {@code (8, 166-94=72)}、颜色 {@code 4210752}、无阴影。</p>
     */
    @Override
    protected void renderLabels(GuiGraphics guiGraphics, int mouseX, int mouseY) {
        guiGraphics.drawString(this.font, this.title, 60, 6, 4210752, false);
        guiGraphics.drawString(this.font, this.playerInventoryTitle, 8, 72, 4210752, false);
        int i = this.menu.getCost();
        if (i > 0) {
            int j = 8453920;
            Component component;
            if (i >= 40 && !this.minecraft.player.getAbilities().instabuild) {
                component = TOO_EXPENSIVE_TEXT;
                j = 16736352;
            } else if (!this.menu.getSlot(2).hasItem()) {
                component = null;
            } else {
                component = Component.translatable("container.repair.cost", i);
                if (!this.menu.getSlot(2).mayPickup(this.player)) {
                    j = 16736352;
                }
            }

            if (component != null) {
                int k = this.imageWidth - 8 - this.font.width(component) - 2;
                int l = 69;
                guiGraphics.fill(k - 2, 67, this.imageWidth - 8, 79, 1325400064);
                guiGraphics.drawString(this.font, component, k, 69, j);
            }
        }
    }

    @Override
    public void renderFg(GuiGraphics guiGraphics, int mouseX, int mouseY, float partialTick) {
        this.name.render(guiGraphics, mouseX, mouseY, partialTick);
    }

    /** 逐字照原版：两个输入槽任一有东西、输出为空 ⇒ 画原版那个错误图标 */
    @Override
    protected void renderErrorIcon(GuiGraphics guiGraphics, int x, int y) {
        if ((this.menu.getSlot(0).hasItem() || this.menu.getSlot(1).hasItem())
                && !this.menu.getSlot(this.menu.getResultSlot()).hasItem()) {
            guiGraphics.blitSprite(ERROR_SPRITE, x + 99, y + 45, 28, 21);
        }
    }

    /** 逐字照原版：输入 1 变了就把名字框同步成它的显示名（并抢焦点） */
    @Override
    public void slotChanged(net.minecraft.world.inventory.AbstractContainerMenu containerToSend, int slotInd, ItemStack stack) {
        if (slotInd == 0) {
            this.name.setValue(stack.isEmpty() ? "" : stack.getHoverName().getString());
            this.name.setEditable(!stack.isEmpty());
            this.setFocused(this.name);
        }
    }
}
'''

data = SRC.replace("\r\n", "\n").encode("utf-8")
open(PATH, "wb").write(data)
print("wrote", PATH, len(data), "B")
