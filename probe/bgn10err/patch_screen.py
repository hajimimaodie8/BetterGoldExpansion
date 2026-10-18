# -*- coding: utf-8 -*-
"""bgn10err: 用 Python bytes 改 SturdygoldAnvilScreen.java（Windows 上不用 PS 改源码）。

三处（每处锚点必须恰好出现 1 次，否则中止、原文件不动）：
  1) 类 javadoc 里的「错误图标」清单行 —— 旧口径原文保留，追加新口径；
  2) 类 javadoc 追加一节「★ 无法锻造时的灰矩形」；
  3) ERROR_SPRITE 常量 —— 换成本模组变体（旧值原文留档在注释里）。

用法: py -3 probe/bgn10err/patch_screen.py [--check]
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREEN = ROOT / "src/main/java/com/hjmmd_8/bettergold/client/SturdygoldAnvilScreen.java"

OLD_ITEM_LINE = (
    " * 错误图标        blitSprite(container/anvil/error, x+99, y+45, 28, 21)</pre>"
)
NEW_ITEM_LINE = (
    " * 错误图标        blitSprite(container/anvil/error, x+99, y+45, 28, 21)   ← 旧口径（bg-n10anvil）\n"
    " *                 bg-n10err 起改成 blitSprite(bettergold:container/sturdygold_anvil/error, x+99, y+45, 28, 21)</pre>"
)

ANCHOR_DOC = (
    " * <p>⇒ 修法 = <b>照原版画 {@code text_field} 精灵 + EditBox</b>，红条被同一位置、同一尺寸的精灵盖住。\n"
    " * <b>没有改任何 PNG 像素</b>（作者素材，SHA256 由关卡钉住）。</p>\n"
)
ADD_DOC = ANCHOR_DOC + (
    " *\n"
    " * <h2>★ 无法锻造时的「灰色矩形」（{@code bg-n10err}，2026-10-18）</h2>\n"
    " * <p>作者原话：「如果『万坚金铁砧』<b>无法锻造</b>时，<b>叉号显示的那一个部分会有一块灰色的矩形区域</b>。\n"
    " * 通常来说这是正常的，但是无法锻造时出现这个问题，看着很别扭」。</p>\n"
    " * <p><b>灰是谁画的（逐像素判定）</b>：是<b>原版精灵自带的</b>，不是作者的图、也不是我们的代码。\n"
    " * 原版 {@code minecraft:container/anvil/error} 是 <b>28×21、alpha 全 255</b> 的一张不透明图，\n"
    " * 只有 4 个颜色：灰底 {@code #C6C6C6} <b>428 px</b> + 灰箭头 {@code #8B8B8B} <b>79 px</b>\n"
    " * + 红叉 {@code #962300} 56 px / {@code #BA370F} 25 px。原版 {@code anvil.png} 同一块是\n"
    " * {@code #C6C6C6} 482 + {@code #8B8B8B} 106 —— 灰底与面板<b>同色</b>，所以在原版里这块矩形\n"
    " * <b>与面板融为一体、看不出来</b>（= 作者说的「通常来说这是正常的」）；换成作者的金色面板后，\n"
    " * 灰底就直接裸露成一个 28×21 的灰色方块，还盖掉了作者画在那一格的深棕色「→」箭头。</p>\n"
    " * <p>作者贴图 {@code (99,45)-(126,65)} 这个 28×21 区域里 <b>R==G==B 的像素 = 0</b>（8 个颜色全是金色系），\n"
    " * 所以<b>不是</b>「作者的灰 + 精灵的灰」叠加。</p>\n"
    " * <p><b>修法（零新美术）</b>：新增精灵 {@code bettergold:container/sturdygold_anvil/error}\n"
    " * （{@code assets/bettergold/textures/gui/sprites/container/sturdygold_anvil/error.png}，28×21，414 B）：\n"
    " * 背景 = 作者 256×256 里 {@code (99,45)-(126,65)} 这 28×21 个像素<b>原样搬运</b>\n"
    " * （含作者自己画的深棕箭头），再把原版那 <b>81 个红叉像素</b>（{@code #962300}/{@code #BA370F}）\n"
    " * 按坐标盖上去。原版的灰底 {@code #C6C6C6} 与灰箭头 {@code #8B8B8B} <b>一个都不搬</b>。\n"
    " * ⇒ 新图 588 个像素里 <b>507 个来自作者贴图、81 个来自原版精灵，没有一个是新颜色</b>；\n"
    " * 作者那张 PNG <b>一个像素都没改</b>（SHA256 由关卡钉住）。位置/尺寸仍与原版一致\n"
    " * （{@code x+99, y+45, 28, 21}），所以只在「无法锻造」时出现的那块灰消失了、<b>叉号照旧</b>。</p>\n"
    " * <p>⚠ 不选「把原版精灵的灰底改成透明」那条路：精灵是灰底/灰箭头/红叉<b>一体</b>的一张不透明图，\n"
    " * 只去掉灰底会把红叉直接压在作者的深棕箭头上、中间那截红色（{@code #962300}）与 {@code #741F00}\n"
    " * 亮度差只有 7，A 级像素比对里 81 个红叉像素中有 30 个亮度差 &lt; 25 ⇒ 反而更难认。</p>\n"
)

OLD_CONST = (
    "    /** 原版砧的三个 GUI 精灵（在 {@code minecraft:gui/sprites} 图集里，blitSprite 用它们是对的） */\n"
    "    private static final ResourceLocation TEXT_FIELD_SPRITE =\n"
    "            ResourceLocation.withDefaultNamespace(\"container/anvil/text_field\");\n"
    "    private static final ResourceLocation TEXT_FIELD_DISABLED_SPRITE =\n"
    "            ResourceLocation.withDefaultNamespace(\"container/anvil/text_field_disabled\");\n"
    "    private static final ResourceLocation ERROR_SPRITE =\n"
    "            ResourceLocation.withDefaultNamespace(\"container/anvil/error\");\n"
)
NEW_CONST = (
    "    /** 原版砧的<b>输入框</b>两个精灵（在 {@code minecraft:gui/sprites} 图集里，blitSprite 用它们是对的） */\n"
    "    private static final ResourceLocation TEXT_FIELD_SPRITE =\n"
    "            ResourceLocation.withDefaultNamespace(\"container/anvil/text_field\");\n"
    "    private static final ResourceLocation TEXT_FIELD_DISABLED_SPRITE =\n"
    "            ResourceLocation.withDefaultNamespace(\"container/anvil/text_field_disabled\");\n"
    "    /**\n"
    "     * <b>错误图标 = 本模组的变体</b>（{@code bg-n10err}，2026-10-18）。\n"
    "     *\n"
    "     * <p>旧口径（bg-n10anvil）用 {@code ResourceLocation.withDefaultNamespace(\"container/anvil/error\")}：\n"
    "     * 原版那张图 28×21 <b>全不透明</b>（灰底 {@code #C6C6C6} 428 px + 灰箭头 {@code #8B8B8B} 79 px\n"
    "     * + 红叉 81 px），盖在作者的金色面板上就是一块<b>灰矩形</b> —— 作者 2026-10-18 报的那条。</p>\n"
    "     *\n"
    "     * <p>现行口径：本模组自己的精灵，28×21，= 作者 256×256 里 {@code (99,45)-(126,65)} 那 28×21 个像素\n"
    "     * <b>原样搬运</b>（含作者画的深棕「→」）+ 只盖原版那 <b>81 个红叉像素</b>；\n"
    "     * 原版灰底与灰箭头<b>一个都不搬</b>。588 = 507（作者）+ 81（原版），<b>零新颜色</b>。</p>\n"
    "     */\n"
    "    private static final ResourceLocation ERROR_SPRITE =\n"
    "            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, \"container/sturdygold_anvil/error\");\n"
)


def patch(text: str) -> str:
    for anchor in (OLD_ITEM_LINE, ANCHOR_DOC, OLD_CONST):
        n = text.count(anchor)
        if n != 1:
            raise SystemExit("锚点出现 %d 次（必须恰好 1 次）：%r" % (n, anchor[:60]))
    text = text.replace(OLD_ITEM_LINE, NEW_ITEM_LINE, 1)
    text = text.replace(ANCHOR_DOC, ADD_DOC, 1)
    text = text.replace(OLD_CONST, NEW_CONST, 1)
    return text


def main():
    check = "--check" in sys.argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    raw = SCREEN.read_bytes()
    src = raw.decode("utf-8")
    before = hashlib.sha256(raw).hexdigest()
    new = patch(src)
    nb = new.encode("utf-8")
    after = hashlib.sha256(nb).hexdigest()
    print("文件 : %s" % SCREEN)
    print("改前 SHA256 = %s（%d B）" % (before, len(raw)))
    print("改后 SHA256 = %s（%d B）" % (after, len(nb)))
    if check:
        same = raw == nb
        print("[check] 已是目标状态: %s" % same)
        return 0 if same else 1
    if raw == nb:
        print("已经是目标状态，未写盘")
        return 0
    SCREEN.write_bytes(nb)
    print("已写盘（bytes）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
