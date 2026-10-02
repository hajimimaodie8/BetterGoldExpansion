package com.hjmmd_8.bettergold.client;

import java.util.ArrayList;
import java.util.List;

import com.hjmmd_8.bettergold.material.MetalFamily;
import com.hjmmd_8.bettergold.material.MetalWeapons;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.neoforged.neoforge.client.extensions.common.IClientItemExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;

/**
 * 本模组武器的客户端装配（1.5 武器轮）：<b>物品模型谓词</b> 与 <b>自定义物品渲染器</b>。
 *
 * <h2>为什么物品模型谓词必须自己登记</h2>
 * <p>1.21 的 {@code ItemProperties} 把谓词按<b>物品实例</b>存在
 * {@code Map<Item, Map<ResourceLocation, ItemPropertyFunction>>} 里
 * （neoforge sources {@code net/minecraft/client/renderer/item/ItemProperties.java:42}），
 * 而 {@code getProperty} 的兜底是 {@code PROPERTIES.get(stack.getItem())}（同文件 80-82 行）——
 * <b>子类不会继承父类登记过的谓词</b>。原版只给 {@code Items.BOW} / {@code Items.CROSSBOW} /
 * {@code Items.TRIDENT} / {@code Items.SHIELD} 登记过（同文件 104-243 行），
 * 所以本模组的弓 / 弩 / 三叉戟 / 盾牌如果只照搬原版模型 JSON，
 * {@code pulling} / {@code charged} / {@code throwing} / {@code blocking} 这些 override
 * 会<b>永远取不到值、贴图永远停在本体那一帧</b>（模型不报错，只是不动）。
 * 这里用同一个 {@code ItemProperties.register(...)} 把整套谓词挂到我们的物品上。</p>
 *
 * <p>登记时机：{@code FMLClientSetupEvent#enqueueWork}（见 {@code bettergoldClient}）。
 * 谓词只在<b>渲染时</b>被查询，而渲染必定晚于客户端 setup，所以这个时机是安全的。</p>
 *
 * <h2>自定义渲染器</h2>
 * <p>盾牌 / 三叉戟的原版外观是「实体模型」，走 {@code Item#builtin/entity} +
 * {@code BlockEntityWithoutLevelRenderer}；原版那两段是写死的物品判定（见
 * {@link MetalWeaponItemRenderer} 的类注释）。这里通过 NeoForge 的
 * {@code RegisterClientExtensionsEvent} 给本模组的盾牌 / 三叉戟挂上自己的渲染器。</p>
 *
 * <h2>1.5 修正轮：5 件「胚底」在这里没有任何登记</h2>
 * <p>胚底是纯合成中间物（见 {@code material.MetalBlanks}）：它们既不是弓 / 弩 / 三叉戟 / 盾牌，
 * 也没有任何 override 谓词与自定义渲染器需求，所以本类只处理六套金属的武器。</p>
 */
public final class MetalWeaponItemProperties {

    /** 本模组全部武器物品（弓 / 弩 / 三叉戟 / 盾牌；不含重锤 —— 它走普通 {@code item/handheld_mace} 模型） */
    private static List<Item> weaponItems() {
        List<Item> out = new ArrayList<>();
        for (MetalFamily family : MetalFamily.all()) {
            out.add(family.bow.get());
            out.add(family.crossbow.get());
            out.add(family.trident.get());
            out.add(family.shield.get());
        }
        return out;
    }

    /** 全部盾牌（六套金属） */
    private static List<Item> shieldItems() {
        List<Item> out = new ArrayList<>();
        for (MetalFamily family : MetalFamily.all()) {
            out.add(family.shield.get());
        }
        return out;
    }

    /** 全部三叉戟（六套金属） */
    private static List<Item> tridentItems() {
        List<Item> out = new ArrayList<>();
        for (MetalFamily family : MetalFamily.all()) {
            out.add(family.trident.get());
        }
        return out;
    }

    private static final ResourceLocation PULL = ResourceLocation.withDefaultNamespace("pull");
    private static final ResourceLocation PULLING = ResourceLocation.withDefaultNamespace("pulling");
    private static final ResourceLocation CHARGED = ResourceLocation.withDefaultNamespace("charged");
    private static final ResourceLocation FIREWORK = ResourceLocation.withDefaultNamespace("firework");
    private static final ResourceLocation THROWING = ResourceLocation.withDefaultNamespace("throwing");
    private static final ResourceLocation BLOCKING = ResourceLocation.withDefaultNamespace("blocking");

    /**
     * 自定义渲染器<b>懒加载</b>：绝不能在类初始化期就 {@code new}。
     *
     * <p>{@code RegisterClientExtensionsEvent} 在 {@code Minecraft} 构造器里
     * （{@code ClientHooks.initClientHooks} → {@code ClientExtensionsManager.init}）就被派发，
     * 那比 {@code Minecraft} 自己初始化完还早；此时 {@code Minecraft.getInstance()} 还是 null，
     * {@code new MetalWeaponItemRenderer()} 里的 {@code Minecraft.getInstance().getEntityModels()}
     * 会抛异常 → 整个模组加载失败（首次实测就是这样崩在启动阶段的）。</p>
     */
    private static MetalWeaponItemRenderer renderer;

    private static synchronized MetalWeaponItemRenderer renderer() {
        if (renderer == null) {
            renderer = new MetalWeaponItemRenderer();
        }
        return renderer;
    }

    /**
     * 注册物品模型谓词。必须 {@code enqueueWork} 到客户端主线程之后调用
     * （{@code bettergoldClient#onClientSetup} 里已经这么做了）。
     */
    public static void register() {
        for (MetalFamily family : MetalFamily.all()) {
            registerBow(family.bow.get());
            registerCrossbow(family.crossbow.get());
            registerShield(family.shield.get());
            registerTrident(family.trident.get());
        }
        com.hjmmd_8.bettergold.bettergold.LOGGER.info(
                "1.5 武器轮：已为 {} 件武器登记物品模型谓词（弓 pull/pulling、弩 pull/pulling/charged/firework、三叉戟 throwing、盾牌 blocking）",
                weaponItems().size());
    }

    /**
     * 弓：{@code pull} 用<b>我们自己的</b> 16 tick 满蓄力当分母（原版用写死的 20）。
     * 模型的 {@code pull: 0.65 / 0.9} 两帧于是分别落在 10.4 / 14.4 tick，
     * 与 {@code MetalWeapons.MetalBowItem#powerForTime} 的曲线同步 —— 不这么写，
     * 16 tick 拉满时 {@code pull} 只到 0.8，第三帧贴图永远不会出现。
     */
    private static void registerBow(Item item) {
        net.minecraft.client.renderer.item.ItemProperties.register(item, PULL,
                (stack, level, entity, seed) -> {
                    if (entity == null) {
                        return 0.0F;
                    }
                    return entity.getUseItem() != stack
                            ? 0.0F
                            : (float) (stack.getUseDuration(entity) - entity.getUseItemRemainingTicks())
                                    / (float) MetalWeapons.BOW_FULL_DRAW_TICKS;
                });
        net.minecraft.client.renderer.item.ItemProperties.register(item, PULLING,
                (stack, level, entity, seed) -> entity != null && entity.isUsingItem()
                        && entity.getUseItem() == stack ? 1.0F : 0.0F);
    }

    /**
     * 弩：{@code pull} 用 {@link MetalWeapons.MetalCrossbowItem#chargeDuration}（20 tick）当分母，
     * 其余三个谓词与数值全部照抄原版（{@code charged} / {@code firework} / {@code pulling}）。
     */
    private static void registerCrossbow(Item item) {
        net.minecraft.client.renderer.item.ItemProperties.register(item, PULL,
                (stack, level, entity, seed) -> {
                    if (entity == null) {
                        return 0.0F;
                    }
                    return CrossbowItem.isCharged(stack) ? 0.0F
                            : (float) (stack.getUseDuration(entity) - entity.getUseItemRemainingTicks())
                                    / (float) MetalWeapons.MetalCrossbowItem.chargeDuration(stack, entity);
                });
        net.minecraft.client.renderer.item.ItemProperties.register(item, PULLING,
                (stack, level, entity, seed) -> entity != null && entity.isUsingItem()
                        && entity.getUseItem() == stack && !CrossbowItem.isCharged(stack) ? 1.0F : 0.0F);
        net.minecraft.client.renderer.item.ItemProperties.register(item, CHARGED,
                (stack, level, entity, seed) -> CrossbowItem.isCharged(stack) ? 1.0F : 0.0F);
        net.minecraft.client.renderer.item.ItemProperties.register(item, FIREWORK,
                (stack, level, entity, seed) -> {
                    ChargedProjectiles charged = stack.get(DataComponents.CHARGED_PROJECTILES);
                    return charged != null && charged.contains(net.minecraft.world.item.Items.FIREWORK_ROCKET)
                            ? 1.0F
                            : 0.0F;
                });
    }

    /** 盾牌：{@code blocking}（与 vanilla {@code Items.SHIELD} 逐字一致） */
    private static void registerShield(Item item) {
        net.minecraft.client.renderer.item.ItemProperties.register(item, BLOCKING,
                (stack, level, entity, seed) -> entity != null && entity.isUsingItem()
                        && entity.getUseItem() == stack ? 1.0F : 0.0F);
    }

    /** 三叉戟：{@code throwing}（与 vanilla {@code Items.TRIDENT} 逐字一致） */
    private static void registerTrident(Item item) {
        net.minecraft.client.renderer.item.ItemProperties.register(item, THROWING,
                (stack, level, entity, seed) -> entity != null && entity.isUsingItem()
                        && entity.getUseItem() == stack ? 1.0F : 0.0F);
    }

    /**
     * NeoForge 客户端扩展：给本模组的盾牌 / 三叉戟挂上
     * {@link MetalWeaponItemRenderer}（取代原版那个只认 {@code Items.SHIELD} / {@code Items.TRIDENT}
     * 的默认渲染器）。
     */
    public static void onRegisterClientExtensions(RegisterClientExtensionsEvent event) {
        IClientItemExtensions extensions = new IClientItemExtensions() {
            @Override
            public net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer getCustomRenderer() {
                return renderer();
            }
        };
        List<Item> shields = shieldItems();
        List<Item> tridents = tridentItems();
        event.registerItem(extensions, shields.toArray(new Item[0]));
        event.registerItem(extensions, tridents.toArray(new Item[0]));
        com.hjmmd_8.bettergold.bettergold.LOGGER.info(
                "1.5 武器轮：已为 {} 件盾牌 + {} 件三叉戟登记自定义物品渲染器（MetalWeaponItemRenderer）",
                shields.size(), tridents.size());
    }

    private MetalWeaponItemProperties() {
    }
}
