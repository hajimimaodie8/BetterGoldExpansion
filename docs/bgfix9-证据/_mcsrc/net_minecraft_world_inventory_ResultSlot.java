package net.minecraft.world.inventory;

import net.minecraft.core.NonNullList;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeType;

public class ResultSlot extends Slot {
    private final CraftingContainer craftSlots;
    private final Player player;
    private int removeCount;

    public ResultSlot(Player player, CraftingContainer craftSlots, Container container, int slot, int xPosition, int yPosition) {
        super(container, slot, xPosition, yPosition);
        this.player = player;
        this.craftSlots = craftSlots;
    }

    /**
     * Check if the stack is allowed to be placed in this slot, used for armor slots as well as furnace fuel.
     */
    @Override
    public boolean mayPlace(ItemStack stack) {
        return false;
    }

    /**
     * Decrease the size of the stack in slot (first int arg) by the amount of the second int arg. Returns the new stack.
     */
    @Override
    public ItemStack remove(int amount) {
        if (this.hasItem()) {
            this.removeCount = this.removeCount + Math.min(amount, this.getItem().getCount());
        }

        return super.remove(amount);
    }

    /**
     * Typically increases an internal count, then calls {@code onCrafting(item)}.
     *
     * @param stack the output - ie, iron ingots, and pickaxes, not ore and wood.
     */
    @Override
    protected void onQuickCraft(ItemStack stack, int amount) {
        this.removeCount += amount;
        this.checkTakeAchievements(stack);
    }

    @Override
    protected void onSwapCraft(int numItemsCrafted) {
        this.removeCount += numItemsCrafted;
    }

    /**
     * @param stack the output - ie, iron ingots, and pickaxes, not ore and wood.
     */
    @Override
    protected void checkTakeAchievements(ItemStack stack) {
        if (this.removeCount > 0) {
            stack.onCraftedBy(this.player.level(), this.player, this.removeCount);
            net.neoforged.neoforge.event.EventHooks.firePlayerCraftingEvent(this.player, stack, this.craftSlots);
        }

        if (this.container instanceof RecipeCraftingHolder recipecraftingholder) {
            recipecraftingholder.awardUsedRecipes(this.player, this.craftSlots.getItems());
        }

        this.removeCount = 0;
    }

    @Override
    public void onTake(Player player, ItemStack stack) {
        this.checkTakeAchievements(stack);
        CraftingInput.Positioned craftinginput$positioned = this.craftSlots.asPositionedCraftInput();
        CraftingInput craftinginput = craftinginput$positioned.input();
        int i = craftinginput$positioned.left();
        int j = craftinginput$positioned.top();
        net.neoforged.neoforge.common.CommonHooks.setCraftingPlayer(player);
        NonNullList<ItemStack> nonnulllist = player.level().getRecipeManager().getRemainingItemsFor(RecipeType.CRAFTING, craftinginput, player.level());
        net.neoforged.neoforge.common.CommonHooks.setCraftingPlayer(null);

        for (int k = 0; k < craftinginput.height(); k++) {
            for (int l = 0; l < craftinginput.width(); l++) {
                int i1 = l + i + (k + j) * this.craftSlots.getWidth();
                ItemStack itemstack = this.craftSlots.getItem(i1);
                ItemStack itemstack1 = nonnulllist.get(l + k * craftinginput.width());
                if (!itemstack.isEmpty()) {
                    this.craftSlots.removeItem(i1, 1);
                    itemstack = this.craftSlots.getItem(i1);
                }

                if (!itemstack1.isEmpty()) {
                    if (itemstack.isEmpty()) {
                        this.craftSlots.setItem(i1, itemstack1);
                    } else if (ItemStack.isSameItemSameComponents(itemstack, itemstack1)) {
                        itemstack1.grow(itemstack.getCount());
                        this.craftSlots.setItem(i1, itemstack1);
                    } else if (!this.player.getInventory().add(itemstack1)) {
                        this.player.drop(itemstack1, false);
                    }
                }
            }
        }
    }

    @Override
    public boolean isFake() {
        return true;
    }
}
