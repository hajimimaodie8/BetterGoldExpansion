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

    public static final ModConfigSpec SPEC = BUILDER.build();

    private static boolean validateItemName(final Object obj) {
        return obj instanceof String itemName && BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(itemName));
    }
}
