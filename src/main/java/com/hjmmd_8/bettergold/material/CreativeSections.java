package com.hjmmd_8.bettergold.material;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

/**
 * 创造模式「分区横幅」的排序规则。
 *
 * <p>设计要点（因为以后金属会非常多）：</p>
 * <ul>
 *   <li><b>金属出场顺序只在这里维护一行</b>：{@link #METAL_ORDER}。新金属往后加即可；
 *       没列进来的金属自动排在最后（按注册顺序），所以忘了加也不会丢物品。</li>
 *   <li><b>靠物品 id 后缀判定分区与位次，绝不枚举物品</b>：{@code <金属>_ingot} 落在金属材料区、
 *       {@code <金属>_bricks} 落在金属建材区……加 16 种还是 100 种金属都不用改这里。</li>
 *   <li><b>金属分区的排序键恒为 (金属位次, 类型位次, 物品 id)</b>，金属位次来自 {@link #METAL_ORDER}、
 *       类型位次来自 {@link #BUILDING_SLOT}（{@code <金属>_block} = 0）；
 *       所以「建筑」分区里每种金属的 11 件建材严格连排、以自己的金属块开头。</li>
 *   <li>认不出来的一律返回 null，由调用方丢进该页的「其他」分区 —— 永远不会把物品弄丢。</li>
 * </ul>
 *
 * <p>分区横幅素材：{@code assets/bettergold/textures/gui/creative_sections/*.png}（162×18）。
 * 本模组只有<b>一个</b>创造页，页内共 <b>5 个分区</b>（材料 / 建筑 / 食物 / 装备 / 乐事），
 * 每个分区一条横幅：分区 key（= 横幅名）→ 横幅贴图 / 释词 / 内部排序规则，
 * 全部集中在 {@link CreativePageSections}。</p>
 */
public final class CreativeSections {

    /**
     * 金属在创造页里的出场顺序（分区内按金属顺序排列，横幅上只写"金属"）。
     * 新金属往后加一行；未列出的金属排在最后。
     */
    public static final List<String> METAL_ORDER = List.of(
            "flamegold",      // 烈燃金
            "sturdygold",     // 万坚金
            "indigoseagold",  // 靛海金（1.5，作者指定：在万坚金与巫毒金之间）
            "voodoogold",     // 巫毒金
            "thundergold",    // 结雷金
            "illusiongold");  // 幻惑金（1.5）

    /** 分区种类（枚举顺序 = 显示顺序） */
    public enum Kind {
        /** 材料页：金属（核心材料 / 原料 / 锭 / 粒 / 模板） */
        METAL_MATERIALS,
        /**
         * 建筑分区：金属建材 = <b>金属块</b> + 砖块 / 柱 / 楼梯 / 台阶 / 墙 / 门 / 活板门 / 栏杆 / 链 / 灯笼。
         *
         * <p>金属块（{@code <金属>_block}）<b>不是独立分组</b>，它就是这套建材的
         * {@link CreativeSections#BUILDING_SLOT 类型位次 0}，所以每种金属的 11 件必然以"块"开头、
         * 严格连排，同一金属内不会插进别的金属的方块（作者 1.4 定稿）。</p>
         */
        METAL_BUILDING,
        /** 装备与工具页：金属装备（剑…靴子） */
        METAL_GEAR
    }

    /** 一个物品在金属分区中的位置：分区、金属位次、类型位次 */
    public record Placement(Kind kind, int metalRank, int slot) {

        /**
         * 排序键：先分区，再金属位次，再类型位次（{@link #slot}）。
         * 同一键内由<b>物品 id</b> 兜底（{@code CreativeTabSections#ordered}），
         * 所以完整排序键是 (分区, 金属位次, 类型位次, 物品 id)。
         */
        public long sortKey() {
            return ((long) this.kind.ordinal() << 32) | ((long) this.metalRank << 16) | this.slot;
        }
    }

    /** 金属 id -> 该金属的「核心材料」物品路径（原料配方里那个被替换掉的主材料） */
    private static final Map<String, String> CORE_ITEMS = new HashMap<>(Map.of(
            "sturdygold", "golden_cowrie"));

    /** 材料区区内位次（核心材料 = 0、原料 = 1 单独判定） */
    private static final Map<String, Integer> MATERIAL_SLOT = Map.ofEntries(
            Map.entry("ingot", 2),
            Map.entry("nugget", 3),
            Map.entry("upgrade_template", 4));

    /**
     * 「建材类型后缀 → 类型位次」：<b>唯一</b>一张类型顺序表
     * （块 → 砖块 → 柱 → 楼梯 → 台阶 → 墙 → 门 → 活板门 → 栏杆 → 链 → 灯笼）。
     *
     * <p><b>块是 0 号位，不是分组</b>（作者 1.4 定稿）：{@code <金属>_block} 与这套金属的
     * 砖块…灯笼<b>同属一个金属组</b>，所以整组的排序键是
     * (金属位次, 类型位次) = (0, 0)…(0, 10)，必然连排且以"块"开头。</p>
     *
     * <p>两个分区共用它：金属物品的「金属建材」分区（{@link #classify} 按 {@code <金属>_后缀} 查），
     * 以及非金属的「其他建筑方块」分区（{@link #suiteRank} 按物品 id 的 {@code _后缀} 查，
     * 于是普通金那套也是"块在最前"的同一规则）。
     * 以后增删建材类型只改这一张表，两个分区同时生效。</p>
     *
     * <p>匹配规则是<b>后缀</b>，所以 {@code golden_wheat_block} 这种"名字里带 block 的杂项"
     * 会被误判成套件的块；由 {@link #suiteSortKey} 里"显式杂项表优先"兜住（见 {@link #OTHER_BLOCK_ORDER}）。</p>
     */
    public static final Map<String, Integer> BUILDING_SLOT = Map.ofEntries(
            Map.entry("block", 0),
            Map.entry("bricks", 1),
            Map.entry("pillar", 2),
            Map.entry("bricks_stairs", 3),
            Map.entry("bricks_slab", 4),
            Map.entry("bricks_wall", 5),
            Map.entry("door", 6),
            Map.entry("trapdoor", 7),
            Map.entry("bars", 8),
            Map.entry("chain", 9),
            Map.entry("lantern", 10));

    /**
     * 金属装备区区内位次：剑 + 1.5 的五类武器 + 四件盔甲 + 1.5 之前的斧镐锹锄（排最后）。
     *
     * <p><b>作者定稿顺序（bg-15w <u>§八 8.1</u>，2026-10-02 17:44 按字面重钉）</b>：
     * <b>剑 重锤 三叉戟 弓 弩 盾牌 头盔 胸甲 护腿 靴子</b>，
     * 作者两次给出的清单里都<b>没有</b>斧 / 镐 / 锹 / 锄 ⇒ 按 §8.1 的保守做法把它们
     * <b>排在这 10 件之后（位次 10~13）、仍然留在本表里</b>。</p>
     *
     * <p>⚠ <b>为什么不能把斧镐锹锄从这张表里删掉</b>（§8.1 明确警告）：本表<b>一表两用</b> ——
     * 既定顺序，又通过 {@link #kindOf} 决定「是不是金属装备」（{@code Kind.METAL_GEAR}），
     * 而 {@code CreativeTabSections.GEAR} 那个「金属装备」槽位的谓词就是 {@code isMetalGear}。
     * 删表项 ⇒ 它们连槽位都进不去，会被<b>静默丢出</b>装备分区（不是「排到最后」，是「看不见」）。
     * 作者若要的是「斧镐锹锄移出装备分区」，必须先指定它们去哪个分区，<b>不要只是删表项</b>。</p>
     *
     * <p>⚠ 顺序变更史（留档以便对照，<b>旧顺序均已被作者推翻</b>）：
     * <ol>
     *   <li>1.5 武器轮第一版：{@code sword axe pickaxe shovel hoe helmet chestplate leggings boots mace bow crossbow trident shield}
     *       —— 五类新武器接在盔甲<b>之后</b>，内部顺序 重锤 → 弓 → 弩 → 三叉戟 → 盾牌；</li>
     *   <li>bg-15w 第 7 项（§3.6）：{@code sword axe pickaxe shovel hoe mace trident bow crossbow shield helmet chestplate leggings boots}
     *       —— 五类新武器<b>前移</b>到盔甲之前，内部顺序改为 重锤 → 三叉戟 → 弓 → 弩 → 盾牌；</li>
     *   <li><b>本轮（§8.1）：{@code sword mace trident bow crossbow shield helmet chestplate leggings boots axe pickaxe shovel hoe}</b>
     *       —— 作者说「按字面来」（他的列表里不含斧镐锹锄），故这四件排到最后。</li>
     * </ol>
     * 于是创造页「装备」分区里，每种金属固定是上面那 14 件连续排布。</p>
     *
     * <p>1.5 修正轮：五件「胚底」（{@code golden_<武器>_blank}）<b>不在</b>这张表里 ——
     * 它们是合成材料，落在「材料」分区（见 {@code material.MetalBlanks}）。</p>
     */
    private static final Map<String, Integer> GEAR_SLOT = Map.ofEntries(
            Map.entry("sword", 0),
            Map.entry("mace", 1),
            Map.entry("trident", 2),
            Map.entry("bow", 3),
            Map.entry("crossbow", 4),
            Map.entry("shield", 5),
            Map.entry("helmet", 6),
            Map.entry("chestplate", 7),
            Map.entry("leggings", 8),
            Map.entry("boots", 9),
            Map.entry("axe", 10),
            Map.entry("pickaxe", 11),
            Map.entry("shovel", 12),
            Map.entry("hoe", 13));

    /**
     * 物品是不是「某套建材」的一员：是则返回它的类型位次（{@link #BUILDING_SLOT}），否则返回 {@code -1}。
     *
     * <p>只看物品 id 的<b>类型后缀</b>（{@code gold_door} → {@code _door} → 6），前缀是哪种材料完全不关心，
     * 所以「其他的也一样」：以后任何一套建材（普通金、新金属、联动方那 16 色）都自动按同一套类型顺序排，
     * 这里不需要为某种材料加任何分支。</p>
     *
     * <p>匹配规则：{@code path} 等于后缀，或以 {@code "_" + 后缀} 结尾；多个后缀同时命中时取<b>最长</b>的那个
     * （{@code bricks_stairs} 赢过 {@code bricks}）。带 {@code _} 边界是为了让 {@code gold_trapdoor}
     * 不被 {@code door} 误判。</p>
     *
     * <p>注意 {@code block} 也在这张表里（类型位次 0），所以 {@code golden_wheat_block} 这类
     * 「名字里带 block 的杂项」也会命中；它们的定稿位置由 {@link #OTHER_BLOCK_ORDER} 显式给出，
     * {@link #suiteSortKey} 会优先采用那张表，不会把它们算进套件。</p>
     */
    public static int suiteRank(String path) {
        int rank = -1;
        int longest = -1;
        for (Map.Entry<String, Integer> entry : BUILDING_SLOT.entrySet()) {
            String suffix = entry.getKey();
            if (suffix.length() > longest && (path.equals(suffix) || path.endsWith("_" + suffix))) {
                rank = entry.getValue();
                longest = suffix.length();
            }
        }
        return rank;
    }

    /**
     * 「其他建筑方块」分区里，<b>套件之后那批杂项的区内位次</b>：表本身就是顺序（索引即位次）。
     *
     * <p>作者定稿顺序（写在 {@link CreativeTabSections#BLOCKS} 的兜底段里）：金染土 → 金麦块 →
     * 筐装方块（一整组）→ 易金柜台 → 金雕（苦力怕 → 末影人 → 青蛙）。
     * 以 {@code "_"} 开头的条目按<b>后缀</b>匹配（"筐装方块"是一整组，组内继续用次级排序键
     * = 物品 id 字典序，因此同组多材料的稳定规则与套件段完全一致）；
     * 其余条目按完整物品路径匹配。金雕的先后由本表给出（作者指定了苦力怕 → 末影人 → 青蛙，
     * 这不是 id 字典序能表达的，所以只能落在这一张有序表里）。</p>
     *
     * <p>没命中这张表的杂项一律取「表长」，因此必然排在这些定稿位置<b>之后</b>
     * （彼此仍按物品 id 排）；以后新增杂项方块既不会插队、也不会丢物品。</p>
     *
     * <p><b>这张表优先级高于套件的类型后缀表</b>（{@link #suiteSortKey}）：例如"金麦块"
     * （{@code golden_wheat_block}）名字里带 {@code _block}，若不先查本表就会被当成"套件的块"
     * 排到全部套件前面 —— 作者要的是它在杂项段、就在金染土之后。</p>
     */
    private static final List<String> OTHER_BLOCK_ORDER = List.of(
            "gold_infused_dirt",        // 金染土
            "golden_wheat_block",       // 金麦块
            "_crate",                   // 筐装方块：一整组（组内按物品 id）
            "gold_exchange_counter",    // 易金柜台
            "golden_creeper_figurine",  // 金雕：苦力怕
            "golden_enderman_figurine", // 金雕：末影人
            "golden_toad_figurine");    // 金雕：青蛙

    /**
     * 杂项分区（建筑分区的「其他建筑方块」）里，套件物品用的通用排序。
     *
     * <p>排序键 = （分组/建材类型位次, 物品注册名）。第一条按<b>建材类型位次</b>让整区先排套件，
     * 「块 → 砖块 → 柱 → 楼梯 → 台阶 → 墙 → 门 → 活板门 → 栏杆 → 链 → 灯笼」
     * （与金属建材同一张表，块同样是最前）；
     * 同类型里有多种材料时（例如以后第二套砖块）按 {@code namespace:path} 字典序稳定排列，
     * 与注册/投放顺序无关，重跑结果一致。</p>
     *
     * <p>不属于任何套件的杂项（金染土 / 金麦块 / 筐装物 / 易金柜台 / 金雕……）第一条改取
     * {@link #explicitOtherRank}（+ 一个高位分组标记），所以杂项必然排在全部套件之后，
     * 且杂项彼此的先后由 {@link #OTHER_BLOCK_ORDER} 这张<b>唯一</b>有序表决定（第二条只做稳定兜底）；
     * 该表也<b>优先于</b>套件类型表，避免 {@code golden_wheat_block} 被抢进套件段。</p>
     */
    public static final java.util.Comparator<net.minecraft.world.item.ItemStack> SUITE_ORDER = java.util.Comparator
            .<net.minecraft.world.item.ItemStack>comparingLong(CreativeSections::suiteSortKey)
            .thenComparing(CreativeSections::itemIdOf);

    /** 排序键高位：0 = 套件（按建材类型），1 = 杂项（按 {@link #OTHER_BLOCK_ORDER}），2 = 空格子（永远最后） */
    private static final long OTHER_GROUP = 1L << 32;
    private static final long EMPTY_SORT_KEY = 2L << 32;

    /** 排序主键：套件取建材类型位次；杂项取杂项位次（高位分组保证套件恒在杂项之前）；空格子恒在最后 */
    private static long suiteSortKey(net.minecraft.world.item.ItemStack stack) {
        if (stack.isEmpty()) {
            return EMPTY_SORT_KEY;
        }
        String path = itemPath(stack);
        // 显式列进 OTHER_BLOCK_ORDER 的杂项优先落"杂项组"：否则 golden_wheat_block 这种
        // 名字里带 _block 的杂项会被上面那张通用后缀表当成"套件的块"，插到全部套件最前面。
        int explicitOther = explicitOtherRank(path);
        if (explicitOther >= 0) {
            return OTHER_GROUP | explicitOther;
        }
        int suite = suiteRank(path);
        return suite >= 0 ? suite : (OTHER_GROUP | OTHER_BLOCK_ORDER.size());
    }

    /** 命中 {@link #OTHER_BLOCK_ORDER} 则返回其索引（定稿杂项），否则返回 {@code -1} */
    private static int explicitOtherRank(String path) {
        for (int i = 0; i < OTHER_BLOCK_ORDER.size(); i++) {
            String key = OTHER_BLOCK_ORDER.get(i);
            if (key.startsWith("_") ? path.endsWith(key) : path.equals(key)) {
                return i;
            }
        }
        return -1;
    }

    /**
     * 乐事分区「小刀」子组的顺序：<b>按所属金属在 {@link #allMetalIds()} 里的出场顺序</b>
     * （烈燃金刀 → 万坚金刀 → 巫毒金刀 → 结雷金刀），不是金属小刀的（古董刀 / 下界合金古董刀）
     * 一律排在全部金属小刀之后，同组按物品 id 字典序。
     *
     * <p>次级排序规则与 {@link #SUITE_ORDER} 一致：同"类型"（同金属 / 同为非金属）多材料时按
     * {@code namespace:path} 字典序，稳定可复现。以后加金属小刀只要该金属进了
     * {@link #METAL_ORDER}（或注册了 {@link MetalFamily}）就自动获得位置，不用改这里。</p>
     */
    public static final java.util.Comparator<net.minecraft.world.item.ItemStack> KNIFE_ORDER = java.util.Comparator
            .<net.minecraft.world.item.ItemStack>comparingInt(CreativeSections::knifeRank)
            .thenComparing(CreativeSections::itemIdOf);

    /** 小刀位次：金属小刀 = 该金属在 {@link #allMetalIds()} 里的下标；非金属小刀 = 金属总数（排最后） */
    private static int knifeRank(net.minecraft.world.item.ItemStack stack) {
        if (stack.isEmpty()) {
            return Integer.MAX_VALUE;
        }
        String path = itemPath(stack);
        List<String> metals = allMetalIds();
        for (int i = 0; i < metals.size(); i++) {
            if (path.equals(metals.get(i) + "_knife")) {
                return i;
            }
        }
        return metals.size();
    }

    /**
     * 排序次键：物品注册名（{@code namespace:path}）字典序，保证同一类型内顺序稳定且可复现。
     *
     * <p>它同时是金属分区完整排序键的<b>最后一位</b>：{@link Placement#sortKey()} 相同时按本键兜底
     * （见 {@code CreativeTabSections#ordered}），所以排序键恒为
     * (分区, 金属位次, 类型位次, 物品 id)，与注册 / 投放顺序无关。</p>
     */
    public static String itemIdOf(net.minecraft.world.item.ItemStack stack) {
        return stack.isEmpty() ? ""
                : net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
    }

    /** 物品注册路径（排序键用；{@code <ns>:<path>} 的 path 部分） */
    private static String itemPath(net.minecraft.world.item.ItemStack stack) {
        return net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
    }

    /** 登记某金属的核心材料（由 {@link MetalFamily} 注册时自动调用） */
    public static void registerCoreItem(String metalId, String itemPath) {
        CORE_ITEMS.put(metalId, itemPath);
    }

    /** 金属位次；未列入 {@link #METAL_ORDER} 的排在最后 */
    public static int metalRank(String metalId) {
        int i = METAL_ORDER.indexOf(metalId);
        return i >= 0 ? i : METAL_ORDER.size();
    }

    /** 物品路径属于哪个金属（长 id 优先匹配，避免 gold 之类的前缀误判） */
    public static @Nullable String metalOf(String path) {
        String best = null;
        for (String metal : allMetalIds()) {
            boolean hit = path.equals("raw_" + metal) || path.equals(metal + "_block")
                    || path.startsWith(metal + "_");
            if (hit && (best == null || metal.length() > best.length())) {
                best = metal;
            }
        }
        return best;
    }

    /** 参与排布的全部金属 id：显式顺序 + 已注册但未列出的家族金属 */
    public static List<String> allMetalIds() {
        java.util.LinkedHashSet<String> ids = new java.util.LinkedHashSet<>(METAL_ORDER);
        for (MetalFamily family : MetalFamily.all()) {
            ids.add(family.id);
        }
        return List.copyOf(ids);
    }

    /**
     * 判定一个物品属于哪个金属分区。
     *
     * @param path 物品注册名（如 {@code flamegold_ingot}、{@code raw_sturdygold}）
     * @return 位置信息；不是金属物品（或暂时没有归属，例如乐事小刀归 FD 页）返回 null
     */
    public static @Nullable Placement classify(String path) {
        // 核心材料没有金属前缀（如 blazing_rod），必须先用"核心材料表"反查
        for (String candidate : allMetalIds()) {
            if (path.equals(coreItemOf(candidate))) {
                return new Placement(Kind.METAL_MATERIALS, metalRank(candidate), 0);
            }
        }
        String metal = metalOf(path);
        if (metal == null) {
            return null;
        }
        int rank = metalRank(metal);

        if (path.equals(CORE_ITEMS.get(metal))) {
            return new Placement(Kind.METAL_MATERIALS, rank, 0);
        }
        if (path.equals("raw_" + metal)) {
            return new Placement(Kind.METAL_MATERIALS, rank, 1);
        }
        String suffix = path.startsWith(metal + "_") ? path.substring(metal.length() + 1) : path;

        Integer material = MATERIAL_SLOT.get(suffix);
        if (material != null) {
            return new Placement(Kind.METAL_MATERIALS, rank, material);
        }
        Integer building = BUILDING_SLOT.get(suffix);
        if (building != null) {
            return new Placement(Kind.METAL_BUILDING, rank, building);
        }
        Integer gear = GEAR_SLOT.get(suffix);
        if (gear != null) {
            return new Placement(Kind.METAL_GEAR, rank, gear);
        }
        return null;
    }

    /** 取某金属的核心材料路径；未登记时按需从家族解析并缓存 */
    private static @Nullable String coreItemOf(String metalId) {
        String cached = CORE_ITEMS.get(metalId);
        if (cached != null) {
            return cached;
        }
        MetalFamily family = MetalFamily.byId(metalId);
        if (family == null || family.coreItem == null) {
            return null;
        }
        String path = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(family.coreItem.get()).getPath();
        CORE_ITEMS.put(metalId, path);
        return path;
    }

    /** 每行物品数（原版创造界面的列数） */
    public static final int ITEMS_PER_ROW = 9;

    /**
     * 每个分区<b>首个物品所在行</b>的行号：<b>key = 分区 key</b>（{@link CreativePageSections.Section#key()}，
     * 例如 {@code materials}）。横幅画在它上面那一行（= 记录值 − 1，必定整行空格子）上，
     * 渲染端按此约定取用，并用这个 key 去 {@link CreativePageSections#byKey(String)} 取该分区的横幅与释词。
     *
     * <p>本模组只有<b>一个</b>创造页、页内只有 <b>5 个分区</b>（材料 / 建筑 / 食物 / 装备 / 乐事），
     * 所以这张表恒为 5 条记录（没装农夫乐事时 4 条）—— 分区内部的先后（其他材料→交易金商人相关→金属……）
     * 只是同一个连续列表里的次序，不会再各占一条记录。</p>
     */
    public static final Map<String, Integer> SECTION_ROWS = new java.util.LinkedHashMap<>();

    /** 一个分区：分区 key + 横幅释词 + 该分区<b>连续</b>排好序的物品（中间不插横幅、不插空行） */
    public record Bucket(String key, String label, List<net.minecraft.world.item.ItemStack> items) {
    }

    /**
     * 把整页的分区排成"物品 + 空行分隔"的最终列表，并记录每个分区的<b>首个物品行号</b>。
     *
     * <p>规则与航空学一致：每个分区之后补满当前行，<b>再空一整行</b>给横幅，
     * 因此下一分区必定从新行开始；最后一个分区之后不补（避免尾部空一大片）。
     * 分区<b>内部</b>不再有任何分隔 —— 一个分区就是一个连续列表，横幅只有分区这一级。</p>
     *
     * <p><b>列表开头先补一整行空格子</b>：横幅画在每个分区物品的<b>上面那一整行空格子</b>上
     * （= {@link #SECTION_ROWS} 记录值 − 1），第一个分区上方本来没有空行，
     * 没有这一行它就没地方画（渲染端约定，勿删）。
     * 于是本页第一个分区的记录值恒为 1（0 是它的横幅行），其余分区同理"横幅行 = 记录值 − 1"。</p>
     *
     * <p>本模组只有这一页，所以进入时<b>整表清空</b>再重记（重复调用结果一致，可幂等重算）。</p>
     */
    public static List<net.minecraft.world.item.ItemStack> layout(List<Bucket> buckets) {
        List<net.minecraft.world.item.ItemStack> out = new java.util.ArrayList<>();
        SECTION_ROWS.clear();
        // 页顶的一整行空格子：给第一个分区的横幅留位置
        for (int i = 0; i < ITEMS_PER_ROW; i++) {
            out.add(net.minecraft.world.item.ItemStack.EMPTY);
        }
        for (int b = 0; b < buckets.size(); b++) {
            Bucket bucket = buckets.get(b);
            // 记录"首个物品行"；横幅行 = 这个值 − 1（上一整行必为空，见上面的补行规则）
            SECTION_ROWS.put(bucket.key(), out.size() / ITEMS_PER_ROW);
            out.addAll(bucket.items());
            boolean last = b == buckets.size() - 1;
            if (last) {
                break;
            }
            int used = bucket.items().size() % ITEMS_PER_ROW;
            int pad = (ITEMS_PER_ROW - used) % ITEMS_PER_ROW + ITEMS_PER_ROW;
            for (int i = 0; i < pad; i++) {
                out.add(net.minecraft.world.item.ItemStack.EMPTY);
            }
        }
        return out;
    }

    private CreativeSections() {
    }
}
