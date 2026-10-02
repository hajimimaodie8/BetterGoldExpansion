package com.hjmmd_8.bettergold.material;

import com.hjmmd_8.bettergold.bettergold;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.MaceItem;
import net.minecraft.world.item.ShieldItem;
import net.minecraft.world.item.TridentItem;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;

/**
 * 新约 1.5「武器扩展」里五类武器的物品类（<b>六套金属</b>用；金制版本不存在，
 * 见图鉴作者的澄清与 {@link MetalBlanks}）。
 *
 * <p>每一类都继承对应的原版物品，只覆写规格第 12.2 节明确要求的<b>数值落点</b>，
 * 其余行为（猛砸、忠诚回旋、格挡延迟、装填音效……）<b>逐字沿用原版</b>。
 * 模型与贴图在资源侧照搬原版结构，客户端渲染见 {@code client.MetalWeaponItemRenderer}。</p>
 *
 * <h2>为什么三叉戟的投掷伤害走事件而不是子类</h2>
 * <p>{@code ThrownTrident#onHitEntity} 把 {@code float f = 8.0F} 写死在方法体里
 * （neoforge sources {@code net/minecraft/world/entity/projectile/ThrownTrident.java:116}），
 * 既不是字段也没有 getter/setter，也没有任何子类覆写点；要改只能整段重写
 * {@code onHitEntity}（会连带重写忠诚回旋、末影人免伤、击退、附魔后效等一大段原版逻辑，风险远大于收益）。
 * 因此投掷伤害在 {@code MetalEvents#onTridentThrownDamage} 里按
 * 「本次命中源自本模组三叉戟」识别后改写，落点见那张方法的注释。</p>
 */
public final class MetalWeapons {

    /** 重锤：最终伤害倍率 ×1.2（规格 12.2「重锤：最终伤害 ×1.2」） */
    public static final float MACE_FINAL_DAMAGE_MULTIPLIER = 1.2F;

    /** 弓：满蓄力 tick 数（规格 12.2「最大拉弓时间 16」） */
    public static final int BOW_FULL_DRAW_TICKS = 16;

    /** 弓：箭矢基础伤害（规格 12.2「弹射物伤害 4.0」；落点 = {@code AbstractArrow#baseDamage}） */
    public static final float BOW_PROJECTILE_DAMAGE = 4.0F;

    /** 弩：蓄力秒数（规格 12.2「蓄力时间 1 秒」） */
    public static final float CROSSBOW_CHARGE_SECONDS = 1.0F;

    /** 弩：箭矢弹速（规格 12.2「弹射物速度 4.5」） */
    public static final float CROSSBOW_ARROW_POWER = 4.5F;

    /** 弩：烟花火箭弹速（沿用原版 1.6，不随箭矢一起加价，见 12.7 第 9 条的决定） */
    public static final float CROSSBOW_FIREWORK_POWER = 1.6F;

    /**
     * 重锤。除了原版 {@code MaceItem} 自带的下坠猛砸，唯一的额外规则是「最终伤害 ×1.2」，
     * 那条落在 {@code MetalEvents#onMaceFinalDamage}（{@code LivingDamageEvent.Pre}），
     * 与物品本身无关，所以这里只需要保证附魔能力不被 {@code MaceItem} 的硬编码 15 吃掉。
     */
    public static class MetalMaceItem extends MaceItem {

        private final int enchantmentValue;

        public MetalMaceItem(Item.Properties properties, int enchantmentValue) {
            super(properties);
            this.enchantmentValue = enchantmentValue;
        }

        /**
         * {@code MaceItem#getEnchantmentValue()} 返回写死的 <b>15</b>
         * （neoforge sources {@code net/minecraft/world/item/MaceItem.java:62-64}），
         * 不覆写的话金属重锤的附魔能力就被固定成 15，与规格的 24 / 30 冲突。
         */
        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }
    }

    /**
     * 弓：满蓄力 {@value #BOW_FULL_DRAW_TICKS} tick（原版 20），
     * 弹射物基础伤害 {@value #BOW_PROJECTILE_DAMAGE}（原版箭写死 2.0）。
     *
     * <p>{@code getPowerForTime(int)} 是 <b>static</b>，Java 里静态方法只能「隐藏」不能覆写，
     * {@code BowItem#releaseUsing} 里的调用按声明类型 {@code BowItem} 解析，覆写它不会生效；
     * 所以蓄力曲线只能在 {@code releaseUsing} 里自己算一份（与原版同式，只换分母）。</p>
     */
    public static class MetalBowItem extends BowItem {

        private final int enchantmentValue;

        public MetalBowItem(Item.Properties properties, int enchantmentValue) {
            super(properties);
            this.enchantmentValue = enchantmentValue;
        }

        /**
         * {@code ProjectileWeaponItem#getEnchantmentValue()} 把附加值写死成 <b>1</b>
         * （neoforge sources {@code net/minecraft/world/item/ProjectileWeaponItem.java:71-73}，
         * 于是原版弓 / 弩也都是 1）。规格 12.2 的武器表给了两档附魔能力（30 / 24），
         * 与重锤 / 三叉戟同一口径，所以这里同样必须覆写。
         */
        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }

        /** 与原版 {@code BowItem#getPowerForTime} 逐字同式，只把分母 20 换成 {@value #BOW_FULL_DRAW_TICKS} */
        public static float powerForTime(int charge) {
            float f = (float) charge / (float) BOW_FULL_DRAW_TICKS;
            f = (f * f + f * 2.0F) / 3.0F;
            return f > 1.0F ? 1.0F : f;
        }

        @Override
        public void releaseUsing(ItemStack stack, Level level, LivingEntity entityLiving, int timeLeft) {
            if (!(entityLiving instanceof net.minecraft.world.entity.player.Player player)) {
                return;
            }
            ItemStack ammo = player.getProjectile(stack);
            if (ammo.isEmpty()) {
                return;
            }
            int charge = this.getUseDuration(stack, entityLiving) - timeLeft;
            charge = net.neoforged.neoforge.event.EventHooks.onArrowLoose(stack, level, player, charge, true);
            if (charge < 0) {
                return;
            }
            float power = powerForTime(charge);
            if (power < 0.1F) {
                return;
            }
            java.util.List<ItemStack> drawn = draw(stack, ammo, player);
            if (level instanceof net.minecraft.server.level.ServerLevel serverLevel && !drawn.isEmpty()) {
                this.shoot(serverLevel, player, player.getUsedItemHand(), stack, drawn,
                        power * 3.0F, 1.0F, power == 1.0F, null);
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    net.minecraft.sounds.SoundEvents.ARROW_SHOOT, net.minecraft.sounds.SoundSource.PLAYERS,
                    1.0F, 1.0F / (level.getRandom().nextFloat() * 0.4F + 1.2F) + power * 0.5F);
            player.awardStat(net.minecraft.stats.Stats.ITEM_USED.get(this));
        }

        /**
         * 弹射物伤害 4.0 的落点：{@code AbstractArrow#baseDamage}。
         *
         * <p>原版箭的最终伤害是 {@code ceil(速度 × baseDamage)}（{@code AbstractArrow#onHitEntity}
         * 第 355-363 行），其中 {@code baseDamage} 默认 2.0 —— 满蓄力速度 3.0 时约 6.0。
         * 把它写成 {@value #BOW_PROJECTILE_DAMAGE} 之后满蓄力为 {@code 3.0 × 4.0 = 12.0}，
         * 与原版弓<b>同一条计算路径</b>、同样随拉弓力度缩放。</p>
         */
        @Override
        protected Projectile createProjectile(Level level, LivingEntity shooter, ItemStack weapon,
                ItemStack ammo, boolean isCrit) {
            Projectile projectile = super.createProjectile(level, shooter, weapon, ammo, isCrit);
            if (projectile instanceof AbstractArrow arrow) {
                arrow.setBaseDamage(BOW_PROJECTILE_DAMAGE);
            }
            return projectile;
        }
    }

    /**
     * 弩：蓄力 {@value #CROSSBOW_CHARGE_SECONDS} 秒（原版 1.25 秒 = 25 tick → 目标 20 tick），
     * 箭矢弹速 {@value #CROSSBOW_ARROW_POWER}（原版 3.15）。
     *
     * <h2>蓄力 20 tick 的落点（两处，缺一不可）</h2>
     * <ol>
     *   <li><b>{@link #getUseDuration}</b> 返回我们自己的「20 + 3」：原版是
     *       {@code getChargeDuration(stack, entity) + 3}（25 + 3 = 28），
     *       而 {@code CrossbowItem#releaseUsing} 的「装满」判定是
     *       {@code getPowerForTime(i, stack, entity) = i / getChargeDuration(...) >= 1.0F}。
     *       两个 i 都来自同一个 {@code getUseDuration}，所以只要它变小、比值自动仍是 1.0
     *       —— 不需要（也无法）重写那段逻辑。
     *       <b>这里必须走 {@code super.getUseDuration()} 再用我们的时长替换基础秒数</b>：
     *       {@code getChargeDuration} 是 static（不能覆写），但它开头的
     *       {@code EnchantmentHelper.modifyCrossbowChargingTime} 是「快速装填」全部效果的唯一入口，
     *       所以我们照同一条链自己算一遍（基础 1.0 秒，每级快速装填 −0.25 秒），手感原样保留。</li>
     *   <li><b>{@link #use}</b>：原版那一发走 {@code CrossbowItem#getShootingPower}（private static，
     *       箭 3.15 / 烟花 1.6），我们覆写 {@code use} 直接给出目标速度，
     *       并<b>按弹种分别给值</b>（见 12.7 第 9 条：烟花沿用原版 1.6，不跟着箭矢一起加价）。</li>
     * </ol>
     *
     * <p>拉弓动画的 {@code pull} 谓词原版也读 {@code CrossbowItem.getChargeDuration}（25），
     * 于是 20 tick 装满时它只到 0.8、三帧拉弓贴图只走到第二帧。这里在客户端
     * （{@code client.MetalWeaponItemProperties}）给本模组的弩单独登记同一套谓词、
     * 分母换成 {@link #chargeDuration}，动画与蓄力同步。</p>
     */
    public static class MetalCrossbowItem extends CrossbowItem {

        private final int enchantmentValue;

        public MetalCrossbowItem(Item.Properties properties, int enchantmentValue) {
            super(properties);
            this.enchantmentValue = enchantmentValue;
        }

        /**
         * 同 {@link MetalBowItem}：{@code ProjectileWeaponItem#getEnchantmentValue()} 写死 1
         * （{@code ProjectileWeaponItem.java:71-73}），规格 12.2 要的是 30 / 24。
         */
        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }

        /** 本弩的蓄力时长（tick）：基础 {@value #CROSSBOW_CHARGE_SECONDS} 秒，快速装填每级 −0.25 秒 */
        public static int chargeDuration(ItemStack stack, LivingEntity shooter) {
            float f = EnchantmentHelper.modifyCrossbowChargingTime(stack, shooter, CROSSBOW_CHARGE_SECONDS);
            return net.minecraft.util.Mth.floor(f * 20.0F);
        }

        @Override
        public int getUseDuration(ItemStack stack, LivingEntity entity) {
            return chargeDuration(stack, entity) + 3;
        }

        @Override
        public net.minecraft.world.InteractionResultHolder<ItemStack> use(Level level,
                net.minecraft.world.entity.player.Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            net.minecraft.world.item.component.ChargedProjectiles charged =
                    stack.get(net.minecraft.core.component.DataComponents.CHARGED_PROJECTILES);
            if (charged != null && !charged.isEmpty()) {
                float power = charged.contains(net.minecraft.world.item.Items.FIREWORK_ROCKET)
                        ? CROSSBOW_FIREWORK_POWER
                        : CROSSBOW_ARROW_POWER;
                this.performShooting(level, player, hand, stack, power, 1.0F, null);
                return net.minecraft.world.InteractionResultHolder.consume(stack);
            }
            if (!player.getProjectile(stack).isEmpty()) {
                player.startUsingItem(hand);
                return net.minecraft.world.InteractionResultHolder.consume(stack);
            }
            return net.minecraft.world.InteractionResultHolder.fail(stack);
        }
    }

    /**
     * 三叉戟：近战 13 / 1.3（属性表在注册处给），投掷伤害 15（{@code MetalEvents} 里改写），
     * 并覆写被 {@code TridentItem} 写死的附魔能力 <b>1</b>。
     */
    public static class MetalTridentItem extends TridentItem {

        private final int enchantmentValue;

        public MetalTridentItem(Item.Properties properties, int enchantmentValue) {
            super(properties);
            this.enchantmentValue = enchantmentValue;
        }

        /**
         * {@code TridentItem#getEnchantmentValue()} 返回写死的 <b>1</b>
         * （neoforge sources {@code net/minecraft/world/item/TridentItem.java:165-167}），
         * 不覆写的话金属三叉戟会变成「附魔能力 1」，与规格的 24 / 30 冲突。
         */
        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }
    }

    /**
     * 盾牌：耐久 3072 / 2048（属性在注册处给），其余（格挡延迟 5 tick、
     * 最低耐久伤害 3.0、{@code UseAnim.BLOCK}、副手装备位）逐字沿用原版 {@code ShieldItem}。
     */
    public static class MetalShieldItem extends ShieldItem {

        private final int enchantmentValue;
        /** 是否属于「特殊金属」（格挡反给攻击者 buff）；万坚金为 false。 */
        private final boolean special;
        /** 是否免疫原版「破盾」；bg-15w 续工轮起**六种金属都免疫**（作者 2026-10-02 的新口径）。 */
        private final boolean breakImmune;

        public MetalShieldItem(Item.Properties properties, int enchantmentValue, boolean special, boolean breakImmune) {
            super(properties);
            this.enchantmentValue = enchantmentValue;
            this.special = special;
            this.breakImmune = breakImmune;
        }

        @Override
        public int getEnchantmentValue() {
            return this.enchantmentValue;
        }

        /**
         * 特殊金属盾牌<b>格挡时反给攻击者该金属的 buff</b>（规格 12.3）。
         *
         * <p>这一条<b>只给</b>五套特殊金属；万坚金盾不反 buff（它改用吸收黄心）。</p>
         */
        public boolean isSpecialMetal() {
            return this.special;
        }

        /**
         * 是否免疫原版「破盾」（斧头命中时给的 100 tick 冷却，见 {@code MetalEvents#onPlayerTickShieldImmunity}）。
         *
         * <p>⚠ 口径变更（bg-15w 续工轮，作者 2026-10-02）：
         * 旧口径是「免疫只给特殊金属、万坚金按字面<b>不</b>免疫」（规格 12.3 / 12.4）；
         * <b>已被作者推翻</b>——现在是<b>本模组六种金属的盾牌全部免疫</b>。
         * 注意它与 {@link #isSpecialMetal()} 是<b>两个不同的判断</b>：免疫归免疫、反 buff 归反 buff。</p>
         */
        public boolean isBreakImmune() {
            return this.breakImmune;
        }
    }

    /** 五类武器的 id 后缀（与 {@code MetalFamily} 的字段名一一对应） */
    public static final String[] WEAPON_SUFFIXES = { "mace", "bow", "crossbow", "trident", "shield" };

    // ==================== 盾牌「自带」主/副手 +10% 击退抗性（bg-15w 续工轮） ====================

    /**
     * 盾牌给出的击退抗性：{@code +0.10}（= 10%）。
     *
     * <p>与盔甲侧的 {@code armorKnockbackResistance = 0.15F}（{@code ArmorMaterial} 上的字段）
     * <b>是两件事</b>：不合并不改数。</p>
     */
    public static final double SHIELD_KNOCKBACK_RESISTANCE = 0.10D;

    /**
     * 盾牌击退抗性的属性修饰符 id。
     *
     * <p><b>主手与副手共用这一个 id</b>：{@code KNOCKBACK_RESISTANCE} 是
     * {@code RangedAttribute(0,0,1)}，同一件物品在两个槽位各挂一个 id 就会叠加成 +20%；
     * 共用一个 id 则「两只手各拿一个盾」仍然只有 +10%。</p>
     *
     * <p>为什么共用 id 不会抛 {@code IllegalArgumentException}
     * （这是本轮更正的一处旧结论，见 {@code mcmod_experience} §4 第 26 条）：
     * {@code LivingEntity#handleEquipmentChanges}（neoforge sources
     * {@code net/minecraft/world/entity/LivingEntity.java:2628-2633}）应用物品属性时是
     * <b>先 {@code removeModifier(modifier.id())} 再 {@code addTransientModifier(modifier)}</b>，
     * 因此同 id 的两条是「覆盖」而不是「重复添加」——净效果恰好只有一份。
     * 而 {@code ItemAttributeModifiers.Builder} 用的是 {@code ImmutableList.Builder}（同文件
     * {@code ItemAttributeModifiers.java:102-113}），允许同一 (属性, id) 挂到两个槽位组上。</p>
     */
    public static final net.minecraft.resources.ResourceLocation SHIELD_KNOCKBACK_RESISTANCE_ID =
            net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                    com.hjmmd_8.bettergold.bettergold.MODID, "shield_knockback_resistance");

    /**
     * 盾牌物品自带的属性表：{@code MAINHAND} 与 {@code OFFHAND} 各一条、**同一个 id**。
     *
     * <p>这样做（而不是「每 tick 运行时挂一个 transient 修饰符」）有三个实测好处：</p>
     * <ol>
     *   <li><b>物品 tooltip 里看得见</b>（{@code item.modifiers.mainhand} / {@code item.modifiers.offhand}
     *       两行）——作者报「盾牌们没有<b>自带</b>……10% 击退抗性」时，指的就是这件事；
     *       改前实测 <b>{@code lines=1}（只有物品名）</b>，改后 7 行、两行 +10%；</li>
     *   <li>换手 / 丢弃 / 死亡由原版的装备变更逻辑自动移除，不需要每 tick 维护、也没有每 tick 开销；</li>
     *   <li>服务端行为与旧实现等价（实测真实玩家 {@code knockback()} 位移 0.4000 → 0.3600，比值 0.9000）。</li>
     * </ol>
     *
     * <p>⚠ <b>不要</b>指望它在「客户端属性面板 / 客户端属性实例」上可见 —— 那是原版设计，
     * 与本次改动无关：{@code Attributes.KNOCKBACK_RESISTANCE} 在 NeoForge 里注册时
     * <b>没有</b> {@code .setSyncable(true)}（neoforge sources {@code Attributes.java:86-89}；
     * {@code Attribute.syncable} 字段默认 false，见 {@code Attribute.java:26,42-43}），
     * 而装备带来的属性修饰符本身也只在服务端应用
     * （{@code LivingEntity#tick()} 里 {@code detectEquipmentUpdates()} 整块位于
     * {@code if (!this.level().isClientSide)} 内，见 {@code LivingEntity.java:2457,2482}）。
     * 实测阳性对照：手里拿铁剑时客户端 {@code attack_damage={v=1.0,ids=[]}}（服务端是 6.0 /
     * {@code minecraft:base_attack_damage}）—— 原版物品也一样，所以这是<b>原版行为</b>不是缺陷。
     * 真正决定击退的是服务端，那里是生效的。</p>
     */
    public static net.minecraft.world.item.component.ItemAttributeModifiers shieldKnockbackModifiers() {
        net.minecraft.world.entity.ai.attributes.AttributeModifier modifier =
                new net.minecraft.world.entity.ai.attributes.AttributeModifier(
                        SHIELD_KNOCKBACK_RESISTANCE_ID, SHIELD_KNOCKBACK_RESISTANCE,
                        net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE);
        return net.minecraft.world.item.component.ItemAttributeModifiers.builder()
                .add(net.minecraft.world.entity.ai.attributes.Attributes.KNOCKBACK_RESISTANCE, modifier,
                        net.minecraft.world.entity.EquipmentSlotGroup.MAINHAND)
                .add(net.minecraft.world.entity.ai.attributes.Attributes.KNOCKBACK_RESISTANCE, modifier,
                        net.minecraft.world.entity.EquipmentSlotGroup.OFFHAND)
                .build();
    }

    /** 家族武器表用的资源位置（配方 id / 语言键都用它拼） */
    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(bettergold.MODID, path);
    }

    private MetalWeapons() {
    }
}
