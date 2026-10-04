package com.hjmmd_8.bettergold.client;

import java.lang.reflect.Field;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.material.CreativePageSections;
import com.hjmmd_8.bettergold.material.CreativeSections;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.CreativeModeTab;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ContainerScreenEvent;

/**
 * 创造模式「分区横幅」的客户端渲染（航空学同款效果，但<b>不使用 Mixin</b>）。
 *
 * <h2>按「分区」选横幅（1.4 定稿）</h2>
 * 本模组只有<b>一个</b>创造页（{@code bettergold:bettergold_tab}），页内共 <b>5 个分区</b>，
 * 每个分区<b>一条</b>横幅（材料 materials.png / 建筑 blocks.png / 食物 food.png / 装备 gear.png / 乐事 fd.png）。
 * 所以这里<b>不按标签页</b>选图，而是：只在本页被选中时，遍历
 * {@link CreativeSections#SECTION_ROWS}（key = 分区 key），用 key 去
 * {@link CreativePageSections#byKey(String)} 取该分区的横幅贴图与释词。
 * 分区 key 与页 id 都由 {@link CreativePageSections} 单点给出，别名/改名不会失配。
 *
 * <h2>绘制落点：{@link ContainerScreenEvent.Render.Foreground}（bg-16 修正）</h2>
 * <p><b>旧口径（1.4 起，已被 bg-16 推翻、此处留档不删）</b>：用 {@code ScreenEvent.Render.Post}，
 * 理由是「它由 {@code ClientHooks#drawScreenInternal} 在 {@code screen.renderWithTooltip(...)}
 * 之后发出，两者时序等价」。<b>那句「时序等价」是错的</b>：
 * {@code renderWithTooltip} = {@code render(...)} + {@code renderTooltip(...)}（{@code Screen.java:111-117}，
 * tooltip 是<b>最后</b>画的），而 {@code ClientHooks.java:429-430} 是在它<b>整段之后</b>才发事件
 * ⇒ 横幅被画在 tooltip <b>之上</b>，鼠标悬停到横幅下方那一行的物品时，物品的名字/tooltip
 * 会被横幅盖住（作者报的「Z 轴深度不够」就是这个现象）。</p>
 *
 * <p><b>为什么不能靠「改 z 深度」修</b>（作者原话给的方向里就有这一条，实测源码后排除）：
 * {@code AbstractContainerScreen#render} 第 141 行是 {@code RenderSystem.disableDepthTest()}
 * —— 物品格那一段的<b>深度测试被整个关掉</b>，z 参数不参与遮挡判定，只有<b>绘制顺序</b>决定谁在上。
 * 所以唯一正确的修法是<b>换绘制落点，而不是换 z 值</b>（更不是隐藏/降透明度）。</p>
 *
 * <p><b>现行落点</b>：{@link ContainerScreenEvent.Render.Foreground}
 * （{@code AbstractContainerScreen#render} 第 158 行 {@code renderLabels(...)} 之后、
 * 第 159 行发出；其 javadoc 原文：「<i>Fired after the container screen's foreground layer and elements
 * are drawn, but <b>before rendering the tooltips</b> and the item stack being dragged by the player</i>」）
 * ⇒ <b>仍在物品/滑条之后（不会被底板盖掉）、但在 tooltip 之前（不再盖住 tooltip）</b>，
 * 与航空学参考实现（注入 {@code render} 的 TAIL）时序一致，且依旧<b>不使用 Mixin</b>。</p>
 *
 * <p>⚠ <b>连带要求：坐标必须改成「容器相对」</b>。该事件是在 {@code pose().translate(leftPos, topPos, 0)}
 * <b>之内</b>发出的（第 142-143 行，push 之后没有 pop），所以物品区左上角在这里的局部坐标就是
 * {@code (ITEM_AREA_X, ITEM_AREA_Y)}；再按旧写法加一次 {@code guiLeft/guiTop} 会整体偏移
 * 一个 (leftPos, topPos)。</p>
 *
 * <h2>绘制顺序（与方案文档一致）</h2>
 * <ol>
 *   <li>先 blit 该分区的横幅底图（162×18，正好一整行）</li>
 *   <li>在横幅左侧画释词底方块（半透明填充）</li>
 *   <li>最后写释词（带阴影）</li>
 * </ol>
 *
 * <h2>反射字段依据（全部来自 1.21.1 源码，不是猜的）</h2>
 * <ul>
 *   <li>{@code private static CreativeModeTab selectedTab} ——
 *       {@code CreativeModeInventoryScreen.java} 第 105 行</li>
 *   <li>{@code private float scrollOffs} —— 同文件第 109 行（屏幕自身的字段，不在 menu 里）</li>
 *   <li>首个可见行公式 = {@code ItemPickerMenu#getRowIndexForScroll} —— 同文件第 1033-1035 行：
 *       {@code Math.max((int)(scrollOffs * calculateRowCount() + 0.5), 0)}，
 *       其中 {@code calculateRowCount() = Mth.positiveCeilDiv(items.size(), 9) - 5}（第 1029-1031 行）</li>
 *   <li>物品格区左上角 = {@code (leftPos + 8, topPos + 17)}：格子坐标是
 *       {@code 9 + 列*18 / 18 + 行*18}（第 1010 行），18×18 格子的左上角再各减 1 像素</li>
 *   <li>{@code leftPos/topPos}：优先反射读 {@code AbstractContainerScreen} 的
 *       {@code protected int leftPos/topPos}（第 74/78 行），兜底用 NeoForge 暴露的
 *       {@code getGuiLeft()/getGuiTop()}（第 752-753 行）</li>
 * </ul>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class CreativeSectionBanners {

    // ==================== 布局常量 ====================

    /** 创造界面尺寸（CreativeModeInventoryScreen 构造器第 130-131 行） */
    private static final int IMAGE_WIDTH = 195;
    private static final int IMAGE_HEIGHT = 136;
    /** 物品格区左上角相对 leftPos / topPos 的偏移（= 首个格子坐标 9/18 各减 1） */
    private static final int ITEM_AREA_X = 8;
    private static final int ITEM_AREA_Y = 17;
    /** 单格边长；横幅高度与单格等高 */
    private static final int CELL = 18;
    private static final int ITEMS_PER_ROW = CreativeSections.ITEMS_PER_ROW;
    /** 可见行数（NUM_ROWS） */
    private static final int VISIBLE_ROWS = 5;
    /** 横幅贴图尺寸：宽 = 9×18 = 一整行 */
    private static final int BANNER_WIDTH = 162;
    private static final int BANNER_HEIGHT = 18;

    /** 释词底方块：半透明黑；文字：不透明白 */
    private static final int TITLE_BACKGROUND = 0x90000000;
    private static final int TITLE_COLOR = 0xFFFFFFFF;
    /** 释词文字相对横幅左上角的偏移 */
    private static final int TITLE_TEXT_X = 5;
    private static final int TITLE_TEXT_Y = 5;
    /** 底方块相对文字左右各留的边距 */
    private static final int TITLE_PADDING = 3;

    /*
     * 横幅贴图不写在这里：贴图是「分区」的属性（{@link CreativePageSections.Section#banner()}），
     * 分区 → 贴图 / 释词 的映射只在 {@link CreativePageSections} 一处维护。
     * 资源实际位置是 {@code assets/bettergold/textures/gui/creative_sections/*.png}，
     * 即 {@code textures/gui/...} 而不是 {@code textures/gui/sprites/...}。
     * 1.21.1 的 GUI 图集只扫描 {@code gui/sprites}（原版 {@code assets/minecraft/atlases/gui.json}
     * 里只有一条 {@code {"type":"directory","source":"gui/sprites"}}，配合
     * {@code GuiSpriteManager} 构造器里的 {@code ResourceLocation.withDefaultNamespace("gui")}），
     * 所以这里不能用 {@code GuiGraphics#blitSprite}（它只查 GUI 图集，查不到会退回 missing sprite
     * 画成紫黑格），而是用 {@code GuiGraphics#blit} 直接 blit 整张贴图 ——
     * 原版创造界面自己的 {@code tab_items.png} 等背景图也是这么画的。
     */

    // ==================== 事件入口 ====================

    /**
     * 绘制入口（bg-16 起改用 {@link ContainerScreenEvent.Render.Foreground}）。
     *
     * <p>旧实现在 {@code ScreenEvent.Render.Post}（= tooltip 之后）⇒ 横幅压住 tooltip；
     * 现行落点在 {@code renderLabels} 之后、tooltip 之前。判据（只在本模组唯一创造页、
     * 且本页被选中时才画）与行号计算全部逐字不变。</p>
     */
    @SubscribeEvent
    public static void onContainerScreenForeground(ContainerScreenEvent.Render.Foreground event) {
        if (!(event.getContainerScreen() instanceof CreativeModeInventoryScreen screen)) {
            return;
        }
        ResourceLocation tabId = selectedTabId();
        // 只在「本模组唯一创造页」被选中时画：别的页（含原版页、FD 自己的页）一律不画
        if (!CreativePageSections.PAGE_TAB_ID.equals(tabId)) {
            return;
        }
        Map<String, Integer> rows = CreativeSections.SECTION_ROWS;
        if (rows.isEmpty()) {
            return;
        }
        CreativeModeInventoryScreen.ItemPickerMenu menu = screen.getMenu();
        int firstVisibleRow = firstVisibleRow(menu, scrollOffs(screen));
        // ⚠ 本事件在 pose().translate(leftPos, topPos, 0) 之内发出 ⇒ 用「容器相对坐标」，
        //    绝不能再加 guiLeft/guiTop（那会整体偏移一个 (leftPos, topPos)）。
        int left = ITEM_AREA_X;
        int top = ITEM_AREA_Y;
        GuiGraphics graphics = event.getGuiGraphics();

        for (Map.Entry<String, Integer> entry : rows.entrySet()) {
            // 键 = 分区 key：横幅与释词都按「分区」取（一个分区一条横幅）
            CreativePageSections.Section section = CreativePageSections.byKey(entry.getKey());
            if (section == null) {
                continue;
            }
            int row = bannerRow(menu, entry.getValue() - firstVisibleRow);
            if (row < 0) {
                continue;
            }
            drawBanner(graphics, section.banner(), section.label(), left, top + row * CELL);
        }
    }

    // ==================== 行号计算 ====================

    /**
     * 当前首个可见行，公式与原版 {@code ItemPickerMenu#getRowIndexForScroll} 完全一致。
     */
    private static int firstVisibleRow(CreativeModeInventoryScreen.ItemPickerMenu menu, float scrollOffs) {
        int rowCount = Mth.positiveCeilDiv(menu.items.size(), ITEMS_PER_ROW) - VISIBLE_ROWS;
        if (rowCount <= 0) {
            return 0;
        }
        return Math.max((int) ((double) (scrollOffs * (float) rowCount) + 0.5), 0);
    }

    /**
     * 求横幅该画在第几个可见行（相对物品区顶部），不是可见行就返回 -1。
     *
     * <p>{@code anchor} = {@link CreativeSections#SECTION_ROWS} 记录的行号 − 首个可见行。
     * 该表记的是<b>分区首个物品所在行</b>：{@code layout()} 在加入本区物品<b>之前</b>取样
     * {@code out.size() / ITEMS_PER_ROW}，并且列表开头先补一整行空格子，所以每页第一个分区的值恒为 1
     * （即它的首物品行）。而「分区之后补满当前行、再空一整行」的排布规则保证了
     * <b>记录行的上一行必定是整行空格子</b>，也就是横幅该待的位置。</p>
     *
     * <p>所以这里<b>不写死 −1，只认「整行空格子」这个事实</b>：目标行是空行就画在那里，
     * 否则退回上一行，两行都不空就不画。这样无论 {@code SECTION_ROWS} 记的是「首个物品行」
     * 还是（以后若改成）「横幅空行」，结果都落在同一条空行上，并且绝不会把横幅画到物品上。</p>
     */
    private static int bannerRow(CreativeModeInventoryScreen.ItemPickerMenu menu, int anchor) {
        if (isRowEmpty(menu, anchor)) {
            return anchor;
        }
        if (isRowEmpty(menu, anchor - 1)) {
            return anchor - 1;
        }
        return -1;
    }

    /** 该可见行是否整行都没有物品（行号必须在 0..4） */
    private static boolean isRowEmpty(CreativeModeInventoryScreen.ItemPickerMenu menu, int row) {
        if (row < 0 || row >= VISIBLE_ROWS) {
            return false;
        }
        int first = row * ITEMS_PER_ROW;
        if (first + ITEMS_PER_ROW > menu.slots.size()) {
            return false;
        }
        for (int i = first; i < first + ITEMS_PER_ROW; i++) {
            Slot slot = menu.getSlot(i);
            if (slot.hasItem()) {
                return false;
            }
        }
        return true;
    }

    // ==================== 绘制 ====================

    /** 横幅 →（左侧）释词底方块 → 释词文字 */
    private static void drawBanner(GuiGraphics graphics, ResourceLocation banner, String title, int x, int y) {
        graphics.blit(banner, x, y, 0, 0.0F, 0.0F, BANNER_WIDTH, BANNER_HEIGHT, BANNER_WIDTH, BANNER_HEIGHT);

        Font font = Minecraft.getInstance().font;
        Component text = Component.literal(title);
        int textWidth = font.width(text);
        graphics.fill(x + TITLE_PADDING, y + TITLE_PADDING,
                x + textWidth + TITLE_TEXT_X + TITLE_PADDING, y + BANNER_HEIGHT - TITLE_PADDING,
                TITLE_BACKGROUND);
        graphics.drawString(font, text, x + TITLE_TEXT_X, y + TITLE_TEXT_Y, TITLE_COLOR, true);
    }

    // ==================== 反射读取（原版字段都是 private，只能反射） ====================

    /** 当前选中的标签页 id；读不到就返回 null（不画） */
    private static @Nullable ResourceLocation selectedTabId() {
        Field field = findField(CreativeModeInventoryScreen.class, "selectedTab");
        if (field == null) {
            return null;
        }
        try {
            if (field.get(null) instanceof CreativeModeTab tab) {
                return BuiltInRegistries.CREATIVE_MODE_TAB.getKey(tab);
            }
        } catch (ReflectiveOperationException ignored) {
            // 忽略：拿不到就不画横幅，绝不因为装饰性渲染把客户端搞崩
        }
        return null;
    }

    /** 卷动位置 0..1（原版 {@code private float scrollOffs}） */
    private static float scrollOffs(CreativeModeInventoryScreen screen) {
        Field field = findField(screen.getClass(), "scrollOffs");
        if (field == null) {
            return 0.0F;
        }
        try {
            return field.getFloat(screen);
        } catch (ReflectiveOperationException ignored) {
            return 0.0F;
        }
    }

    /*
     * bg-16：原来这里还有 guiLeft(screen) / guiTop(screen) / readInt(...) 三个助手
     * （反射读 leftPos/topPos，兜底用 getGuiLeft()/getGuiTop()）。
     * 改用 ContainerScreenEvent.Render.Foreground 之后坐标必须是「容器相对」的，
     * 这三个助手没有任何调用点，故整块删除（不是注释掉；旧口径已写在类 javadoc 里留档）。
     * findField(...) 仍然被 selectedTabId / scrollOffs 使用，保留。
     */

    /** 沿继承链找字段（leftPos/topPos 声明在 AbstractContainerScreen 上，不在子类） */
    private static @Nullable Field findField(Class<?> type, String name) {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Field field = current.getDeclaredField(name);
                field.setAccessible(true);
                return field;
            } catch (NoSuchFieldException ignored) {
                // 继续往父类找
            }
        }
        return null;
    }

    // ==================== 小工具 ====================

    private CreativeSectionBanners() {
    }
}
