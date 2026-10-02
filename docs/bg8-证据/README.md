# bg-15w §八 追加轮②「装备顺序重钉 / 纹饰物品形态取证 / 真正的游泳速度」取证与实测证据

> 会话标记 `bg-15w`；需求 = 同一份需求文档 `20261002-1330_bg-15w_weapon-final-fixes.md` 的
> **§八 追加轮②**（2026-10-02 17:44 追加的三项：8.1 / 8.2 / 8.3）。
> 本目录是**长期留档**（`build/` 被 `.gitignore` 忽略，不留档）；结论已同步进 `docs/1.5-规格.md` **§17**，
> 并在 §13.5 / §16.4 各留一行指针（旧文一字未删）。

## 一、两轮实机探针（`runClient` + 整合服务端 + **真实玩家**）

| 轮次 | 环境 | 结果 | 文件 |
|---|---|---|---|
| 改前基线 runA2 | `git stash` 掉本轮 Java 改动后重建的**改动前代码** | **137 PASS / 26 FAIL**（红的正是本轮要改的两族：`gear_order_*` ×6 + 游泳速度 ×20） | `01-改前基线-runA2-探针结果.txt` |
| 改后 runB3 | 本轮全部改动 | **159 PASS / 4 FAIL**（4 条红是"端到端位移比值 == 属性比值"这个**需求括号里的期望**，见下） | `02-改后-runB3-探针结果.txt` |

- **移动测量不是 FakePlayer、也不是手工 post 事件**：用**真实 `LocalPlayer` + 真实按键输入**
  （`options.keyUp.setDown(true)` → `KeyboardInput#tick` → `zza` → `LivingEntity#travel`），
  量的是**真实位移**（40 tick 测量窗、前 20 tick 加速、48×48 场地、**撞墙守护** `localEndZ ≤ 27.45 < 44` 全 PASS）。
- 两轮的 0 件基线**逐位相同**（水中 3.9144 / 陆地 8.6344）⇒ 测量可复现。
- 4 条红的**不是实现缺陷**，而是需求括号里的口径与物理不符：
  `MOVEMENT_SPEED` 属性比值**精确**是 1.25/1.50/1.75/2.00，
  而**端到端位移**比值是 1.76/2.60/3.49/4.41 —— 机理与"要精确 ×1.25/件就该用 `neoforge:swim_speed`"
  的完整说明见 `docs/1.5-规格.md` §17.4。
- 关键 PASS（摘）：`swim_modifier_single_id_water_p1..p4`（**恒 1 个 id**）、
  `swim_modifier_value_water_p1..p4`（0.125/0.150/0.175/0.200）、
  `swim_modifier_absent_land_p1..p4`（**盔甲还穿着、一上岸就被移除**）、
  `movement_speed_unchanged_land_p*`（0.100000 五行全同）、
  `client_attr_ratio_is_1p25n_water_p1..p4`（客户端实例逐值相同 ⇒ 该属性 `setSyncable(true)`）、
  `forceload_released`（探针自撤 9 个区块，`stillForced=0 / levelForcedCount=0`）。

## 二、关卡自身的扰动实测（§3.4 纪律）

- `03-关卡扰动实测.txt`：1 条基线（不扰动必须 `exit 0`）+ **6 条扰动全部命中各自期望的 `exit 1` 与报错子串**
  （GEAR_SLOT 位次换回旧顺序 / hoe 改名 / 泳速 id 字面量重复 / `ADD_MULTIPLIED_TOTAL` 改回 `ADD_VALUE` /
  往 `getDefaultAttributeModifiers` 塞 `MOVEMENT_SPEED` / `0.25F` 改 `0.5F`）+ 1 条收尾基线。
  **mismatches = 0**。
- ⚠ 其中 D 用例第一版**假绿**（方法体内的**内联注释**还写着"必须 `ADD_MULTIPLIED_TOTAL`"）⇒
  已把判据改成在**去注释后**的代码上跑，D 才真正红。这条已回流 `mcmod_experience.md` §3.4。
- `05-扰动脚本-bg8-perturb.py.txt` 是那次扰动的脚本副本（原脚本放 `build/`，跑完已删）。

## 三、色卡像素（§8.2 的原料之一）

- `04-色卡像素-七张.txt`：7 张 `textures/trims/color_palettes/*.png` + 原版 client jar 里的 `quartz`，
  逐像素 dump。**indigoseagold 与原版 quartz 8 个值逐字相同**；另 6 张 == 各自的彩色 8 值
  ⇒ §7.3 的"只改这一张"在**这一轮之后依然成立**。
- §8.2 的完整四步取证结论（两种形态的实际颜色、物品模型实际叠的哪一层、为什么"卡在第 4 步"）
  见 `docs/1.5-规格.md` **§17.2**。

## 四、B 级（命令与输出）

```
.\gradlew.bat compileJava                        → BUILD SUCCESSFUL
.\gradlew.bat runData                            → BUILD SUCCESSFUL（兼作 Bootstrap/mixin 冒烟）
.\gradlew.bat processResources jar --rerun-tasks  → BUILD SUCCESSFUL（bettergold-1.5.0.jar = 1090070 B）
python tools\asset-generator\validate_metal_assets.py  → exit 0
python tools\asset-generator\validate_metal_data.py    → exit 0（新增 §8.1/§8.3 断言族，问题 0）
python tools\asset-generator\validate_trim_assets.py   → exit 0
python tools\asset-generator\check_jar_clean.py        → *Probe* 0 / 含 halt 字节 0 / BG-PROBE 0（1882 文件）
python tools\asset-generator\check_forced_chunks.py    → data.Forced = []（run/world 侧 0）
```

## 五、收尾清理（探针铁律）

| 项 | 结果 |
|---|---|
| `src` 下 `grep 'BG8PROBE\|Bg8Probe\|bg8-probe\|bg8probe'` | **0 命中**（探针三个类整块删除，不是注释掉） |
| 开关文件 `run/bg8-probe.enabled` | 已删除 |
| 探针世界副本 `run/saves/bg8probe` | 已删除（作者原本的 `run/saves/新的世界` **29 个文件、mtime 全停在 14:29**，未被打开过） |
| 临时脚本 `build/bg8-*.py` / 探针结果 / 解包出来的源码 | 全部删除（`build/` 本身不进版本库） |
| forceload | 探针自己撤销 9 个区块并断言归零；`check_forced_chunks.py` 对 `run/world` exit 0 |
| 生产代码里的 `server.halt` | **0 处** |
