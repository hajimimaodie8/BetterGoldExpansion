# -*- coding: utf-8 -*-
"""第九轮收尾：临时改 run\\server.properties（level-name / level-seed），只改这两行，其余字节不动。

用法（工作区自带 Python，禁用 py -3）：
  gpn_set_patch.py save
  gpn_set_patch.py apply <name> <seed>
  gpn_set_patch.py restore
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
P = os.path.join(ROOT, "run", "server.properties")
BAK = P + ".gpn.bak"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "save":
        shutil.copyfile(P, BAK)
        print("backup sha256 =", sha(open(BAK, "rb").read()))
        return
    if cmd == "restore":
        b = open(BAK, "rb").read()
        open(P, "wb").write(b)
        b2 = open(P, "rb").read()
        print("restored sha256 =", sha(b2), "| bak =", sha(b), "| equal =", b == b2)
        if b != b2:
            raise SystemExit(1)
        return
    if cmd == "apply":
        name = sys.argv[2]
        seed = sys.argv[3]
        b = open(BAK, "rb").read()
        lines = b.split(b"\n")
        out = []
        n_name = n_seed = 0
        for line in lines:
            if line.startswith(b"level-name="):
                out.append(b"level-name=" + name.encode())
                n_name += 1
            elif line.startswith(b"level-seed="):
                out.append(b"level-seed=" + seed.encode())
                n_seed += 1
            else:
                out.append(line)
        if n_name != 1 or n_seed != 1:
            raise SystemExit("unexpected keys: name=%d seed=%d" % (n_name, n_seed))
        nb = b"\n".join(out)
        open(P, "wb").write(nb)
        print("applied level-name=%s level-seed=%s sha256=%s" % (name, seed, sha(nb)))
        for line in nb.split(b"\n"):
            if line.startswith((b"level-name=", b"level-seed=", b"online-mode=")):
                print("  ", line.decode())
        return
    raise SystemExit("usage: save|apply <name> <seed>|restore")


if __name__ == "__main__":
    main()
