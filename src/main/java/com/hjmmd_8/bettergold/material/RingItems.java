package com.hjmmd_8.bettergold.material;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllItems;
import com.mojang.serialization.Codec;

import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 1.8 阶段 3 · 段 C：<b>12 枚转化之戒 + 1 件胚底</b>的物品注册（§I-36~40）。
 *
 * <h2>口径（逐条对着规格）</h2>
 * <ul>
 *   <li><b>戒指本身始终注册</b> —— Curios 是 <b>A 类口径</b>（与 Patchouli 的 B 类<b>方向相反</b>）：
 *       没装 Curios 只是「没有戒指栏」，副手照样能用；见 {@code compat/CuriosCompat}。</li>
 *   <li><b>胚底</b>{@code ring_blank} = 纯合成材料（与 1.5 那 5 件 {@code golden_*_blank} 同一口径）：
 *       最普通的 {@link Item}、无功能、无耐久、无属性、进<b>材料</b>分区。</li>
 *   <li><b>模式</b>存在<b>物品数据组件</b> {@link #ALL_DAMAGE}（{@code bettergold:ring_all_damage}）上：
 *       {@code true} = 全部伤害转化、{@code false} / 缺省 = <b>仅物理伤害转化</b>（§I-37 的两种模式，默认取前者）。</li>
 *   <li><b>耐久</b>：只有<b>混源稳定</b>有 64（§I-38 末行「唯一有耐久：64」），其余 12 件都不设耐久
 *       （普通堆叠 64）。分崩离析是它的升级款 ⇒ <b>刻意不给耐久</b>。</li>
 * </ul>
 */
public final class RingItems {

    /** 数据组件注册表（在 {@code bettergold#create} 里挂到 mod 总线） */
    public static final DeferredRegister<DataComponentType<?>> COMPONENT_TYPES =
            DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, bettergold.MODID);

    /**
     * 模式组件：{@code true} = 「全部伤害转化」、{@code false} / 缺省 = 「仅物理伤害转化」。
     *
     * <p>按 {@code ChaosRange#VALUE} 的同一写法：{@code persistent(Codec.BOOL)} 进物品栈、
     * {@code networkSynchronized} 让客户端也能读（tooltip / 预测用）。</p>
     */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Boolean>> ALL_DAMAGE =
            COMPONENT_TYPES.register("ring_all_damage",
                    () -> DataComponentType.<Boolean>builder()
                            .persistent(Codec.BOOL)
                            .networkSynchronized(ByteBufCodecs.BOOL)
                            .build());

    /** 12 枚戒指（枚举顺序 = 注册顺序） */
    private static final Map<RingType, DeferredItem<Item>> RINGS = new EnumMap<>(RingType.class);

    static {
        for (RingType type : RingType.values()) {
            // 混源稳定 = 唯一有耐久的那一枚（§I-38）；其余一律不调 durability
            Item.Properties props = type == RingType.CHAOS_STABLE
                    ? new Item.Properties().durability(64)
                    : new Item.Properties();
            RINGS.put(type, AllItems.ITEMS.register(type.itemId(), () -> new RingItem(type, props)));
        }
    }

    /** 转化之戒胚底（纯合成材料，作者：与 1.5 的 5 件胚底同一口径） */
    public static final DeferredItem<Item> BLANK = AllItems.ITEMS.registerSimpleItem("ring_blank");

    /** 一枚戒指（{@code metalId} = 族 id；不是戒指返回 null） */
    public static @Nullable RingType typeOf(ItemStack stack) {
        if (stack == null || stack.isEmpty() || !(stack.getItem() instanceof RingItem ring)) {
            return null;
        }
        return ring.type;
    }

    /** 注册好的戒指物品（按枚举序） */
    public static List<DeferredItem<Item>> all() {
        return RingType.all().stream().map(RINGS::get).toList();
    }

    public static DeferredItem<Item> of(RingType type) {
        return RINGS.get(type);
    }

    /** 这枚戒指是不是「全部伤害转化」模式（缺省 = 仅物理） */
    public static boolean allDamage(ItemStack stack) {
        return stack.getOrDefault(ALL_DAMAGE.get(), Boolean.FALSE);
    }

    public static void setAllDamage(ItemStack stack, boolean value) {
        stack.set(ALL_DAMAGE.get(), value);
    }

    /** 当前模式的语言键（主手右键时给玩家一条 action bar 提示） */
    public static String modeKey(boolean allDamage) {
        return allDamage ? "message.bettergold.ring_mode_all" : "message.bettergold.ring_mode_physical";
    }

    /**
     * 戒指物品。右键（主手）= 切换模式（§I-37）。
     *
     * <p>⚠ <b>幻奏 / 混源稳定 / 分崩离析 没有两种模式</b> ⇒ 主手右键<b>什么都不做</b>
     * （不存组件、不提示，也不消耗动作）。</p>
     */
    public static final class RingItem extends Item {

        public final RingType type;

        RingItem(RingType type, Properties properties) {
            super(properties);
            this.type = type;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (!this.type.hasModes()) {
                return InteractionResultHolder.pass(stack);
            }
            if (!level.isClientSide) {
                boolean now = !allDamage(stack);
                setAllDamage(stack, now);
                player.displayClientMessage(Component.translatable(modeKey(now)), true);
                if (this.type.sound != null) {
                    level.playSound(null, player.getX(), player.getY(), player.getZ(),
                            this.type.sound.get(), net.minecraft.sounds.SoundSource.PLAYERS, 0.6F, 1.2F);
                }
            }
            return InteractionResultHolder.success(stack);
        }
    }

    private static final ResourceLocation MODE_KEY_ID =
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "ring_all_damage");

    /** 组件 id（探针 / 关卡读它，别再写字面量） */
    public static ResourceLocation componentId() {
        return MODE_KEY_ID;
    }

    /** 触发静态初始化（12 枚 + 胚底都在这时候登记进 {@link AllItems#ITEMS}） */
    public static void bootstrap() {
    }

    private RingItems() {
    }
}
