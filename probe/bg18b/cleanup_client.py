# -*- coding: utf-8 -*-
"""bg18b · 客户端跑测收尾：逐字节复原 build.gradle、删开关/世界/quickplay、复核作者存档。"""
import hashlib
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tree(root):
    rows = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            rows.append((os.path.relpath(p, root).replace("\\", "/"), os.path.getsize(p),
                         sha(p)))
    rows.sort()
    return rows


def main():
    # 1) build.gradle 逐字节复原
    p = os.path.join(BASE, "build.gradle")
    bak = p + ".bg18bak"
    before = sha(p)
    shutil.copyfile(bak, p)
    after = sha(p)
    print("build.gradle modified=%s restored=%s" % (before, after))
    assert after == "2aac7860e5b1f03128d42637b9f002c7a44f37e269ee6b7bc9dfbe41ad478c2f", after
    os.remove(bak)
    print("build.gradle .bak removed, sha=%s" % sha(p))

    # 2) 开关文件
    for sw in ("bg18b-client-probe.enabled", "bg18b-probe.enabled"):
        q = os.path.join(BASE, "run", sw)
        if os.path.exists(q):
            os.remove(q)
        print("switch %s exists=%s" % (sw, os.path.exists(q)))

    # 3) quickplay json（只删本轮那个）
    qp = os.path.join(BASE, "run", "logs", "quickplay", "bg18qb.json")
    if os.path.exists(qp):
        os.remove(qp)
    print("quickplay bg18qb.json exists=%s" % os.path.exists(qp))

    # 4) 探针世界（先留清单再删）
    outdir = os.path.join(BASE, "docs", "bg18-证据", "09-客户端世界")
    os.makedirs(outdir, exist_ok=True)
    for name in ("bg18cprobe", "bg18probe"):
        root = os.path.join(BASE, "run", "saves", name) if name == "bg18cprobe" else os.path.join(BASE, "run", name)
        if not os.path.isdir(root):
            print("world %s absent" % name)
            continue
        rows = tree(root)
        with open(os.path.join(outdir, "删除的-" + name + ".txt"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("%s files=%d bytes=%d\n" % (name, len(rows), sum(r[1] for r in rows)))
            for n, s, h in rows:
                fh.write("%s\t%d\t%s\n" % (n, s, h))
        shutil.rmtree(root)
        print("world %s deleted (files=%d bytes=%d)" % (name, len(rows), sum(r[1] for r in rows)))

    # 5) 作者存档复核
    a = tree(os.path.join(BASE, "run", "saves", "新的世界"))
    prev = os.path.join(outdir, "作者存档跑前快照.txt")
    txt = open(prev, encoding="utf-8").read().splitlines()
    hdr = txt[0]
    ok = hdr == "run/saves/新的世界 files=%d bytes=%d" % (len(a), sum(r[1] for r in a))
    detail = []
    for i, (n, s, h) in enumerate(a):
        want = txt[1 + i].split("\t")
        if want != [n, str(s), h]:
            detail.append(n)
    print("author save files=%d bytes=%d header_same=%s mismatches=%r total_now=%r"
          % (len(a), sum(r[1] for r in a), ok, detail,
             txt[0]))
    # 6) run/saves 只剩作者存档
    print("run/saves dirs=%r" % [d for d in os.listdir(os.path.join(BASE, "run", "saves"))])
    return 0 if ok and not detail else 1


if __name__ == "__main__":
    raise SystemExit(main())
