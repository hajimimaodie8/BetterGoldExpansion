# bg-15w 第四轮续工 · §8.3「真正的游泳速度」改成 `SWIM_SPEED` 的取证与实测证据

> 会话标记 `bg-15w`；需求 = `开工需求\20261002-1330_bg-15w_weapon-final-fixes.md` 的 **§8.3**
> （作者 **2026-10-02 19:42 整节重做**：把 17:44 那版的 `MOVEMENT_SPEED` + 运行期条件修饰符方案
> **换成 `NeoForgeMod.SWIM_SPEED`**，参考 Aether Gravitation 的海皇戒指）。
> 本目录是**长期留档**；结论已同步进 `docs/1.5-规格.md` **§17.8**（§17.3 / §17.4 的旧口径**只标注、不删**）。

## 一、三份留档

| 文件 | 内容 |
|---|---|
| `01-改前基线-runB2-探针结果.txt` | **改动前**（旧口径：`MOVEMENT_SPEED` + `ADD_MULTIPLIED_TOTAL` 运行期条件修饰符）跑同一套探针：**102 PASS / 60 FAIL** |
| `02-改后-runC2-探针结果.txt` | **改动后**（新口径：`SWIM_SPEED` 常驻、每部位一个 id）：**165 PASS / 0 FAIL** |
| `04-首轮探针-启动瞬态与水池越界-runA.txt` | 探针**第一版**的结果，留着说明两件事：① 前 2 例有**启动瞬态**（p0/p1 = 平台的 0.9042/0.9479）⇒ 加了"预热例"；② 深水池顶超出建筑高度上限 319 ⇒ p4 冲破水面被抓 |
| `03-关卡扰动实测.txt` + `05-扰动脚本-bg8b-perturb.py.txt` | 静态关卡的**扰动实测**（1 基线 + 6 条改坏必红 + 1 条"只改注释必须仍绿"的反向对照 + 1 条收尾基线），**mismatches = 0** |
| `06-B级-构建与校验器.txt` | `compileJava` / `runData` / `processResources jar --rerun-tasks` 与 **5 个校验器**的命令 + 退出码 + 输出摘要（jar = 1,089,658 B） |

## 二、实测环境与方法（A 级：真玩家 + 真实按键 + 端到端位移）

- `runClient` + **整合服务端**；受试 = **真实 `ServerPlayer` + 真实 `LocalPlayer`**（**不是** `FakePlayer`、
  **不是**手工 post 事件）。探针自己订阅 `PlayerTickEvent.Post` 计数（1409 / 1240 tick）以证明"真的在 tick"。
- 驱动 = **真实按键输入**：`options.keyUp.setDown(true)` → `KeyboardInput#tick` → `zza` → `LivingEntity#travel`。
- 场地：48×48 跑道（origin `48,-48`，浅水 y=200 一格深 ⇒ 玩家**在水底行走**、`onGround=true`，
  与上一轮 `docs/bg8-证据/` 完全同一几何）+ 一条 y=220 陆地对照道 + 一个 y=260、40 深的**上浮水池**
  （只按跳跃键、无水平漂移）。
- 测量窗：**前 20 tick 只加速、量第 20..60 tick**（40 tick）；**撞墙守护写成断言**
  （`move_not_clipped_*`：`endZ < -1.5`，实测最远 -20.12 ⇒ 离墙 18.6 格）。
- 世界 = 作者存档 `run/saves/新的世界` 的**副本** `run/saves/bg8bprobe`（作者存档全程只读：
  29 个文件、mtime 与 SHA256 manifest 逐条比对未变；副本跑完已删）。
- 用例：水中 0/1/2/3/4 件、陆地 0/1/2/3/4 件、上浮 0/1/2/3/4 件 + 1 例`脱甲移除`+ 1 例 tooltip。

## 三、一句话结论

- **`SWIM_SPEED` 这一层自己的位移倍率精确 = 1 + 0.25 × 件数**
  （改后 ÷ 上一轮"只有浅水那条"的留档 = **1.2501 / 1.5000 / 1.7500 / 2.0000**）。
- **端到端总位移**（vs 0 件）= **1.8994 / 2.7554 / 3.5893 / 4.4104** —— 因为**被要求原样保留**的
  `WATER_MOVEMENT_EFFICIENCY`（浅水那条）自己就把水中位移抬到 1.5199→2.2058，两个因子相乘。
  ⇒ 「总位移 ≈ ×1.25/件」在保留浅水那条的前提下**物理上不可能达到**，需作者一句话裁定（见 §17.8 末节）。
- **陆地逐值不变**（0~4 件都是 8.6344，比值 1.0000）；`MOVEMENT_SPEED` 恒 0.1000（旧口径下是 0.125/0.150/0.175/0.200）。

## 四、B 级（命令 + 输出）

见 `docs/1.5-规格.md` §17.8 的收尾小节（`compileJava` / `runData` / `processResources jar --rerun-tasks`
与 5 个校验器的命令与退出码）。

## 五、收尾清理（探针铁律）

| 项 | 结果 |
|---|---|
| `src` 下 `grep 'BG8BPROBE\|Bg8bProbe\|bg8b-probe\|bg8bprobe'` | **0 命中**（探针类 + `bettergoldClient` 里的注册块整块删除，不是注释掉） |
| 开关文件 `run/bg8b-probe.enabled` | 已删除 |
| 探针世界副本 `run/saves/bg8bprobe` | 已删除（作者的 `run/saves/新的世界` **29 个文件**、manifest 逐条未变） |
| 临时脚本 `build/bg8b-*.py` | 已删除（扰动脚本副本留在本目录） |
| forceload | 探针自己撤销 25 个区块并断言 `levelForcedCount=0`；`check_forced_chunks.py` 对 `run/world` exit 0 |
| 生产代码里的 `server.halt` | **0 处** |
