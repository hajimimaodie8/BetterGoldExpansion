# -*- coding: utf-8 -*-
"""核对 forceload：打印 run/world/data/chunks.dat 的 data 段键与 Forced 长度。

用法: python check_forced_chunks.py [<chunks.dat 路径>]

==================== 关卡退出码契约（bgfix6，2026-10-08）====================
  0 = 全绿：真的读到了 chunks.dat，且 `data.Forced` **为空**（收尾态不该有残留 forceload）
  1 = 有「问题」：`data.Forced` **非空**（有残留 forceload）
  2 = 基线被破坏 / 前置缺失 / 脚本自身出错：文件不存在 / 解不开 gzip / NBT 解析失败 /
      根不是 compound / 没有 `data` 段 / **没有 `Forced` 键** / `Forced` 不是列表
  ★ **任何未捕获异常都不许变成 0**：顶层 try/except 一律转成 2。
  ★ **反空转**：必须打印「实际检查了 N 项」并断言 N > 0。
  依据：`docs/构建与跑测注意事项.md`「关卡的退出码契约」；
        `mod_experience\\ex\\03-验证与证据.md` §3.19。

⚠⚠ bgfix6（2026-10-08）**就地标注**：本关卡原先**全篇没有 `sys.exit`**，而且
  `forced is None`（**键缺失 = 未知**）时它打印的是「chunks.dat 侧 forceload 为 0 = True」
  —— 这正是「**把未知 / 未覆盖当 0**」的假绿第二形态。**旧打印一字未删**；
  现在：`Forced` 键缺失 ⇒ exit 2，`Forced` 非空 ⇒ exit 1。
  为什么"键缺失"可以判成 2（源码级依据，不是猜）：`ForcedChunksSavedData#save`
  **无条件**执行 `tag.putLongArray("Forced", this.chunks.toLongArray())`
  （`build/moddev/artifacts/neoforge-21.1.228-sources.jar:net/minecraft/world/level/ForcedChunksSavedData.java`）
  ⇒ 正常的 `chunks.dat` 里这个键**一定存在**；不存在 ⇒ 文件被外力改坏或不是这个存档的产物。
"""
import gzip
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "run" / "world" / "data" / "chunks.dat"


def read_nbt(data, pos=0):
    tag = data[pos]
    pos += 1
    if tag == 0:
        return None, pos
    nlen = struct.unpack(">H", data[pos:pos + 2])[0]
    pos += 2
    name = data[pos:pos + nlen].decode("utf-8", "replace")
    pos += nlen
    if tag == 1:
        return (name, struct.unpack(">b", data[pos:pos + 1])[0]), pos + 1
    if tag == 2:
        return (name, struct.unpack(">h", data[pos:pos + 2])[0]), pos + 2
    if tag == 3:
        return (name, struct.unpack(">i", data[pos:pos + 4])[0]), pos + 4
    if tag == 4:
        return (name, struct.unpack(">q", data[pos:pos + 8])[0]), pos + 8
    if tag == 5:
        return (name, struct.unpack(">f", data[pos:pos + 4])[0]), pos + 4
    if tag == 6:
        return (name, struct.unpack(">d", data[pos:pos + 8])[0]), pos + 8
    if tag == 7:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(data[pos + 4:pos + 4 + ln])), pos + 4 + ln
    if tag == 8:
        ln = struct.unpack(">H", data[pos:pos + 2])[0]
        return (name, data[pos + 2:pos + 2 + ln].decode("utf-8", "replace")), pos + 2 + ln
    if tag == 9:
        et = data[pos]
        ln = struct.unpack(">i", data[pos + 1:pos + 5])[0]
        pos += 5
        items = []
        for _ in range(ln):
            v, pos = read_payload(data, pos, et)
            items.append(v)
        return (name, items), pos
    if tag == 10:
        out = {}
        while True:
            if data[pos] == 0:
                pos += 1
                break
            (k, v), pos = read_nbt(data, pos)
            out[k] = v
        return (name, out), pos
    if tag == 11:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(struct.unpack(">" + "i" * ln, data[pos + 4:pos + 4 + 4 * ln]))), pos + 4 + 4 * ln
    if tag == 12:
        ln = struct.unpack(">i", data[pos:pos + 4])[0]
        return (name, list(struct.unpack(">" + "q" * ln, data[pos + 4:pos + 4 + 8 * ln]))), pos + 4 + 8 * ln
    raise ValueError(f"unsupported tag {tag} at {pos}")


def read_payload(data, pos, tag):
    if tag == 3:
        return struct.unpack(">i", data[pos:pos + 4])[0], pos + 4
    if tag == 4:
        return struct.unpack(">q", data[pos:pos + 8])[0], pos + 8
    if tag == 10:
        out = {}
        while True:
            if data[pos] == 0:
                pos += 1
                break
            (k, v), pos = read_nbt(data, pos)
            out[k] = v
        return out, pos
    if tag == 8:
        ln = struct.unpack(">H", data[pos:pos + 2])[0]
        return data[pos + 2:pos + 2 + ln].decode("utf-8", "replace"), pos + 2 + ln
    raise ValueError(f"unsupported list element tag {tag}")


def main() -> int:
    # ---------------- bgfix6：前置缺失 ⇒ exit 2 ----------------
    if not PATH.is_file():
        print(f"FAIL [chunks-forced-missing] chunks.dat 不存在：{PATH}")
        print("      ⇒ 基线被破坏（前置缺失）；本关卡 exit 2")
        return 2
    try:
        raw = gzip.decompress(PATH.read_bytes())
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL [chunks-forced-unreadable] 解不开 gzip：{exc!r}（{PATH}）⇒ 前置坏；本关卡 exit 2")
        return 2
    try:
        (_, root), _ = read_nbt(raw, 0)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL [chunks-forced-nbt] NBT 解析失败：{exc!r} ⇒ 前置坏；本关卡 exit 2")
        return 2
    if not isinstance(root, dict):
        print(f"FAIL [chunks-forced-nbt] 根不是 compound（{type(root).__name__}）⇒ 前置坏；本关卡 exit 2")
        return 2
    if not isinstance(root.get("data"), dict):
        print(f"FAIL [chunks-forced-nbt] 根里没有 `data` compound（keys={list(root.keys())}）"
              f"⇒ 前置坏；本关卡 exit 2")
        return 2

    inner = root.get("data", {})
    print("chunks.dat top-level keys =", list(root.keys()))
    print("chunks.dat data keys      =", list(inner.keys()))
    forced = inner.get("Forced")
    print("data.Forced               =", forced)
    print("data.Forced length        =", 0 if forced is None else len(forced))
    print("chunks.dat 侧 forceload 为 0 =", forced is None or len(forced) == 0)

    # ---------------- bgfix6：反空转 ----------------
    _checked = len(inner) + (len(forced) if isinstance(forced, list) else 0)
    print(f"[chunks-forced-anti-vacuum] 实际检查了 {_checked} 项"
          f"（data 段键 {len(inner)} + Forced 列表项 {len(forced) if isinstance(forced, list) else 'n/a'}；必须 > 0）")

    # ---------------- bgfix6：结论 + 退出码 ----------------
    if forced is None:
        print("FAIL [chunks-forced-key-absent] `data.Forced` 键不存在 —— **不许把未知当 0**；")
        print("      正常 chunks.dat 一定有这个键（ForcedChunksSavedData#save 无条件 putLongArray）"
              "⇒ 基线被破坏；本关卡 exit 2")
        return 2
    if not isinstance(forced, list):
        print(f"FAIL [chunks-forced-key-type] `data.Forced` 不是列表（{type(forced).__name__}）⇒ 前置坏；本关卡 exit 2")
        return 2
    if _checked <= 0:
        print("FAIL [chunks-forced-anti-vacuum] 检查项数 = 0 ⇒ 基线坏了；本关卡 exit 2")
        return 2
    if forced:
        print(f"FAIL [chunks-forced-residual] 收尾态仍有残留 forceload：{len(forced)} 项 {forced[:8]} "
              f"⇒ 本关卡 exit 1")
        return 1
    print("[chunks-forced-ok] data.Forced 为空（收尾态无残留 forceload）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"关卡自身出错（exit 2）：{exc!r}")
        raise SystemExit(2)
