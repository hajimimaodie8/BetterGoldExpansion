package net.minecraft.advancements;

import com.google.common.annotations.VisibleForTesting;
import it.unimi.dsi.fastutil.objects.ReferenceOpenHashSet;
import java.util.Set;
import javax.annotation.Nullable;

public class AdvancementNode {
    private final AdvancementHolder holder;
    @Nullable
    private final AdvancementNode parent;
    private final Set<AdvancementNode> children = new ReferenceOpenHashSet<>();

    @VisibleForTesting
    public AdvancementNode(AdvancementHolder holder, @Nullable AdvancementNode parent) {
        this.holder = holder;
        this.parent = parent;
    }

    public Advancement advancement() {
        return this.holder.value();
    }

    public AdvancementHolder holder() {
        return this.holder;
    }

    @Nullable
    public AdvancementNode parent() {
        return this.parent;
    }

    public AdvancementNode root() {
        return getRoot(this);
    }

    public static AdvancementNode getRoot(AdvancementNode node) {
        AdvancementNode advancementnode = node;

        while (true) {
            AdvancementNode advancementnode1 = advancementnode.parent();
            if (advancementnode1 == null) {
                return advancementnode;
            }

            advancementnode = advancementnode1;
        }
    }

    public Iterable<AdvancementNode> children() {
        return this.children;
    }

    @VisibleForTesting
    public void addChild(AdvancementNode child) {
        this.children.add(child);
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        } else {
            if (other instanceof AdvancementNode advancementnode && this.holder.equals(advancementnode.holder)) {
                return true;
            }

            return false;
        }
    }

    @Override
    public int hashCode() {
        return this.holder.hashCode();
    }

    @Override
    public String toString() {
        return this.holder.id().toString();
    }
}
