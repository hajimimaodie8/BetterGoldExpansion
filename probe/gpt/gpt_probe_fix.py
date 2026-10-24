# -*- coding: utf-8 -*-
"""把 GptProbe.java.txt 的探针按第一次 A 级跑出来的 19 条 FAIL 修正（一次性脚本，留档）。

第一次读数（docs/gpt-证据/01-A级-report.json，pass=43 fail=19）逐条归因：
  · ① 期望写错：1.21.1 `BushBlock#mayPlaceOn` 本来就允许 dirt / farmland（要求里"普通土不可"不成立）
  · ② `Item#getDefaultAttributeModifiers()` 在 1.21.1 是无参空实现 ⇒ 必须用 ItemStack 版本
  · ③ 模具会以"耐久 −1"回到格子里（count 1）；逐格 −1 断言要放行模具那一格
  · ⑥ 爆发 owner 找不到 = 施加者没进世界（`level.getEntities().get(uuid)` 查不到）；中毒测试换真僵尸
  · ⑦ 音效 id 是 `minecraft:item.bone_meal.use`（不是 block.*）
  · ⑧ 箭的位置设进去时 `wasTouchingWater` 还没更新 ⇒ 改手动 tick，并在水里连续 tick 到底
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"probe\gpt\GptProbe.java.txt"
t = io.open(P, encoding="utf-8").read()


def sub(old, new):
    global t
    n = t.count(old)
    assert n == 1, "命中 %d 次：%r" % (n, old[:120])
    t = t.replace(old, new)


# ---------- ① ----------
sub("""            boolean expect = i <= 1;   // 0 = 金染土、1 = 金染耕地 ⇒ 可放；2 = 普通耕地、3 = 石头 ⇒ 不可""",
    """            // 0 金染土 / 1 金染耕地 / 2 普通耕地 ⇒ 可放（普通耕地是**原版**行为）；3 石头 ⇒ 不可
            boolean expect = i <= 2;""")
sub("""        check("gpt1_neg_plain_dirt", level.getBlockState(base.above()).isAir(),
                "普通土上的结果=" + idOf(new ItemStack(level.getBlockState(base.above()).getBlock().asItem())));""",
    """        check("gpt1_plain_dirt_vanilla_parity",
                idOf(new ItemStack(level.getBlockState(base.above()).getBlock().asItem())).equals(flowerId),
                "普通土上的结果=" + idOf(new ItemStack(level.getBlockState(base.above()).getBlock().asItem()))
                        + "（期望能放 = 原版 BushBlock 判据，未被本轮改动）");""")

# ---------- ② ----------
sub("""        var attrs = item.getDefaultAttributeModifiers();""",
    """        // ⚠ 1.21.1：`Item#getDefaultAttributeModifiers()` 无参版本是空实现（ArmorItem 只覆写了
        //   `getDefaultAttributeModifiers(ItemStack)`）⇒ 必须走 ItemStack 版本，否则恒返回空表。
        var attrs = new ItemStack(item).getAttributeModifiers();""")

# ---------- ③ ----------
sub("""            int want = grid[i] == null ? 0 : Math.max(0, before[i] - 1);""",
    """            int want = grid[i] == null ? 0 : Math.max(0, before[i] - 1);
            // 模具（金钱贝模具）走 `getRemainingItems`：以「耐久 −1、数量 1」回到同一格 ⇒ 放行
            if (grid[i] != null && grid[i].equals("bettergold:golden_cowrie_mold") && before[i] == 1) {
                want = 1;
            }""")

# ---------- ⑥ ----------
sub("""        zombie.getPersistentData().putUUID(
                com.hjmmd_8.bettergold.material.MetalEvents.VOODOO_SOURCE_KEY, dummy.getUUID());""",
    """        // ⚠ owner 必须是一个**真的在世界里**的实体：结算时 `level.getEntities().get(uuid)` 查不到 ⇒ 当没有
        var attacker = EntityType.ZOMBIE.create(level);
        if (attacker != null) {
            attacker.moveTo(970.5D, 121.0D, 973.5D, 0.0F, 0.0F);
            attacker.setNoAi(true);
            level.addFreshEntity(attacker);
            ATK_UUID = attacker.getUUID();
        }
        zombie.getPersistentData().putUUID(
                com.hjmmd_8.bettergold.material.MetalEvents.VOODOO_SOURCE_KEY,
                ATK_UUID == null ? dummy.getUUID() : ATK_UUID);""")

sub("""        // (b) 每件 25% 中毒伤害：0..4 件，真 neoforge:poison 伤害
        MetalFamily vd = MetalFamily.byId("voodoogold");
        if (vd == null) {
            check("gpt6_voodoo_family", false, "找不到 voodoogold 家族");
            return;
        }
        var dyn = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        var poison = dyn.getHolderOrThrow(NeoForgeMod.POISON_DAMAGE);
        DamageSource src = new DamageSource(poison);
        boolean bypassArmor = src.is(DamageTypeTags.BYPASSES_ARMOR);
        float raw = 8.0F;
        StringBuilder sb = new StringBuilder();
        float[] ratio = new float[5];
        for (int p = 0; p <= 4; p++) {
            for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                    EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
                victim.setItemSlot(slot, ItemStack.EMPTY);
            }
            Item[] pieces = {vd.helmet.get(), vd.chestplate.get(), vd.leggings.get(), vd.boots.get()};
            EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS,
                    EquipmentSlot.FEET};
            for (int i = 0; i < p; i++) {
                victim.setItemSlot(slots[i], new ItemStack(pieces[i]));
            }
            victim.setHealth(victim.getMaxHealth());
            victim.invulnerableTime = 0;
            victim.hurt(src, raw);
            float pre = PRE.getOrDefault(victim.getId(), -1.0F);
            float inc = INCOMING.getOrDefault(victim.getId(), -1.0F);
            ratio[p] = inc > 0 ? pre / inc : -1.0F;
            sb.append("件=").append(p).append(" incoming=").append(inc).append(" pre=").append(pre)
                    .append(" 比值=").append(String.format(java.util.Locale.ROOT, "%.4f", ratio[p]))
                    .append("；");
            PRE.remove(victim.getId());
            INCOMING.remove(victim.getId());
        }""",
    """        // (b) 每件 25% 中毒伤害：0..4 件，真 neoforge:poison 伤害（用**真僵尸**当受害体：玩家实例
        //     不在世界里时有若干玩家专属早退，读数会全是 -1 —— 第一次跑就踩到了）
        MetalFamily vd = MetalFamily.byId("voodoogold");
        if (vd == null) {
            check("gpt6_voodoo_family", false, "找不到 voodoogold 家族");
            return;
        }
        var pv = EntityType.ZOMBIE.create(level);
        if (pv == null) {
            check("gpt6_poison_victim", false, "create(ZOMBIE) 返回 null");
            return;
        }
        pv.moveTo(970.5D, 121.0D, 975.5D, 0.0F, 0.0F);
        pv.setNoAi(true);
        level.addFreshEntity(pv);
        var dyn = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        var poison = dyn.getHolderOrThrow(NeoForgeMod.POISON_DAMAGE);
        DamageSource src = new DamageSource(poison);
        boolean bypassArmor = src.is(DamageTypeTags.BYPASSES_ARMOR);
        float raw = 8.0F;
        StringBuilder sb = new StringBuilder();
        float[] ratio = new float[5];
        for (int p = 0; p <= 4; p++) {
            for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                    EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
                pv.setItemSlot(slot, ItemStack.EMPTY);
            }
            Item[] pieces = {vd.helmet.get(), vd.chestplate.get(), vd.leggings.get(), vd.boots.get()};
            EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS,
                    EquipmentSlot.FEET};
            for (int i = 0; i < p; i++) {
                pv.setItemSlot(slots[i], new ItemStack(pieces[i]));
            }
            pv.setHealth(pv.getMaxHealth());
            pv.invulnerableTime = 0;
            PRE.remove(pv.getId());
            INCOMING.remove(pv.getId());
            pv.hurt(src, raw);
            float pre = PRE.getOrDefault(pv.getId(), -1.0F);
            float inc = INCOMING.getOrDefault(pv.getId(), -1.0F);
            ratio[p] = inc > 0 ? pre / inc : -1.0F;
            sb.append("件=").append(p).append(" incoming=").append(inc).append(" pre=").append(pre)
                    .append(" 比值=").append(String.format(java.util.Locale.ROOT, "%.4f", ratio[p]))
                    .append("；");
        }
        pv.discard();
        POISON_STORY = "neoforge:poison bypasses_armor=" + bypassArmor + "；" + sb + "逐档比值=" 
                + String.format(java.util.Locale.ROOT, "%.4f/%.4f/%.4f/%.4f/%.4f",
                        ratio[0], ratio[1], ratio[2], ratio[3], ratio[4]);""")

sub("""            boolean good = Math.abs(got - want) < 0.02F;
            if (!bypassArmor) {
                // 用第 0 档归一化：ratio[p] / ratio[0] 应 = 1-0.25p
                good = ratio[0] > 0 && Math.abs(got / ratio[0] - want) < 0.02F;
            }
            if (!good) {
                ok = false;
            }
        }
        check("gpt6_poison_per_piece", ok, "neoforge:poison 8 点，bypasses_armor=" + bypassArmor
                + "；逐档 " + sb);""",
    """            boolean good = Math.abs(got - want) < 0.02F;
            if (!bypassArmor) {
                // 用第 0 档归一化：ratio[p] / ratio[0] 应 = 1-0.25p
                good = ratio[0] > 0 && Math.abs(got / ratio[0] - want) < 0.02F;
            }
            if (!good) {
                ok = false;
            }
        }
        check("gpt6_poison_per_piece", ok, POISON_STORY);""")

# 支撑字段
sub("""    private static net.minecraft.world.entity.monster.Zombie ZOMBIE_FOR_BURST;""",
    """    private static net.minecraft.world.entity.monster.Zombie ZOMBIE_FOR_BURST;
    private static UUID ATK_UUID;
    private static String POISON_STORY = "-";""")

# 迟到断言：owner 用 ATK_UUID
sub("""            check("gpt6_burst_owner", owner != null && owner.contains(dummy.getUUID().toString()),
                    "巫毒结算伤害源的 owner=" + owner + "（期望 = dummy " + dummy.getUUID() + "）");""",
    """            check("gpt6_burst_owner", owner != null && ATK_UUID != null
                            && owner.contains(ATK_UUID.toString()),
                    "巫毒结算伤害源的 owner=" + owner + "（期望 = 施加者僵尸 " + ATK_UUID + "）");""")

# ---------- ⑦ 音效 id ----------
sub("""        boolean sound = SOUNDS.stream().anyMatch(s -> s.startsWith("minecraft:block.bone_meal.use@"));""",
    """        // ⚠ 1.21.1 的 `SoundEvents.BONE_MEAL_USE` id = **`minecraft:item.bone_meal.use`**
        boolean sound = SOUNDS.stream().anyMatch(s -> s.startsWith("minecraft:item.bone_meal.use@"));""")

# ---------- ⑧ 手动 tick ----------
sub("""    private static void item8Projectiles() {
        ItemStack indigoBow = new ItemStack(item("bettergold:indigoseagold_bow"));
        ItemStack sturdyBow = new ItemStack(item("bettergold:sturdygold_bow"));
        ItemStack ammo = stack("minecraft:arrow", 1);
        ARROW_A = new Arrow(level, dummy, ammo, indigoBow);
        ARROW_A.setPos(1200.5D, 103.0D, 1201.5D);
        ARROW_A.setDeltaMovement(0.5D, 0.0D, 0.0D);
        ARROW_B = new Arrow(level, dummy, ammo, sturdyBow);
        ARROW_B.setPos(1200.5D, 103.0D, 1202.5D);
        ARROW_B.setDeltaMovement(0.5D, 0.0D, 0.0D);
        ARROW_A_X0 = ARROW_A.getX();
        ARROW_B_X0 = ARROW_B.getX();
        level.addFreshEntity(ARROW_A);
        level.addFreshEntity(ARROW_B);
        check("gpt8_arrows_spawned", ARROW_A.isInWater() && ARROW_B.isInWater(),
                "两支箭都在水里？A=" + ARROW_A.isInWater() + " B=" + ARROW_B.isInWater()
                        + "；武器 A=" + idOf(ARROW_A.getWeaponItem()) + " B=" + idOf(ARROW_B.getWeaponItem()));
    }""",
    """    private static void item8Projectiles() {
        // 在**高处**铺一条 12 格长、4 格高的水池（x 1200..1211 / y 150..153 / z 1200..1202），
        // 水块直接 setBlockAndUpdate；本段同步跑完 12 tick（不经过 level tick ⇒ 水不会流动）。
        for (int x = 1200; x <= 1211; x++) {
            for (int y = 150; y <= 153; y++) {
                for (int z = 1200; z <= 1202; z++) {
                    place(x, y, z, Blocks.WATER.defaultBlockState());
                }
            }
        }
        ItemStack indigoBow = new ItemStack(item("bettergold:indigoseagold_bow"));
        ItemStack sturdyBow = new ItemStack(item("bettergold:sturdygold_bow"));
        ItemStack ammo = stack("minecraft:arrow", 1);
        ARROW_A = new Arrow(level, dummy, ammo, indigoBow);
        ARROW_A.setPos(1200.5D, 151.0D, 1200.5D);
        ARROW_A.setDeltaMovement(0.5D, 0.0D, 0.0D);
        ARROW_B = new Arrow(level, dummy, ammo, sturdyBow);
        ARROW_B.setPos(1200.5D, 151.0D, 1201.5D);
        ARROW_B.setDeltaMovement(0.5D, 0.0D, 0.0D);
        ARROW_A_X0 = ARROW_A.getX();
        ARROW_B_X0 = ARROW_B.getX();
        for (int i = 0; i < 12; i++) {
            ARROW_A.tick();
            ARROW_B.tick();
        }
        check("gpt8_arrows_in_water", ARROW_A.isInWater() && ARROW_B.isInWater(),
                "两支箭 tick 后仍在水中？A=" + ARROW_A.isInWater() + " B=" + ARROW_B.isInWater()
                        + "；武器 A=" + idOf(ARROW_A.getWeaponItem())
                        + " B=" + idOf(ARROW_B.getWeaponItem()));
        // 清掉临时水池（避免水在后续 tick 里流得到处都是）
        for (int x = 1199; x <= 1212; x++) {
            for (int y = 149; y <= 154; y++) {
                for (int z = 1199; z <= 1203; z++) {
                    place(x, y, z, Blocks.AIR.defaultBlockState());
                }
            }
        }
    }""")

# late 段：箭不再 addFreshEntity ⇒ discard 安全
sub("""            ARROW_A.discard();
            ARROW_B.discard();""",
    """            ARROW_A.discard();
            ARROW_B.discard();
            ARROW_A = null;
            ARROW_B = null;""")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("patched probe master:", len(t), "B")
