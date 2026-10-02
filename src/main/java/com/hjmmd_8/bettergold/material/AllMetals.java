package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.registry.AllItems;

import net.minecraft.tags.BlockTags;

/**
 * 新约 1.4 的金属族清单。
 *
 * <p>每一种金属在这里只写一份规格，材料链（锭/粒/原料）、全套建材、五件器具、四件盔甲、
 * 升级锻造模板就全部注册完毕；贴图与模型由 {@code tools/asset-generator} 批量生成。</p>
 *
 * <p>以后再加金属：新建一个 {@link MetalFamily.Spec} 即可，不用碰 AllItems / AllBlocks。</p>
 */
public final class AllMetals {

    /** 烈燃金：挖掘自动熔炼，建材互动给 6 秒燃烧 */
    public static final MetalFamily FLAMEGOLD = MetalFamily.register(
            new MetalFamily.Spec("flamegold", "烈燃金")
                    .autoSmelt()
                    .contactFire()
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.BLAZING_ROD.get()));

    /** 巫毒金：建材互动给 6 秒中毒 I */
    public static final MetalFamily VOODOOGOLD = MetalFamily.register(
            new MetalFamily.Spec("voodoogold", "巫毒金")
                    .contactEffect(() -> net.minecraft.world.effect.MobEffects.POISON)
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.VOODOO_FEATHER.get()));

    /** 结雷金：攻击落雷 + 3×3 额外伤害与颤栗，建材互动给 6 秒虚弱 I */
    public static final MetalFamily THUNDERGOLD = MetalFamily.register(
            new MetalFamily.Spec("thundergold", "结雷金")
                    .thunderStrike()
                    .contactEffect(() -> net.minecraft.world.effect.MobEffects.WEAKNESS)
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.AMETHYST_ENERGY_DUST.get()));

    /**
     * 靛海金（新约 1.5）：主题「窒息 / 挤压 / 深海」。
     *
     * <ul>
     *   <li>材料链：靛蓝海洋之心（1 海洋之心 + 4 青金石块）→ 靛海金原料 → 靛海金锭。</li>
     *   <li>建材：末影人 / 烈焰人 / 雪傀儡 / 炽足兽 踩踏或紧贴时每次 4 点伤害，每 10 tick 最多一次
     *       （规格第七节第 1 条作者默认值）；伤害类型 {@code in_wall}。
     *       另外<b>接触时补满美西螈的空气值</b>（1.5 修正③：氧气/湿润）。</li>
     *   <li>器具：4096 / 24 / 14 / 下界合金级；每次命中叠加 1 级 16 秒沉淀（无上限）；
     *       对上述四种生物<b>双倍伤害</b>（1.5 修正④，{@code LivingDamageEvent.Pre} 里乘 2）。</li>
     *   <li>盔甲：护甲 5·10·8·5、耐久 814·1184·1110·962、附魔 24、韧性 6、击退抗性 15%、
     *       单件即猪灵中立；每件 25% 窒息 / 溺水抗性 + 每件 25% 给攻击者叠沉淀，四件全套完全免疫 + 100%；
     *       另外<b>每件 +25% 游泳速度</b>（1.5 修正⑤：{@code WATER_MOVEMENT_EFFICIENCY}，四件打满 100%）。</li>
     * </ul>
     */
    public static final MetalFamily INDIGOSEAGOLD = MetalFamily.register(
            new MetalFamily.Spec("indigoseagold", "靛海金")
                    .contactDamage(
                            net.minecraft.world.entity.EntityType.ENDERMAN,
                            net.minecraft.world.entity.EntityType.BLAZE,
                            net.minecraft.world.entity.EntityType.SNOW_GOLEM,
                            net.minecraft.world.entity.EntityType.STRIDER)
                    .contactRestoreAxolotlAir()
                    .doubleDamageOnTargets()
                    .sedimentOnAttack()
                    .suffocationResist()
                    .sedimentReflect()
                    .swimSpeed(MetalFamily.SWIM_SPEED_PER_PIECE)
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.INDIGO_OCEAN_HEART.get()));

    /**
     * 幻惑金（新约 1.5）：主题「幻惑 / 安抚 / 错觉」。
     *
     * <ul>
     *   <li>材料链：紫颂樱花枝（1 紫颂花 + 8 樱花树苗）→ 幻惑金原料 → 幻惑金锭。</li>
     *   <li>建材：踩踏 / 紧贴 / 破坏 / 右键互动时给<b>玩家与友善生物</b>
     *       （{@code !(entity instanceof Enemy)}）1 级 120 tick 生命恢复（规格第七节第 4、9 条）。</li>
     *   <li>器具：4096 / 24 / 14 / 下界合金级；命中 16% 概率施加 1 秒安抚（目标失去 AI）。</li>
     *   <li>盔甲：同靛海金的一套数值；每件 4% 几率对攻击者施加 1 秒安抚，四件全套 16%
     *       （规格第二节 2.2 的算术自洽解读：4% × 4 件 = 16%）。</li>
     * </ul>
     */
    public static final MetalFamily ILLUSIONGOLD = MetalFamily.register(
            new MetalFamily.Spec("illusiongold", "幻惑金")
                    .contactBenefit(() -> net.minecraft.world.effect.MobEffects.REGENERATION,
                            MetalFamily.CONTACT_EFFECT_TICKS, 0)
                    .sootheOnAttack(0.16F)
                    .sootheReflect(0.04F)
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.CHORUS_CHERRY_BRANCH.get()));

    /**
     * 万坚金（新约 1.4：从 {@code AllItems} / {@code AllBlocks} 的硬编码，以及当时还各自独立的
     * 工具材料 / 盔甲材质数值，一起迁移到金属族）。
     *
     * <p>注册出来的 id 与迁移前逐字相同（{@code sturdygold_ingot}、{@code raw_sturdygold}、
     * {@code sturdygold_sword}、{@code sturdygold_bricks_stairs}、{@code sturdygold_upgrade_template} …），
     * 升级模板的语言键也天然就是 {@code item.bettergold.smithing_template.sturdygold_upgrade.*}，
     * 所以数据文件 / 标签 / 语言 / 战利品表都不用改。</p>
     *
     * <p>放在三套新金属之后注册，是为了不打乱它们的注册顺序（创造页分区按 id 判定，与顺序无关）。</p>
     */
    public static final MetalFamily STURDYGOLD = registerSturdygold();

    /**
     * 万坚金的规格：逐项照抄迁移前的实现，一个数都不改。
     *
     * <ul>
     *   <li>工具材料 ← 旧万坚金数值（迁移前）：耐久 6144 / 速度 10.0F / 攻击加成 4.5F / 附魔 30 /
     *       下界合金级挖掘（{@code INCORRECT_FOR_NETHERITE_TOOL}）；修复材料由家族统一用万坚金锭</li>
     *   <li>盔甲材质 ← 旧万坚金数值（迁移前）：附魔 30 / 韧性 6.0F / 击退抗性 0.15F /
     *       护甲 靴 5、腿 8、胸 10、头 5；单件即让猪灵中立（{@link MetalFamily.MetalArmorItem}）</li>
     *   <li>盔甲耐久 ← {@code AllItems}：头盔 1221 / 胸甲 1776 / 护腿 1665 / 靴子 1443</li>
     *   <li>建材强度 ← {@code AllBlocks}：块 / 砖 / 柱 55.0F-1500.0F；栏杆 / 门 / 活板门 / 灯笼 / 链 8.0F-12.0F</li>
     *   <li>核心材料 = 金钱贝（原料配方里的主材料，创造页"金属"分区排在万坚金最前面）</li>
     *   <li>1.5 修正⑥：盔甲新增「每 {@value MetalFamily#ABSORPTION_INTERVAL_TICKS} tick 给 1 颗伤害吸收黄心」
     *       （{@value MetalFamily#ABSORPTION_PER_GRANT} 点），上限 = {@value MetalFamily#ABSORPTION_CAP_PER_PIECE}
     *       点 × 穿戴件数 —— 单件 4 点、四件 16 点。</li>
     * </ul>
     */
    private static MetalFamily registerSturdygold() {
        MetalFamily.Spec spec = new MetalFamily.Spec("sturdygold", "万坚金")
                .coreItem(() -> AllItems.GOLDEN_COWRIE.get())
                .absorptionPerInterval(MetalFamily.ABSORPTION_INTERVAL_TICKS);
        spec.fireResistant = true;
        spec.durability = 6144;
        spec.miningSpeed = 10.0F;
        spec.attackDamageBonus = 4.5F;
        spec.enchantmentValue = 30;
        spec.incorrectForDrops = BlockTags.INCORRECT_FOR_NETHERITE_TOOL;
        spec.armorDefense = new int[] { 5, 8, 10, 5 };                  // 靴 / 腿 / 胸 / 头
        spec.armorDurability = new int[] { 1443, 1665, 1776, 1221 };    // 靴 / 腿 / 胸 / 头
        spec.armorEnchantmentValue = 30;
        spec.armorToughness = 6.0F;
        spec.armorKnockbackResistance = 0.15F;
        spec.blockStrength = 55.0F;
        spec.blockResistance = 1500.0F;
        spec.detailStrength = 8.0F;
        spec.detailResistance = 12.0F;
        // 万坚金是「基础套装」：不调用 specialWeaponMetal(...) ⇒ 盾牌不免疫破盾、格挡不反 buff，
        // 改为「佩戴在主/副手后每 16 秒 1 颗吸收黄心、上限 4 点」（规格 12.3）。
        // 盾牌耐久单独一档：万坚金 3072（其余 2048）。
        spec.shieldDurability = 3072;
        return MetalFamily.register(spec);
    }

    /** 触发静态初始化（在 mod 构造器里调用） */
    public static void bootstrap() {
        bettergold.LOGGER.info("已注册金属族 {} 套: {}", MetalFamily.all().size(),
                MetalFamily.all().stream().map(f -> f.id + "(" + f.cnName + ")").toList());
    }

    private AllMetals() {
    }
}
