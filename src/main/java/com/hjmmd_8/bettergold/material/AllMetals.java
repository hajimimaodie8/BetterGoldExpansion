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
                    .coreItem(() -> MetalSpecialItems.BLAZING_ROD.get()));

    /** 巫毒金：建材互动给 6 秒中毒 I */
    public static final MetalFamily VOODOOGOLD = MetalFamily.register(
            new MetalFamily.Spec("voodoogold", "巫毒金")
                    .contactEffect(() -> net.minecraft.world.effect.MobEffects.POISON)
                    .coreItem(() -> MetalSpecialItems.VOODOO_FEATHER.get()));

    /** 结雷金：攻击落雷 + 3×3 额外伤害与颤栗，建材互动给 6 秒虚弱 I */
    public static final MetalFamily THUNDERGOLD = MetalFamily.register(
            new MetalFamily.Spec("thundergold", "结雷金")
                    .thunderStrike()
                    .contactEffect(() -> net.minecraft.world.effect.MobEffects.WEAKNESS)
                    .coreItem(() -> MetalSpecialItems.AMETHYST_ENERGY_DUST.get()));

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
     * </ul>
     */
    private static MetalFamily registerSturdygold() {
        MetalFamily.Spec spec = new MetalFamily.Spec("sturdygold", "万坚金")
                .coreItem(() -> AllItems.GOLDEN_COWRIE.get());
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
