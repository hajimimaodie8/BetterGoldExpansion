package com.hjmmd_8.bettergold.patchouli;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.minecraft.world.level.Level;

import vazkii.patchouli.client.book.BookContentsBuilder;
import vazkii.patchouli.client.book.BookEntry;
import vazkii.patchouli.client.book.BookPage;
import vazkii.patchouli.client.book.ClientBookRegistry;
import vazkii.patchouli.client.book.page.PageCrafting;
import vazkii.patchouli.client.book.page.PageSmelting;
import vazkii.patchouli.client.book.page.abstr.PageDoubleRecipe;

/**
 * 自定义页型 <b>{@code bettergold:double_recipe}</b>：<b>一页</b>里上下各画一条配方，
 * 而且这两条<b>可以是不同 recipe class</b>（作者 P4 的硬要求：第 1 屏右页 = 上「混沌金粒（烧制）」
 * + 下「混沌金锭（合成）」）。
 *
 * <h2>为什么要自己写页型（取证结论，不是偷懒）</h2>
 * <p>读 {@code run/mods/Patchouli-1.21.1-93-NEOFORGE.jar} 的字节码（无 sources，`javap -p -c`）：</p>
 * <ul>
 *   <li>{@code PageDoubleRecipe<T>} 的字段就是 {@code recipeId} / {@code recipe2Id} / {@code linkRecipe} /
 *       {@code linkRecipe2} / {@code title} + 两个 transient 的 {@code recipe1} / {@code recipe2}；</li>
 *   <li>{@code PageDoubleRecipe#render} 已经天然是「上 / 下」两格：recipe1 画在
 *       {@code (getX(), getY())}，recipe2 画在 {@code (getX(), getY() + getRecipeHeight() - 10)}；</li>
 *   <li>限制在<b>子类</b>：{@code PageCrafting} 走 {@code PageDoubleRecipeRegistry<Recipe<?>>}
 *       （构造器把 {@code RecipeType.CRAFTING} 写死）、{@code PageSmelting} 走
 *       {@code PageSimpleProcessingRecipe<SmeltingRecipe>}（同样写死类型），
 *       {@code PageDoubleRecipeRegistry#loadRecipe} 里那句
 *       {@code holder.value().getType() == recipeType} 就是「一个页型只收一种 recipe class」的根，
 *       ⇒ 同页放 smelting + crafting 在既有页型上<b>不可能</b>，只能新写一个页型。</li>
 * </ul>
 *
 * <h2>这个版本的 Patchouli 没有 Codec / StreamCodec（⚠ 别照抄新版教程）</h2>
 * <p>取证：页面的反序列化入口是 {@code ClientBookRegistry$LexiconPageAdapter}（GSON 的
 * {@code JsonDeserializer<BookPage>}）：读 json 的 {@code type} 字符串 → 没有冒号就补
 * {@code patchouli:} 前缀 → 在 {@code ClientBookRegistry.INSTANCE.pageTypes} 这张
 * {@code Map<ResourceLocation, Class<? extends BookPage>>} 里查类 → 用
 * {@code SerializationUtil.RAW_GSON.fromJson(json, clazz)} 反射填字段（{@code recipe} → {@code recipeId}
 * 的改名靠 {@code @SerializedName}，我们 <b>继承</b> 那两个字段就等于继承了这个映射）→
 * 最后把原始 json 塞进 {@code BookPage#sourceObject}。</p>
 * <p>所以：<b>没有 Codec、没有 StreamCodec、也没有网络同步</b> —— 整本书的内容都在
 * <b>客户端</b>（{@code assets/.../patchouli_books/...}，见生成器的文件头注释），服务端根本不参与
 * 页面反序列化。「页型要过网络同步」这个担心在这个版本不成立。</p>
 * <p>注册方式因此只有一条：直接往那张 <b>public</b> 的 {@code pageTypes} 表里 {@code put}
 * （{@code PatchouliAPI.IPatchouliAPI} 里<b>没有</b> {@code registerPageType}，
 * {@code ClientBookRegistry#addPageTypes} 是 private 且只增不清）⇒ 在客户端 setup 里 put 一次即可，
 * 与 Patchouli 自己 {@code init()} 的先后顺序无关。</p>
 *
 * <h2>隔离（口径 B：没装 Patchouli ⇒ 手册整格不存在）</h2>
 * <p>本文件是<b>第二个</b>允许出现 {@code vazkii.patchouli} 的文件（白名单见
 * {@code validate_metal_data.py} 的 {@code [bgbook-isolation-single-file]}）。规则与
 * {@link PatchouliCompat} 一样：<b>对 Patchouli 类型的触碰只许在方法体内、且经过
 * {@link HandbookModule#isLoaded()} 早退</b>；本类被加载本身是安全的（JVM 惰性解析），
 * 真正会把对方的类拖进来的是 {@code register()} 里那一行 —— 它前面有早退。</p>
 * <p>⚠ 嵌套类 {@link DoubleRecipePage} 在<b>类声明</b>上就 {@code extends PageDoubleRecipe}
 * （类加载即解析），所以它<b>只许</b>被 {@code register()} 的守卫<b>之后</b>那一行
 * {@code DoubleRecipePage.class} 触碰。全仓对这个类名的引用仅此一处，关卡
 * {@code [bg19-page-type-guard]} 守着。</p>
 */
public final class HandbookPageTypes {

    /** 页型的 path（id = {@code bettergold:double_recipe}；注册命名空间恒 bettergold，红线） */
    public static final String PAGE_PATH = "double_recipe";

    /** 页型完整 id */
    public static final ResourceLocation DOUBLE_RECIPE =
            ResourceLocation.fromNamespaceAndPath(com.hjmmd_8.bettergold.bettergold.MODID, PAGE_PATH);

    private HandbookPageTypes() {
    }

    /**
     * 把 {@code bettergold:double_recipe} 登记进 Patchouli 的页型表。
     *
     * <p>调用点：{@code bettergoldClient#onClientSetup}（客户端类，服务端不会加载本类）。</p>
     */
    public static void register() {
        if (!HandbookModule.isLoaded()) {
            // 没装 Patchouli ⇒ 手册物品都不存在，页型当然也不注册（口径 B）。
            com.hjmmd_8.bettergold.bettergold.LOGGER.info(
                    "[bg-book] Patchouli not loaded -> page type {} is NOT registered", DOUBLE_RECIPE);
            return;
        }
        // ↓ 守卫之后的第一次 Patchouli 类型触碰（这一行才会解析对方的类）
        ClientBookRegistry.INSTANCE.pageTypes.put(DOUBLE_RECIPE, DoubleRecipePage.class);
        com.hjmmd_8.bettergold.bettergold.LOGGER.info(
                "[bg-book] page type {} registered -> {} (pageTypes={})",
                DOUBLE_RECIPE, DoubleRecipePage.class.getName(),
                ClientBookRegistry.INSTANCE.pageTypes.size());
    }

    // ==================================================================================
    // 页面本体
    // ==================================================================================

    /**
     * 上下各一条配方、两条可以是不同 recipe class 的页。
     *
     * <p>几何：直接沿用 {@code PageDoubleRecipe#render} 的「上 / 下」两格（不重写 render），
     * 只把 {@code getRecipeHeight()} 取成 {@code 78}（= {@code PageCrafting} 那个值）⇒
     * 上格在 {@code (9, 4)}、下格在 {@code (9, 72)}（下格标题在 62 行），两条都落在 156 高的页面内。</p>
     */
    public static final class DoubleRecipePage extends PageDoubleRecipe<Recipe<?>> {

        /** 上格（= json 的 {@code recipe}）已解析出的配方；可空 */
        public Recipe<?> topRecipe() {
            return this.recipe1;
        }

        /** 下格（= json 的 {@code recipe2}）已解析出的配方；可空 */
        public Recipe<?> bottomRecipe() {
            return this.recipe2;
        }

        /** 上格在 json 里写的配方 id（A 级探针读它；字段 {@code recipeId} 是包私有的，读不到） */
        public ResourceLocation topRecipeId() {
            return idFromSource("recipe");
        }

        /** 下格在 json 里写的配方 id */
        public ResourceLocation bottomRecipeId() {
            return idFromSource("recipe2");
        }

        private ResourceLocation idFromSource(String key) {
            // sourceObject 由 LexiconPageAdapter 在反序列化后塞进来（public 字段），一定是原始 json
            if (this.sourceObject == null || !this.sourceObject.has(key)) {
                return null;
            }
            var e = this.sourceObject.get(key);
            return e.isJsonPrimitive() ? ResourceLocation.tryParse(e.getAsString()) : null;
        }

        /**
         * 按 id 取配方，<b>不按 RecipeType 过滤</b>（这正是本页型存在的理由）。
         *
         * <p>照 {@code PageDoubleRecipeRegistry#loadRecipe} 的口径逐条对齐：
         * 先按本 id 找，找不到再用 {@code crafttweaker:<同 path>} 兜底；
         * 找到且 {@code linkRecipe} 为真时，把产物登记成「本页相关物品」
         * （Patchouli 用它做条目图标 / 已解锁判定，漏了不报错但图标会少东西）。</p>
         */
        @Override
        protected Recipe<?> loadRecipe(Level level, BookContentsBuilder builder, BookEntry entry,
                                       ResourceLocation id, boolean linkRecipe) {
            if (id == null || level == null) {
                return null;
            }
            Recipe<?> found = null;
            var holder = level.getRecipeManager().byKey(id);
            if (holder.isPresent()) {
                found = holder.get().value();
            }
            if (found == null) {
                var ct = level.getRecipeManager().byKey(
                        ResourceLocation.fromNamespaceAndPath("crafttweaker", id.getPath()));
                if (ct.isPresent()) {
                    found = ct.get().value();
                }
            }
            if (found == null) {
                com.hjmmd_8.bettergold.bettergold.LOGGER.warn(
                        "[bg-book] recipe {} not found (page type {})", id, DOUBLE_RECIPE);
                return null;
            }
            if (linkRecipe && entry != null) {
                entry.addRelevantStack(builder, found.getResultItem(level.registryAccess()), this.pageNum);
            }
            return found;
        }

        /**
         * 画一格：<b>按 recipe 的实际类</b>分派给原版那两种画法（照搬，不自己重画）。
         *
         * <p>这就是「两条可以是不同 recipe class」的落点：同一页的上下两格各走各的分支。</p>
         */
        @Override
        protected void drawRecipe(GuiGraphics graphics, Recipe<?> recipe, int x, int y,
                                  int mouseX, int mouseY, boolean second) {
            if (recipe == null) {
                return;
            }
            Component title = getTitle(second);
            if (recipe instanceof CraftingRecipe) {
                CraftingDrawer drawer = new CraftingDrawer();
                drawer.adopt(this, title);
                drawer.draw(graphics, recipe, x, y, mouseX, mouseY, second);
            } else if (recipe instanceof SmeltingRecipe) {
                SmeltingDrawer drawer = new SmeltingDrawer();
                drawer.adopt(this, title);
                drawer.draw(graphics, recipe, x, y, mouseX, mouseY, second);
            } else if (this.parent != null) {
                // 兜底：未知配方类只画产物图标（不出空白格、也不抛异常）
                Level level = Minecraft.getInstance().level;
                if (level != null) {
                    this.parent.renderItemStack(graphics, x + 40, y + 10, mouseX, mouseY,
                            recipe.getResultItem(level.registryAccess()));
                }
            }
        }

        /** 与 {@code PageCrafting} 同一个值（78）⇒ 下格正好落在 72 行 */
        @Override
        protected int getRecipeHeight() {
            return 78;
        }

        @Override
        protected ItemStack getRecipeOutput(Level level, Recipe<?> recipe) {
            if (recipe == null || level == null) {
                return ItemStack.EMPTY;
            }
            return recipe.getResultItem(level.registryAccess());
        }

        // ------------------------------------------------------------------------------
        // 两个「借来的画笔」：都是 Patchouli 原版页的子类，只为了能调到 protected 的
        // `drawRecipe`（跨包不许直接调别人的 protected 成员，子类里调自己的就没问题）
        // ------------------------------------------------------------------------------

        /** 借 {@code PageCrafting} 的画法：3×3 网格 + 结果 + 工作台小图标 + 无序配方提示 */
        private static final class CraftingDrawer extends PageCrafting {

            /**
             * 把宿主页的 transient 状态搬过来。
             *
             * <p>⚠ 三个 {@code protected transient}（{@code title1} / {@code title2} / {@code recipe*}）不许
             * 从宿主对象上读（跨包 protected 只许经**本类类型**的引用访问），所以标题由调用方传参。</p>
             */
            void adopt(BookPage host, Component title) {
                this.book = host.book;
                this.parent = host.parent;
                this.mc = host.mc;
                this.fontRenderer = host.fontRenderer;
                this.title1 = title;
                this.title2 = title;
            }

            void draw(GuiGraphics graphics, Recipe<?> recipe, int x, int y,
                      int mouseX, int mouseY, boolean second) {
                drawRecipe(graphics, recipe, x, y, mouseX, mouseY, second);
            }
        }

        /** 借 {@code PageSmelting}（{@code PageSimpleProcessingRecipe}）的画法：单格 → 箭头 → 产物 */
        private static final class SmeltingDrawer extends PageSmelting {

            void adopt(BookPage host, Component title) {
                this.book = host.book;
                this.parent = host.parent;
                this.mc = host.mc;
                this.fontRenderer = host.fontRenderer;
                this.title1 = title;
                this.title2 = title;
            }

            void draw(GuiGraphics graphics, Recipe<?> recipe, int x, int y,
                      int mouseX, int mouseY, boolean second) {
                if (recipe instanceof SmeltingRecipe smelting) {
                    drawRecipe(graphics, smelting, x, y, mouseX, mouseY, second);
                }
            }
        }
    }
}
