package com.hjmmd_8.bettergold.config;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.config.ModConfigEvent;
import net.neoforged.neoforge.common.ModConfigSpec;

// An example config class. This is not required, but it's a good idea to have one to keep your config organized.
// Demonstrates how to use Neo's config APIs
public class Config {
    private static final ModConfigSpec.Builder BUILDER = new ModConfigSpec.Builder();

    public static final ModConfigSpec.BooleanValue LOG_DIRT_BLOCK = BUILDER
            .comment("Whether to log the dirt block on common setup")
            .define("logDirtBlock", true);

    public static final ModConfigSpec.IntValue MAGIC_NUMBER = BUILDER
            .comment("A magic number")
            .defineInRange("magicNumber", 42, 0, Integer.MAX_VALUE);

    public static final ModConfigSpec.ConfigValue<String> MAGIC_NUMBER_INTRODUCTION = BUILDER
            .comment("What you want the introduction message to be for the magic number")
            .define("magicNumberIntroduction", "The magic number is... ");

    // a list of strings that are treated as resource locations for items
    public static final ModConfigSpec.ConfigValue<List<? extends String>> ITEM_STRINGS = BUILDER
            .comment("A list of items to log on common setup.")
            .defineListAllowEmpty("items", List.of("minecraft:iron_ingot"), () -> "", Config::validateItemName);

    // ==================== 万坚金工具爆金掉落配置 ====================

    /** 掉落过滤模式：whitelist = 仅掉落列表中的物品；blacklist = 掉列表中以外的物品 */
    public static final ModConfigSpec.ConfigValue<String> GOLD_LOOT_MODE = BUILDER
            .comment("万坚金工具攻击爆金掉落过滤模式。",
                    "whitelist: 只掉落列表中的物品（未列出的不落）",
                    "blacklist: 掉落列表中以外的物品（列出的不落）",
                    "默认: blacklist（空列表 = 全部掉落）")
            .define("goldLootMode", "blacklist");

    /** 爆金掉落物品列表（物品注册名，如 minecraft:gold_ingot / bettergold:golden_eggplant） */
    public static final ModConfigSpec.ConfigValue<List<? extends String>> GOLD_LOOT_ITEMS = BUILDER
            .comment("爆金掉落过滤的物品列表（注册名）。",
                    "黑名单模式：这些物品不会掉落；白名单模式：只有这些物品会掉落。",
                    "可填 minecraft: 或 bettergold: 开头的任意金系物品注册名。")
            .defineListAllowEmpty("goldLootItems", List.of(), () -> "", Config::validateItemName);

    // ==================== 巫毒：累积伤害模型（1.5 作者定稿：36% 提取 + 等级） ====================

    /**
     * 巫毒（voodoo）窗口内伤害的<b>提取比例</b>，默认 0.36（= 36%）。
     *
     * <p>巫毒窗口内，目标<b>受到的每一次伤害</b>（玩家、摔落、其它来源……都算）都会按本比例累加为
     * 「窗口内伤害提取值」。取的是护甲 / 抗性 / 吸收减免之后的<b>最终掉血值</b>
     * （{@code LivingDamageEvent.Post#getNewDamage()}），避免被护甲干扰。
     * 巫毒结算自身造成的伤害会被显式排除，不参与提取（防止自反馈）。</p>
     *
     * <p>1.5 变更：旧键 {@code voodooStoreRatio}（默认 0.8）已被本键取代 ——
     * 作者 2026-09-30 拍板新公式「字面运算顺序：先乘除、后加减」，
     * 提取比例从 0.8 改为规格里的 <b>36%</b>。</p>
     */
    public static final ModConfigSpec.DoubleValue VOODOO_EXTRACT_RATIO = BUILDER
            .comment("巫毒（voodoo）窗口内伤害的「提取比例」。",
                    "公式：提取值 += 本次实际掉血值 × 本比例（窗口内每一次受到伤害都累加）。",
                    "实际掉血值 = 护甲 / 抗性 / 吸收减免之后的最终值（LivingDamageEvent.Post 的 newDamage）。",
                    "巫毒结算自身造成的伤害不计入提取（显式排除，避免自反馈）。",
                    "默认 0.36 = 提取窗口内伤害总量的 36%。",
                    "1.5 起取代旧的 voodooStoreRatio（默认 0.8）。")
            .defineInRange("voodooExtractRatio", 0.36D, 0.0D, 100.0D);

    /**
     * 巫毒的<b>每级固定伤害</b>，默认 1.0（= 1 级 1 点、2 级 2 点……）。
     *
     * <p>作者 2026-09-30 拍板的最终公式（字面运算顺序：先乘除、后加减）：
     * {@code 结算伤害 = 提取值 + 本系数 × 效果等级}，其中 {@code 效果等级 = amplifier + 1}。
     * 默认即规格里的 {@code 伤害总量 × 36% + buff 等级}。</p>
     */
    public static final ModConfigSpec.DoubleValue VOODOO_FLAT_PER_LEVEL = BUILDER
            .comment("巫毒的「每级固定伤害」（公式里加在 36% 提取值后面的那一项）。",
                    "公式：结算伤害 = 提取值 + 本系数 × 效果等级，效果等级 = amplifier + 1。",
                    "默认 1.0：1 级 +1、2 级 +2、3 级 +3 …… 即规格里的「×36% + buff 等级」。",
                    "注意（字面公式的必然结果）：窗口内一次伤害都没挨到时，结算仍为 等级 × 本系数 点。",
                    "只在效果「自然到期」时结算一次；提前移除 / 目标死亡 / 实体离开世界 / 读档 都不结算，并清空提取值。")
            .defineInRange("voodooFlatPerLevel", 1.0D, 0.0D, 100.0D);

    // ==================== 结雷金落雷音效机制 ====================

    /**
     * 结雷金落雷的音效机制。
     *
     * <ul>
     *   <li>{@code client_payload}（默认，最可靠）：服务端发一条自定义 payload 告诉客户端「在这里播雷声」，
     *       客户端用与原版逐字相同的 {@code ClientLevel.playLocalSound(...)} 播放
     *       （THUNDER 音量 10000 / IMPACT 音量 2.0，均为 {@code SoundSource.WEATHER}）。
     *       这条路径<b>不依赖</b>「客户端那颗雷实体是否收到、是否 tick 到 life == 2」，
     *       因此客户端收不到实体时也照样出声。</li>
     *   <li>{@code vanilla_local}：与原版逐字一致 —— 服务端只生成雷实体，
     *       音效由客户端那颗雷实体自己在 {@code LightningBolt.tick()} 里用
     *       {@code level.playLocalSound(LIGHTNING_BOLT_THUNDER / LIGHTNING_BOLT_IMPACT, WEATHER)} 播放。</li>
     *   <li>{@code server_broadcast}：服务端再用 {@code ServerLevel.playSound} 广播一次
     *       （走原版 {@code ClientboundSoundPacket}，与原版打雷参数相同）。</li>
     * </ul>
     *
     * <p>注意：客户端最终音量 = {@code clamp(音量 × 设置里该音源的音量, 0, 1)}
     * （{@code SoundEngine.calculateVolume}），所以「设置 → 音乐和声音 → 天气」为 0 时以上三档都听不到，
     * 这和原版打雷一样。</p>
     *
     * <p>{@code client_payload} 档的 payload 是<b>非 optional</b> 注册的：客户端与服务端的模组版本必须一致，
     * 否则连接会被 NeoForge 直接拒绝并给出明确报错（这也是最快的「版本不一致」自证方式）。</p>
     */
    public static final ModConfigSpec.ConfigValue<String> THUNDER_SOUND_MODE = BUILDER
            .comment("结雷金落雷的音效机制。",
                    "client_payload（默认）: 服务端发自定义 payload，客户端用原版同一条 playLocalSound 播放（不依赖客户端雷实体）",
                    "vanilla_local: 服务端只生成雷实体，音效由客户端雷实体自己播放（与原版打雷完全一致）",
                    "server_broadcast: 额外再由服务端 ServerLevel.playSound 广播一次")
            .define("thunderSoundMode", "client_payload");

    // ==================== bg-fix 第 7 条（2026-10-05）：8 族 × 2 = 16 条「触发概率 / 能力间隔」 ====================
    //
    // 作者原话（需求 §3.7）：
    //   「某某金武器工具触发 Buff 概率（然后再次填写概率）／某某金盔甲盾牌触发 buff 的概率（然后在此填写概率）；
    //     万坚金则是：万坚金武器工具触发能力概率（然后在此填写概率）／万坚金盔甲盾牌触发能力间隔
    //     （然后在此填写关于乘法的比例）」
    //
    // 形状 = 8 族 × 2 = 16 条（7 族「特殊金属」各 2 条 + 万坚金 2 条）：
    //   · 非万坚金 · 武器工具：**概率**（0–1），默认 1.0；幻惑金 0.16（它本来就是「16% 概率施加安抚」）
    //   · 非万坚金 · 盔甲盾牌：**每件**概率（0–1），默认 0.25；幻惑金 0.04
    //       有效概率 = min(1, 该族穿戴件数 × 本条)（穿满 4 件默认 = 100% / 16%，与 1.4/1.5 逐位相同）
    //   · 万坚金 · 武器工具：**概率**（0–1），默认 1.0 = 「必定掉落一件金系物品」那条**能力**（爆金）
    //       ⚠ 「礼品金票 6%」（{@code ModEvents.GIFT_TICKET_CHANCE}）是**另一条**，不在本次 16 条里
    //   · 万坚金 · 盔甲盾牌：**乘法系数**（0–100），默认 1.0
    //       间隔 = 基础 × 本条，基础 = {@code MetalFamily.absorptionIntervalTicks}（现行 320）——
    //       基础**不写死进配置**（读族旗标），配置只提供系数
    //
    // ⚠ **唯一真源**：运行期只读这 16 条（见本类的 weaponBuffChance / armorBuffChance / absorptionInterval）；
    //   族里的旧常量（{@code sootheOnAttackChance} / {@code sootheReflectPerPiece} /
    //   {@code MetalEvents.counterChance} 里的 0.25F）**不再参与概率**，关卡
    //   {@code [bgfix-config-single-source]} 守着这一点（配置改成 0 ⇒ 该 buff 永不触发）。
    // ⚠ 键名一律英文 camelCase（照既有 voodooExtractRatio 风格），中文说明走 .comment(...)；
    //   **既有 8 个键（logDirtBlock / magicNumber / magicNumberIntroduction / items / goldLootMode /
    //   goldLootItems / voodooExtractRatio / voodooFlatPerLevel / thunderSoundMode）一个都不改名**
    //   —— 配置键名是存档红线（改名 = 老玩家设置静默丢失）。

    // ==================== bg-fix4 §二：16 条的**声明顺序** ====================
    //
    // ★ **顺序真源 = `CreativeSections.METAL_ORDER`**（那一行注释原文：「金属出场顺序只在这里维护一行」）。
    //   作者 2026-10-08 原话：「关于贵金进度的上下排版还需要重做,需要改成这种从上到下分别是:
    //   烈燃金 / 万坚金 / 树棘金 / 幽咆金 / 靛海金 / 巫毒金 / 结雷金 / 幻惑金。**模组设置也要用这种规律排序**」
    //   ⇒ 本类这 16 条**按那个列表逐族声明**：NeoForge 配置界面与 `bettergold-common.toml` 的条目顺序
    //     = 声明顺序 = 创造页金属顺序（`CreativeSections.METAL_ORDER`）。
    //
    // ⚠ **旧顺序（原文留档，已被 2026-10-08 取代）**：flamegold → voodoogold → thundergold →
    //   indigoseagold → illusiongold → thornsgold → echogold → sturdygold（1.6.0 的原样，未列过顺序，
    //   只是"谁先写的谁在前"）。
    // ⚠ **键名 / 默认值 / 取值范围 / .comment 文案一个字都没改**（配置键名是存档红线，见上）。
    // ⚠ 关卡 `[bgfix4-metal-order-single-source]` 守着"本类 16 键的声明顺序 == METAL_ORDER"
    //    （以及生成器侧 `generate_advancements.py` / `generate_handbook_data.py` 的 METALS 同序）。

    /** 烈燃金 · 武器工具触发高燃的概率（默认 1.0 = 必定，与 1.6.0 行为一致） */
    public static final ModConfigSpec.DoubleValue FLAMEGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("烈燃金【武器工具】触发 Buff（高燃）的概率。", "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("flamegoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 烈燃金 · 盔甲盾牌反制高燃的每件概率（默认 0.25 = 每件 25%，穿满 4 件 100%） */
    public static final ModConfigSpec.DoubleValue FLAMEGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("烈燃金【盔甲盾牌】反制 Buff（高燃）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。",
                    "0 = 永不触发。")
            .defineInRange("flamegoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /**
     * 万坚金 · 武器工具触发**能力**的概率（默认 1.0 = 必定）。
     *
     * <p>「能力」指 1.4 起的那条<b>爆金</b>：万坚金武器工具命中时<b>必定掉落一件金系物品</b>
     * （{@code ModEvents#onLivingIncomingDamage} + {@code rollGoldLoot}，受 {@code goldLootMode} /
     * {@code goldLootItems} 过滤）。默认 1.0 ⇒ 与 1.6.0 行为逐位一致。</p>
     *
     * <p>⚠ 「礼品金票 6%」（{@code ModEvents.GIFT_TICKET_CHANCE}）是**另一条能力**，
     * <b>不在本次 16 条里</b>，本轮未纳入（作者点名即可加第 17 个键）。</p>
     */
    public static final ModConfigSpec.DoubleValue STURDYGOLD_WEAPON_ABILITY_CHANCE = BUILDER
            .comment("万坚金【武器工具】触发能力（爆金：命中必定掉落一件金系物品）的概率。",
                    "0 = 永不触发；1 = 必定触发（默认，与 1.6.0 一致）。",
                    "注：「礼品金票 6%」是另一条能力，不在本键范围内。")
            .defineInRange("sturdygoldWeaponAbilityChance", 1.0D, 0.0D, 1.0D);

    /**
     * 万坚金 · 盔甲盾牌触发**能力**的间隔**乘法系数**（默认 1.0 = 间隔不变）。
     *
     * <p>作者的裁定原话是「间隔（然后在此填写关于乘法的比例）」⇒ 本条是**乘数**，不是 tick 数：
     * {@code 间隔 = 基础 × 本条}，{@code 基础 = MetalFamily.absorptionIntervalTicks}（现行 320 tick = 16 秒）。</p>
     *
     * <p>例：填 2.0 ⇒ 每 640 tick（32 秒）给一份伤害吸收；填 0.5 ⇒ 每 160 tick（8 秒）一份；
     * 填 0 ⇒ 被钳到最小 1 tick（= 每 tick 一份，慎用）。每次给的量（2 点）与上限
     * （4 点 × 穿戴件数 + 持盾 4 点）**不受本键影响**。</p>
     */
    public static final ModConfigSpec.DoubleValue STURDYGOLD_ARMOR_ABILITY_INTERVAL_MULTIPLIER = BUILDER
            .comment("万坚金【盔甲盾牌】触发能力（每 16 秒 1 份伤害吸收）的间隔乘法系数。",
                    "间隔 = 基础(320 tick) × 本条；1.0 = 不变（默认），2.0 = 间隔翻倍，0.5 = 间隔减半。",
                    "0 会被钳到最小 1 tick（每 tick 一份，慎用）。每次给的量与吸收上限不受本键影响。")
            .defineInRange("sturdygoldArmorAbilityIntervalMultiplier", 1.0D, 0.0D, 100.0D);

    /** 树棘金 · 武器工具触发寄生的概率（默认 1.0） */
    public static final ModConfigSpec.DoubleValue THORNSGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("树棘金【武器工具】触发 Buff（寄生）的概率。", "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("thornsgoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 树棘金 · 盔甲盾牌反制寄生的每件概率（默认 0.25） */
    public static final ModConfigSpec.DoubleValue THORNSGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("树棘金【盔甲盾牌】反制 Buff（寄生）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。")
            .defineInRange("thornsgoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /** 幽咆金 · 武器工具触发音咆的概率（默认 1.0） */
    public static final ModConfigSpec.DoubleValue ECHOGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("幽咆金【武器工具】触发 Buff（音咆，内部 id echo_roar）的概率。",
                    "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("echogoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 幽咆金 · 盔甲盾牌反制音咆的每件概率（默认 0.25） */
    public static final ModConfigSpec.DoubleValue ECHOGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("幽咆金【盔甲盾牌】反制 Buff（音咆）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。")
            .defineInRange("echogoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /** 靛海金 · 武器工具触发沉淀的概率（默认 1.0） */
    public static final ModConfigSpec.DoubleValue INDIGOSEAGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("靛海金【武器工具】触发 Buff（沉淀）的概率。", "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("indigoseagoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 靛海金 · 盔甲盾牌反制沉淀的每件概率（默认 0.25） */
    public static final ModConfigSpec.DoubleValue INDIGOSEAGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("靛海金【盔甲盾牌】反制 Buff（沉淀）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。")
            .defineInRange("indigoseagoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /** 巫毒金 · 武器工具触发巫毒的概率（默认 1.0） */
    public static final ModConfigSpec.DoubleValue VOODOOGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("巫毒金【武器工具】触发 Buff（巫毒）的概率。", "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("voodoogoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 巫毒金 · 盔甲盾牌反制巫毒的每件概率（默认 0.25） */
    public static final ModConfigSpec.DoubleValue VOODOOGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("巫毒金【盔甲盾牌】反制 Buff（巫毒）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。")
            .defineInRange("voodoogoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /** 结雷金 · 武器工具触发落雷/颤栗的概率（默认 1.0） */
    public static final ModConfigSpec.DoubleValue THUNDERGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("结雷金【武器工具】触发能力（落雷 + 3×3 伤害 + 颤栗）的概率。",
                    "0 = 永不触发；1 = 必定触发（默认）。")
            .defineInRange("thundergoldWeaponBuffChance", 1.0D, 0.0D, 1.0D);

    /** 结雷金 · 盔甲盾牌反制颤栗的每件概率（默认 0.25） */
    public static final ModConfigSpec.DoubleValue THUNDERGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("结雷金【盔甲盾牌】反制 Buff（颤栗）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.25 ⇒ 1 件 25%、4 件 100%。")
            .defineInRange("thundergoldArmorBuffChance", 0.25D, 0.0D, 1.0D);

    /** 幻惑金 · 武器工具施加安抚的概率（默认 0.16 = 16%，与 1.5/1.6 现状逐位相同） */
    public static final ModConfigSpec.DoubleValue ILLUSIONGOLD_WEAPON_BUFF_CHANCE = BUILDER
            .comment("幻惑金【武器工具】触发 Buff（安抚）的概率。", "默认 0.16 = 16%。0 = 永不触发。")
            .defineInRange("illusiongoldWeaponBuffChance", 0.16D, 0.0D, 1.0D);

    /** 幻惑金 · 盔甲盾牌反制安抚的每件概率（默认 0.04 = 每件 4%，穿满 4 件 16%） */
    public static final ModConfigSpec.DoubleValue ILLUSIONGOLD_ARMOR_BUFF_CHANCE = BUILDER
            .comment("幻惑金【盔甲盾牌】反制 Buff（安抚）的【每件】概率。",
                    "有效概率 = min(1, 穿戴件数 × 本条)；默认 0.04 ⇒ 1 件 4%、4 件 16%。")
            .defineInRange("illusiongoldArmorBuffChance", 0.04D, 0.0D, 1.0D);

    /**
     * 「武器工具触发概率」的**唯一读取入口**（bg-fix 第 7 条）。
     *
     * @param familyId 金属族 id（= {@code MetalFamily.id}；8 族之一）
     * @return 0–1；配置读不出来时回落到该族的出厂默认值
     * @throws IllegalArgumentException 未登记的族 id —— <b>故意抛</b>：新增一族若忘了补配置键，
     *         要在运行期当场炸出来，而不是静默拿一个合法值继续跑（§4 第 21 条 / §2.6）
     */
    public static float weaponBuffChance(String familyId) {
        return switch (familyId) {
            case "flamegold" -> read(FLAMEGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "voodoogold" -> read(VOODOOGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "thundergold" -> read(THUNDERGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "indigoseagold" -> read(INDIGOSEAGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "illusiongold" -> read(ILLUSIONGOLD_WEAPON_BUFF_CHANCE, 0.16F);
            case "thornsgold" -> read(THORNSGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "echogold" -> read(ECHOGOLD_WEAPON_BUFF_CHANCE, 1.0F);
            case "sturdygold" -> read(STURDYGOLD_WEAPON_ABILITY_CHANCE, 1.0F);
            default -> throw new IllegalArgumentException(
                    "未登记配置项的金属族: " + familyId + "（bg-fix：8 族 × 2 条配置项，新增族必须同时补本类的 case）");
        };
    }

    /**
     * 「盔甲盾牌反制概率（**每件**）」的唯一读取入口（bg-fix 第 7 条）。
     *
     * <p>有效概率 = {@code min(1, 穿戴件数 × 本值)} —— 件数的乘与钳位在调用点
     * （{@code MetalEvents#counterChance}）做，本方法只给"每件"的系数。</p>
     *
     * <p>万坚金返回 <b>0</b>：它没有"盔甲触发概率"这一条（盔甲能力是**间隔**，见
     * {@link #absorptionInterval}），0 = 永不触发，与 {@code MetalEvents} 里的
     * 「该族是否参与反制」判据一致 —— 这是**有意的语义值**，不是兜底。</p>
     */
    public static float armorBuffChance(String familyId) {
        return switch (familyId) {
            case "flamegold" -> read(FLAMEGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "voodoogold" -> read(VOODOOGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "thundergold" -> read(THUNDERGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "indigoseagold" -> read(INDIGOSEAGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "illusiongold" -> read(ILLUSIONGOLD_ARMOR_BUFF_CHANCE, 0.04F);
            case "thornsgold" -> read(THORNSGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "echogold" -> read(ECHOGOLD_ARMOR_BUFF_CHANCE, 0.25F);
            case "sturdygold" -> 0.0F;
            default -> throw new IllegalArgumentException(
                    "未登记配置项的金属族: " + familyId + "（bg-fix：8 族 × 2 条配置项，新增族必须同时补本类的 case）");
        };
    }

    /**
     * 万坚金盔甲/盾牌的能力间隔（tick）= <b>基础 × 配置系数</b>（bg-fix 第 7 条）。
     *
     * @param baseTicks 基础间隔，来自族旗标 {@code MetalFamily.absorptionIntervalTicks}（现行 320）；
     *                  <b>不写死进配置</b> —— 配置只提供乘法系数（作者原话「关于乘法的比例」）
     * @return 钳到 {@code >= 1} 的整数 tick（配置 0 ⇒ 1 tick = 每 tick 一份）
     */
    public static int absorptionInterval(int baseTicks) {
        if (baseTicks <= 0) {
            return 0;   // 该族没有这条机制（调用点也先判过一遍）
        }
        double multiplier = read(STURDYGOLD_ARMOR_ABILITY_INTERVAL_MULTIPLIER, 1.0D);
        long ticks = Math.round(baseTicks * multiplier);
        return (int) Math.max(1L, Math.min(ticks, Integer.MAX_VALUE));
    }

    /**
     * 16 条配置项的**一行读数**（bg-fix 第 7 条；给启动自证与 A 级取证用）。
     *
     * <p>每一项都走与运行期<b>同一个入口</b>（{@link #weaponBuffChance} / {@link #armorBuffChance}），
     * 所以日志里的数字就是真正生效的数字 —— 这比"文件里写了什么"强一档（§3.1 铁律）。</p>
     *
     * <p>格式示例：{@code bgfix16 flamegold[w=1.000 a=0.250] … sturdygoldArmorIntervalMultiplier=1.000}</p>
     */
    public static String describeEffectChances() {
        StringBuilder sb = new StringBuilder("bgfix16");
        for (String id : new String[] {"flamegold", "voodoogold", "thundergold", "indigoseagold",
                "illusiongold", "thornsgold", "echogold", "sturdygold"}) {
            sb.append(' ').append(id)
                    .append("[w=").append(String.format(java.util.Locale.ROOT, "%.3f", weaponBuffChance(id)))
                    .append(" a=").append(String.format(java.util.Locale.ROOT, "%.3f", armorBuffChance(id)))
                    .append(']');
        }
        sb.append(" sturdygoldArmorIntervalMultiplier=")
                .append(String.format(java.util.Locale.ROOT, "%.3f",
                        read(STURDYGOLD_ARMOR_ABILITY_INTERVAL_MULTIPLIER, 1.0D)));
        return sb.toString();
    }

    /** 配置读不出来时的兜底（配置尚未加载 / 被外部改坏）：回落到该族的出厂默认值 */
    private static float read(ModConfigSpec.DoubleValue value, float fallback) {
        try {
            return value.get().floatValue();
        } catch (RuntimeException | LinkageError e) {
            return fallback;
        }
    }

    private static double read(ModConfigSpec.DoubleValue value, double fallback) {
        try {
            return value.get();
        } catch (RuntimeException | LinkageError e) {
            return fallback;
        }
    }

    public static final ModConfigSpec SPEC = BUILDER.build();

    private static boolean validateItemName(final Object obj) {
        return obj instanceof String itemName && BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(itemName));
    }
}
