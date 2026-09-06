package com.hjmmd_8.bettergold.fd;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingEntityUseItemEvent;

/**
 * FD（农夫乐事）联动分支的事件处理：FD 物品的特有行为。
 * 由 {@link FdModule} 在农夫乐事加载时注册到 NeoForge.EVENT_BUS。
 *
 * - 炼金贝肉家族食用后施加 FD"滋养"效果（nourishment）。
 *   滋养是 FD 效果；物品本体不引用 FD 类，这里动态查 registry 施加（FD 未装则本类不会被注册）。
 */
public class FdEvents {

    @SubscribeEvent
    public static void onItemUseFinish(LivingEntityUseItemEvent.Finish event) {
        LivingEntity entity = event.getEntity();
        if (entity.level().isClientSide) {
            return;
        }
        Item item = event.getItem().getItem();

        // 炼金贝肉系列：按物品名施加对应时长的滋养（未吃炼金贝肉则跳过）
        if (item == FdItems.ALCHEMICAL_MEAT.get() || item == FdItems.ALCHEMICAL_MEAT_SKEWER.get()) {
            applyNourishment(entity, 3600); // 3 分钟滋养1
        } else if (item == FdItems.ALCHEMICAL_MEAT_SANDWICH.get()) {
            applyNourishment(entity, 7200); // 6 分钟滋养1
        } else if (item == FdItems.STURDYGOLD_ALCHEMICAL_MEAT.get()
                || item == FdItems.STURDYGOLD_ALCHEMICAL_MEAT_SKEWER.get()
                || item == FdItems.STURDYGOLD_ALCHEMICAL_MEAT_SANDWICH.get()) {
            applyNourishment(entity, 19200); // 16 分钟滋养1
        }
    }

    /** 施加 FD"滋养"效果；效果缺失时静默跳过 */
    private static void applyNourishment(LivingEntity entity, int ticks) {
        try {
            var lookup = entity.level().registryAccess()
                    .lookupOrThrow(net.minecraft.core.registries.Registries.MOB_EFFECT);
            var holder = lookup.get(net.minecraft.resources.ResourceKey.create(
                    net.minecraft.core.registries.Registries.MOB_EFFECT,
                    net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("farmersdelight", "nourishment")));
            if (holder.isPresent()) {
                entity.addEffect(new MobEffectInstance(holder.get(), ticks, 0));
            }
        } catch (Exception ignored) {
            // 注册表未就绪或 FD 缺失时跳过
        }
    }

    private FdEvents() {
    }
}
