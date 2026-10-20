# -*- coding: utf-8 -*-
"""收尾回流：给 ex\\03 追加 §3.36 + 给 mcmod_experience.md 附录 D 追加一行（只追加，删除 0 行）。"""
import io
import os
import sys

EXP = r'E:\mc\mcmod\mod_experience'
EX03 = os.path.join(EXP, 'ex', '03-验证与证据.md')
MAIN = os.path.join(EXP, 'mcmod_experience.md')

SEC = '''
### 3.36 worldgen 结构（jigsaw）类任务的六条验证要点（2026-10-20，bettergold `bg-prison` / 「金之牢狱」）

> 背景：本仓第一个 worldgen 结构。素材是**作者存档里的 14 个预制件**（不是 `.nbt` 包），
> 要反解口位 → 自己注 jigsaw → 导出模板 → 写 template_pool / structure / structure_set → 做战利品 → A 级真实生成。
> 现象 → 根因 → 规则 → 依据等级，逐条如下。

**① 「jigsaw 放边界格还是内侧一格」只能由引擎的对齐公式决定，不能凭"看着在洞里"摆。**
现象：按"往件内侧缩一格"摆口，生成时那一口**再也不长东西**、也不报错。
根因：`JigsawPlacement.tryPlacingChildren` 把子件原点算成
`父口世界坐标 + 父口朝向 − 子口局部坐标`（`JigsawPlacement.java:403-426`），再把候选包围盒与"剩余空闲体"做
`Shapes.joinIsNotEmpty(free, Shapes.create(AABB.of(bbox).deflate(0.25)), ONLY_SECOND)`
（`:432`）——**子件只要与父件重叠就被整条跳过**（不是异常，是静默不接）。
规则：jigsaw 一律放在**件自己的边界层、洞口正中、洞底那一格**；验证要按公式把「父口 × 子件 × 4 个旋转」
全跑一遍，并断言"子件包围盒沿 D 恰好落在父件外一层 + 两件不重叠"。
依据：【读源码】`JigsawPlacement` + 本轮 `[bgp-gate]` 181 组 + A 级 34 个成对口 0 落单。

**② 「固定 N 步循环」只能靠"同一个件的两个口同构 + 池 fallback 指向自己"。**
现象：想让"三件连一起必含某一种变体"，于是给入口口/出口口起不同名字 ⇒ 生成里**循环根本不成立**。
根因：`canAttach` 是**单向**匹配（父 `target` == 子 `name`，`JigsawBlock.java`），而子件可被
`Rotation.getShuffled` 任意旋转；只要两个口不同构，"哪个口朝向父件"就随旋转变，多数旋转下**接不上**。
规则：循环件写成**两个口同名同目标**（同构），再让 `cell_x_2/3` 这类池的 `fallback` 指向**自己**
⇒ 深度截断时下一步仍会放（不会留断头）。校验要逐口断言 `name/target/pool` 三项逐字。
依据：【读源码】+ 本轮 `[bgp-cycle]` + A 级（18 件里 9 个不同模板、三步链真的出现）。

**③ 池 `fallback` 不是"失败才用"，而是"候选列表的第二段"；`EmptyPoolElement` 会 `break`。**
根因：`JigsawPlacement.java:350-360`——`depth != maxDepth` 时先放主池、**再把 fallback 拼在后面**；
遇到 `EmptyPoolElement` 直接 `break`（不是 continue）。所以"到临界点换成出入口/终端件"只能靠 fallback，
而且**深度奇偶要对着算**（哪一层的件、它的 `target` 指哪个池，决定末端用谁的 fallback）。
规则：把"链的节奏"写成表（本轮的 15 个池），再让关卡校验**深度上限那件**是不是"房间类"（偶数 `size`）。
依据：【读源码】`:350/:354/:360/:474` + 本轮 A 级 3 个出入口全在末端。

**④ 结构模板 `.nbt` 的两个"不可复现/不可随手改"陷阱。**
现象：同一份件导出两次，SHA256 不同 ⇒ 关卡没法钉哈希；箱子照 1.20.5+ 的组件写法写 ⇒ 开箱为空。
根因：(a) `gzip` 头带 **mtime**；(b) 1.21.1 的箱子块实体**仍然用旧式字符串 `LootTable` 字段**
（原版自带的 1180 个结构模板全都这样，`RandomizableContainer#trySaveLootTable` 也还写这个键）。
规则：导出用 `gzip.compress(raw, 9, mtime=0)`；箱子只写 `{id:"minecraft:chest", LootTable:"<ns>:chests/x"}`；
写完**立刻重新解析逐格比对**（坐标 → id + 属性），别只比方块数。
依据：【实测】本轮 20 个 `.nbt` 二次导出 SHA 相同 + 原版模板实测 3/1180 抽样 + A 级 12/12 箱子带表。

**⑤ 「开箱受幸运影响」的唯一 vanilla 通道是 `bonus_rolls × luck`；`enchanted_count_increase` 对箱子恒无效。**
根因：`LootPool#addRandomItems` 里 `i = rolls + floor(bonusRolls * lootContext.getLuck())`（`LootPool.java:108`），
而 `unpackLootTable(Player)` 会 `withLuck(player.getLuck())`（`RandomizableContainer` 默认方法）；
`EnchantedCountIncreaseFunction` 读的是 `LootContextParams.ATTACKING_ENTITY`，开箱时没有攻击者。
规则：要"幸运提升"就给池 `bonus_rolls > 0`；要"抢夺提升"**必须写代码**；A 级用 `luck 0 vs 3` 各 100 箱
报平均件数（本轮 29.13 → 39.98），并给一条"每箱 ≥5 件"的反空箱断言。
依据：【读源码】`:108` + `RandomizableContainer#unpackLootTable` + A 级两档读数。

**⑥ 关卡在"被扰动到结构都不成形"时不许崩成 exit 2。**
现象：把某个口平移一格（本来就是最该命中的扰动），关卡 `exit 2`、`hit_expected=NO` —— 读起来像"用例坏了"。
根因：所有"按口取件"的地方（`[...][0]`）假设口一定存在；口不在外侧面上时列表为空 ⇒ `IndexError` ⇒ 顶层兜底记成 2。
规则：凡"从集合里取唯一元素"的地方一律 `next(iter(...), None)` + 空时**记一条 NG 并 continue**；
退出码契约里 2 只能留给"前置缺失/脚本自身"，结构坏了是 1。
依据：【实测】本轮 P2 用例首版 exit 2，改完 exit 1 且一次命中 6 条 NG。
'''

LINE = ('| 2026-10-20 | bettergold | **`bg-prison` 执行轮：「金之牢狱」= 本仓第一个 worldgen 结构**'
        '（14 件反解 → 20 个模板（+镜像/丰饶 6 个）/ 42 个 jigsaw / 15 个模板池 / structure+structure_set / '
        '单池战利品 / 新关卡 `[bgp-*]`） | **指针**：① **jigsaw 摆位只能由对齐公式定**（放内侧一格 ⇒ 子件插进父件、'
        '被 `Shapes.joinIsNotEmpty(deflate(0.25))` 静默拒绝）+ **"固定 N 步循环"只能靠"两口同构 + fallback 指向自己"**'
        '（`canAttach` 单向匹配 + 子件随机旋转）+ **池 fallback 是"候选第二段"不是"失败才用"** + **`.nbt` 的 gzip mtime'
        ' 与旧式 `LootTable` 字段** + **箱子受幸运影响只有 `bonus_rolls × luck`** + **扰动到结构不成形时关卡不许崩成 exit 2**'
        ' → `ex\\03` **§3.36**（新增 6 条） | **未写**（只对本项目成立）：20 件逐件尺寸/方块数/SHA256、'
        '15 个池的接线表与权重、6 条自拍口径（`size=6` / `spacing32-16` / 出入口 target / 中·大牢房不循环 / 农田搬了哪些方块 / 镜像轴）、'
        '战利品 27 条与 2 条"算不出来"的处置、八关卡 exit+计数、8 用例扰动矩阵、A 级 18 行读数（宝藏=1 / 出入口=3 / startY=34 / '
        'junction 34·0 / 箱子 12·12 / 幸运 29.13→39.98）、探针源码留档 SHA、交接清单 —— 全在 `docs\\金之牢狱-实现记录.md`、'
        '`docs\\金之牢狱-蓝图\\`（20 PNG）与 `docs\\金之牢狱-实现-证据\\`。**删除 0 行** |\n')


def main():
    b = open(EX03, 'rb').read()
    txt = b.decode('utf-8')
    if '### 3.36' in txt:
        print('ex03 already has 3.36, skip')
    else:
        add = SEC if txt.endswith('\n') else '\n' + SEC
        open(EX03, 'wb').write(b + add.encode('utf-8'))
        print('ex03 appended, bytes %d -> %d' % (len(b), os.path.getsize(EX03)))
    b2 = open(MAIN, 'rb').read()
    t2 = b2.decode('utf-8')
    if 'bg-prison' in t2:
        print('appendix D already has bg-prison, skip')
    else:
        add2 = LINE if t2.endswith('\n') else '\n' + LINE
        open(MAIN, 'wb').write(b2 + add2.encode('utf-8'))
        print('appendix appended, bytes %d -> %d' % (len(b2), os.path.getsize(MAIN)))
    # 自证：删除 0 行（新的行数 = 旧行数 + 追加行数）
    return 0


if __name__ == '__main__':
    sys.exit(main())
