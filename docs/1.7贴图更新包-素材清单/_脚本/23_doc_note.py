# -*- coding: utf-8 -*-
"""给 docs/1.7-贴图更新包翻新.md 追加 §4.1「并发会话下的读数时间线」（只追加）。"""
import sys, os
sys.stdout.reconfigure(errors="replace")

DOC = r"E:\mc\mcmod\bettergold-template-1.21.1\docs\1.7-贴图更新包翻新.md"

NOTE = """
### §4.1 并发会话下的读数时间线（必须一起读）

本轮**不是独占工作树**：开工时 `git status` 就有另一个会话（`bg-n10rc` 配方）的未提交改动，
它在**本轮工作期间**自行提交（HEAD `f9e60eb` → `7680845`），随后又继续改 Java。
因此"七关卡全绿"是**某一时刻**的读数，必须连时间线一起报：

| 时刻 | 事件 | 七关卡读数 |
|---|---|---|
| 20:19 | 开局 HEAD `f9e60eb`，工作树有别人 3 个 `M` + 若干 `??`（**我只读，未碰**） | — |
| 20:36:43 | 对方自行提交 `7680845`（HEAD 前移） | — |
| 20:41–20:44 | 我做 A 级探针两轮 + `build` | 20:44 首跑：**7/7 exit 0** |
| 20:45:28 / 20:45:38 | **对方**改 `RawSturdygoldRecipe.java`（催化剂改为可配置字段，`+48/-5`） | — |
| ~20:47 | 我复跑七关卡（反映当前树） | `validate_metal_data.py` **exit 1**，唯一问题 = `RawSturdygoldRecipe 不再对 alchemic_fuel 的 glass_bottle`（对方那次保存的中间态：`ALCHEMIC_FUEL` 一度只在注释里） |
| 20:48 起 | 对方第二次保存，文件恢复 | 收尾最终跑：**7/7 exit 0** |

**结论**：那条瞬时红**与贴图无关**——`validate_metal_data.py` 的 `bg9-2` 断言读的是
`src/main/java/.../recipe/RawSturdygoldRecipe.java`（第 699–702 行，`strip_comments` 后要求
`GLASS_BOTTLE` 与 `ALCHEMIC_FUEL` 同时出现），而本轮我只改了 72 个 `.png`。
⚠ **我没有改那个 Java 文件、也没有改 `validate_metal_data.py`**（它当时正是对方 `M` 的文件之一）。

**给后来的接手者一条提醒**：在有别的会话并发改源码时，
「关卡全绿」必须写成**时间点 + 当时的 `git status`**，否则下一个人复跑可能看到红而误以为是贴图的问题。
"""


def main():
    b = open(DOC, "rb").read()
    t = b.decode("utf-8")
    if "§4.1 并发会话下的读数时间线" in t:
        print("[note] already present, skip")
        return
    if not t.endswith("\n"):
        t += "\n"
    t += NOTE
    with open(DOC, "wb") as f:
        f.write(t.encode("utf-8"))
    print("[note] %s: %d B -> %d B" % (os.path.basename(DOC), len(b), os.path.getsize(DOC)))


if __name__ == "__main__":
    main()
