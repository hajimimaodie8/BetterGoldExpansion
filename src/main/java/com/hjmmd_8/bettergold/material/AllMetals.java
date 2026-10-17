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
                    // 1.7 轮6（作者原话「烈燃金对金钱妖双倍」）：把本模组自己的实体加进
                    // 「器具双倍伤害」的**唯一判定入口** MetalFamily#isDoubleDamageTarget。
                    // 用 Supplier 是因为实体注册晚于 AllMetals 的静态初始化；靛海金那四个原版
                    // 生物仍走原来的 contactDamageTargets，行为一个字节都没变。
                    .doubleDamageOnDeferredTarget(
                            () -> com.hjmmd_8.bettergold.registry.AllEntities.MONEY_GREMLIN.get())
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
     *   <li>建材（bg-fix §七 第 8 条，作者 2026-10-05）：<b>踩踏 / 贴近</b>时，<b>对玩家发起敌意状态的
     *       中立生物</b>（{@code NeutralMob} 且"当前目标是玩家"或"怒气计时>0 且怒气指向在场玩家"）
     *       <b>瞬间变为被动形态</b>（{@code NeutralMob#stopBeingAngry()}）；作者原话只写了这两个动作
     *       ⇒ <b>破坏 / 右键不含</b>（落在 {@code MetalEvents#scanContact}，不在 {@code applyContact}）。</li>
     *   <li>器具：4096 / 24 / 14 / 下界合金级；命中 16% 概率施加 1 秒安抚（目标失去 AI）。</li>
     *   <li>盔甲：同靛海金的一套数值；每件 4% 几率对攻击者施加 1 秒安抚，四件全套 16%
     *       （规格第二节 2.2 的算术自洽解读：4% × 4 件 = 16%）。</li>
     * </ul>
     */
    public static final MetalFamily ILLUSIONGOLD = MetalFamily.register(
            new MetalFamily.Spec("illusiongold", "幻惑金")
                    .contactBenefit(() -> net.minecraft.world.effect.MobEffects.REGENERATION,
                            MetalFamily.CONTACT_EFFECT_TICKS, 0)
                    .contactPacifyNeutral()
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
     * 混沌金（1.7 · bg-n10 轮1 后半 / 轮2）：主题「混沌 / 区间值」。
     *
     * <p>作者数值（原话照抄）：<b>426 耐久 / 24 附魔能力 / 挖掘等级铁</b>；
     * 「挖掘能力在挖掘成功和反复手持之间不断转换，最低 2 最高 12」；伤害区间见轮3。</p>
     *
     * <ul>
     *   <li><b>形态子集</b>（作者 2026-10-16 裁定 §4.0 ⑪d + 立档 §3 的缺口表）：
     *       11 种建材齐全 + 粒，但 zip 里<b>没有</b>「混沌金原料」与「混沌金升级锻造模板」
     *       ⇒ {@link MetalFamily.Form#RAW} 与 {@link MetalFamily.Form#UPGRADE_TEMPLATE}
     *       <b>不注册</b>（作者禁止自己补画；歧义 ⑱c / ㉑ 未裁 ⇒ 工作值 = 跳过）。</li>
     *   <li><b>区间值</b>：挖掘 {@code 2..12} 落在共用组件 {@link ChaosRange} 上
     *       （规则 / 存储 / 触发点只写那一处）；轮3 把它接进实际挖掘速度与伤害。</li>
     *   <li><b>coreItem = 混沌金币</b>（{@code chaos_coin}）：立档 §2.2 可执行口径第 2 条给的默认
     *       —— 没有 raw 时用金币当"材料链最前面那件"。</li>
     *   <li>盔甲数值走 {@code Spec} 默认（作者说"照抄"，立档 D8：护甲 5·8·10·5 / 韧性 6 /
     *       击退 15% / 附魔 24）；单件即猪灵中立由 {@link MetalFamily.MetalArmorItem} 自动继承。</li>
     * </ul>
     */
    public static final MetalFamily CHAOSGOLD = registerChaosgold();

    /**
     * 崩乱合金（1.7 · bg-n10 轮1 后半）：主题「崩乱 / 失衡」。
     *
     * <p>作者数值（原话照抄）：<b>8192 耐久 / 32 附魔能力 / 挖掘等级下界合金</b>；
     * 挖掘 {@code 8..16}；盔甲 <b>32 附魔能力 / 8 韧性 / 20% 击退抗性</b>；
     * 块属性 = 下界合金块 ×3（立档 D7：{@code 150.0F} 硬度 / {@code 3600.0F} 抗爆）。</p>
     *
     * <ul>
     *   <li><b>形态子集</b>（§4.0 ⑪d 裁定「按照现有的贴图标准来」+「这玩意可算不上是'贵金'」）：
     *       只注册 <b>锭 + 块 + 升级锻造模板</b>（zip 里就只有这三件）——
     *       砖块 / 楼梯 / 台阶 / 墙 / 柱 / 栏杆 / 门 / 活板门 / 链 / 灯笼、以及粒与原料<b>全部不做</b>，
     *       且<b>不自己补画</b>贴图。</li>
     *   <li>器具 / 武器 / 盔甲仍然照常注册（作者的"形态子集"讲的是建材与材料链）⇒
     *       轮7 才接它们的数值与配方；本轮只有骨架 + 形态声明。</li>
     *   <li>区间值只声明挖掘 {@code 8..16}；盔甲的 {@code 4%..10%} 与失衡概率属轮7。</li>
     * </ul>
     */
    public static final MetalFamily CHAOSALLOY = registerChaosalloy();

    /** 混沌金的规格：作者 2026-10-16 给的数逐项照抄（铁级挖掘 / 426 / 24 / 区间 2..12） */
    private static MetalFamily registerChaosgold() {
        MetalFamily.Spec spec = new MetalFamily.Spec("chaosgold", "混沌金")
                .withoutForms(MetalFamily.Form.RAW, MetalFamily.Form.UPGRADE_TEMPLATE)
                .chaosRange(ChaosRange.Channel.MINING, 2, 12)
                // ---- 轮3：14 件套的伤害区间（作者逐件给的数；两端乒乓、当前值即实际值）----
                //     ⚠ 表里的下（上）端就是**注册值与差值**的唯一来源 —— 不许在别处再写一份。
                .chaosRange(MetalFamily.Form.SWORD, ChaosRange.Channel.ATTACK, 4, 8)
                .chaosRange(MetalFamily.Form.MACE, ChaosRange.Channel.ATTACK, 3, 7)
                .chaosRange(MetalFamily.Form.TRIDENT, ChaosRange.Channel.ATTACK, 7, 11)
                .chaosRange(MetalFamily.Form.AXE, ChaosRange.Channel.ATTACK, 7, 10)
                .chaosRange(MetalFamily.Form.PICKAXE, ChaosRange.Channel.ATTACK, 2, 6)
                .chaosRange(MetalFamily.Form.SHOVEL, ChaosRange.Channel.ATTACK, 2.5F, 6.5F)
                .chaosRange(MetalFamily.Form.HOE, ChaosRange.Channel.ATTACK, 1, 5)
                .chaosRange(MetalFamily.Form.KNIFE, ChaosRange.Channel.ATTACK, 1.5F, 5.5F)
                .chaosRange(MetalFamily.Form.BOW, ChaosRange.Channel.ATTACK, 2.0F, 3.5F)
                .chaosRange(MetalFamily.Form.CROSSBOW, ChaosRange.Channel.ATTACK, 3.5F, 4.5F)
                // ---- 攻速（作者给的**最终值**，换算成属性修正的减法只在 gearSpeed 一处做）----
                .attackSpeed(MetalFamily.Form.SWORD, 1.6F)
                .attackSpeed(MetalFamily.Form.MACE, 0.6F)
                .attackSpeed(MetalFamily.Form.TRIDENT, 1.1F)
                .attackSpeed(MetalFamily.Form.AXE, 1.0F)
                .attackSpeed(MetalFamily.Form.PICKAXE, 1.2F)
                .attackSpeed(MetalFamily.Form.SHOVEL, 1.0F)
                .attackSpeed(MetalFamily.Form.HOE, 4.0F)
                .attackSpeed(MetalFamily.Form.KNIFE, 2.0F)
                // ---- 区间之外的固定值 ----
                .tridentThrowDamage(MetalFamily.Form.TRIDENT, 9, 13)   // 投掷 9..13（近战 7..11）
                .maceFinalDamageMultiplier(1.0F)                        // 作者：「最终伤 ×1.0」（不额外乘算）
                .bowFullDraw(20, 0.0F)                                  // 作者：拉弓 20 tick（弹伤由 ATTACK 区间 2.0..3.5 给）
                .crossbowCharge(1.2F)                                   // 作者：1.2 秒 = 24 tick
                .knifeAttributes(1.5F, 2.0F)                            // 乐事刀：伤害区间下端 1.5 / 攻速 2.0
                .coreItem(() -> AllItems.CHAOS_COIN.get());
        spec.durability = 426;
        spec.enchantmentValue = 24;
        spec.incorrectForDrops = BlockTags.INCORRECT_FOR_IRON_TOOL;   // 作者：挖掘等级「铁」
        // ---------- 轮4：混沌金盔甲（作者逐件给的数 + 衰减区间）----------
        // 作者（立档 §2.5 / 父代理派单）：附魔能力 **24**、盔甲韧性 **3**、
        //   「穿戴单件即可猪灵中立」（由 MetalArmorItem 自动继承，零新增代码）；
        //   护甲值 / 耐久：头盔 2/200、胸甲 5/264、护腿 3/240、靴子 2/246。
        // ⚠ 数组顺序是 **靴 / 腿 / 胸 / 头**（与既有 8 族的 armorDefense 同序），别按"头盔在前"填。
        spec.armorDefense = new int[] { 2, 3, 5, 2 };        // 靴 / 腿 / 胸 / 头
        spec.armorDurability = new int[] { 246, 240, 264, 200 };   // 靴 / 腿 / 胸 / 头
        spec.armorEnchantmentValue = 24;
        spec.armorToughness = 3.0F;
        // 击退抗性作者没给 ⇒ 走 `Spec` 默认 15%（立档 D8 的"照抄默认"口径，已在规格里记账）。
        // 减伤：单件 0%..6%（区间值、乒乓、触发点 = 受到伤害），四件之和 = 0%..24%
        //   —— 通道 `Channel.ARMOR` 在轮3 就预留好了，这里是它的**第一个消费者**（接线在 MetalEvents#onDamagePre）。
        // ⚠ `chaosRange(...)` 是 **Spec 的 void 方法**（不是 builder 链）⇒ 必须像上面伤害那批一样**独立成句**。
        spec.chaosRange(MetalFamily.Form.HELMET, ChaosRange.Channel.ARMOR, 0, 6);
        spec.chaosRange(MetalFamily.Form.CHESTPLATE, ChaosRange.Channel.ARMOR, 0, 6);
        spec.chaosRange(MetalFamily.Form.LEGGINGS, ChaosRange.Channel.ARMOR, 0, 6);
        spec.chaosRange(MetalFamily.Form.BOOTS, ChaosRange.Channel.ARMOR, 0, 6);
        // ⚠ 挖掘速度本体只有一个数（Tier 是按族共享的），而作者要的是**区间 2..12** ⇒
        //   注册时取**区间上端**（12.0F）当基准，运行期由 ChaosWiring#onBreakSpeed
        //   补「当前值 − 上端」的差值（按物品栈、每次挖掘读一次）—— 见轮3 §12 的接线说明。
        spec.miningSpeed = 12.0F;
        // 盾牌：作者没点名混沌金盾的"格挡反 buff"⇒ 不调用 specialWeaponMetal（工作值，轮4 可一句话改）。
        // 免疫破盾走 Spec 默认（shieldBreakImmune = true，七套金属一致）。
        return MetalFamily.register(spec);
    }

    /** 崩乱合金的规格：8192 / 32 / 下界合金级 / 区间 8..16 / 盔甲 32·8·20% / 块 3 倍下界合金 */
    private static MetalFamily registerChaosalloy() {
        MetalFamily.Spec spec = new MetalFamily.Spec("chaosalloy", "崩乱合金")
                .forms(MetalFamily.Form.INGOT, MetalFamily.Form.BLOCK, MetalFamily.Form.UPGRADE_TEMPLATE)
                .chaosRange(ChaosRange.Channel.MINING, 8, 16);
        spec.durability = 8192;
        spec.enchantmentValue = 32;
        spec.incorrectForDrops = BlockTags.INCORRECT_FOR_NETHERITE_TOOL;   // 作者：挖掘等级「下界合金」
        spec.miningSpeed = 16.0F;      // 同上：区间 8..16 的上端占位，轮7 接线
        spec.armorEnchantmentValue = 32;
        spec.armorToughness = 8.0F;
        spec.armorKnockbackResistance = 0.20F;
        // 块属性 = 下界合金块 ×3（立档 D7 / 歧义 ⑪a 的 (A)）：下界合金块 50.0F / 1200.0F
        spec.blockStrength = 150.0F;
        spec.blockResistance = 3600.0F;
        // 护甲值 / 耐久 / 细节件强度：作者没给 ⇒ 走 Spec 默认（崩乱合金没有细节件形态，后者用不到）
        return MetalFamily.register(spec);
    }

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
