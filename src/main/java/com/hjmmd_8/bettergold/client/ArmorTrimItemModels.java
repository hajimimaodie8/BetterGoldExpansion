package com.hjmmd_8.bettergold.client;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;

import javax.annotation.Nullable;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.material.MetalFamily;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.block.model.ItemOverrides;
import net.minecraft.client.renderer.block.model.ItemTransforms;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.client.resources.model.Material;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.armortrim.ArmorTrim;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ModelEvent;

/**
 * 1.5 修正⑦：让<b>盔甲纹饰在物品形态（背包 / 手持 / 展示框里的那件盔甲本身）</b>按对应材质颜色显示。
 *
 * <h2>真因（读源码与资源，不是猜）</h2>
 * <ol>
 *   <li><b>物品形态的纹饰不是渲染器画的，而是「物品模型 override」选的。</b>
 *       1.21.1 里 {@code ItemProperties} 注册了一个通用谓词 {@code minecraft:trim_type}
 *       （neoforge sources {@code net/minecraft/client/renderer/item/ItemProperties.java:96-100}）：
 *       它返回 {@code stack.get(DataComponents.TRIM).material().value().itemModelIndex()}，
 *       没有纹饰时返回 {@code Float.NEGATIVE_INFINITY}；
 *       而 {@code ItemRenderer} 第 224 行先做
 *       {@code bakedmodel.getOverrides().resolve(bakedmodel, stack, ...)}，
 *       {@code ItemOverrides#resolve} 依次用「阈值 ≤ 谓词值」挑出第一条命中的 override
 *       （同文件 92-101 行 + {@code BakedOverride#test} 的 {@code f < value → false}）。</li>
 *   <li><b>原版盔甲模型带的 override 只认原版材料。</b>
 *       {@code assets/minecraft/models/item/netherite_chestplate.json} 的 {@code overrides} 是
 *       {@code trim_type 0.1 → netherite_chestplate_quartz_trim}、{@code 0.2 → …_iron_trim} … {@code 1.0 → …_amethyst_trim}
 *       （10 条，0.1~1.0，见原版 client jar）。</li>
 *   <li><b>我们七个纹饰材质的 {@code item_model_index} 全都撞在原版值上</b>
 *       （改动前：六个金属 = 0.1 = <b>quartz</b>，unwanted_antique = 0.2 = iron）——
 *       于是「任何一件原版盔甲 + 我方纹饰」都会命中 <b>quartz</b> 那条，
 *       即 {@code trims/items/<type>_trim_quartz}，而 quartz 色卡就是白灰阶 ⇒ <b>纹饰一律显示成白色</b>，
 *       这正是作者说的「印上盔甲纹饰后纹饰都是白色」。</li>
 *   <li><b>我们自己的盔甲模型则完全没有 trim overlay</b>：
 *       {@code assets/bettergold/models/item/<金属>_<部位>.json} 只有
 *       {@code {parent: minecraft:item/generated, textures: {layer0: …}}}，
 *       既没有 {@code overrides}、也没有 {@code layer1 = minecraft:trims/items/<type>_trim_<asset>} 的兄弟模型
 *       （对照原版 {@code netherite_chestplate_quartz_trim.json}）⇒ 自己的盔甲连纹饰都不显示。</li>
 *   <li><b>物品图集（item atlas）里也没有我方材质的纹饰精灵</b>：
 *       {@code trims/items/*_trim_<asset>} 是由 {@code assets/minecraft/atlases/blocks.json} 的
 *       {@code paletted_permutations} 源生成的，而原版那份只列了 14 个原版材质名，没有我们七个
 *       （{@code SpriteSourceList#load} 用 {@code getResourceStack} 把各包同名图集**拼接**，
 *       所以本仓库新增一份同名 blocks.json 是**追加**，不会覆盖原版的源）。</li>
 * </ol>
 *
 * <h2>修法（本类 + 资源侧）</h2>
 * <ul>
 *   <li>资源侧：新增 {@code assets/minecraft/atlases/blocks.json}，为我方七个材质生成
 *       {@code trims/items/{helmet,chestplate,leggings,boots}_trim_<asset>} 精灵（色卡用各自的 8×1）。
 *       同时把七个 {@code trim_material} 的 {@code item_model_index} 改成互不相同、
 *       且<b>落在原版 0.1~1.0 之外的下方</b>（0.01~0.07）—— 这样即使某个渲染路径没经过本类的包装，
 *       也只会「不显示纹饰」，而不会错误地显示成 quartz 的白色。</li>
 *   <li>本类：在 {@code ModelEvent.ModifyBakingResult} 里给<b>所有带纹饰槽位的盔甲物品模型</b>
 *       （原版 25 件 + 我方六套 24 件）套一层包装，把 {@code getOverrides()} 换成自己的实现：
 *       纹饰材质是我方七个之一时，直接返回「原模型四边形 + 用对应纹饰精灵再画一层」的模型；
 *       其它情况原样交给原版 override 链。因此原版盔甲打上我方纹饰同样能出正确颜色，
 *       而且不需要复制/覆盖原版的 25 个模型 JSON。</li>
 * </ul>
 *
 * <p><b>可信度</b>：本类的判定（命中哪个模型、用哪个精灵名、精灵在不在图集里）都可以在客户端里
 * 用 {@code BakedModel#getOverrides().resolve(...)} + {@code BakedQuad#getSprite()} 复算，
 * 见 {@code docs/1.5-规格.md} 第十二节；最终「看起来对不对」仍需人眼。</p>
 */
@EventBusSubscriber(modid = bettergold.MODID, value = Dist.CLIENT)
public final class ArmorTrimItemModels {

    /**
     * 我方纹饰材质的 {@code asset_name} 集合：六套金属族的 id + 1.3 的老古董。
     * 与 {@code data/bettergold/trim_material/*.json} 的 {@code asset_name} 逐字一致
     * （各金属族的 trim_material 由 {@code generate_metal_trims.py} 生成，asset_name 就是族 id）。
     *
     * <p><b>必须懒解析</b>：本类的静态初始化可能发生在自动事件订阅类扫描时（早于模组构造器里
     * {@code AllMetals.bootstrap()}），那会儿 {@code MetalFamily.all()} 还是空的。</p>
     */
    private static volatile Set<String> trimAssets;

    private static Set<String> trimAssets() {
        Set<String> cached = trimAssets;
        if (cached == null) {
            Set<String> set = new HashSet<>();
            for (MetalFamily family : MetalFamily.all()) {
                set.add(family.id);
            }
            set.add("unwanted_antique");
            cached = Set.copyOf(set);
            trimAssets = cached;
        }
        return cached;
    }

    @SubscribeEvent
    public static void onModifyBakingResult(ModelEvent.ModifyBakingResult event) {
        Map<ModelResourceLocation, BakedModel> models = event.getModels();
        Function<Material, TextureAtlasSprite> textureGetter = event.getTextureGetter();
        Set<String> assets = trimAssets();
        int wrapped = 0;
        for (Item item : BuiltInRegistries.ITEM) {
            if (!(item instanceof ArmorItem armor) || !armor.getType().hasTrims()) {
                continue;   // 只有头盔 / 胸甲 / 护腿 / 靴子有纹饰槽位
            }
            ResourceLocation itemId = BuiltInRegistries.ITEM.getKey(item);
            if (itemId == null) {
                continue;
            }
            ModelResourceLocation key = ModelResourceLocation.inventory(itemId);
            BakedModel base = models.get(key);
            if (base == null) {
                continue;
            }
            models.put(key, new TrimAwareModel(base, armor.getType().getName(), textureGetter, assets));
            wrapped++;
        }
        bettergold.LOGGER.info("[bettergold] 盔甲纹饰物品模型：已包装 {} 件盔甲物品模型，我方纹饰材质 = {}",
                wrapped, assets);
    }

    /** 只改 {@code getOverrides()}，其余一律透传给原模型（含 GUI 变换、粒子图标、渲染层） */
    private static final class TrimAwareModel implements BakedModel {

        private final BakedModel base;
        private final ItemOverrides overrides;

        TrimAwareModel(BakedModel base, String armorTypeName,
                Function<Material, TextureAtlasSprite> textureGetter, Set<String> assets) {
            this.base = base;
            this.overrides = new TrimItemOverrides(base, armorTypeName, textureGetter, assets);
        }

        @Override
        public List<BakedQuad> getQuads(@Nullable BlockState state, @Nullable Direction direction, RandomSource random) {
            return this.base.getQuads(state, direction, random);
        }

        @Override
        public boolean useAmbientOcclusion() {
            return this.base.useAmbientOcclusion();
        }

        @Override
        public boolean isGui3d() {
            return this.base.isGui3d();
        }

        @Override
        public boolean usesBlockLight() {
            return this.base.usesBlockLight();
        }

        @Override
        public boolean isCustomRenderer() {
            return this.base.isCustomRenderer();
        }

        @Override
        public TextureAtlasSprite getParticleIcon() {
            return this.base.getParticleIcon();
        }

        @Override
        public ItemTransforms getTransforms() {
            return this.base.getTransforms();
        }

        @Override
        public ItemOverrides getOverrides() {
            return this.overrides;
        }
    }

    /**
     * 纹饰感知的 override 链：我方材质 → 自己算的「原模型 + 纹饰层」；其余 → 原版 override 链。
     *
     * <p>继承 {@code ItemOverrides} 只为覆写 {@code resolve}（它是 public 非 final），
     * {@code super()} 给出空表，我们根本不走父类的 BakedOverride 机制。</p>
     */
    private static final class TrimItemOverrides extends ItemOverrides {

        private final BakedModel base;
        private final String armorTypeName;
        private final Function<Material, TextureAtlasSprite> textureGetter;
        private final ItemOverrides delegate;
        private final Set<String> assets;
        private final Map<TextureAtlasSprite, BakedModel> cache = new IdentityHashMap<>();

        TrimItemOverrides(BakedModel base, String armorTypeName,
                Function<Material, TextureAtlasSprite> textureGetter, Set<String> assets) {
            super();
            this.base = base;
            this.armorTypeName = armorTypeName;
            this.textureGetter = textureGetter;
            this.delegate = base.getOverrides();
            this.assets = assets;
        }

        @Override
        public BakedModel resolve(BakedModel model, ItemStack stack, @Nullable ClientLevel level,
                @Nullable LivingEntity entity, int seed) {
            ArmorTrim trim = stack.get(net.minecraft.core.component.DataComponents.TRIM);
            if (trim != null) {
                String asset = trim.material().value().assetName();
                if (this.assets.contains(asset)) {
                    TextureAtlasSprite sprite = trimSprite(asset);
                    if (sprite != null) {
                        return this.cache.computeIfAbsent(sprite, s -> layered(this.base, s));
                    }
                }
            }
            return this.delegate.resolve(this.base, stack, level, entity, seed);
        }

        /** 取 {@code minecraft:trims/items/<部位>_trim_<材质>} 精灵；不在图集里（会退化成 missingno）返回 null */
        private @Nullable TextureAtlasSprite trimSprite(String asset) {
            ResourceLocation name = ResourceLocation.withDefaultNamespace(
                    "trims/items/" + this.armorTypeName + "_trim_" + asset);
            try {
                TextureAtlasSprite sprite = this.textureGetter.apply(new Material(InventoryMenu.BLOCK_ATLAS, name));
                if (sprite == null || MissingTextureAtlasSprite.getLocation().equals(sprite.contents().name())) {
                    return null;
                }
                return sprite;
            } catch (RuntimeException e) {
                bettergold.LOGGER.warn("[bettergold] 取盔甲纹饰精灵失败 {}: {}", name, e.toString());
                return null;
            }
        }
    }

    /**
     * 「原模型 + 纹饰层」：把原模型的四边形原样复制一遍、只把精灵换成纹饰精灵即可 ——
     * {@code item/generated} 与 {@code trims/items/<type>_trim} 都是 16×16、UV 归一化后含义相同
     * （顶点里的 UV 是 0..1 归一化的，实际像素位置由 {@code BakedQuad#getSprite()} 在图集里的位置决定）。
     */
    private static BakedModel layered(BakedModel base, TextureAtlasSprite trimSprite) {
        List<BakedQuad> source = base.getQuads(null, null, RandomSource.create(42L));
        List<BakedQuad> all = new ArrayList<>(source.size() * 2);
        all.addAll(source);
        for (BakedQuad quad : source) {
            all.add(new BakedQuad(quad.getVertices(), quad.getTintIndex(), quad.getDirection(),
                    trimSprite, quad.isShade()));
        }
        return new LayeredModel(base, all);
    }

    /** 只换四边形清单的模型；粒子图标 / 变换 / 渲染层照抄原模型，override 链刻意清空避免自递归 */
    private static final class LayeredModel implements BakedModel {

        private final BakedModel base;
        private final List<BakedQuad> quads;

        LayeredModel(BakedModel base, List<BakedQuad> quads) {
            this.base = base;
            this.quads = quads;
        }

        @Override
        public List<BakedQuad> getQuads(@Nullable BlockState state, @Nullable Direction direction, RandomSource random) {
            return this.quads;
        }

        @Override
        public boolean useAmbientOcclusion() {
            return this.base.useAmbientOcclusion();
        }

        @Override
        public boolean isGui3d() {
            return this.base.isGui3d();
        }

        @Override
        public boolean usesBlockLight() {
            return this.base.usesBlockLight();
        }

        @Override
        public boolean isCustomRenderer() {
            return this.base.isCustomRenderer();
        }

        @Override
        public TextureAtlasSprite getParticleIcon() {
            return this.base.getParticleIcon();
        }

        @Override
        public ItemTransforms getTransforms() {
            return this.base.getTransforms();
        }

        @Override
        public ItemOverrides getOverrides() {
            return ItemOverrides.EMPTY;
        }
    }

    private ArmorTrimItemModels() {
    }
}
