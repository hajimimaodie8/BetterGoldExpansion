package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 新约 1.4 迁移用的「旧字段名别名」。
 *
 * <p>万坚金原来在 {@code AllItems}（约 48 处）/ {@code AllBlocks}（约 32 处）里自己注册，
 * 1.4 起实物一律交给 {@link MetalFamily} 注册。为了不动外面 40+ 处引用（以及数据文件、标签、语言），
 * {@code AllItems} / {@code AllBlocks} 保留原来的 public 字段名，只是把值改成这里的别名。</p>
 *
 * <p><b>为什么别名不是直接写 {@code AllMetals.STURDYGOLD.ingot}？</b>
 * 那会构成一个类初始化循环：{@code AllBlocks.<clinit>} 读到别名 → 触发 {@code AllMetals.<clinit>}
 * → 家族构造器要往 {@code AllItems.ITEMS} / {@code AllBlocks.BLOCKS} 里注册 → 触发
 * {@code AllItems.<clinit>} → 而 AllItems 的字段初始化又要读 {@code AllMetals.STURDYGOLD}，
 * 此时它还没被赋值，JVM 直接返回 null → {@code NullPointerException}。
 * （最小复现见 {@code build/scratch/CycleDemo.java}：{@code Cannot read field "ingot" because
 * "AllMetals.STURDYGOLD" is null}。）</p>
 *
 * <p>本类别名<b>按注册名懒绑定</b>（{@link DeferredBlock#createBlock} / {@link DeferredItem#createItem}）：
 * 不参与注册、不产生循环，解析出来的正是家族注册的同一个注册项 ——
 * {@code AllItems.STURDYGOLD_INGOT.get() == AllMetals.STURDYGOLD.ingot.get()}（运行时探针核对过）。</p>
 */
public final class MetalAliases {

    /** 按注册名建一个物品别名（不注册，只懒绑定；注册名不存在时 {@code get()} 会明确报 unbound） */
    public static <T extends Item> DeferredItem<T> item(String path) {
        return DeferredItem.createItem(ResourceLocation.fromNamespaceAndPath(bettergold.MODID, path));
    }

    /** 按注册名建一个方块别名（不注册，只懒绑定） */
    public static <T extends Block> DeferredBlock<T> block(String path) {
        return DeferredBlock.createBlock(ResourceLocation.fromNamespaceAndPath(bettergold.MODID, path));
    }

    private MetalAliases() {
    }
}
