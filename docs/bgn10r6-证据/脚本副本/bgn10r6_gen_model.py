# -*- coding: utf-8 -*-
"""把归档的 Blockbench 导出（1.17/1.19 旧 API）搬到 1.21.1 原版 API。

只读 `docs/新约10-素材清单/金钱妖/*.java`，新文件写到 src。
所有读写走 bytes（UTF-8，无 BOM，CRLF），不碰归档副本。
"""
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "新约10-素材清单" / "金钱妖"
OUT = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "client"

MODEL_IN = SRC / "money_gremlin.java"
ANIM_IN = SRC / "money_gremlin.animation.java"


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    path.write_bytes(data)


def gen_model() -> str:
    text = read_text(MODEL_IN)
    # 去掉旧文件头两行（导出器注释保留为类注释），从 public class 开始
    idx = text.index("public class money_gremlin")
    body = text[idx:]

    body = body.replace(
        "public class money_gremlin<T extends Entity> extends EntityModel<T> {",
        "public class MoneyGremlinModel extends HierarchicalModel<MoneyGremlin> {",
    )
    body = body.replace(
        'public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(new ResourceLocation("modid", "money_gremlin"), "main");',
        "public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(\n"
        "            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, \"money_gremlin\"), \"main\");",
    )
    body = body.replace("public money_gremlin(ModelPart root) {", "public MoneyGremlinModel(ModelPart root) {")

    # 1.21.1 的 setupAnim：HierarchicalModel + AnimationState / KeyframeAnimations
    old_setup = body[body.index("\t@Override\n\tpublic void setupAnim("): body.index("\t@Override\n\tpublic void renderToBuffer(")]
    new_setup = (
        "\t@Override\n"
        "\tpublic void setupAnim(MoneyGremlin entity, float limbSwing, float limbSwingAmount,\n"
        "\t\t\tfloat ageInTicks, float netHeadYaw, float headPitch) {\n"
        "\t\t// 每帧先把骨骼复位：idle / walk 两套动画的骨骼集合相同，切档时不能残留上一套的偏移\n"
        "\t\tfor (ModelPart part : this.all.getAllParts().toList()) {\n"
        "\t\t\tpart.resetPose();\n"
        "\t\t}\n"
        "\t\t// 裁定 ③b：移动 / 追击 ⇒ walk；静止 / 未锁定 ⇒ idle（不造第三套）\n"
        "\t\tif (limbSwingAmount > 0.05F || entity.getDeltaMovement().horizontalDistanceSqr() > 1.0E-4) {\n"
        "\t\t\tthis.animateWalk(MoneyGremlinAnimations.WALK, limbSwing, limbSwingAmount, 2.0F, 2.5F);\n"
        "\t\t} else {\n"
        "\t\t\tthis.animate(entity.idleAnimationState, MoneyGremlinAnimations.IDLE, ageInTicks);\n"
        "\t\t}\n"
        "\t}\n\n"
        "\t@Override\n"
        "\tpublic ModelPart root() {\n"
        "\t\treturn this.all;\n"
        "\t}\n"
    )
    body = body.replace(old_setup, new_setup)

    # 旧 renderToBuffer（float 颜色版）整块删掉：HierarchicalModel 已经按 root() 渲染
    old_render = body[body.index("\t@Override\n\tpublic void renderToBuffer("):]
    body = body.replace(old_render, "}\n")

    # 去掉开头可能残留的空白行
    body = body.lstrip("\r\n")

    header = (
        "package com.hjmmd_8.bettergold.client;\n"
        "\n"
        "import com.hjmmd_8.bettergold.bettergold;\n"
        "import com.hjmmd_8.bettergold.entity.MoneyGremlin;\n"
        "\n"
        "import net.minecraft.client.model.HierarchicalModel;\n"
        "import net.minecraft.client.model.geom.ModelLayerLocation;\n"
        "import net.minecraft.client.model.geom.ModelPart;\n"
        "import net.minecraft.client.model.geom.PartPose;\n"
        "import net.minecraft.client.model.geom.builders.CubeDeformation;\n"
        "import net.minecraft.client.model.geom.builders.CubeListBuilder;\n"
        "import net.minecraft.client.model.geom.builders.LayerDefinition;\n"
        "import net.minecraft.client.model.geom.builders.MeshDefinition;\n"
        "import net.minecraft.client.model.geom.builders.PartDefinition;\n"
        "import net.minecraft.resources.ResourceLocation;\n"
        "\n"
        "/**\n"
        " * 金钱妖模型（Blockbench 5.2.1 / 「Modded Entity」导出，作者：异星之尘）。\n"
        " *\n"
        " * <p>搬 1.21.1 时改了这些（其余 17 个 ModelPart 的几何逐字保留）：\n"
        " * ① {@code EntityModel<T>} → {@link HierarchicalModel}（1.21.1 的 {@code KeyframeAnimations.animate}\n"
        " * 要求 {@code HierarchicalModel}，并实现 {@code root()}）；\n"
        " * ② {@code new ResourceLocation('modid', ...)} → {@code ResourceLocation.fromNamespaceAndPath(...)}；\n"
        " * ③ 旧 {@code renderToBuffer(PoseStack, VertexConsumer, int, int, float×4)} 换成 1.21.1 的\n"
        " * {@code int color} 签名 —— 这里不再手写，直接用 {@code HierarchicalModel#renderToBuffer}（按 {@code root()} 画）；\n"
        " * ④ {@code setupAnim} 从空实现改成「idle / walk 二选一」（裁定 ③b）。</p>\n"
        " */\n"
    )
    return header + body


def gen_animations() -> str:
    text = read_text(ANIM_IN)
    idx = text.index("public class money_gremlinAnimation")
    body = text[idx:]
    body = body.replace("public class money_gremlinAnimation {", "public final class MoneyGremlinAnimations {")
    body = body.replace("public static final AnimationDefinition idle", "public static final AnimationDefinition IDLE")
    body = body.replace("public static final AnimationDefinition walk", "public static final AnimationDefinition WALK")
    body = body.rstrip()
    assert body.endswith("}")
    body = body[:-1].rstrip() + "\n\n\tprivate MoneyGremlinAnimations() {\n\t}\n}\n"

    header = (
        "package com.hjmmd_8.bettergold.client;\n"
        "\n"
        "import net.minecraft.client.animation.AnimationChannel;\n"
        "import net.minecraft.client.animation.AnimationDefinition;\n"
        "import net.minecraft.client.animation.Keyframe;\n"
        "import net.minecraft.client.animation.KeyframeAnimations;\n"
        "\n"
        "/**\n"
        " * 金钱妖的两套动画（Blockbench 导出，**逐帧数值一个没改**）：\n"
        " * {@link #IDLE}（2.5 s，looping）与 {@link #WALK}（1.5 s，looping）。\n"
        " *\n"
        " * <p>1.21.1 的 API 与 1.19 导出件的唯一差别是类名 / 常量名；\n"
        " * {@code AnimationDefinition.Builder} / {@code AnimationChannel} / {@code Keyframe} /\n"
        " * {@code KeyframeAnimations.degreeVec|posVec|scaleVec} 在 1.21.1 逐字相同（1.21.1 sources 核对）。</p>\n"
        " */\n"
    )
    return header + body


model_out = OUT / "MoneyGremlinModel.java"
anim_out = OUT / "MoneyGremlinAnimations.java"
write_text(model_out, gen_model())
write_text(anim_out, gen_animations())
print("[gen] wrote", model_out.relative_to(REPO), model_out.stat().st_size, "B")
print("[gen] wrote", anim_out.relative_to(REPO), anim_out.stat().st_size, "B")
