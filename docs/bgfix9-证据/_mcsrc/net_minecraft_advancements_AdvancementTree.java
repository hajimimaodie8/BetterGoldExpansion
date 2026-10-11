package net.minecraft.advancements;

import com.mojang.logging.LogUtils;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectLinkedOpenHashSet;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import javax.annotation.Nullable;
import net.minecraft.resources.ResourceLocation;
import org.slf4j.Logger;

public class AdvancementTree {
    private static final Logger LOGGER = LogUtils.getLogger();
    private final Map<ResourceLocation, AdvancementNode> nodes = new Object2ObjectOpenHashMap<>();
    private final Set<AdvancementNode> roots = new ObjectLinkedOpenHashSet<>();
    private final Set<AdvancementNode> tasks = new ObjectLinkedOpenHashSet<>();
    @Nullable
    private AdvancementTree.Listener listener;

    private void remove(AdvancementNode node) {
        for (AdvancementNode advancementnode : node.children()) {
            this.remove(advancementnode);
        }

        LOGGER.info("Forgot about advancement {}", node.holder());
        this.nodes.remove(node.holder().id());
        if (node.parent() == null) {
            this.roots.remove(node);
            if (this.listener != null) {
                this.listener.onRemoveAdvancementRoot(node);
            }
        } else {
            this.tasks.remove(node);
            if (this.listener != null) {
                this.listener.onRemoveAdvancementTask(node);
            }
        }
    }

    public void remove(Set<ResourceLocation> advancements) {
        for (ResourceLocation resourcelocation : advancements) {
            AdvancementNode advancementnode = this.nodes.get(resourcelocation);
            if (advancementnode == null) {
                LOGGER.warn("Told to remove advancement {} but I don't know what that is", resourcelocation);
            } else {
                this.remove(advancementnode);
            }
        }
    }

    public void addAll(Collection<AdvancementHolder> advancements) {
        List<AdvancementHolder> list = new ArrayList<>(advancements);

        while (!list.isEmpty()) {
            if (!list.removeIf(this::tryInsert)) {
                LOGGER.error("Couldn't load advancements: {}", list);
                break;
            }
        }

        LOGGER.info("Loaded {} advancements", this.nodes.size());
    }

    private boolean tryInsert(AdvancementHolder advancement) {
        Optional<ResourceLocation> optional = advancement.value().parent();
        AdvancementNode advancementnode = optional.map(this.nodes::get).orElse(null);
        if (advancementnode == null && optional.isPresent()) {
            return false;
        } else {
            AdvancementNode advancementnode1 = new AdvancementNode(advancement, advancementnode);
            if (advancementnode != null) {
                advancementnode.addChild(advancementnode1);
            }

            this.nodes.put(advancement.id(), advancementnode1);
            if (advancementnode == null) {
                this.roots.add(advancementnode1);
                if (this.listener != null) {
                    this.listener.onAddAdvancementRoot(advancementnode1);
                }
            } else {
                this.tasks.add(advancementnode1);
                if (this.listener != null) {
                    this.listener.onAddAdvancementTask(advancementnode1);
                }
            }

            return true;
        }
    }

    public void clear() {
        this.nodes.clear();
        this.roots.clear();
        this.tasks.clear();
        if (this.listener != null) {
            this.listener.onAdvancementsCleared();
        }
    }

    public Iterable<AdvancementNode> roots() {
        return this.roots;
    }

    public Collection<AdvancementNode> nodes() {
        return this.nodes.values();
    }

    @Nullable
    public AdvancementNode get(ResourceLocation id) {
        return this.nodes.get(id);
    }

    @Nullable
    public AdvancementNode get(AdvancementHolder advancement) {
        return this.nodes.get(advancement.id());
    }

    public void setListener(@Nullable AdvancementTree.Listener listener) {
        this.listener = listener;
        if (listener != null) {
            for (AdvancementNode advancementnode : this.roots) {
                listener.onAddAdvancementRoot(advancementnode);
            }

            for (AdvancementNode advancementnode1 : this.tasks) {
                listener.onAddAdvancementTask(advancementnode1);
            }
        }
    }

    public interface Listener {
        void onAddAdvancementRoot(AdvancementNode advancement);

        void onRemoveAdvancementRoot(AdvancementNode advancement);

        void onAddAdvancementTask(AdvancementNode advancement);

        void onRemoveAdvancementTask(AdvancementNode advancement);

        void onAdvancementsCleared();
    }
}
