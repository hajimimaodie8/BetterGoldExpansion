# 创造页「分区横幅栏目」参考实现 —— 总览

> **本文档解决什么问题：** 讲清「创造模式标签页里，用一整行横幅把物品分成若干区」这个效果到底怎么实现、
> 有四条路可以走、以及在你自己的模组里落地前必须先知道的几件事。
> **适合谁看：** 已经会写 NeoForge 1.21.1 模组、想给自己模组的创造页做分区横幅（或类似「空行间隔 + 栏目名」布局）
> 的开发者。读者**不需要**任何其它对话的上下文，本文件夹里的内容自成闭环。

---

## 一、效果长什么样

一个创造模式标签页（tab）里，物品按 9 个一行（`9 列 × 5 行 = 45` 个可见格）排列。这个效果在物品列表里插入
**整行空格子**，然后在空行上画一条 **162×18 像素**的横幅贴图，横幅左端写这一区的名字（下称**释词**）。
滚动时横幅跟着物品一起滚。

```
┌──────────────────────────────────────────────┐  ← 物品格区域（宽 162 = 9 × 18）
│                                              │  ← 第 0 行：整行空格子 → 在这上面画「其他材料」横幅
│ [其他材料 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  │
│  物品 物品 物品 物品 物品 物品 物品 物品 物品 │  ← 第 1 行：本区物品
│  ...                                          │
│                                              │  ← 整行空格子 → 「交易金商人相关」横幅
│ [交易金商人相关 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  │
│  ...                                          │
│                                              │  ← 整行空格子 → 「金属」横幅
│ [金属 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]  │
│  ...                                          │
└──────────────────────────────────────────────┘
```

关键点只有三个，其余都是细节：

1. **列表里存在「整行空格子」**（渲染端靠这个事实决定横幅画在哪一行）；
2. **横幅是画上去的，不是物品**（横幅不进物品列表，由客户端渲染钩子叠加绘制）；
3. **横幅行 = 某个分区物品的上一整行**，所以分区之间必须有恰好一行的空档。

术语一次性说明（后文直接用）：

| 术语 | 含义 |
|---|---|
| **标签页 / tab** | `CreativeModeTab` 的实例，创造界面顶部那一排图标 |
| **显式物品列表** | `CreativeModeTab#getDisplayItems()` 返回的 `Collection<ItemStack>`，创造界面只读它 |
| **分区 / 桶（Bucket）** | 一组物品 + 它横幅上的释词，例：`金属` + 该区所有金属物品 |
| **释词** | 横幅左端那段文字，例：「其他材料」 |
| **横幅行** | 画横幅的那一整行空格子 |
| **图集（atlas）** | 1.21.1 里 GUI 贴图会被打进的 `minecraft:textures/atlas/gui.png` 大图；`blitSprite` 只能取图集里的「精灵（sprite）」 |
| **精灵（sprite）** | 图集里的一小块贴图，用 `ResourceLocation`（如 `simulated:banner`）引用 |

---

## 二、四条可行路径对比

四种做法都能做出这个效果，代价差别很大。**我们采用的方案是 ②**。

| # | 路径 | 核心动作 | 是否引 Mixin | 优点 | 代价 / 风险 |
|---|---|---|---|---|---|
| ① | **Mixin 直接换私有 `displayItems`** | `@Mixin(CreativeModeTab.class)` + `@Shadow private Collection<ItemStack> displayItems`，在 `buildContents` 里把整个字段换成自己的 `LinkedList`（里面可以有 `ItemStack.EMPTY`） | 是（必需） | 最自由：想怎么排就怎么排，空行可以直接进列表；弹 tooltip、搜索页都能一起接管 | 依赖 Mixin 与映射；私有字段一改名就崩（编译期发现不了）；和其它改创造页的模组容易打架；要用 MixinExtras 的 `@WrapMethod`。参考实现 Aeronautics 就是这么做的（见 `05-参考来源与出处.md`） |
| ② | **NeoForge 官方扩展点 `withTabFactory` + 覆写 `getDisplayItems()`** | 生成器里**只 accept 非空格子**（按分区顺序），另外把「每个分区有多少个物品」记下来；再覆写 `getDisplayItems()`，把空格子按记录的长度补回去 | **否** | 零 Mixin、零反射（排布侧）；用的是 NeoForge 公开 API；`displayItems` 字段与 `Output` 校验都被绕开 | 仍需一个 `CreativeModeTab` 子类；`getDisplayItems()` 每次调用都要重算（我们做了长度守卫）；**不能用 `output.accept(ItemStack.EMPTY)`**（会抛异常，见 `02` 第 1 条） |
| ③ | **只做横幅，不分区** | 客户端渲染钩子里，按物品坐标算出「某类物品从哪一行开始」，在那里画横幅；列表里不加任何空行 | 否 | 改动最小，不需要动注册代码；适合「物品本来就已经天然按类别排列」的情况 | 分区边界和物品行数强耦合：只要有一个物品被别的模组插进来、或物品数量变化，横幅就会**盖住物品**；不同区的物品会连在一起，观感差；维护成本随分区数上升 |
| ④ | **用现成库** | 直接依赖一个已经实现了「分区 + 横幅」的库 | 否（库内部可能有） | 代码量最少，通常还附赠配置/数据驱动 | 多一个依赖；升级要等库跟进；许可与「抄没抄别人的代码」的问题转移到依赖上。1.21.1 上至少有两个真实存在的候选：<br>• **[ModernTabs](https://modrinth.com/mod/moderntabs)**（MIT，客户端侧，Fabric + NeoForge，1.21.1）——描述里明确写了「分区 + 横幅」的灵感来自 Create Aeronautics / Simulated，并**包含其少量代码**；<br>• **[Creative Tab Layouts (CTL)](https://modrinth.com/mod/creative-tab-layouts)**（LGPL-2.1-or-later，仅 NeoForge，客户端 + 服务端，1.21.1）——page/subtab/section/header/banner 的 API。<br>两者只用 Modrinth API 的元数据与项目描述核实过（2026-09），**本仓库没有实际安装试跑**，选它之前请自己评估 API 稳定性与许可传染性 |

> **为什么我们没走 ①：** 不是为了「反对 Mixin」，而是**没有必要**。空行的唯一难点是
> `output.accept(...)` 不接受空 stack（`02` 第 1 条）；而「往外暴露物品列表」这件事原版自己就留了口子 ——
> 创造界面读的是 `getDisplayItems()`，那是个 `public` 方法，可以直接覆写。既然公开 API 够用，就不值得
> 为它背上 Mixin 的映射耦合。

---

## 三、给实现者的 TL;DR

**先做什么（顺序不要颠倒）**

1. **先想清楚分区表**：每页有哪些分区、释词是什么、顺序如何；分区内的物品**靠 id 后缀/规则判定，不要枚举物品**
   （金属会越来越多，枚举是死路）。见 `01-原理与数据结构.md`。
2. **再做排布**：分桶（每件物品只进第一个命中的分区）→ 每区之后「补满当前行 + 再空一整行」→ 在加入本区物品**之前**
   记下「本区首个物品所在行」。列表**开头还要补一整行空格子**，否则第一个分区的横幅没有地方画。
   见 `01` 的 `layout()` 与 `SECTION_ROWS` 语义。
3. **然后做注册**：`CreativeModeTab.builder().displayItems(只 accept 非空格子).withTabFactory(b -> new 你的子类(b, layout))`，
   子类覆写 `getDisplayItems()` 把空行补回去。见 `03-落地步骤.md` 的骨架。
4. **最后做渲染**：客户端 `ScreenEvent.Render.Post` → 只在自己页被选中时 → 反射读 `selectedTab` / `scrollOffs` /
   `leftPos` / `topPos` → 按原版公式把物品列表首行换算出来 → 用**自适应判定**找到那条空行 → 画横幅 + 释词。
   见 `03` 第 6~7 节与 `04-验证清单.md`。

**坑在哪（按踩到的概率排序）**

| 坑 | 一句话结论 | 详见 |
|---|---|---|
| 想用 `output.accept(ItemStack.EMPTY)` 插空行 | **会抛 `IllegalArgumentException`**（`EMPTY` 的 `count` 是 0，NeoForge 校验 `count == 1`），不是被过滤 | `02` §1 |
| 贴图放在 `textures/gui/某子目录/`，用 `blitSprite` 画 | **静默变成紫黑格，不报错**：GUI 图集只扫 `textures/gui/sprites/`；改 `graphics.blit(...)` 或把贴图挪进 `sprites/` | `02` §2 |
| 别名写成 `= Family.holder` | 触发**类初始化循环**，运行时 `NullPointerException`（编译期不报）；改用 `DeferredItem.createItem` 懒绑定 | `02` §3 |
| 只按 `记录行 − 1` 定位横幅 | 一旦有别的模组动了物品列表就会**盖住物品**；改成「只认整行空格子」的自适应判定 | `02` §4 |
| `withTabsBefore` 锚了 `HOTBAR/SEARCH/...` | 语义是「X 在本页之前」；锚 `DEFAULT_TABS` 里的页会把它们**重新拉进排序图**，原版页被挤到第二页 | `02` §5 |
| 卷动跟随自己猜公式 | 字段是 `CreativeModeInventoryScreen#scrollOffs`，首个可见行公式在 `ItemPickerMenu#getRowIndexForScroll` | `02` §6 |
| 探针关服写 `stopServer()` 再 `halt(false)` | 会走**两遍**关闭/存盘流程，日志看起来像卡死；只调一次 `halt(false)` | `02` §7 |
| 用 PowerShell 判构建成败 | javac 打在 stderr 的「注:」会被记成 `NativeCommandError`，pwsh 假报 exit 1；看 `BUILD SUCCESSFUL` | `02` §8 |
| 只读了 JSON/源码就说「好了」 | **不算验证**；必须让游戏真的加载并留日志证据 | `02` §9 |

**验证什么（最小可信集合）**

- `runServer`：分区数 = 桶数 = 非空物品数（三方相等，一个都不丢）；每区「首物品行 / 横幅行 / 横幅行是否整行空」
  三项全对；创造页排序表里自己的页都在预期位置（见 `04` §2）。
- `runClient`：`menu.getSlot(0).getItem() == displayItems.get(首个可见行 × 9)`（交叉校验卷动公式与行映射）；
  `scrollOffs` 取 0 / 0.25 / 0.5 / 0.75 / 1.0 时首个可见行符合原版公式（见 `04` §3）。
- **只能靠人眼**：横幅配色、释词位置/字号、滚动时横幅跟随的手感、会不会盖住物品。见 `04` §6。

---

## 四、本文件夹导航

| 文件 | 内容 |
|---|---|
| `README.md` | 本文件：效果、四路径对比、TL;DR |
| `01-原理与数据结构.md` | `Slot` / `Bucket` / 分区枚举 / `layout()` 规则 / `SECTION_ROWS` 语义 / 排序键 / 规则驱动判定 |
| `02-关键坑与对策.md` | 逐条：现象 → 根因 → 修法 → 依据（源码行号或实测日志） |
| `03-落地步骤.md` | 可照抄的实现步骤与代码骨架（NeoForge 1.21.1） |
| `04-验证清单.md` | 探针要打印哪些量、交叉校验、runServer/runClient 各自确认什么、只能靠人眼的部分 |
| `05-参考来源与出处.md` | Aeronautics 类路径清单 + jsDelivr 抓取命令 + 许可注意 + 本仓库范例位置 |

---

## 五、依据等级约定（全文件夹通用）

涉及原版 / NeoForge 行为的地方，一律标注来源等级，**不要把推断当结论**：

| 标注 | 含义 | 本文件夹里的形式 |
|---|---|---|
| **【实测】** | 在本机真的跑过游戏、日志里有对应行 | 形如 `build\server-sections5.log:60`（仓库根为基准的相对路径 + 行号） |
| **【读源码】** | 读过具体的 jar/文件并给出类名 + 行号 | 形如 `CreativeModeInventoryScreen.java:1033`（1.21.1 NeoForge 21.1.228 反编译源） |
| **【像素实测】** | 直接读原版资源文件（贴图）的像素值，比读代码更硬 | 例：`tab_items.png` 第一格确实是 `x 8..25 / y 17..34`（见 `05` §4.3） |
| **【推断】** | 由上面几类推出来的解释，没有直接证据 | 会明确写「推断」 |
| **【记录】** | 转述作者/前序开发留下的笔记，本轮**没有**重新验证 | 会给出原笔记位置 |

行号来自本机这两处，可复现（详见 `05` §4）：

- NeoForge 源码：`~\.gradle\caches\modules-2\files-2.1\net.neoforged\neoforge\21.1.228\<哈希>\neoforge-21.1.228-sources.jar`
- Minecraft 1.21.1 反编译 + NeoForge 补丁源码：`~\.gradle\caches\neoformruntime\intermediate_results\sourcesAndCompiledWithNeoForge_*_output.jar`

> **提醒：** 换 NeoForge / Parchment 版本后行号会漂移。**行号只用来定位，最终以代码片段为准** ——
> 每个引用都附了可以 `grep` 的片段。

---

## 六、本仓库里的可运行范例（NeoForge 版）

| 文件 | 作用 |
|---|---|
| [`src\main\java\com\hjmmd_8\bettergold\material\SectionedCreativeTab.java`](../../src/main/java/com/hjmmd_8/bettergold/material/SectionedCreativeTab.java) | 会补空行的 `CreativeModeTab` 子类 + `withTabFactory` 工厂 |
| [`src\main\java\com\hjmmd_8\bettergold\material\CreativeSections.java`](../../src/main/java/com/hjmmd_8/bettergold/material/CreativeSections.java) | 排序规则引擎 + `layout()` + `SECTION_ROWS` |
| [`src\main\java\com\hjmmd_8\bettergold\material\CreativeTabSections.java`](../../src/main/java/com/hjmmd_8/bettergold/material/CreativeTabSections.java) | 各页的分区声明（`Slot` 列表）+ 分桶 |
| [`src\main\java\com\hjmmd_8\bettergold\client\CreativeSectionBanners.java`](../../src/main/java/com/hjmmd_8/bettergold/client/CreativeSectionBanners.java) | 客户端横幅渲染（`ScreenEvent.Render.Post` + 反射 + 自适应行判定） |
| [`bettergold.java`](../../src/main/java/com/hjmmd_8/bettergold/bettergold.java) | 本模组**唯一**创造页的注册与 `withTabsBefore(CreativeModeTabs.SPAWN_EGGS)` 排序（1.4 定稿：内容合并成一页、页内 5 条横幅分区） |
