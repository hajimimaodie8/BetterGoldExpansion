#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgfix9：把根因证据收成一份文件（**可复跑**）。

产出：`02-根因取证-源码与判据.txt`
  * A ㊽：`InventoryChangeTrigger` 的两分支（源码逐行）+ 旧/新 JSON 的 `items` 形状 + 生成器调用点
  * B ㊹：`LocationPredicate#matches` 的 `structures` 分支 + 旧/新 JSON 的判据
  * C  ：`BushBlock#mayPlaceOn` / `#canSurvive`、`CropBlock#canSurvive`、两种金染土的 `canSustainPlant`
  * 父链：`PlayerAdvancements#registerListeners` / `#award`（**不看 parent**）+ `AdvancementVisibilityEvaluator`
"""
from __future__ import annotations

import io
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MC = HERE / "_mcsrc"
ADV = REPO / "src/main/resources/data/bettergold/advancement"
OUT = HERE / "02-根因取证-源码与判据.txt"


def read(p: Path) -> str:
    return io.open(p, encoding="utf-8", errors="replace").read()


def lines_of(p: Path, a: int, b: int) -> str:
    src = read(p).split("\n")
    return "\n".join(f"{i+1:>5}: {src[i]}" for i in range(a - 1, min(b, len(src))))


def block(title: str) -> str:
    return f"\n{'=' * 100}\n{title}\n{'=' * 100}\n"


def main() -> int:
    o: list[str] = []
    o.append("bgfix9 根因取证（源码逐行 + 产物判据逐字 + 生成器调用点）")
    o.append("源码出处：build/moddev/artifacts/neoforge-21.1.228-sources.jar（探针解包副本在 probe/bgfix9/_mcsrc/）")

    o.append(block("A ㊽ treasure/any_raw_metal「齐活，烧炼，拿下！」—— 判据形状"))
    o.append("【源码】InventoryChangeTrigger.TriggerInstance#matches：items.size()==1 只比『变化的那一格』；"
             "!=1 扫全背包逐条都要命中（= AND）\n")
    o.append(lines_of(MC / "net_minecraft_advancements_critereon_InventoryChangeTrigger.java", 86, 110))
    for tag, p in (("改前（历史副本）", HERE / "_adv-before/treasure/any_raw_metal.json"),
                   ("改后（现行产物）", ADV / "treasure/any_raw_metal.json")):
        o.append(f"\n---- {tag}：{p.relative_to(REPO)} ----")
        o.append(read(p).rstrip())
    o.append("\n---- 对照：同类『任意一种』的另一条（一直是 1 条谓词 + 数组 = OR）----")
    o.append(read(ADV / "treasure/any_core_material.json").rstrip())
    o.append("\n---- 生成器调用点（唯一真源）----")
    gen = read(REPO / "tools/asset-generator/generate_advancements.py").split("\n")
    for i, ln in enumerate(gen, 1):
        if "c_inv(RAW_MATERIALS)" in ln or "c_inv([RAW_MATERIALS])" in ln:
            o.append(f"{i:>5}: {ln}")
    o.append("（去注释后现行代码里必须只剩 `c_inv([RAW_MATERIALS])`；"
             "旧形状 `c_inv(RAW_MATERIALS)` 只许出现在注释里 —— 关卡 [bgfix9-generator-raw-metal] 守着）")

    o.append(block("B ㊹ agriculture/eggplant_seeds「光辉岁月之种」—— 结构条件"))
    o.append("【源码】LocationPredicate#matches：structures 必须命中『该位置的结构部件』"
             "（getStructureWithPieceAt(...).isValid()，第 54 行）\n")
    o.append(lines_of(MC / "net_minecraft_advancements_critereon_LocationPredicate.java", 45, 60))
    o.append("\n【源码】TriggerInstance 的 player 字段类型 = EntityPredicate.ADVANCEMENT_CODEC"
             "（= 位置/结构条件挂在『玩家』这一侧）\n")
    o.append(lines_of(MC / "net_minecraft_advancements_critereon_InventoryChangeTrigger.java", 50, 61))
    for tag, p in (("改前（历史副本）", HERE / "_adv-before/agriculture/eggplant_seeds.json"),
                   ("改后（现行产物）", ADV / "agriculture/eggplant_seeds.json")):
        o.append(f"\n---- {tag}：{p.relative_to(REPO)} ----")
        o.append(read(p).rstrip())
    o.append("\n---- 种子来源（与『结构条件』不一致的那一条）----")
    o.append(lines_of(REPO / "src/main/java/com/hjmmd_8/bettergold/registry/AllLootModifiers.java", 56, 63))

    o.append(block("C 金玫瑰丛 × 金染土 —— 存活判据链"))
    o.append("【源码】BushBlock#mayPlaceOn（22-24）与 #canSurvive（38-45）：先问下方方块的 canSustainPlant，"
             "不是 DEFAULT 就以它为准\n")
    o.append(lines_of(MC / "net_minecraft_world_level_block_BushBlock.java", 22, 45))
    o.append("\n【源码】CropBlock#canSurvive（163-168）：**普通作物也先看 canSustainPlant** ⇒ "
             "若金染土恒 TRUE，作物就能绕过 GoldCropBlock#mayPlaceOn 直接种在金染土上\n")
    o.append(lines_of(MC / "net_minecraft_world_level_block_CropBlock.java", 163, 168))
    o.append("\n---- 金染耕地（既有口径 = 恒 TRUE）----")
    o.append(lines_of(REPO / "src/main/java/com/hjmmd_8/bettergold/block/GoldInfusedFarmlandBlock.java", 50, 56))
    o.append("\n---- 金染土（bgfix9 现行 = 只放行金玫瑰丛）----")
    o.append(lines_of(REPO / "src/main/java/com/hjmmd_8/bettergold/block/GoldInfusedDirtBlock.java", 61, 68))
    o.append("\n---- 注册点（AllBlocks）----")
    o.append(lines_of(REPO / "src/main/java/com/hjmmd_8/bettergold/registry/AllBlocks.java", 188, 206))
    o.append("\n---- 金玫瑰丛注册（TallFlowerBlock，属性照抄原版玫瑰丛）----")
    o.append(lines_of(REPO / "src/main/java/com/hjmmd_8/bettergold/registry/AllBlocks.java", 131, 135))

    o.append(block("父链两态：`PlayerAdvancements` **不看 parent**"))
    o.append("【源码】`registerListeners(ServerAdvancementManager)` 对**全部**成就注册判据监听（97-101）\n")
    o.append(lines_of(MC / "net_minecraft_server_PlayerAdvancements.java", 97, 101))
    o.append("\n【源码】`award(...)`（168-195）：**没有任何 parent 判定**（只有 FakePlayer 早退 + 判据授予 + 奖励）\n")
    o.append(lines_of(MC / "net_minecraft_server_PlayerAdvancements.java", 168, 195))
    o.append("\n【源码】`AdvancementVisibilityEvaluator`：`flag1 = flag`（本节点已达成）⇒ "
             "**已达成的节点一定 visible**；未达成的才看父链（40-59）\n")
    o.append(lines_of(MC / "net_minecraft_server_advancements_AdvancementVisibilityEvaluator.java", 40, 59))

    OUT.write_text("\n".join(o) + "\n", encoding="utf-8", newline="\n")
    print(f"写出 {OUT.relative_to(REPO)}：{len(o)} 段 / {OUT.stat().st_size} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
