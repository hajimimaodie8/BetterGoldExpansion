# bg-15w 续工轮「§七 追加轮五项 + §3.8 口径改正」取证与实测证据（2026-10-02 16:15 追加轮）

> 会话标记 `bg-15w`；需求 = 同一份需求文档 `20261002-1330_bg-15w_weapon-final-fixes.md` 的
> **§七 追加轮**（16:15 追加的五项）与 **§3.8 的就地改正**。
> 本目录是**长期留档**（`build/` 被 `.gitignore` 忽略，不留档）；结论已同步进
> `docs/1.5-规格.md` **§16**，以及 §12.3 / §12.4 / §12.8 / §13.7 / §14.7 的「已被续工轮取代」标注。

## 一、三轮实机探针（`runClient` + 整合服务端 + **真实玩家**）

| 轮次 | 环境 | 结果 | 文件 |
|---|---|---|---|
| 改前基线 | 改动前的代码，没装 mut | **64 PASS / 65 FAIL**（红的正是本轮要修/要做的那些） | `01-改前基线-run1b-探针结果.txt` |
| 改后 · 没装 mut | 本轮全部改动 | **126 PASS / 3 FAIL** | `02-改后-没装mut-run2-探针结果.txt` |
| 改后 · 装了 mut | `MoreUpgradeTemplate 1.21.1-neoforge-0.5.0-beta3`（Modrinth 下载，跑完已删） | **126 PASS / 3 FAIL** | `03-改后-装mut-run3b-探针结果.txt` |

- **唯一稳定的 3 条 FAIL 是「客户端属性实例」断言**，且它是**原版行为**（不是缺陷）：
  `Attributes.KNOCKBACK_RESISTANCE` 没有 `setSyncable(true)`，装备属性也只在服务端应用；
  阳性对照——手里拿铁剑时客户端 `attack_damage` 同样是 `{v=1.0,ids=[]}`。详见 `docs/1.5-规格.md` §16.2。
- 探针**不是** FakePlayer：它用 `openWorld` 打开作者存档的**副本** `bg7probe`，读的是真实
  `LocalPlayer` / `ServerPlayer`；并且探针**自己**订阅 `EntityTickEvent.Post` / `PlayerTickEvent.Post` 计数
  （`player_tick_post_fires_for_real_player` / `entity_tick_post_fires_for_real_player` 两条 PASS）。
- 第一版探针有一次**计划表用累加偏移**的错误，导致 §7.4 六条假阴性；改成绝对 tick 后
  改前基线得到真实结果「万坚金红 / 五套特殊金属绿」。这条已回流经验库（§3.2 规则 11）。

## 二、只改一张贴图（§7.3）

- `04-只改一张贴图-资源哈希.txt`：`assets/**` + `data/bettergold/trim_material/**` 共 1194 → 1200 个文件的
  SHA256 清单对比，**变更的 PNG 恰好 1 个**（`textures/trims/color_palettes/indigoseagold.png`），
  新增/删除 PNG = 0；`04a`/`04b` 是逐文件原始清单。
- 新像素 = 原版 quartz 色卡 `(242,239,237)…(42,40,34)`（从 client jar 取出逐像素对照，8 个值逐字相同）；
  `item_model_index=0.06` 与两份图集置换未动；`validate_trim_assets.py` exit 0。

## 三、关卡自身的扰动实测（§3.4 纪律）

- `05-关卡扰动实测.txt`：2 条基线（不扰动必须 exit 0）+ **7 条扰动全部命中各自期望的 `exit 1` 与报错子串**：
  三叉戟 in_hand 丢 `throwing` override / mixins 配置行改回注释态 / mixins.json 少写 mixin 类 /
  胚底工作台配方丢条件 / MUT 配方丢 `mod_loaded` 条件 / 以胚底为 base 的锻造配方被改成 MUT 版 /
  旧白字行语言键被加回来。

## 四、B 级（命令与输出）

```
.\gradlew.bat compileJava                        → BUILD SUCCESSFUL
.\gradlew.bat runData                            → BUILD SUCCESSFUL（兼作 Bootstrap/mixin 冒烟）
.\gradlew.bat processResources jar --rerun-tasks  → BUILD SUCCESSFUL（bettergold-1.5.0.jar 1089556 B）
python tools\asset-generator\validate_metal_assets.py  → exit 0（425 JSON；含三模型结构 + mixin 接线断言）
python tools\asset-generator\validate_metal_data.py    → exit 0（231 语言键 0 缺；双向条件配方 0 问题）
python tools\asset-generator\validate_trim_assets.py   → exit 0
python tools\asset-generator\check_jar_clean.py        → *Probe* 0 / 含 halt 字节 0 / BG-PROBE 0（1882 文件）
python tools\asset-generator\check_forced_chunks.py    → data.Forced = []（run/world 与作者存档都 0）
```

## 五、收尾清理（探针铁律）

| 项 | 结果 |
|---|---|
| `src` 下 `grep 'BG7PROBE\|Bg7Probe\|bg7-probe\|bg7probe'` | **0 命中**（探针类整块删除，不是注释掉） |
| 开关文件 `run/bg7-probe.enabled` | 已删除 |
| 探针世界副本 `run/saves/bg7probe` | 已删除（作者原本的 `run/saves/新的世界` 未改动） |
| 临时装进 `run/mods` 的 MUT jar | 已删除（`run/mods` 恢复为只有 JEI） |
| 生产代码里的 `server.halt` | **0 处**（探针从未使用 `halt`，客户端自己 `Minecraft.stop()`） |
| forceload | `run/world` 与作者存档的 `data/chunks.dat` 双向 **0** |
| 一次性脚本 | `build/bg7-*.py` 全部删除（不进版本库） |
