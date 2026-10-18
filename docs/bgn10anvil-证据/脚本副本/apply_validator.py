import sys
sys.stdout.reconfigure(errors="replace")

P = r"E:\mc\mcmod\bettergold-template-1.21.1\tools\asset-generator\validate_metal_data.py"
s = open(P, "rb").read().decode("utf-8")
orig = s


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, "anchor count %d != %d for %r" % (n, count, old[:120])
    s = s.replace(old, new)


OLD_SCREEN = '''# 界面常量 + 两条禁令
_r8_screen_path = _R8_JAVA / "client" / "SturdygoldAnvilScreen.java"
if not _r8_screen_path.is_file():
    _bgn10r8_bad("bgn10r8-screen", "缺 client/SturdygoldAnvilScreen.java")
    _r8_screen = ""
else:
    _r8_screen = strip_comments(_r8_screen_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends AbstractContainerScreen<SturdygoldAnvilMenu>", "界面不是自建 AbstractContainerScreen"),
        ("PANEL_WIDTH = 176", "主面板宽度不是 176（原版砧尺寸，槽位才对齐）"),
        ("PANEL_HEIGHT = 166", "主面板高度不是 166"),
        ("TAB_W = 28", "右上装饰宽不是 28（原图 x 176..203）"),
        ("TAB_H = 21", "右上装饰高不是 21（原图 y 0..20）"),
        ("PLATES_W = 110", "左下两条灰条宽不是 110（原图 x 0..109）"),
        ("PLATES_H = 32", "左下两条灰条高不是 32（原图 y 166..197）"),
        ("TEX_W = 256", "blit 的 textureWidth 不是 256（uv 会算错）"),
        ("setColor(1.0F, 1.0F, 1.0F, 0.35F)", "空槽幽灵图标不是 35% 半透明"),
        ("setColor(1.0F, 1.0F, 1.0F, 1.0F)", "半透明画完没有还原 shader 颜色"),
        ("ADDITIONAL_SLOT_X = 76", "幽灵图标的 x 不是输入 2 槽的 76"),
        ("ADDITIONAL_SLOT_Y = 47", "幽灵图标的 y 不是输入 2 槽的 47")):
    _bgn10r8_checked += 1
    if _needle not in _r8_screen:
        _bgn10r8_bad("bgn10r8-screen", _why + "（缺 " + _needle + "）")
_bgn10r8_checked += 1
if "blitSprite" in _r8_screen:
    _bgn10r8_bad("bgn10r8-screen",
                 "界面用了 blitSprite（gui/container 下的贴图不在 gui/sprites 图集里 ⇒ 静默紫黑格）")
'''

NEW_SCREEN = '''# 界面：⚠ 旧口径（bg-n10 轮8）原文留档、已作废 —— 旧期望是「自建 AbstractContainerScreen +
#   主面板 176x166 + 右上装饰 28x21 + 左下两条 110x32 + 35% 幽灵图标 + 禁 blitSprite」。
#   作者 2026-10-18 试玩要求「GUI 完全照普通铁砧」⇒ 现在走原版 ItemCombinerScreen（与 AnvilScreen 同一层），
#   右上/左下装饰与幽灵图标全部删除；blitSprite 改为**只许**用原版 minecraft:gui/sprites 里的
#   container/anvil/text_field[_disabled] + error 三个精灵（它们在 gui/sprites 图集里，不是 gui/container）。
#   逐项新口径由下面的 [bgn10anvil-*] 段钉住；这里只留「不退回旧形状」的反向断言。
_r8_screen_path = _R8_JAVA / "client" / "SturdygoldAnvilScreen.java"
if not _r8_screen_path.is_file():
    _bgn10r8_bad("bgn10r8-screen", "缺 client/SturdygoldAnvilScreen.java")
    _r8_screen = ""
else:
    _r8_screen = strip_comments(_r8_screen_path.read_text(encoding="utf-8"))
for _needle, _why in (
        ("extends ItemCombinerScreen<SturdygoldAnvilMenu>", "界面没有走原版 ItemCombinerScreen 那一层"),
        ("PANEL_WIDTH = 176", "主面板宽度不是 176（原版砧尺寸，槽位才对齐）"),
        ("PANEL_HEIGHT = 166", "主面板高度不是 166"),
        ("TEXT_FIELD_SPRITE", "没有画原版统一的名字输入框底图精灵"),
        ("this.titleLabelX = 60", "标题 x 不是原版的 60")):
    _bgn10r8_checked += 1
    if _needle not in _r8_screen:
        _bgn10r8_bad("bgn10r8-screen", _why + "（缺 " + _needle + "）")
_bgn10r8_checked += 1
if "blit(TEXTURE" in _r8_screen or "blit(this.menuResource" in _r8_screen:
    _bgn10r8_bad("bgn10r8-screen", "界面还在自己 blit 主面板之外的东西（旧口径已作废）")
'''
rep(OLD_SCREEN, NEW_SCREEN)

ANCHOR = "# ==================== 1.7 轮9 收口（bg-n10r9，2026-10-17）===================="

NEW_SECTION = '''# ==================== 1.7 万坚金砧贴图/GUI 重做（bg-n10anvil，2026-10-18）====================
#
# 作者试玩原话：「贴图严重匹配错误……看看原版的铁砧是怎么覆盖贴图的，就这么设置」「更换一下这个铁砧的
# GUI，应该是这个模组里面的铁砧」「把模组里面铁砧所有的 GUI 标识之类的东西，换成和普通铁砧的 GUI 完全一致」。
#
# 原版真源（build/mcsrc，逐行取）：
#   * 模型 assets/minecraft/models/block/template_anvil.json = **2 个贴图槽** `particle` + `body`；
#     anvil.json 只再补一个 `top` ⇒ 原版实际只有 **2 张图**：block/anvil.png（body：所有侧面 +
#     底盘上下 + 顶块 down）+ block/anvil_top.png（顶块 up）。两张都是 16×16。
#   * GUI：ItemCombinerScreen.renderBg = blit(176×166) + renderErrorIcon；
#     AnvilScreen：标题 (60,6) / 物品栏 (8,72) / 花费 (k,69) / EditBox (62,24,103,12) /
#     text_field 精灵 (59,20,110,16) / error 精灵 (99,45,28,21)。
#
# 作者 5 张 16×16 不是原版图集碎片，而是 5 张正交投影视图（alpha 实测）：
#   ew = 正视投影轮廓（IoU 1.0000、对称差 0 像素）  ← 内容 = 前后
#   ns = 侧视投影轮廓（IoU 1.0000、对称差 0 像素）  ← 内容 = 左右
#   top / base_top / base_bottom = 10×16 / 12×12 / 12×12 的独立视图
#   ⇒ 文件名与内容相反，按像素判、不按名字猜（作者素材文件名不改）。
_bgn10anvil_problems: list[str] = []
_bgn10anvil_checked = 0


def _bgn10anvil_bad(tag: str, msg: str) -> None:
    bgn10anvil_problems.append("[%s] %s" % (tag, msg))


_ANVIL_MODEL = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "models" / "block" / "sturdygold_anvil.json"
_ANVIL_SCREEN = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "client" / "SturdygoldAnvilScreen.java"
_ANVIL_MENU = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "menu" / "SturdygoldAnvilMenu.java"
_ANVIL_BLOCK = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "block" / "SturdygoldAnvilBlock.java"
_ANVIL_TEXDIR = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "textures" / "block"

# 表 = (from X,Y,Z, to X,Y,Z) -> {face: (slot, uv, rotation)}。uv = 该 element 在对应视图里的投影矩形；
# direction 成对镜像：north 用 x1 到 x0、east 用 z1 到 z0（与原版 east/west uv 反序同构 = 物理连续）。
_ANVIL_FACES = {
    (2, 0, 2, 14, 4, 14): {  # 底盘
        "down":  ("base_bottom", [2, 2, 14, 14], 180),
        "up":    ("base_top", [2, 2, 14, 14], 0),
        "north": ("ew", [14, 12, 2, 16], 0),
        "south": ("ew", [2, 12, 14, 16], 0),
        "west":  ("ns", [2, 12, 14, 16], 0),
        "east":  ("ns", [14, 12, 2, 16], 0),
    },
    (4, 4, 3, 12, 5, 13): {  # 下段窄腰
        "up":    ("base_top", [4, 3, 12, 13], 0),
        "north": ("ew", [12, 11, 4, 12], 0),
        "south": ("ew", [4, 11, 12, 12], 0),
        "west":  ("ns", [3, 11, 13, 12], 0),
        "east":  ("ns", [13, 11, 3, 12], 0),
    },
    (6, 5, 4, 10, 10, 12): {  # 上段腰
        "north": ("ew", [10, 6, 6, 11], 0),
        "south": ("ew", [6, 6, 10, 11], 0),
        "west":  ("ns", [4, 6, 12, 11], 0),
        "east":  ("ns", [12, 6, 4, 11], 0),
    },
    (3, 10, 0, 13, 16, 16): {  # 顶块
        "down":  ("top", [3, 0, 13, 16], 180),
        "up":    ("top", [3, 0, 13, 16], 0),
        "north": ("ew", [13, 0, 3, 6], 0),
        "south": ("ew", [3, 0, 13, 6], 0),
        "west":  ("ns", [0, 0, 16, 6], 0),
        "east":  ("ns", [16, 0, 0, 6], 0),
    },
}

try:
    _am = json.loads(_ANVIL_MODEL.read_text(encoding="utf-8"))
except Exception as _e:
    _bgn10anvil_bad("bgn10anvil-model", "模型 JSON 读不出来: " + str(_e))
    _am = {"elements": []}

_bgn10anvil_checked += 2
if _am.get("parent") != "block/block":
    _bgn10anvil_bad("bgn10anvil-model", "parent 不是 block/block（与原版 template_anvil 同层）")
if _am.get("textures", {}).get("particle") != "bettergold:block/sturdygold_anvil_ns":
    _bgn10anvil_bad("bgn10anvil-model", "particle 槽不是作者那张 ns（旧口径保留，避免破坏方块粒子）")

_got = {}
for _el in _am.get("elements", []):
    _key = tuple(_el.get("from", [])) + tuple(_el.get("to", []))
    _got[_key] = _el.get("faces", {})

_bgn10anvil_checked += 1
if set(_got) != set(_ANVIL_FACES):
    _bgn10anvil_bad("bgn10anvil-model", "element 集合不是原版 template_anvil 那 4 个: " + str(sorted(_got)))

for _key, _want in _ANVIL_FACES.items():
    _have = _got.get(_key, {})
    _bgn10anvil_checked += 1
    if set(_have) != set(_want):
        _bgn10anvil_bad("bgn10anvil-model", "element " + str(_key) + " 的面集合不是 "
                        + str(sorted(_want)) + "（实际 " + str(sorted(_have)) + "）")
    for _face, (_slot, _uv, _rot) in _want.items():
        _bgn10anvil_checked += 1
        _fd = _have.get(_face)
        if not isinstance(_fd, dict):
            continue
        _actual = (_fd.get("texture", "").lstrip("#"), list(_fd.get("uv", [])), int(_fd.get("rotation", 0)))
        if _actual != (_slot, list(_uv), _rot):
            _bgn10anvil_bad("bgn10anvil-model", "面 " + str(_key) + "/" + _face
                            + " 不是表里的「槽 " + _slot + " / uv " + str(_uv) + " / rotation " + str(_rot)
                            + "」（实际 " + str(_actual) + "）")

# ② 5 张源 PNG 的 SHA256：钉死作者素材一个像素都没改（值 = 2026-10-18 实测）
_ANVIL_PNG_SHA = {
    "sturdygold_anvil_top.png": "f254af49fb67217f6281751d72586ea03c435f0a661f8baea0d04155319546bd",
    "sturdygold_anvil_ns.png": "41f47eb97584f5eff49c2d5fae85b54618cdb6774178ce1af188c724a653873c",
    "sturdygold_anvil_ew.png": "782e3db8cf04397d4ecc173b1128139ba4f1718c7b87aadf80ff2ed12f5a98c2",
    "sturdygold_anvil_base_top.png": "dff345dd69e120fdcfb65ba643811644f191760300dcca10ec3692cbb46e92b5",
    "sturdygold_anvil_base_bottom.png": "5badbfb56bfa84e545369571110131db86fa58072b79e5fdc9ff8ef5d2d61e0b",
}
for _name, _sha in _ANVIL_PNG_SHA.items():
    _bgn10anvil_checked += 2
    _p = _ANVIL_TEXDIR / _name
    if not _p.is_file():
        _bgn10anvil_bad("bgn10anvil-tex", "缺贴图 " + _name)
    elif _r8_sha256(_p) != _sha:
        _bgn10anvil_bad("bgn10anvil-tex", "贴图被改过（SHA256 不是作者原件）: " + _name)

# ③ / ④ Screen：反向断言（旧自加元素一个都不许回来）+ 原版三处文字/输入框逐项
_sc = strip_comments(_ANVIL_SCREEN.read_text(encoding="utf-8")) if _ANVIL_SCREEN.is_file() else ""
_bgn10anvil_checked += 1
if not _sc:
    _bgn10anvil_bad("bgn10anvil-screen", "缺 client/SturdygoldAnvilScreen.java")
for _bad_needle in ("COST_BAR", "GHOST_COIN", "TAB_U", "TAB_V", "PLATES_U", "PLATES_V",
                    "ADDITIONAL_SLOT_X", "ADDITIONAL_SLOT_Y", "setColor(", "blit(TEXTURE"):
    _bgn10anvil_checked += 1
    if _bad_needle in _sc:
        _bgn10anvil_bad("bgn10anvil-screen", "旧自加元素又出现了（作者要求全部删掉）: " + _bad_needle)

_SC_NEEDLES = (
    ("extends ItemCombinerScreen<SturdygoldAnvilMenu>", "没有走原版 AnvilScreen 的同一层"),
    ("ResourceLocation.withDefaultNamespace(\\"container/anvil/text_field\\")", "没有原版输入框底图精灵"),
    ("ResourceLocation.withDefaultNamespace(\\"container/anvil/text_field_disabled\\")", "没有原版禁用态输入框精灵"),
    ("ResourceLocation.withDefaultNamespace(\\"container/anvil/error\\")", "没有原版错误图标精灵"),
    ("new EditBox(this.font, i + 62, j + 24, 103, 12, Component.translatable(\\"container.repair\\"))",
     "名字输入框不是原版的 (62,24,103,12)"),
    ("this.name.setMaxLength(50)", "名字最大长度不是原版 50"),
    ("this.name.setBordered(false)", "名字框不是原版无边框"),
    ("this.name.setResponder(this::onNameChanged)", "名字框没有接原版 onChange"),
    ("this.menu.setItemName(s)", "名字没有走原版 setItemName"),
    ("new ServerboundRenameItemPacket(s)", "名字没有走原版重命名包（只改客户端、服务端不知道）"),
    ("this.name.render(guiGraphics, mouseX, mouseY, partialTick)", "renderFg 没有画名字框"),
    ("this.leftPos + 59, this.topPos + 20, 110, 16", "输入框底图不是原版的 (59,20,110,16)"),
    ("guiGraphics.blitSprite(ERROR_SPRITE, x + 99, y + 45, 28, 21)", "错误图标不是原版的 (99,45,28,21)"),
    ("guiGraphics.drawString(this.font, this.title, 60, 6, 4210752, false)", "标题不是原版坐标/颜色/无阴影"),
    ("guiGraphics.drawString(this.font, this.playerInventoryTitle, 8, 72, 4210752, false)",
     "物品栏标题不是原版坐标/颜色/无阴影"),
    ("int j = 8453920", "花费够级的颜色不是原版 8453920"),
    ("j = 16736352", "花费不够级/过于昂贵的颜色不是原版 16736352"),
    ("component = TOO_EXPENSIVE_TEXT", "没有原版「过于昂贵」分支"),
    ("Component.translatable(\\"container.repair.cost\\", i)", "没有原版「花费 X 级」文案"),
    ("i >= 40", "「过于昂贵」的阈值不是原版 40"),
    ("int k = this.imageWidth - 8 - this.font.width(component) - 2", "花费右对齐 x 不是原版公式"),
    ("int l = 69", "花费 y 不是原版 69"),
    ("guiGraphics.fill(k - 2, 67, this.imageWidth - 8, 79, 1325400064)", "花费底色不是原版的 (k-2,67..168,79)"),
    ("guiGraphics.drawString(this.font, component, k, 69, j)", "花费文字不是原版 (k,69) + 默认阴影"),
    ("this.name.setEditable(this.menu.getSlot(0).hasItem())", "输入框可编辑判定不是原版"),
    ("this.name.setValue(stack.isEmpty() ? \\"\\" : stack.getHoverName().getString())",
     "slotChanged 没有把输入物品的名字同步进名字框"),
)
for _needle, _why in _SC_NEEDLES:
    _bgn10anvil_checked += 1
    if _needle not in _sc:
        _bgn10anvil_bad("bgn10anvil-screen", _why + "（缺 " + _needle + "）")

# ⑤ 菜单：名字走原版链路 + 金币串那条路也按原版语义落名字
_mn = strip_comments(_ANVIL_MENU.read_text(encoding="utf-8")) if _ANVIL_MENU.is_file() else ""
_bgn10anvil_checked += 1
if not _mn:
    _bgn10anvil_bad("bgn10anvil-menu", "缺 menu/SturdygoldAnvilMenu.java")
for _needle, _why in (
        ("private String requestedName", "没有记录原版链路送进来的名字"),
        ("public boolean setItemName(String itemName)", "没有接住原版 setItemName"),
        ("this.requestedName = itemName;", "setItemName 没有先写字段（super 内部会虚派发 createResult）"),
        ("StringUtil.isBlank(this.requestedName)", "金币串那条路没有原版的「名字为空」语义"),
        ("result.set(DataComponents.CUSTOM_NAME, Component.literal(this.requestedName))",
         "金币串那条路没有把玩家改的名字写到结果上"),
        ("this.coinCost.set(used * COST_PER_COIN + renameCost);", "等级花费没有算上原版的改名 1 级"),
):
    _bgn10anvil_checked += 1
    if _needle not in _mn:
        _bgn10anvil_bad("bgn10anvil-menu", _why + "（缺 " + _needle + "）")
_bgn10anvil_checked += 1
if "syncNameFromInput" in _mn:
    _bgn10anvil_bad("bgn10anvil-menu", "旧的强制名字同步又回来了（会把玩家改的名字立刻抹掉）")

# ⑥ 方块：容器标题 = 原版 container.repair（原版 AnvilBlock.java:44 同一个键）
_bl = strip_comments(_ANVIL_BLOCK.read_text(encoding="utf-8")) if _ANVIL_BLOCK.is_file() else ""
_bgn10anvil_checked += 1
if 'Component.translatable("container.repair")' not in _bl:
    _bgn10anvil_bad("bgn10anvil-block", "容器标题不是原版 container.repair（作者要求 GUI 标识完全一致）")

_bgn10anvil_checked += 1
if _bgn10anvil_checked < 60:
    _bgn10anvil_bad("bgn10anvil-anti-vacuum", "本段判定数 < 60（反空转）")

print("1.7 万坚金砧贴图/GUI 重做（bg-n10anvil）问题: "
      + str(len(bgn10anvil_problems)) + " " + str(bgn10anvil_problems[:4])
      + "（本段判定 " + str(_bgn10anvil_checked) + " 条）")
if not bgn10anvil_problems:
    print("[bgn10anvil-ok] 模型 21 个面 → 槽/uv/rotation 逐项 == 投影表（ew=前后 / ns=左右，"
          "按 alpha IoU 1.0000 判）/ 5 张源 PNG SHA256 未改 / Screen 三处文字 == 原版 + "
          "输入框与三个精灵全抄 / 红条·装饰·幽灵图标反向断言 0 命中")

'''

rep(ANCHOR, NEW_SECTION + ANCHOR)

rep("                       bgn10up_problems, bgn10fix_problems)",
    "                       bgn10up_problems, bgn10fix_problems, bgn10anvil_problems)")

assert s != orig
open(P, "wb").write(s.encode("utf-8"))
print("validator written", len(s.encode("utf-8")), "B")
