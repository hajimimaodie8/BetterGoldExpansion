package net.minecraft.advancements.critereon;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.mojang.serialization.codecs.RecordCodecBuilder.Instance;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Stream;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.advancements.Criterion;
import net.minecraft.core.HolderSet;
import net.minecraft.core.component.DataComponentPredicate;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ItemLike;

public class InventoryChangeTrigger extends SimpleCriterionTrigger<InventoryChangeTrigger.TriggerInstance> {
    @Override
    public Codec<InventoryChangeTrigger.TriggerInstance> codec() {
        return InventoryChangeTrigger.TriggerInstance.CODEC;
    }

    public void trigger(ServerPlayer player, Inventory inventory, ItemStack stack) {
        int i = 0;
        int j = 0;
        int k = 0;

        for (int l = 0; l < inventory.getContainerSize(); l++) {
            ItemStack itemstack = inventory.getItem(l);
            if (itemstack.isEmpty()) {
                j++;
            } else {
                k++;
                if (itemstack.getCount() >= itemstack.getMaxStackSize()) {
                    i++;
                }
            }
        }

        this.trigger(player, inventory, stack, i, j, k);
    }

    private void trigger(ServerPlayer player, Inventory inventory, ItemStack stack, int full, int empty, int occupied) {
        this.trigger(player, p_43166_ -> p_43166_.matches(inventory, stack, full, empty, occupied));
    }

    public static record TriggerInstance(Optional<ContextAwarePredicate> player, InventoryChangeTrigger.TriggerInstance.Slots slots, List<ItemPredicate> items)
        implements SimpleCriterionTrigger.SimpleInstance {
        public static final Codec<InventoryChangeTrigger.TriggerInstance> CODEC = RecordCodecBuilder.create(
            p_337367_ -> p_337367_.group(
                        EntityPredicate.ADVANCEMENT_CODEC.optionalFieldOf("player").forGetter(InventoryChangeTrigger.TriggerInstance::player),
                        InventoryChangeTrigger.TriggerInstance.Slots.CODEC
                            .optionalFieldOf("slots", InventoryChangeTrigger.TriggerInstance.Slots.ANY)
                            .forGetter(InventoryChangeTrigger.TriggerInstance::slots),
                        ItemPredicate.CODEC.listOf().optionalFieldOf("items", List.of()).forGetter(InventoryChangeTrigger.TriggerInstance::items)
                    )
                    .apply(p_337367_, InventoryChangeTrigger.TriggerInstance::new)
        );

        public static Criterion<InventoryChangeTrigger.TriggerInstance> hasItems(ItemPredicate.Builder... items) {
            return hasItems(Stream.of(items).map(ItemPredicate.Builder::build).toArray(ItemPredicate[]::new));
        }

        public static Criterion<InventoryChangeTrigger.TriggerInstance> hasItems(ItemPredicate... items) {
            return CriteriaTriggers.INVENTORY_CHANGED
                .createCriterion(
                    new InventoryChangeTrigger.TriggerInstance(Optional.empty(), InventoryChangeTrigger.TriggerInstance.Slots.ANY, List.of(items))
                );
        }

        public static Criterion<InventoryChangeTrigger.TriggerInstance> hasItems(ItemLike... items) {
            ItemPredicate[] aitempredicate = new ItemPredicate[items.length];

            for (int i = 0; i < items.length; i++) {
                aitempredicate[i] = new ItemPredicate(
                    Optional.of(HolderSet.direct(items[i].asItem().builtInRegistryHolder())), MinMaxBounds.Ints.ANY, DataComponentPredicate.EMPTY, Map.of()
                );
            }

            return hasItems(aitempredicate);
        }

        public boolean matches(Inventory inventory, ItemStack stack, int full, int empty, int occupied) {
            if (!this.slots.matches(full, empty, occupied)) {
                return false;
            } else if (this.items.isEmpty()) {
                return true;
            } else if (this.items.size() != 1) {
                List<ItemPredicate> list = new ObjectArrayList<>(this.items);
                int i = inventory.getContainerSize();

                for (int j = 0; j < i; j++) {
                    if (list.isEmpty()) {
                        return true;
                    }

                    ItemStack itemstack = inventory.getItem(j);
                    if (!itemstack.isEmpty()) {
                        list.removeIf(p_340607_ -> p_340607_.test(itemstack));
                    }
                }

                return list.isEmpty();
            } else {
                return !stack.isEmpty() && this.items.get(0).test(stack);
            }
        }

        public static record Slots(MinMaxBounds.Ints occupied, MinMaxBounds.Ints full, MinMaxBounds.Ints empty) {
            public static final Codec<InventoryChangeTrigger.TriggerInstance.Slots> CODEC = RecordCodecBuilder.create(
                p_337368_ -> p_337368_.group(
                            MinMaxBounds.Ints.CODEC
                                .optionalFieldOf("occupied", MinMaxBounds.Ints.ANY)
                                .forGetter(InventoryChangeTrigger.TriggerInstance.Slots::occupied),
                            MinMaxBounds.Ints.CODEC
                                .optionalFieldOf("full", MinMaxBounds.Ints.ANY)
                                .forGetter(InventoryChangeTrigger.TriggerInstance.Slots::full),
                            MinMaxBounds.Ints.CODEC
                                .optionalFieldOf("empty", MinMaxBounds.Ints.ANY)
                                .forGetter(InventoryChangeTrigger.TriggerInstance.Slots::empty)
                        )
                        .apply(p_337368_, InventoryChangeTrigger.TriggerInstance.Slots::new)
            );
            public static final InventoryChangeTrigger.TriggerInstance.Slots ANY = new InventoryChangeTrigger.TriggerInstance.Slots(
                MinMaxBounds.Ints.ANY, MinMaxBounds.Ints.ANY, MinMaxBounds.Ints.ANY
            );

            public boolean matches(int full, int empty, int occupied) {
                if (!this.full.matches(full)) {
                    return false;
                } else {
                    return !this.empty.matches(empty) ? false : this.occupied.matches(occupied);
                }
            }
        }
    }
}
