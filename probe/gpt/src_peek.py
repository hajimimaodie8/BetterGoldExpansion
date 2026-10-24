# -*- coding: utf-8 -*-
"""只读查看 neoforge sources jar 里的类（探针，收尾留档不删）。"""
import sys, zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
JAR = r"build\moddev\artifacts\neoforge-21.1.228-sources.jar"


def main():
    path = sys.argv[1]
    z = zipfile.ZipFile(JAR)
    hits = [n for n in z.namelist() if n.endswith(path)]
    if not hits:
        print("no entry ends with", path)
        # 列出候选
        key = path.split("/")[-1].split(".")[0]
        for n in z.namelist():
            if key in n:
                print("  cand:", n)
        return 2
    for n in hits:
        print("==== %s ====" % n)
        text = z.read(n).decode("utf-8", "replace")
        if len(sys.argv) > 2:
            lo = int(sys.argv[2])
            hi = int(sys.argv[3]) if len(sys.argv) > 3 else lo + 60
            lines = text.splitlines()
            for i in range(max(0, lo - 1), min(len(lines), hi)):
                print("%5d %s" % (i + 1, lines[i]))
        else:
            print(text)
    return 0


sys.exit(main())
