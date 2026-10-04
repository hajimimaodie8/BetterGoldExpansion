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
     *       另外<b>每件 +25% 游泳速度</b>（1.5 修正⑤：{@code WATER_MOVEMENT_EFFICIENCY}，四件打满 100%）；
     *       <b>再新增一条</b>「真正的游泳速度」（bg-15w §8.3，作者 2026-10-02 <b>19:42 整节重做</b>的裁定：
     *       {@code NeoForgeMod.SWIM_SPEED} / {@code neoforge:swim_speed}，{@code ADD_VALUE} +0.25，
     *       值 = 1 + 0.25 × 件数、<b>每个部位一个 id</b> {@code swim_speed_water_<部位>}，
     *       与浅水那条一起挂在 {@code MetalFamily.MetalArmorItem#getDefaultAttributeModifiers()} —— 常驻属性，
     *       只在水里那一段被读；<b>17:44 那版往 {@code MOVEMENT_SPEED} 挂条件修饰符的实现已被作者推翻并删除</b>，
     *       见 {@code docs/1.5-规格.md} §17.4 / §17.8）。两条<b>并存、不合并</b>。</li>
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
                    .submergedMiningImmunity()
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
     * 树棘金（1.6 · bg-16）：主题「荆棘 / 仙人掌 / 寄生」。
     *
     * <ul>
     *   <li><b>数值一个字段都不覆盖</b>（§0.1 的省事结论）：4096 / 24 / 14 / 下界合金级与
     *       {@code Spec} 默认值逐项相同，逐件伤害与攻速也由 {@code 1 + 4.5 + 每武器常量} 自动得出。</li>
     *   <li>核心材料：<b>闪耀藤条</b>（掉落物，见 {@code MetalSpecialItems.GLITTERING_VINE}）。</li>
     *   <li>建材：踩踏 / 紧贴 / 破坏 / 右键 ⇒ 对触发者 1 点<b>仙人掌同款</b>伤害（{@code cactus}），
     *       同一实体每 10 tick 最多一次；<b>不会清除掉落物</b>（本轮不写任何 {@code ItemEntity} 摧毁逻辑）。</li>
     *   <li>器具（含五类武器与盾牌）：每次命中叠加 1 级 16 秒<b>寄生</b>（无上限）；
     *       寄生每秒造成「等级」点 {@code cactus} 伤害，且每次结算 36% 概率给施加者回「等级」点血。</li>
     *   <li>盔甲：每件 25% 仙人掌伤害减免 + 每件 25% 几率给攻击者叠寄生，四件全套 = 100% 免疫 + 100% 施加。</li>
     *   <li><b>免疫仙人掌</b>（§3.8 的"新机制"）：该族物品的掉落物形态不被仙人掌摧毁
     *       （{@code EntityInvulnerabilityCheckEvent}）、装备不因仙人掌伤害扣耐久
     *       （{@code ArmorHurtEvent}，两者都是现成 NeoForge 事件 ⇒ <b>不需要 mixin</b>）。</li>
     * </ul>
     */
    public static final MetalFamily THORNSGOLD = MetalFamily.register(
            new MetalFamily.Spec("thornsgold", "树棘金")
                    .contactCactusThorns()
                    .parasiteOnAttack()
                    .cactusResist()
                    .parasiteReflect()
                    .cactusImmune()
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.GLITTERING_VINE.get()));

    /**
     * 幽咆金（1.6 · bg-16）：主题「深暗 / 监守者声波 / 幽咆」。
     *
     * <ul>
     *   <li>数值同样<b>一个字段都不覆盖</b>（吃 {@code Spec} 默认值）。</li>
     *   <li>核心材料：<b>集束回响碎片</b>（3×3 有序：中心幽匿脉络 + 外圈 8 回响碎片）。</li>
     *   <li>建材：四个动作 ⇒ 以该<b>方块中心</b>为心、3×3×3 内全部生物 3 点 {@code sonic_boom} 伤害 +
     *       {@code SONIC_BOOM} 粒子；同一实体每 10 tick 最多一次。</li>
     *   <li>器具（含五类武器与盾牌）：每次命中叠加 1 级 6 秒<b>幽咆</b>；
     *       幽咆每秒以目标为中心（方块坐标 ±1，含目标自己）造成「等级」点 {@code sonic_boom} 伤害 + 粒子。</li>
     *   <li>盔甲：每件 25% 声波伤害减免 + 每件 25% 几率给攻击者叠幽咆，四件全套 = 100% + 100%。</li>
     * </ul>
     */
    public static final MetalFamily ECHOGOLD = MetalFamily.register(
            new MetalFamily.Spec("echogold", "幽咆金")
                    .contactSonicBoom()
                    .echoRoarOnAttack()
                    .sonicResist()
                    .echoRoarReflect()
                    .specialWeaponMetal(true, 2048)
                    .coreItem(() -> MetalSpecialItems.BUNDLED_ECHO_SHARD.get()));

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
