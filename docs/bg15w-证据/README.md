# bg-15w「1.5 武器轮收尾八项」取证与实测证据（2026-10-02）

> 会话标记 `bg-15w`；需求文档 `E:\mc\mcmod\mod_experience\开工需求\20261002-1330_bg-15w_weapon-final-fixes.md`。
> 本目录是**长期留档**（`build/` 被 `.gitignore` 忽略，不留档）。
> 三条证据与两轮实机探针结果全部在这里；结论已同步进 `docs/1.5-规格.md` §12.3 / §12.4 / §12.7 / §12.8 / §13.6 与新增的 §14。

---

## 一、第 1 项「模型全黑」的三份取证（需求 §3.1 要求先取证再动代码）

### (i) 登记件数：**12**（不是 0）⇒ 嫌疑①「登记时机太晚」**排除**

`run/logs/latest.log`（2026-10-02 13:22:39，改代码前的最后一次 `runClient`）：

```
[Render thread/INFO] [com.hjmmd_8.bettergold.bettergold/]:
  1.5 武器轮：已为 6 件盾牌 + 6 件三叉戟登记自定义物品渲染器（MetalWeaponItemRenderer）
[Render thread/INFO] [com.hjmmd_8.bettergold.bettergold/]:
  1.5 武器轮：已为 24 件武器登记物品模型谓词（弓 pull/pulling、弩 pull/pulling/charged/firework、三叉戟 throwing、盾牌 blocking）
```

> 同目录更早的几次运行打的是 `7 件盾牌 + 7 件三叉戟`（当时还有 `*_golden` 那一套）；
> 1.5 修正轮删掉金制那一套之后，正确值就是 **6 + 6 = 12**。

### (ii) 贴图 id 逐字比对：**代码拼出来的 id 少了 `textures/` 前缀与 `.png` 后缀**（真根因）

| | 值 |
|---|---|
| `MetalWeaponItemRenderer` **改前**拼出的 id | `bettergold:entity/shield_sturdygold` / `bettergold:entity/trident_sturdygold` |
| 磁盘上的实际文件 | `assets/bettergold/textures/entity/shield_sturdygold.png` / `trident_sturdygold.png`（12 张全在） |
| 原版同类常量的写法 | `TridentModel.TEXTURE = minecraft:textures/entity/trident.png`；`ThrownTridentRenderer.TRIDENT_LOCATION` 同 |
| 关键源码 | `SimpleTexture.TextureImage.load`：`resourceManager.getResourceOrThrow(location)` —— **原样当资源路径用，不做任何补全**（neoforge sources `net/minecraft/client/renderer/texture/SimpleTexture.java:81-83`） |

运行时直接证据（同一次 `runClient`，13:23:56，栈含 `GuiGraphics.renderItem` ← `CreativeModeInventoryScreen`）：

```
[Render thread/WARN] [net.minecraft.client.renderer.texture.TextureManager/]: Failed to load texture: bettergold:entity/shield_flamegold
java.io.FileNotFoundException: bettergold:entity/shield_flamegold
	at ...ResourceProvider.getResourceOrThrow(ResourceProvider.java:18)
	at ...SimpleTexture$TextureImage.load(SimpleTexture.java:83)
	at ...SimpleTexture.getTextureImage(SimpleTexture.java:57)
	... 共 5 条：shield_flamegold / shield_sturdygold / shield_indigoseagold / shield_voodoogold / trident_indigoseagold
```

**「黑」是怎么来的（机制级）**：`TextureManager#loadTexture` 吞掉 `IOException` 后返回 `MissingTextureAtlasSprite.getTexture()`
—— 一张 16×16 的 missingno（`k < h/2 ^ l < w/2` ⇒ **左上象限 = 纯黑** `-16777216`）；
而盾牌 / 三叉戟模型的 UV 恰好整块落在左上那个象限 ⇒ **整个模型渲染成纯黑**，与作者描述的「模型全都是黑的」逐字吻合。

### (iii) 12 张 PNG 像素统计：**都不是全黑 / 全透明** ⇒ 嫌疑③「PNG 本身全黑」**排除**

见 `03-实体贴图像素统计.txt`，要点（可复算：`PIL` 解码 + 逐像素 alpha 统计）：

- 6 张盾牌实体图：**64×64**、不透明像素 **716 / 4096（17.48%）**、maxAlpha **255**、不透明区平均 RGB 分别是金/紫/蓝/…（六套金属各不相同）；
- 6 张三叉戟实体图：**32×32**、不透明像素 **209 / 1024（20.41%）**、maxAlpha **255**；
- `anyFullyTransparent=False`、`anyFullyBlack=False`。

### 结论（写进 `docs/1.5-规格.md` §12.4 (1c)）

**根因 = 嫌疑②（贴图 id 拼错）**，不是①（登记时机）、不是③（素材坏）。
修法：把两个方法拼的路径改成完整资源路径 `bettergold:textures/entity/{shield,trident}_<金属>.png`，
回落值同样改成原版完整路径（`minecraft:textures/entity/shield_base_nopattern.png` / `trident.png`）。
**12 张贴图一个字都没改**（本项目贴图红线：动手前必须问作者；本轮没有任何贴图改动）。

---

## 二、实机探针（`runClient` + 整合服务端，作者世界的**副本** `bg15wprobe`）

探针类 `client/Bg15wProbe` 与两个开关文件**已整块删除**（`src` 下 `grep 'BG15W-PROBE|Bg15wProbe|Probe'` = **0 命中**）。
客户端自己走正常退出路径（`Minecraft.stop()`）；**全程没有 `server.halt`**。

| 轮次 | 环境 | 结果 | 明细文件 |
|---|---|---|---|
| 1 | **没装** MUT | **147 PASS / 0 FAIL**（无 SKIP） | `01-未装mut-探针结果.txt` |
| 2 | **装了** MUT `0.5.0-beta3`（Modrinth 下载，跑完已删） | **147 PASS / 0 FAIL / 1 SKIP** | `02-装mut-探针结果.txt` |

关键断言（逐条可在明细文件里查）：

| 断言 id | 没装 mut | 装了 mut |
|---|---|---|
| `shield_texture_resolves_<6 金属>` / `trident_texture_resolves_<6 金属>` | PASS ×12 | PASS ×12 |
| `negative_control_old_*_path_not_a_resource`（改前的坏路径确实解析不到） | PASS ×2 | PASS ×2 |
| `shield_item_model_custom_renderer_*` / `trident_throwing_pose_custom_renderer_*` | PASS ×12 | PASS ×12 |
| `thrown_trident_entity_renderer_is_ours(_in_world)` | PASS | PASS |
| `attachment_type_registered_and_synced` | PASS | PASS |
| `server_trident_attachment_written_<6 金属>`（服务端写入） | PASS ×6 | PASS ×6 |
| `trident_sync_<6 金属>`（**同步到了客户端**） | PASS ×6 | PASS ×6 |
| `trident_renderer_texture_<6 金属>` + `_resolves_` | PASS ×12 | PASS ×12 |
| `shield_knockback_main_hand` / `_off_hand` / `_both_hands_still_10pct` / `_removed_when_no_shield` | 0.10 / 0.10 / **0.10** / 0.00 | 同 |
| `absorption_cap_shield_only` / `_armor4_no_shield` / `_armor4_plus_shield_is_20` | 4.0 / 16.0 / **20.0** | 同 |
| `shield_hit_dispatches_family_buff`（烈燃金盾打中 ⇒ 目标获高燃） | PASS | PASS |
| `drop_sturdygold_mace` / `_bow_arrow_not_main_hand` / `_trident_thrown_hand_empty` / `_shield` | PASS ×4 | PASS ×4 |
| `drop_negative_special_metal_weapon`（特殊金属不掉） | PASS | PASS |
| `creative_page_hides_all_blanks` + `creative_page_no_<5 胚底>` | PASS ×6 | PASS ×6 |
| `gear_order_<6 金属>` + `gear_contiguous_*`（14 件顺序） | PASS ×18 | PASS ×18 |
| `swim_tooltip_present_zh` / `_absent_on_other_metal` / `_present_with_player` | PASS ×3 | 前两条 **SKIP**（原因见下）、带玩家那条 PASS |
| `mut_recipe_not_loaded_without_mut` | PASS（1885 条配方里没有它） | — |
| `mut_recipe_loaded_with_mut` + `mut_smithing_recipe_matches_with_mut` + `mut_smithing_result_with_mut` | — | PASS ×3（产物 = `bettergold:sturdygold_mace`） |
| `probe_chunk_forceload_revoked` | PASS | PASS |

### SKIP 的原因（不是本模组的问题）

装了 MUT 时，**用 `Item.TooltipContext.EMPTY`（没有 level 的上下文）取 tooltip** 会在 **MUT 自己的 tooltip 处理器**里抛
`NullPointerException: Cannot invoke "LevelAccessor.registryAccess()" because "world" is null`；
探针把这两条标记成 SKIP（不算过、不算失败），改用**带真实 level + 真玩家**的那条 `swim_tooltip_present_with_player` 验，PASS。
同一现象在**探针跑之前**（14:07:47，启动期）也出现过 1 次并被打成 `EVENTBUS ERROR`，即它并非探针独有，但**与本模组无关**。

### 装了 MUT 时的两条「别误判」记录

1. **MUT 自己刷 37 条配方解析错误**（`Parsing error loading recipe mut:spear/...`、`mut:diamond_horse_armor_...`）
   与 `Couldn't load tag spearcore:spear` —— 它引用了未安装的 `spearcore`。**其中 `bettergold:` 的条数是 0**。
2. 装了 MUT 后配方总数 1885 → **2592**（MUT 自带的 + 我们那 30 条）。

### ⚠ 探针环境的两条「假阴性」教训（已回流经验库）

- 第一版受试生物用 `Zombie`，**18 条断言全红**：作者的世界难度是**和平**，
  `Mob#checkDespawn` 对 `Monster` 在和平难度下直接 `discard()` ——
  现象是 `addFreshEntity=true` 但 2 tick 后 `removed=true / alive=false / tickCount=0`，
  于是「属性修饰符不生效」「`hurt()` 返回 false」「命中不给 buff」全是同一个假阴性。换成牛（`EntityType.COW`）后全绿。
- 作者的世界里本来就有 **25 块 forceload**（不是本轮加的）；探针只核对自己那一块（chunk 3,-3）已撤销。

## 三、生产代码侧的清理证据

| 项 | 结果 |
|---|---|
| `src` 下 `grep 'BG15W-PROBE\|Bg15wProbe\|bg15w-probe\|Probe'` | **0 命中** |
| 开关文件 `run/bg15w-probe.enabled` | 已删除 |
| 探针世界副本 `run/saves/bg15wprobe` | 已删除（作者原本的「新的世界」未改动） |
| 临时装进 `run/mods` 的 MUT jar | 已删除（`run/mods` 恢复为只有 JEI） |
| 生产代码里的 `server.halt` | **0 处**（探针从未使用 `halt`，客户端自己 `Minecraft.stop()`） |
| 运行期 forceload / `chunks.dat` | 探针自己那一块运行期已撤销；`check_forced_chunks.py` 见 §14 的构建证据 |
