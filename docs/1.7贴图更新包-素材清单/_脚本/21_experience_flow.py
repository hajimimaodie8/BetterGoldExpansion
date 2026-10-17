# -*- coding: utf-8 -*-
"""经验回流：向 mod_experience 追加两条规则 + 附录 D 一行（只追加，幂等保护，bytes 写入）。"""
import sys, os
sys.stdout.reconfigure(errors="replace")

EX06 = r"E:\mc\mcmod\mod_experience\ex\06-贴图模型素材.md"
MAIN = r"E:\mc\mcmod\mod_experience\mcmod_experience.md"

RULE = """
### 规则 10 · ★★ 作者的贴图包里**只有数字文件名**时，怎么「认亲」（像素匹配，可复算）

> 现象：作者交回一个更新包，条目全是 `1792201245321.png` 这类时间戳，**没有任何名字**；
> 要求「按像素匹配认出每一张是谁」。本项目 `bg-n10tex`（1.7 贴图更新包，72 张）走通了一套可复算的做法。

| 层 | 做法 | 判据（本轮实测值） |
|---|---|---|
| ① 精确层 | SHA256 全等 | 若是「翻新」，这一层必然 0 命中（本轮 0/72） |
| ② 分桶层 | **先按 PNG 尺寸分桶**再认 | 16×16 / 16×48 / 64×32 三桶 ⇒ 候选立刻砍到 1/3（本轮 56/8/8） |
| ③ 像素层 | 同尺寸下算 **逐像素 RGBA 平均绝对误差 `MAE = mean(abs(A-B))`**（含 alpha 通道） | 真配 **0.1–1.9**；任何错配 **≥ 20**（差 10 倍以上） |
| ④ 指派层 | **类内全局一对一指派**（`scipy.optimize.linear_sum_assignment`，最大化 −MAE） | 天然给出「第二名差距」`ratio = 2nd/MAE`；本轮 1.8×–75× |
| ⑤ 硬校验 | 「MAE ≤ 2」「ratio ≥ 1.5」「**alpha 掩码逐字节相同且不透明像素数相同**」三条同时满足才算「确定」 | 本轮 72/72 确定，0 疑似，0 认不出 |

**五条硬教训（都是本轮踩过/差点踩的）**

| 现象 | 规则 |
|---|---|
| 用「不透明像素平均色」或「alpha IoU」当主判据，在**同族近似配色**上失效（本轮 `flamegold` 与 `sturdygold` 的 Lab 均值只差 0.2–0.4） | **主判据必须是逐像素 MAE**：这两个族靠 MAE 才分开（1.03 vs 2.61）。平均色只配当辅助证据 |
| 以为「翻新」就是重绘，结果 72 张全部 **alpha 掩码 0 变化、不透明像素数完全相同** | 先做「改动解剖」：① alpha 变了没有；② 改了多少像素（本轮每张 2–18）；③ **改动像素的 alpha 是否为 255**。<br>⚠ **改动全落在 `alpha == 0` 区 ⇒ 两图视觉完全相同**（多半只是重新导出/清底）⇒ 不要当成「翻新」报给作者；**落在 alpha=255 ⇒ 才是可见的定点修正**（本轮 840 处 100% 可见，且新的颜色值都取自**同一族自己的调色板**） |
| 「两种样式」这种措辞按字面去凑数量 | **必须落到具体文件**：同一器件可能有两张目标（本轮「链」就有 `block/<族>_chain.png` 方块样式 与 `item/<族>_chain.png` 物品图标样式两组，各自独立、跨类 MAE 差 40–70 倍）。<br>若作者说的种类在包里对不上（本轮「斧/锹/刀」各只有 1 套，他说的「两种样式」只成立在「链」上）⇒ **如实报缺口 + 列「待作者确认」，绝不硬凑、不自己补画** |
| 只按「类内逐张取最大」认亲 | **改用全局指派**：① 保证一对一；② 天然产生 `ratio`（第二名差距）用于分档；③ 可用「**多个类的族顺序是否一致**」做第 4 条交叉验证（本轮 9 个类的族顺序完全相同，其中 7 个类差距 4–75 倍，足以锚定顺序） |
| 只比「是不是我们仓库的」 | 还要跑一次 **原版排除**：本轮 72 张对本项目的 MAE ≤ 1.88，对原版 jar 的最小 MAE 是 3.99–45.1（差 2–40 倍）⇒ 才敢说「确认是我们的」。<br>⚠ 手上没有对应版本的客户端 jar 时，可退用相邻版本（本轮用 1.20.1 `client-extra.jar` 的 2431 张），但**必须在汇报里写明版本**，不能假装是 1.21.1 |

`【像素实测】` bettergold `bg-n10tex`：`docs/1.7贴图更新包-素材清单/认亲表.md`（72 行逐张 MAE/2nd/ratio）、
脚本 `_脚本/03_match.py`…`13_write_md.py`（全部 `py -3` 可复算）。

### 规则 11 · 用「客户端启动探针」验贴图，有三个会直接造成**假红/假绿**的坑

| 坑 | 症状（本轮实测） | 规则 |
|---|---|---|
| 以为所有贴图都会进 `BLOCKS` 图集 | **盔甲穿戴层**（`models/armor/*_layer_1.png`）拿 `mc.getTextureAtlas(TextureAtlas.LOCATION_BLOCKS).apply(id)` 得到的是 **16×16 占位精灵**，逐像素比 **256/256 全不等**（8 张全红，看起来像「贴图没换进去」） | 盔甲层由 `TextureManager` **按路径直接载入**、不参与图集缝合。验它要走**资源层**：`mc.getResourceManager().getResource(...)` 读 PNG → 算 **SHA-256** 与清单对账（本轮 classpath SHA256 72/72 相等）。<br>⚠ 也**别指望标题界面 `TextureManager` 已加载**它 —— 没有玩家/盔甲架渲染就没有加载，`getTexture()` 会返回 null（那是假红，不是缺贴图） |
| 把动画条当成一张图 | **16×48 三帧灯笼**在 `SpriteContents#width()/height()` 读到的是 **16×16**，按「条高 48」断言 ⇒ 8 张全红 | `SpriteContents` 的宽高 = **单帧尺寸**；帧数走 **`getUniqueFrames().count()`**（`{"animation":{"frametime":8}}` 且未写 width/height ⇒ 48/16 = **3 帧**）。两句都要断言，且**顺序**是先帧数、再单帧尺寸 |
| 用 Gradle 的 task 状态判客户端探针成败 | `Runtime.halt(0)`（仓库既有探针退出方式）在 Windows 上让 Gradle 报 `Execution failed for task ':runClient' > ... finished with non-zero exit value -1073740791`（= `0xC0000409`） | 这是**探针退出方式的副作用，不是游戏崩溃**。判读三件套：① 日志里 `... SUMMARY pass=N fail=0`；② `run/crash-reports/` **有无新增**（比对 mtime）；③ `Unable to load model` / `Missing texture` 计数 = 0。<br>**外加一条硬要求**：探针**先写 SUMMARY 再 halt**，否则进程被杀时什么证据都没有 |

`【实测】` bettergold `bg-n10tex`：`docs/1.7贴图更新包-素材清单/_证据/A级读数.txt`
（资源层 72/72、图集逐像素 64/64、灯笼 8/8 = 3 帧、物品模型 413 件 missing 0、方块状态 5959 个 missing 0、
`Unable to load model` 0、`run/saves` 目录清单与 mtime 跑前跑后一致）。
"""

ROW = (
    "| 2026-10-17 | bettergold | **`bg-n10tex`：1.7 贴图更新包（72 张无名字）按像素认亲 + 翻新 + 第五次贴图授权** | "
    "**指针**：① **无名字贴图包的认亲方法**（尺寸分桶 → 逐像素 RGBA MAE → 匈牙利全局一对一 → "
    "alpha 掩码/不透明像素数硬校验；MAE ≤ 2 且 ratio ≥ 1.5 判「确定」）与 **「翻新」的解剖口径**"
    "（alpha 0 变化 + 改动像素 alpha 是否为 255 ⇒ 区分「可见定点修正」与「重新导出」），"
    "以及「两种样式必须落到具体文件、对不上就报缺口不硬凑」 → `ex\\06` **§10.11 规则 10**；"
    "② **客户端启动探针验贴图的三坑**（盔甲层不进 BLOCKS 图集 ⇒ 改走资源层 SHA-256；"
    "`SpriteContents` 宽高 = 单帧尺寸、帧数走 `getUniqueFrames()`；`Runtime.halt(0)` 会让 Gradle 报 "
    "`-1073740791`/`0xC0000409`，判读要看 SUMMARY + crash-reports + `Unable to load model` 计数）"
    " → `ex\\06` **§10.11 规则 11** | "
    "**未写**（只对本项目成立）：72 张逐张改前/改后 SHA256、认亲表、9 类 × 8 族的族顺序证据、"
    "`[bg17tex-*]` 关卡 7 条判据与 9 例扰动矩阵 —— 全部落在 `docs/1.7-贴图更新包翻新.md` 与 "
    "`docs/1.7贴图更新包-素材清单/`。**另记一条协作事实**：本轮开工时工作树有另一会话未提交的改动"
    "（`bg-n10rc` 配方），我全程只碰自己的 72 张贴图；该会话在**我工作期间**自行提交"
    "（HEAD `f9e60eb` → `7680845`）⇒ 多会话并发下**汇报必须写「开工时」与「收尾时」两个工作树状态**，不能只写一个。 |\n"
)


def main():
    for p, payload in ((EX06, RULE), (MAIN, ROW)):
        b = open(p, "rb").read()
        txt = b.decode("utf-8")
        if payload.strip() in txt:
            print("[flow] %s: payload already present, skip" % os.path.basename(p))
            continue
        if not txt.endswith("\n"):
            txt += "\n"
        txt += payload
        with open(p, "wb") as f:
            f.write(txt.encode("utf-8"))
        print("[flow] %s: %d B -> %d B (+%d)"
              % (os.path.basename(p), len(b), os.path.getsize(p),
                 os.path.getsize(p) - len(b)))


if __name__ == "__main__":
    main()
