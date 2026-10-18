# -*- coding: utf-8 -*-
"""bgn10err 经验回流：只追加（不删任何行），Python bytes 写盘。"""
import hashlib
import sys
from pathlib import Path

BASE = Path(r"E:\mc\mcmod\mod_experience")

RULE15 = """
### 规则 15 · 原版 GUI 精灵的**不透明灰底**在换色 GUI 上会整块裸露（2026-10-18 bettergold `bg-n10err`）

| 现象 | 根因 | 规则（可执行动作） | 依据 |
|---|---|---|---|
| 换色 GUI（金色万坚金砧）在「无法锻造」时，叉号那块出现一个**灰矩形**；同一个位置在原版铁砧里却什么都看不出来 | 1.21 起 GUI 装饰走精灵图集 `textures/gui/sprites/...`。原版 `container/anvil/error` 是 **28×21、alpha 全 255** 的一张**不透明**图：灰板 `#C6C6C6` **428 px** + 灰箭头 `#8B8B8B` **79 px** + 红叉 81 px。灰板与原版面板**同色**（原版 `anvil.png` 同块 = `#C6C6C6` 482 + `#8B8B8B` 106）⇒ 原版无缝；换色面板一贴上去，灰板直接裸露，还把作者画在同一格的箭头盖成灰 | ① 判「灰是谁画的」必须**打三份像素**：精灵本体 / 原版面板同一矩形 / 作者换色贴图同一矩形（数 `R==G==B` 的像素，别只看精灵）；② 修法优先「**搬运作者同矩形像素 + 只盖精灵里的图案像素**」（本轮 = 507 个作者像素 + 81 个红叉像素，**零新颜色**）；③ **不要**图省事把灰底改透明后直接盖图案——图案会与作者底色撞色（本轮 81 个红叉像素里 **30 个**与底色亮度差 < 25，最小 7）；④ 新精灵**必须**放 `gui/sprites/` 下（放 `gui/container/` 会静默变紫黑格）；⑤ 关卡钉 **SHA256 + 逐像素来源集合 + 反向「灰一个都没搬」** | bettergold `bg-n10err`：`docs\\bgn10err-证据\\01-像素分析\\`（逐像素/直方图/放大对照）、`docs\\1.7-...md` §26 |
"""

SEC334 = """
### 3.34 「像素级修图」类改动的三条验证要点（2026-10-18 bettergold `bg-n10err`）

1. **`NativeImage#getPixelRGBA` 返回的是 ABGR 打包的 int**（RGBA 四个字节按小端读回）：`#D89106` 读出来是 `ff0691d8`。
   探针里按 RGBA 写期望值会**假红**（本轮实测 3 条 FAIL，精灵其实完全正确，改成 ABGR 后 13 PASS / 0 FAIL）。
   ⇒ 写像素断言前**先打印一个已知像素校准**，把字节序写进注释。
2. **校验器要能「逐像素复算来源」，不能只钉 SHA256**：本轮在校验器里放了一个 ~40 行、只用 `zlib` 的 8 位 RGBA PNG 解码器
   （含 Sub/Up/Average/Paeth 全部 filter），于是可以断言「每个像素要么 == 作者同坐标像素、要么 == 原版那两个红值」，
   并数出 `507 + 81 = 588`。这比 SHA 更能证明「没有新颜色 / 没有新美术」；只钉 SHA 的关卡在被"重导出一次"时
   只能报红、说不清哪里变了。
3. **扰动里必须有一条「把来源换回去」**：把 `ERROR_SPRITE` 改回原版那张 ⇒ 灰矩形会回来 ⇒ 关卡必须红。
   本轮 5 个用例：来源换回去红 / 删精灵红 / 只加注释仍绿 / 塞一个灰像素红 / 红叉少一个红；每个用例逐字节复原 + SHA256 自证。
"""

ROWD = "| 2026-10-18 | bettergold | **`bg-n10err`：万坚金砧「无法锻造时的灰矩形」（先诊断 A/B/C/D，再修）** | **指针**：① 「原版看起来正常、换色后露出灰块」的根因 = **原版 GUI 精灵自带不透明灰底**（`container/anvil/error` 28×21、alpha 全 255：`#C6C6C6` 428 + `#8B8B8B` 79 + 红叉 81），灰底与原版面板**同色**才看不见 ⇒ 判「灰是谁画的」要**同时打精灵 / 原版面板 / 作者贴图三份像素** → `ex\\06` **规则 15**（新增）；② 修法 = **搬运作者同矩形像素 + 只盖精灵里的图案像素**（507 + 81 = 588，零新颜色；**不**做「灰底改透明」，因为红叉会与作者深棕箭头撞色）→ 同节；③ `NativeImage#getPixelRGBA` 是 **ABGR 打包**（本轮探针因此假红 3 条）+ 校验器里用**自带 zlib PNG 解码器**钉「逐像素来源」→ `ex\\03` **§3.34**（新增） | **未写**（只对本项目成立）：28×21 的像素统计、作者 `(99,45)-(126,65)` 来源矩形、新精灵 SHA256 `dcbac590…`、`[bgn10err-*]` 22 条判定、5 用例扰动、A 级 17/13 PASS —— 全在 `docs\\1.7-...md` **§26** 与 `docs\\bgn10err-证据\\`（01~08 + 脚本副本）。**删除 0 行** |"

TARGETS = (
    (BASE / "ex" / "06-贴图模型素材.md", RULE15),
    (BASE / "ex" / "03-验证与证据.md", SEC334),
    (BASE / "mcmod_experience.md", ROWD),
)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    for path, chunk in TARGETS:
        raw = path.read_bytes()
        old = raw.decode("utf-8")
        n_old = len(old.splitlines())
        if chunk.strip() and chunk.strip() in old:
            print("[skip] 已存在: %s" % path.name)
            continue
        new = old
        if not new.endswith("\n"):
            new += "\n"
        new += chunk
        nb = new.encode("utf-8")
        path.write_bytes(nb)
        n_new = len(new.splitlines())
        print("[append] %-28s 行数 %d -> %d（新增 %d 行，删除 0 行）SHA %s -> %s"
              % (path.name, n_old, n_new, n_new - n_old,
                 hashlib.sha256(raw).hexdigest()[:16], hashlib.sha256(nb).hexdigest()[:16]))


if __name__ == "__main__":
    main()
