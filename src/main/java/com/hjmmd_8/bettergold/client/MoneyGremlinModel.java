package com.hjmmd_8.bettergold.client;

import com.hjmmd_8.bettergold.bettergold;
import com.hjmmd_8.bettergold.entity.MoneyGremlin;

import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;

/**
 * 金钱妖模型（Blockbench 5.2.1 / 「Modded Entity」导出，作者：异星之尘）。
 *
 * <p>搬 1.21.1 时改了这些（其余 17 个 ModelPart 的几何逐字保留）：
 * ① {@code EntityModel<T>} → {@link HierarchicalModel}（1.21.1 的 {@code KeyframeAnimations.animate}
 * 要求 {@code HierarchicalModel}，并实现 {@code root()}）；
 * ② {@code new ResourceLocation('modid', ...)} → {@code ResourceLocation.fromNamespaceAndPath(...)}；
 * ③ 旧 {@code renderToBuffer(PoseStack, VertexConsumer, int, int, float×4)} 换成 1.21.1 的
 * {@code int color} 签名 —— 这里不再手写，直接用 {@code HierarchicalModel#renderToBuffer}（按 {@code root()} 画）；
 * ④ {@code setupAnim} 从空实现改成「idle / walk 二选一」（裁定 ③b）。</p>
 */
public class MoneyGremlinModel extends HierarchicalModel<MoneyGremlin> {
	// This layer location should be baked with EntityRendererProvider.Context in the entity renderer and passed into this model's constructor
	public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(
            ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "money_gremlin"), "main");
	private final ModelPart all;
	private final ModelPart head;
	private final ModelPart base;
	private final ModelPart misc;
	private final ModelPart A1;
	private final ModelPart A2;
	private final ModelPart eye;
	private final ModelPart body;
	private final ModelPart ring;
	private final ModelPart B1;
	private final ModelPart B2;
	private final ModelPart B3;
	private final ModelPart B4;
	private final ModelPart B5;
	private final ModelPart B6;
	private final ModelPart B7;
	private final ModelPart B8;

	public MoneyGremlinModel(ModelPart root) {
		this.all = root.getChild("all");
		this.head = this.all.getChild("head");
		this.base = this.head.getChild("base");
		this.misc = this.head.getChild("misc");
		this.A1 = this.misc.getChild("A1");
		this.A2 = this.misc.getChild("A2");
		this.eye = this.head.getChild("eye");
		this.body = this.all.getChild("body");
		this.ring = this.body.getChild("ring");
		this.B1 = this.body.getChild("B1");
		this.B2 = this.body.getChild("B2");
		this.B3 = this.body.getChild("B3");
		this.B4 = this.body.getChild("B4");
		this.B5 = this.body.getChild("B5");
		this.B6 = this.body.getChild("B6");
		this.B7 = this.body.getChild("B7");
		this.B8 = this.body.getChild("B8");
	}

	public static LayerDefinition createBodyLayer() {
		MeshDefinition meshdefinition = new MeshDefinition();
		PartDefinition partdefinition = meshdefinition.getRoot();

		PartDefinition all = partdefinition.addOrReplaceChild("all", CubeListBuilder.create(), PartPose.offset(0.0F, 24.0F, 0.0F));

		PartDefinition head = all.addOrReplaceChild("head", CubeListBuilder.create(), PartPose.offset(0.0F, -8.0F, 0.0F));

		PartDefinition base = head.addOrReplaceChild("base", CubeListBuilder.create().texOffs(0, 0).addBox(-7.0F, -4.0F, -2.0F, 14.0F, 4.0F, 4.0F, new CubeDeformation(0.0F))
		.texOffs(0, 8).addBox(-7.0F, -14.0F, -2.0F, 14.0F, 4.0F, 4.0F, new CubeDeformation(0.0F))
		.texOffs(0, 36).addBox(3.0F, -10.0F, -2.0F, 4.0F, 6.0F, 4.0F, new CubeDeformation(0.0F))
		.texOffs(36, 0).addBox(-7.0F, -10.0F, -2.0F, 4.0F, 6.0F, 4.0F, new CubeDeformation(0.0F)), PartPose.offset(0.0F, 0.0F, 0.0F));

		PartDefinition misc = head.addOrReplaceChild("misc", CubeListBuilder.create().texOffs(32, 40).addBox(-0.5F, -4.0F, -2.0F, 1.0F, 4.0F, 4.0F, new CubeDeformation(0.1F))
		.texOffs(42, 40).addBox(-0.5F, -14.0F, -2.0F, 1.0F, 4.0F, 4.0F, new CubeDeformation(0.1F))
		.texOffs(32, 48).addBox(-1.0F, -15.0F, -1.0F, 2.0F, 1.0F, 2.0F, new CubeDeformation(-0.1F))
		.texOffs(48, 36).addBox(-1.0F, 0.0F, -1.0F, 2.0F, 1.0F, 2.0F, new CubeDeformation(-0.1F)), PartPose.offset(0.0F, 0.0F, 0.0F));

		PartDefinition A1 = misc.addOrReplaceChild("A1", CubeListBuilder.create().texOffs(36, 14).addBox(-1.5F, -0.9F, -0.5F, 3.0F, 1.0F, 1.0F, new CubeDeformation(0.0F))
		.texOffs(44, 14).addBox(-1.5F, -3.9F, -0.5F, 3.0F, 1.0F, 1.0F, new CubeDeformation(0.0F))
		.texOffs(46, 48).addBox(-1.5F, -2.9F, -0.5F, 1.0F, 2.0F, 1.0F, new CubeDeformation(0.0F))
		.texOffs(16, 50).addBox(0.5F, -2.9F, -0.5F, 1.0F, 2.0F, 1.0F, new CubeDeformation(0.0F)), PartPose.offsetAndRotation(0.0F, -14.9F, 0.0F, -0.1309F, 0.0F, 0.0F));

		PartDefinition A2 = misc.addOrReplaceChild("A2", CubeListBuilder.create().texOffs(40, 48).addBox(-1.0F, 0.0F, -0.5F, 2.0F, 4.0F, 1.0F, new CubeDeformation(0.0F))
		.texOffs(46, 29).addBox(0.0F, 4.0F, -0.5F, 1.0F, 1.0F, 1.0F, new CubeDeformation(0.0F)), PartPose.offset(0.0F, 0.9F, 0.0F));

		PartDefinition eye = head.addOrReplaceChild("eye", CubeListBuilder.create().texOffs(32, 24).addBox(-3.5F, -10.5F, 0.0F, 7.0F, 7.0F, 0.0F, new CubeDeformation(0.0F)), PartPose.offset(0.0F, 0.0F, 0.0F));

		PartDefinition body = all.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(0.0F, -6.0F, 0.0F));

		PartDefinition ring = body.addOrReplaceChild("ring", CubeListBuilder.create().texOffs(0, 24).addBox(-7.0F, -2.0F, 11.4F, 14.0F, 2.0F, 2.0F, new CubeDeformation(0.0F))
		.texOffs(0, 28).addBox(-7.0F, -2.0F, -13.4F, 14.0F, 2.0F, 2.0F, new CubeDeformation(0.0F)), PartPose.offset(0.0F, 1.0F, 0.0F));

		PartDefinition cube_r1 = ring.addOrReplaceChild("cube_r1", CubeListBuilder.create().texOffs(22, 32).addBox(0.0F, -2.0F, -2.0F, 9.0F, 2.0F, 2.0F, new CubeDeformation(-0.01F)), PartPose.offsetAndRotation(13.4F, 0.0F, -7.0F, 0.0F, 2.3562F, 0.0F));

		PartDefinition cube_r2 = ring.addOrReplaceChild("cube_r2", CubeListBuilder.create().texOffs(32, 20).addBox(-9.0F, -2.0F, -2.0F, 9.0F, 2.0F, 2.0F, new CubeDeformation(-0.01F)), PartPose.offsetAndRotation(-13.4F, 0.0F, -7.0F, 0.0F, -2.3562F, 0.0F));

		PartDefinition cube_r3 = ring.addOrReplaceChild("cube_r3", CubeListBuilder.create().texOffs(32, 16).addBox(-9.0F, -2.0F, 0.0F, 9.0F, 2.0F, 2.0F, new CubeDeformation(-0.01F)), PartPose.offsetAndRotation(-13.4F, 0.0F, 7.0F, 0.0F, 2.3562F, 0.0F));

		PartDefinition cube_r4 = ring.addOrReplaceChild("cube_r4", CubeListBuilder.create().texOffs(0, 32).addBox(0.0F, -2.0F, 0.0F, 9.0F, 2.0F, 2.0F, new CubeDeformation(-0.01F)), PartPose.offsetAndRotation(13.4F, 0.0F, 7.0F, 0.0F, -2.3562F, 0.0F));

		PartDefinition cube_r5 = ring.addOrReplaceChild("cube_r5", CubeListBuilder.create().texOffs(0, 20).addBox(-7.0F, -2.0F, -1.0F, 14.0F, 2.0F, 2.0F, new CubeDeformation(0.0F)), PartPose.offsetAndRotation(12.4F, 0.0F, 0.0F, 0.0F, -1.5708F, 0.0F));

		PartDefinition cube_r6 = ring.addOrReplaceChild("cube_r6", CubeListBuilder.create().texOffs(0, 16).addBox(-7.0F, -2.0F, -1.0F, 14.0F, 2.0F, 2.0F, new CubeDeformation(0.0F)), PartPose.offsetAndRotation(-12.4F, 0.0F, 0.0F, 0.0F, -1.5708F, 0.0F));

		PartDefinition B1 = body.addOrReplaceChild("B1", CubeListBuilder.create().texOffs(36, 10).addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 36).addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(44, 31).addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(0, 46).addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 44).addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)), PartPose.offset(0.0F, 1.1F, -12.4F));

		PartDefinition B2 = body.addOrReplaceChild("B2", CubeListBuilder.create().texOffs(32, 36).addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 40).addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(8, 46).addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(46, 24).addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(24, 44).addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)), PartPose.offsetAndRotation(-9.5F, 1.1F, -9.5F, 0.0F, 0.7854F, 0.0F));

		PartDefinition B3 = body.addOrReplaceChild("B3", CubeListBuilder.create().texOffs(36, 10).addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 36).addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(44, 31).addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(0, 46).addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 44).addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)), PartPose.offset(0.0F, 1.1F, 12.4F));

		PartDefinition B4 = body.addOrReplaceChild("B4", CubeListBuilder.create().texOffs(32, 36).addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 40).addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(8, 46).addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(46, 24).addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(24, 44).addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)), PartPose.offsetAndRotation(-9.5F, 1.1F, 9.5F, 0.0F, -0.7854F, 0.0F));

		PartDefinition B5 = body.addOrReplaceChild("B5", CubeListBuilder.create().texOffs(32, 36).mirror().addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(16, 40).mirror().addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(8, 46).mirror().addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(46, 24).mirror().addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(24, 44).mirror().addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)).mirror(false), PartPose.offsetAndRotation(9.5F, 1.1F, 9.5F, 0.0F, 0.7854F, 0.0F));

		PartDefinition B6 = body.addOrReplaceChild("B6", CubeListBuilder.create().texOffs(32, 36).mirror().addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(16, 40).mirror().addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(8, 46).mirror().addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(46, 24).mirror().addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(24, 44).mirror().addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)).mirror(false), PartPose.offsetAndRotation(9.5F, 1.1F, -9.5F, 0.0F, -0.7854F, 0.0F));

		PartDefinition B7 = body.addOrReplaceChild("B7", CubeListBuilder.create().texOffs(36, 10).addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 36).addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(44, 31).addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(0, 46).addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F))
		.texOffs(16, 44).addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)), PartPose.offsetAndRotation(-12.4F, 1.1F, -0.1F, 0.0F, -1.5708F, 0.0F));

		PartDefinition B8 = body.addOrReplaceChild("B8", CubeListBuilder.create().texOffs(36, 10).mirror().addBox(-3.0F, 0.9F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(16, 36).mirror().addBox(-3.0F, 5.1F, -1.0F, 6.0F, 2.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(44, 31).mirror().addBox(1.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(0, 46).mirror().addBox(-3.0F, 2.5F, -1.0F, 2.0F, 3.0F, 2.0F, new CubeDeformation(-0.2F)).mirror(false)
		.texOffs(16, 44).mirror().addBox(-1.0F, -0.9F, -1.0F, 2.0F, 4.0F, 2.0F, new CubeDeformation(-0.05F)).mirror(false), PartPose.offsetAndRotation(12.4F, 1.1F, -0.1F, 0.0F, 1.5708F, 0.0F));

		return LayerDefinition.create(meshdefinition, 64, 64);
	}

	@Override
	public void setupAnim(MoneyGremlin entity, float limbSwing, float limbSwingAmount,
			float ageInTicks, float netHeadYaw, float headPitch) {
		// 每帧先把骨骼复位：idle / walk 两套动画的骨骼集合相同，切档时不能残留上一套的偏移
		for (ModelPart part : this.all.getAllParts().toList()) {
			part.resetPose();
		}
		// 裁定 ③b：移动 / 追击 ⇒ walk；静止 / 未锁定 ⇒ idle（不造第三套）
		if (limbSwingAmount > 0.05F || entity.getDeltaMovement().horizontalDistanceSqr() > 1.0E-4) {
			this.animateWalk(MoneyGremlinAnimations.WALK, limbSwing, limbSwingAmount, 2.0F, 2.5F);
		} else {
			this.animate(entity.idleAnimationState, MoneyGremlinAnimations.IDLE, ageInTicks);
		}
	}

	@Override
	public ModelPart root() {
		return this.all;
	}
}
