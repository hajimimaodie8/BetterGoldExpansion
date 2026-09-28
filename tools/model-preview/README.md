# tools/model-preview

离线检查 / 转换方块模型的小工具。用 Python + Pillow，**不需要开游戏**就能看到模型长什么样。
（注：Hindsight 知识库工具在本次会话里不可用，相关结论先记在这里。）

## render.py —— 离线预览

```powershell
python render.py --model <模型.json> --texture <贴图.png> --out <输出.png> [选项]
```

| 选项 | 说明 |
|---|---|
| `--view iso\|front\|back\|left\|right\|top` | `iso` 是等轴测（默认），其余是正交视图。`front` = 从北往南看（显示 north 面），用来判断模型的"正面"朝哪 |
| `--size 800` | 画布尺寸。**排查贴图问题一定要开大**，小图看不出拉伸/错位 |
| `--uv-scale su [sv]` | 每个 UV 单位对应多少贴图像素，默认贴图宽度/16。用来试探"模型 UV 是按多大的画布标的" |
| `--fit` | 先把几何收进 0..16 再渲染 |

## convert.py —— 把美术给的 Blockbench 模型转成合规的 Java 方块模型

```powershell
python convert.py --model <源.json> --id <方块 id> --out <模型目录> [选项]
```

做的处理：
- 按**旋转后**的真实包围盒把模型收进 0..16（`--fit-mode uniform`，只缩不放）、水平居中、底面贴 y=0；
- 旋转只保留 Java 允许的单轴，角度吸附到 -45/-22.5/0/22.5/45，0 则删除；
- UV 夹到 0..16（负值会采到图集外面变成杂色）；
- 贴图 key 统一成 `#all`，并加 `"parent": "minecraft:block/block"`
  （原版只提供 `gui_light` 和标准 display 变换，不影响放置后的渲染，但物品形态才不会 1:1 顶脸）；
- `--fit-mode none`：保持美术原始尺寸（可能伸出方块）；`--keep-x`：x 方向不居中；
- `--fit-mode squash-y`：水平保持原始尺寸，只压扁高度塞进方块。

## 三条踩过的坑（改模型前务必看）

1. **不要为了"正面朝北"去烘焙 90 度旋转。**
   只转盒子坐标、不转面 UV，会把每个面接到隔壁面的贴图区域上（新 north 面其实来自旧 west 面），
   游戏里表现为"有的地方被严重放大、有的地方被严重拉伸"。
   正确做法：模型按原样导出，朝向交给 blockstate 的 `y` 旋转（渲染时连 UV 一起转）。
   金猫的模型正面朝西，所以它的 blockstate 整体多转 90 度：`north→y:90 / east→180 / south→270 / west→0`；
   其余三座摆件原模型朝北，用常规 `0/90/180/270`。
   如果确实要烘焙（`--rotate-y`），`rotate_y()` 现在会连面 UV 一起转，但优先用 blockstate 方案。

2. **贴图画布必须和模型 UV 假设的画布一致，注意画布不一定是正方形。**
   用 `uv_check.py` 判定：它对每个面算 `k = (面宽/面高) * (dv/du)`，**无拉伸时 k 必须恒定**，
   那个常数就是画布的宽高比。
   - 金蟾/末影人/苦力怕：k = 1.000（正方形画布）→ 它们的 64×64 贴图没问题；
   - **金猫：k = 2.000（66 个面全部一致）→ 画布是 2:1**，正是源模型里写的 `"texture_size": [64, 32]`。
     再核对密度：UV 粒度是 0.25(u)/0.5(v)，只有 64×32 画布能让它正好等于 1 像素
     （也就是 1 像素 = 1 格模型，标准像素材质）→ 画布确定为 **64×32**。
     曾经错误地裁成 32×32（正方形），于是所有面被横向压缩 2 倍，
     表现就是"好端端的正方形被拉成很窄的长方形"。
   - 现在 `golden_cat_figurine.png` = **64×32**。美术原图只有 64×64 且图案只画在左上 33×30，
     所以用 `crop_canvas.py --size 64x32 --fill mirror` 裁到正确画布，并把每行已绘制部分
     左右镜像补满（否则右侧那些 UV 会采到空白，表现为透明破洞）。
   - 顺带：`render.py` 以前两个轴共用同一个像素比例（用宽度算），非正方形贴图会采错行；
     现在 u/v 各自用 `宽/16`、`高/16`。

3. **非整块方块 + 带透明像素的贴图**，必须同时做三件事：
   `RenderType.cutout()` 渲染层（否则透明区被 solid 画成黑色）、
   `parent: minecraft:block/block`（要当物品用的话）、
   按真实体积给 `VoxelShape`（否则有空气墙、还会像整块一样压暗周围）。

## 工具一览

| 脚本 | 用途 |
|---|---|
| `render.py` | 离线渲染预览（等轴测 / 正交视图），不开游戏就能看模型 |
| `convert.py` | Blockbench 模型 → 合规 Java 方块模型（收进 0..16、旋转合法化、UV 移入范围、加 parent） |
| `uv_check.py` | 用 `k=(宽/高)*(dv/du)` 判定模型 UV 要求的**贴图画布宽高比** |
| `uv_canvas.py` | 枚举候选画布，看哪些面能落在已绘制区域内 |
| `crop_canvas.py` | 把贴图重整到正确画布尺寸，可选按行镜像补满空白列 |

## 自定义盔甲纹饰材质：三样缺一不可

1. `data/<modid>/trim_material/<name>.json`（`asset_name` / `ingredient` / `description` / `item_model_index`）；
2. `assets/<modid>/textures/trims/color_palettes/<asset_name>.png`（8×1 色卡）+ **图集置换表**：
   纹饰贴图不是直接读色卡，而是由 `armor_trims` 图集的 `paletted_permutations` 源按材质名生成的。
   本仓库自带 `assets/minecraft/atlases/armor_trims.json`，列出原版 36 张基础贴图 + 自己的材质
   （1.21 的 `SpriteSourceList.load()` 会把各资源包的同名 atlas 源列表**拼接**，不是覆盖）。
3. **把材料物品加进 `#minecraft:trim_materials` 物品标签**（`data/minecraft/tags/item/trim_materials.json`）。
   这条最坑：原版 `smithing_trim` 配方写的是 `"addition": {"tag": "minecraft:trim_materials"}`，
   材料不在这个标签里，锻造台**根本不会匹配**，表现就是"纹饰完全没效果"。缺的只有这一条时，
   纹理、色卡、材质 JSON 全都是对的，照样做不出来。
   顺带：要让**自己的盔甲**也能打纹饰，还得把盔甲加进 `head/chest/leg/foot_armor` 四个物品标签
   （`#minecraft:trimmable_armor` 由它们拼出来）。

验证手段（不靠肉眼）：在 `ServerStartedEvent` 里跑一次配方查询
`recipeManager.getRecipeFor(RecipeType.SMITHING, new SmithingRecipeInput(样板, 盔甲, 材料), level)`，
能拿到结果就说明整条链通了；客户端再监听 `TextureAtlasStitchedEvent` 检查
`trims/models/armor/coast_<asset_name>` 精灵是否存在。

## 自定义配方：CraftingInput 的取物品方法有坑

`CraftingInput.getItem(int row, int column)` 的参数名是**误导**的，内部实现是
`items.get(row + column * width)` —— 两个参数实际是 **(x, y)**。按名字当 (行, 列) 用会导致
网格读错位置（本仓库的易金柜台配方就因此一直匹配失败）。
稳妥写法：用单参数重载自己算索引 `input.getItem(x + y * input.width())`。

## 顺手记：别用 PowerShell 的 Set-Content -Encoding UTF8 写资源文件

PS 5.1 会写成 **带 BOM** 的 UTF-8（`EF BB BF` 开头）。Minecraft 的 Gson 能容忍，但属于隐患，
本轮一次扫出 77 个带 BOM 的 json 并已清理。要写文件就用编辑工具，
或在 PS 里显式 `[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))`。
