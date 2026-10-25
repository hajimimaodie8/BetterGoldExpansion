# -*- coding: utf-8 -*-
"""bg18 / P2-b：把**手册正文**里的裸 `%` 转义成 `%%`（只碰两份语言文件）。

根因（已读源码，不是猜）：
    `net/minecraft/client/resources/language/I18n.java:23-30`
        String s = language.getOrDefault(key);
        try { return String.format(s, parameters); }
        catch (IllegalFormatException e) { return "Format error: " + s; }
    Patchouli 解析页正文 / 页眉走的是 `I18n.get(key)`（**零参数**）⇒ 值里出现 `50%` 时
    `String.format("…50% 的…")` 抛 `UnknownFormatConversionException` ⇒ 页面上直接印
    `Format error: …`。`%%` 在零参 format 下渲染为 `%`，是**唯一不改语义**的修法。

口径：
  * 只改 `bettergold.handbook.` 前缀的键（手册渲染面）；其余键一个字节不动。
  * 幂等：已经是 `%%` 的不再动。
  * 中 / 英两侧同样处理。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = [os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", n)
         for n in ("zh_cn.json", "en_us.json")]

PREFIX = "bettergold.handbook."
# 一个 `%` 前后都不是 `%` ⇒ 裸 %（`%%` 的两颗都不再命中 ⇒ 幂等）
BARE = re.compile(r"(?<!%)%(?!%)")


def escape(value):
    return BARE.sub("%%", value)


def main():
    total = 0
    for path in FILES:
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
        changed = []
        for k, v in data.items():
            if not k.startswith(PREFIX) or "%" not in v:
                continue
            new = escape(v)
            if new != v:
                changed.append(k)
                data[k] = new
        if changed:
            with io.open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
        print("%s: 转义 %d 条 %s" % (os.path.basename(path), len(changed), changed))
        total += len(changed)

    # 复核：转义后手册面**恰好 0 条裸 %**
    bad = 0
    for path in FILES:
        data = json.load(io.open(path, encoding="utf-8"))
        for k, v in data.items():
            if k.startswith(PREFIX) and BARE.search(v):
                bad += 1
                print("残留裸 %%: %s = %r" % (k, v[:60]))
    print("合计转义 %d 条；残留裸 %% %d 条" % (total, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
