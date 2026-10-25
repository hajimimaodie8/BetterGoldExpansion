# -*- coding: utf-8 -*-
"""bg18b · 准备客户端复跑：把服务端探针世界重拷到 run/saves/bg18cprobe。"""
import hashlib
import os
import shutil

SRC = os.path.join("run", "bg18probe")
DST = os.path.join("run", "saves", "bg18cprobe")
AUTHOR = os.path.join("run", "saves", "新的世界")


def tree(root):
    rows = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            rows.append((os.path.relpath(p, root).replace("\\", "/"), os.path.getsize(p),
                         hashlib.sha256(open(p, "rb").read()).hexdigest()))
    rows.sort()
    return rows


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    print("recopied %s -> %s files=%d" % (SRC, DST, len(tree(DST))))
    a = tree(AUTHOR)
    print("author save files=%d bytes=%d" % (len(a), sum(r[1] for r in a)))
    with open(os.path.join("docs", "bg18-证据", "09-客户端世界", "作者存档跑后快照.txt"),
              "w", encoding="utf-8", newline="\n") as fh:
        fh.write("run/saves/新的世界 files=%d bytes=%d\n" % (len(a), sum(r[1] for r in a)))
        for n, s, h in a:
            fh.write("%s\t%d\t%s\n" % (n, s, h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
