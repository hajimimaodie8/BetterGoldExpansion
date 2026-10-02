#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1.5 武器轮资产生成器 —— 从作者的 `更有用的金 新约8.zip` 生成五类武器的贴图 / 模型。

用法:
    python generate_weapon_assets.py --zip "E:\\mc\\mc资料\\更有用的金 新约8.zip"            # 演练
    python generate_weapon_assets.py --zip "E:\\mc\\mc资料\\更有用的金 新约8.zip" --apply    # 写入

作者本轮的澄清：
  1. **盾牌没有独立的 16×16 物品图标是正常的**：原版盾牌的物品外观就是「物品模型引用实体贴图」
     （`item/shield.json` 的 parent 是 `builtin/entity`，由 BlockEntityWithoutLevelRenderer
      用 64×64 的 `entity/shield_base_nopattern.png` 画 3D 模型）。本模组照搬同一做法：
      金属盾牌的 64×64 贴图放 `textures/entity/shield_<金属>.png`，配自定义渲染器。
  2. **模型 JSON 一律照搬原版对应物品的结构**，只替换贴图引用与必要的 override
     （弓 pulling_0/1/2、弩 pulling_*/charged/arrow/firework、三叉戟 throwing、盾牌 blocking）。
  3. **命名笔误**：`重锤/黄制重锤胚底.png` = 「金制重锤胚底」；
     `弓/巫毒金3.png` = 缺「弓」字的「巫毒金弓3.png」。
  4. **1.5 修正轮（关键）**：5 张「胚底」贴图**不是武器**。作者原话：
     「那只是胚底，纯用于合成用的！……它没有实际用途，根本就没有相应的金制器具……
      没有金制系列工具！！！！」
     所以它们只生成「一张 16×16 贴图 + 一个最普通的 `minecraft:item/generated` 单层模型」，
     **不生成**拉弓 / 蓄力 / 投掷 / 格挡变体，也**不生成** `entity/*` 贴图。
     上一轮把它们当金制武器做的那 21 个模型与 8 张帧贴图已整批撤掉。

四类真实素材缺口（不是笔误，报告里单独列）：
  * 弓箭 / 弩箭的拉弓帧、弩的箭与烟花帧：六套金属的素材里有，逐张对应；
  * 六套金属盾牌只有 64×64 实体贴图（物品形态走 entity 渲染器，与原版一致）；
  * 六套金属三叉戟的 32×32 投掷实体贴图在 `三叉戟/<金属>三叉戟2.png`；
  * 弓的 `巫毒金3.png` 缺「弓」字 → 回退到 `巫毒金弓3.png`。

命名口径（本脚本里 **wid = 武器 id 前缀**：六套金属是 `<金属>`；
五件胚底的完整 id 是 `golden_<武器>_blank`）：
    物品贴图  textures/item/<wid>_mace.png / _bow.png / _bow_pulling_0..2.png /
              _crossbow.png / _crossbow_pulling_0..2.png / _crossbow_arrow.png /
              _crossbow_firework.png / _trident.png
    实体贴图  textures/entity/shield_<wid>.png（64×64）/ trident_<wid>.png（32×32）
    物品模型  models/item/<wid>_mace.json 等，layer0 指向 bettergold:item/<wid>_...
    胚底贴图  textures/item/golden_<武器>_blank.png（16×16）
    胚底模型  models/item/golden_<武器>_blank.json（parent = minecraft:item/generated，无 override）
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "src" / "main" / "resources" / "assets" / "bettergold"

METALS = {
    "烈燃金": "flamegold",
    "巫毒金": "voodoogold",
    "结雷金": "thundergold",
    "靛海金": "indigoseagold",
    "幻惑金": "illusiongold",
    "万坚金": "sturdygold",
}

# 胚底 id 后缀（物品 id = golden_<武器>_blank）
BLANK_SUFFIX = "_blank"

# 「胚底」贴图（作者的命名，含已知笔误）-> 武器后缀
# 完整物品路径 = f"golden_{后缀}{BLANK_SUFFIX}"，例如 golden_mace_blank
BLANK_TEXTURES = {
    "重锤/黄制重锤胚底.png": "mace",          # 笔误：黄制 = 金制
    "弓/金制弓箭胚底.png": "bow",
    "弩/金制弩胚底.png": "crossbow",
    "三叉戟/金制三叉戟胚底.png": "trident",
    "盾牌/金制盾牌胚底.png": "shield",
}

TEX_ITEM = "textures/item"
TEX_ENTITY = "textures/entity"
MODELS_ITEM = "models/item"

problems: list[str] = []
written: list[str] = []


def fail(msg: str) -> None:
    print(f"[错误] {msg}")
    sys.exit(1)


def decode_name(info: zipfile.ZipInfo) -> str:
    """zip 里中文名是 GBK 编的，zipfile 按 cp437 解，这里还原。"""
    try:
        return info.filename.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


def read_zip(zip_path: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.filename.lower().endswith(".png"):
                out[decode_name(info)] = z.read(info)
    return out


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("不是 PNG")
    return struct.unpack(">II", data[16:24])


def j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


# ==================== 模型 JSON（照搬原版结构，只换贴图引用） ====================
# wid 例子：flamegold / sturdygold / indigoseagold

def mace_model(wid: str) -> str:
    """原版 models/item/mace.json：parent = item/handheld_mace，一层 layer0"""
    return j({
        "parent": "minecraft:item/handheld_mace",
        "textures": {"layer0": f"bettergold:item/{wid}_mace"},
    })


def bow_models(wid: str) -> dict[str, str]:
    """原版 models/item/bow.json：pulling 1 起步，pull 0.65 / 0.9 换到第 1 / 2 帧"""
    base = {
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"bettergold:item/{wid}_bow"},
        "display": {
            "thirdperson_righthand": {"rotation": [-80, 260, -40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
            "thirdperson_lefthand": {"rotation": [-80, -280, 40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
            "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
            "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        },
        "overrides": [
            {"predicate": {"pulling": 1}, "model": f"bettergold:item/{wid}_bow_pulling_0"},
            {"predicate": {"pulling": 1, "pull": 0.65}, "model": f"bettergold:item/{wid}_bow_pulling_1"},
            {"predicate": {"pulling": 1, "pull": 0.9}, "model": f"bettergold:item/{wid}_bow_pulling_2"},
        ],
    }
    out = {f"{wid}_bow.json": j(base)}
    for i in range(3):
        out[f"{wid}_bow_pulling_{i}.json"] = j({
            "parent": f"bettergold:item/{wid}_bow",
            "textures": {"layer0": f"bettergold:item/{wid}_bow_pulling_{i}"},
        })
    return out


def crossbow_models(wid: str) -> dict[str, str]:
    """原版 models/item/crossbow.json：pulling 1 / pull 0.58 / pull 1.0，charged→arrow、charged+firework"""
    base = {
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"bettergold:item/{wid}_crossbow"},
        "display": {
            "thirdperson_righthand": {"rotation": [-90, 0, -60], "translation": [2, 0.1, -3], "scale": [0.9, 0.9, 0.9]},
            "thirdperson_lefthand": {"rotation": [-90, 0, 30], "translation": [2, 0.1, -3], "scale": [0.9, 0.9, 0.9]},
            "firstperson_righthand": {"rotation": [-90, 0, -55], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
            "firstperson_lefthand": {"rotation": [-90, 0, 35], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        },
        "overrides": [
            {"predicate": {"pulling": 1}, "model": f"bettergold:item/{wid}_crossbow_pulling_0"},
            {"predicate": {"pulling": 1, "pull": 0.58}, "model": f"bettergold:item/{wid}_crossbow_pulling_1"},
            {"predicate": {"pulling": 1, "pull": 1.0}, "model": f"bettergold:item/{wid}_crossbow_pulling_2"},
            {"predicate": {"charged": 1}, "model": f"bettergold:item/{wid}_crossbow_arrow"},
            {"predicate": {"charged": 1, "firework": 1}, "model": f"bettergold:item/{wid}_crossbow_firework"},
        ],
    }
    out = {f"{wid}_crossbow.json": j(base)}
    for i in range(3):
        out[f"{wid}_crossbow_pulling_{i}.json"] = j({
            "parent": f"bettergold:item/{wid}_crossbow",
            "textures": {"layer0": f"bettergold:item/{wid}_crossbow_pulling_{i}"},
        })
    for kind in ("arrow", "firework"):
        out[f"{wid}_crossbow_{kind}.json"] = j({
            "parent": f"bettergold:item/{wid}_crossbow",
            "textures": {"layer0": f"bettergold:item/{wid}_crossbow_{kind}"},
        })
    return out


def trident_models(wid: str) -> dict[str, str]:
    """
    三叉戟**按原版 1:1 落成三个模型**（bg-15w 续工轮 §7.1，作者裁定 Mixin 3D）。

    原版资产（client jar `assets/minecraft/models/item/`）逐字对照：

      `trident.json`          平面 `item/generated`，**没有 overrides**
      `trident_in_hand.json`  `builtin/entity` + display + **`overrides: throwing -> trident_throwing`**
      `trident_throwing.json` `builtin/entity` + 蓄力（第三/第一人称）姿态 display

    为什么必须是三个（上一轮这里是两个、且把 throwing 姿态写在了 `_trident_in_hand` 上）：
    验收要求「物品栏图标 / 手持第一人称 / 第三人称 / 掉在地上 / 展示框 / **蓄力投掷中**」
    六种情形都与原版一致 —— 缺 `_trident_throwing` 那一档时，蓄力时的第三人称姿态就不一样了
    （原版正常持握 `thirdperson_*` 是 `[0,60,0]`，蓄力时是 `[0,90,180]`）。
    平面那一份的 overrides 也交还给 `_trident_in_hand`（与原版同构），
    由 `client/ItemRendererTridentMixin` 负责「拿在手里走 3D、GUI/地上/展示框走平面」。
    """
    particle = f"bettergold:item/{wid}_trident"
    flat = {
        "parent": "minecraft:item/generated",
        "textures": {"layer0": particle},
    }
    in_hand_display = {
        "thirdperson_righthand": {"rotation": [0, 60, 0], "translation": [11, 17, -2], "scale": [1, 1, 1]},
        "thirdperson_lefthand": {"rotation": [0, 60, 0], "translation": [3, 17, 12], "scale": [1, 1, 1]},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [-3, 17, 1], "scale": [1, 1, 1]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [13, 17, 1], "scale": [1, 1, 1]},
        "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
        "fixed": {"rotation": [0, 180, 0], "translation": [-2, 4, -5], "scale": [0.5, 0.5, 0.5]},
        "ground": {"rotation": [0, 0, 0], "translation": [4, 4, 2], "scale": [0.25, 0.25, 0.25]},
    }
    throwing_display = {
        "thirdperson_righthand": {"rotation": [0, 90, 180], "translation": [8, -17, 9], "scale": [1, 1, 1]},
        "thirdperson_lefthand": {"rotation": [0, 90, 180], "translation": [8, -17, -7], "scale": [1, 1, 1]},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [-3, 17, 1], "scale": [1, 1, 1]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [13, 17, 1], "scale": [1, 1, 1]},
        "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
        "fixed": {"rotation": [0, 180, 0], "translation": [-2, 4, -5], "scale": [0.5, 0.5, 0.5]},
        "ground": {"rotation": [0, 0, 0], "translation": [4, 4, 2], "scale": [0.25, 0.25, 0.25]},
    }
    in_hand = {
        "parent": "builtin/entity",
        "gui_light": "front",
        "textures": {"particle": particle},
        "display": in_hand_display,
        "overrides": [
            {"predicate": {"throwing": 1}, "model": f"bettergold:item/{wid}_trident_throwing"},
        ],
    }
    throwing = {
        "parent": "builtin/entity",
        "gui_light": "front",
        "textures": {"particle": particle},
        "display": throwing_display,
    }
    return {
        f"{wid}_trident.json": j(flat),
        f"{wid}_trident_in_hand.json": j(in_hand),
        f"{wid}_trident_throwing.json": j(throwing),
    }


def shield_models(wid: str) -> dict[str, str]:
    """
    原版 models/item/shield.json + shield_blocking.json：parent = builtin/entity，
    blocking:1 换到 <wid>_shield_blocking。

    `particle` 用**原版**的 `minecraft:block/dark_oak_planks`（与 vanilla `item/shield.json`
    逐字一致）。这是实测教训：一开始写成我们的 `bettergold:entity/shield_<wid>`，
    客户端会刷 7 条
    `Missing textures in model bettergold:<金属>_shield#inventory:
     minecraft:textures/atlas/blocks.png:bettergold:entity/shield_<金属>`
    —— `particle` 走的是**方块图集**（blocks.png），而实体贴图不在图集里；
    换回原版的方块粒子既消掉告警、又与 vanilla 观感一致。
    """
    normal = {
        "parent": "builtin/entity",
        "gui_light": "front",
        "textures": {"particle": "minecraft:block/dark_oak_planks"},
        "display": {
            "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
            "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
            "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25, 1.25, 1.25]},
            "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25, 1.25, 1.25]},
            "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
            "fixed": {"rotation": [0, 180, 0], "translation": [-4.5, 4.5, -5], "scale": [0.55, 0.55, 0.55]},
            "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25, 0.25, 0.25]},
        },
        "overrides": [
            {"predicate": {"blocking": 1}, "model": f"bettergold:item/{wid}_shield_blocking"},
        ],
    }
    blocking = {
        "parent": "builtin/entity",
        "gui_light": "front",
        "textures": {"particle": "minecraft:block/dark_oak_planks"},
        "display": {
            "thirdperson_righthand": {"rotation": [45, 155, 0], "translation": [-3.49, 11, -2], "scale": [1, 1, 1]},
            "thirdperson_lefthand": {"rotation": [45, 155, 0], "translation": [11.51, 7, 2.5], "scale": [1, 1, 1]},
            "firstperson_righthand": {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25, 1.25, 1.25]},
            "firstperson_lefthand": {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25, 1.25, 1.25]},
            "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
        },
    }
    return {
        f"{wid}_shield.json": j(normal),
        f"{wid}_shield_blocking.json": j(blocking),
    }


def weapon_models(wid: str) -> dict[str, str]:
    """一个金属 wid 对应的全部物品模型（15 个）"""
    out: dict[str, str] = {f"{wid}_mace.json": mace_model(wid)}
    out.update(bow_models(wid))
    out.update(crossbow_models(wid))
    out.update(trident_models(wid))
    out.update(shield_models(wid))
    return out


def blank_model(blank_id: str) -> str:
    """胚底：最普通的单层物品模型（**没有任何 override**，它不是武器）"""
    return j({
        "parent": "minecraft:item/generated",
        "textures": {"layer0": f"bettergold:item/{blank_id}"},
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    zip_path = Path(args.zip)
    if not zip_path.is_file():
        fail(f"找不到压缩包 {zip_path}")
    textures = read_zip(zip_path)

    def write(rel: str, data: bytes | str) -> None:
        written.append(rel)
        if not args.apply:
            return
        target = ASSETS / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            target.write_text(data, encoding="utf-8", newline="\n")
        else:
            target.write_bytes(data)

    def tex(src: str, rel: str, expect: tuple[int, int] | None = None,
            fallback: str | None = None) -> bytes | None:
        if src not in textures:
            if fallback is not None and fallback in textures:
                problems.append(f"素材缺失，已按作者笔误回退到 {fallback}: {src}")
                src = fallback
            else:
                problems.append(f"素材缺失且无回退: {src}")
                return None
        data = textures[src]
        if expect is not None and png_size(data) != expect:
            got = png_size(data)
            problems.append(f"尺寸不符: {src} = {got[0]}x{got[1]}，期望 {expect[0]}x{expect[1]}")
            return None
        write(rel, data)
        return data

    # ---------- 六套金属 ----------
    for cn, wid in METALS.items():
        tex(f"重锤/{cn}重锤.png", f"{TEX_ITEM}/{wid}_mace.png", (16, 16))

        tex(f"弓/{cn}弓.png", f"{TEX_ITEM}/{wid}_bow.png", (16, 16))
        for i in range(3):
            # 命名笔误兜底：`弓/巫毒金3.png` 应为 `弓/巫毒金弓3.png`
            tex(f"弓/{cn}弓{i + 1}.png", f"{TEX_ITEM}/{wid}_bow_pulling_{i}.png", (16, 16),
                fallback=f"弓/{cn}{i + 1}.png")

        tex(f"弩/{cn}弩.png", f"{TEX_ITEM}/{wid}_crossbow.png", (16, 16))
        for i in range(3):
            tex(f"弩/{cn}弩{i + 1}.png", f"{TEX_ITEM}/{wid}_crossbow_pulling_{i}.png", (16, 16))
        tex(f"弩/{cn}弩4.png", f"{TEX_ITEM}/{wid}_crossbow_arrow.png", (16, 16))
        tex(f"弩/{cn}弩5.png", f"{TEX_ITEM}/{wid}_crossbow_firework.png", (16, 16))

        tex(f"三叉戟/{cn}三叉戟.png", f"{TEX_ITEM}/{wid}_trident.png", (16, 16))
        tex(f"三叉戟/{cn}三叉戟2.png", f"{TEX_ENTITY}/trident_{wid}.png", (32, 32))

        tex(f"盾牌/{cn}盾牌.png", f"{TEX_ENTITY}/shield_{wid}.png", (64, 64))

        for name, text in weapon_models(wid).items():
            write(f"{MODELS_ITEM}/{name}", text)

    # ---------- 五件「胚底」（纯合成中间物：一张 16×16 贴图 + 一个最简单的模型） ----------
    for src, weapon in BLANK_TEXTURES.items():
        blank_id = f"golden_{weapon}{BLANK_SUFFIX}"
        tex(src, f"{TEX_ITEM}/{blank_id}.png", (16, 16))
        write(f"{MODELS_ITEM}/{blank_id}.json", blank_model(blank_id))

    print(f"{'已写入' if args.apply else '演练（未写入）'}: {len(written)} 个文件")
    if problems:
        print(f"[提示] {len(problems)} 条:")
        for p in problems:
            print("   ", p)
    else:
        print("全部素材与模板均已匹配。")

    # 自检：胚底不许有 override，也不许生成 entity 贴图
    for weapon in BLANK_TEXTURES.values():
        blank_id = f"golden_{weapon}{BLANK_SUFFIX}"
        model = json.loads(blank_model(blank_id))
        if model.get("overrides"):
            fail(f"胚底模型不该有 override: {blank_id}")
        if (ASSETS / f"{TEX_ENTITY}/shield_golden.png").exists() if args.apply else False:
            fail("残留 entity/shield_golden.png（金制武器已撤）")


if __name__ == "__main__":
    main()
