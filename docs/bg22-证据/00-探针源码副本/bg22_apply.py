# -*- coding: utf-8 -*-
"""bg22 生产代码：树棘金盔甲**不因甜浆果丛伤害掉耐久**。

落点 = `ArmorHurtEvent`（NeoForge 21.1.228 已把原版逐槽 hurtAndBreak 架空，见方法 javadoc）。
只**追加**一个处理器，`onArmorHurtCactusImmunity` 一个字节不动（仙人掌那一半照旧）。

全部走 bytes（AGENTS.md 红线：PowerShell 5.1 会双重编码写坏中文注释）。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
REL = "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
P = os.path.join(ROOT, REL)

ANCHOR = """    /** 接触伤害的「上次结算 tick」在实体持久数据里的键（跟着实体走，不会泄漏、也不怕卸载重载） */
"""

INSERT = '''    /**
     * <b>§35 树棘金装备不因甜浆果丛伤害掉耐久</b>（1.7 {@code bg22}，作者 2026-11-10 原话：
     * 「让树棘金盔甲不会因为甜浆果伤害掉耐久」）。
     *
     * <h2>为什么落点还是 {@code ArmorHurtEvent}，而不是 mixin —— 以源码为准的结论</h2>
     * <p>上一轮的遗留判断是「{@code hurtArmor} 没有事件可拦 ⇒ 必须 mixin」。本轮逐行读了
     * {@code build/moddev/artifacts/neoforge-21.1.228-sources.jar}（= 1.21.1 + NeoForge 21.1.228 补丁源码），
     * <b>那个判断与源码不符</b>：</p>
     * <pre>Player#hurtArmor(DamageSource, float)                       // Player.java:981-983
     *   └─ this.doHurtEquipment(ds, dmg, FEET, LEGS, CHEST, HEAD)
     *        └─ net.neoforged.neoforge.common.CommonHooks.onArmorHurt(...)   // LivingEntity.java:1711
     *           if (true) return; //Neo: Invalidates the loop. ...          // LivingEntity.java:1712
     *        └─ ArmorHurtEvent（可取消 / 逐槽 newDamage）
     *        └─ entry.armorItemStack.hurtAndBreak((int) entry.newDamage, ...) // CommonHooks.java:359</pre>
     * <p>原版那段「逐槽 {@code hurtAndBreak}」（{@code LivingEntity.java:1713-1718}）已被 NeoForge
     * <b>用 {@code if (true) return;} 整个架空</b> ⇒ <b>盔甲耐久的唯一执行点</b>就是
     * {@code CommonHooks#onArmorHurt} 里那一次（{@code CommonHooks.java:348-360}）。
     * 同一个事件已经用在仙人掌免疫上（{@link #onArmorHurtCactusImmunity}，A 级实测过）。</p>
     *
     * <p>为什么<b>不用</b> mixin：能注入的最近位置是 {@code doHurtEquipment}，它的粒度是
     * <b>整次调用</b>（一次伤害带一组槽位）—— 在那里取消/归零会把同一脚上<b>别的族</b>的盔甲
     * 一起免掉，正好违反「只针对树棘金」。逐件判定只有事件里的 {@code armorMap} 能做。</p>
     *
     * <p>{@code newDamage = 0.0F} ⇒ {@code hurtAndBreak((int) 0.0F, ...)}：{@code ItemStack#hurtAndBreak}
     * （{@code ItemStack.java:490-499} → {@code :464-488}）在 {@code p_220158_ <= 0} 时既不扣耐久、
     * 也不触发损毁回调与统计 ⇒ 「0 点耐久伤害」是**真的什么都没发生**（不是"扣了 0 点"的近似）。</p>
     *
     * <h2>范围（两条负向都靠这里守）</h2>
     * <ul>
     *   <li><b>只认 {@code minecraft:sweet_berry_bush}</b>：{@link #isSweetBerryBush} 是唯一判据；
     *       魔法 / 摔落 / 仙人掌等其它来源照旧扣耐久（{@code cactus} 另有它自己那条 handler，
     *       两条并存、互不覆盖）。</li>
     *   <li><b>只认声明了 {@code berryResist} 的族</b>：{@code family != null && family.berryResist}
     *       ⇒ 全仓只有树棘金（{@code AllMetals.THORNSGOLD}）。逐槽判断 ⇒ 同一个玩家身上的
     *       <b>别的族盔甲件</b>（混合套装）仍在同一次事件里按原 {@code newDamage} 扣耐久。</li>
     * </ul>
     */
    @SubscribeEvent
    public static void onArmorHurtBerryImmunity(
            net.neoforged.neoforge.event.entity.living.ArmorHurtEvent event) {
        if (!isSweetBerryBush(event.getDamageSource())) {
            return;                     // 只针对甜浆果丛：其它伤害源一个字节都不碰
        }
        event.getArmorMap().forEach((slot, entry) -> {
            MetalFamily family = MetalFamily.of(entry.armorItemStack);
            if (family != null && family.berryResist) {
                entry.newDamage = 0.0F; // 树棘金件：0 点耐久伤害（hurtAndBreak 空转，见 javadoc）
            }
        });
    }

'''


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


raw = open(P, "rb").read()
text = raw.decode("utf-8")
before = sha(raw)

n = text.count(ANCHOR)
assert n == 1, "锚点命中 %d 次（期望 1）" % n
i = text.index(ANCHOR)
# 幂等：已经装过就报错，避免重复插入
assert "onArmorHurtBerryImmunity" not in text, "处理器已存在（不要重复插入）"

new_text = text[:i] + INSERT + text[i:]
data = new_text.encode("utf-8")
open(P, "wb").write(data)

print("MetalEvents.java  %d B -> %d B" % (len(raw), len(data)))
print("SHA256 before =", before)
print("SHA256 after  =", sha(data))
print("插入位置：anchor 前（原第 %d 行）" % (text[:i].count("\n") + 1))
