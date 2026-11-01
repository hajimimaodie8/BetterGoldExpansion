import hashlib
import os
import shutil
import sys

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")
EVID = os.path.join("docs", "bg19-证据")
os.makedirs(EVID, exist_ok=True)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tree(root):
    rows = []
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            n = os.path.getsize(p)
            total += n
            rows.append((os.path.relpath(p, root), n))
    return sorted(rows), total


# 1) 探针世界清单（删前留档）
world = os.path.join("run", "bg19probe")
rows, total = tree(world)
with open(os.path.join(EVID, "01-删除的探针世界-bg19probe.txt"), "w", encoding="utf-8") as f:
    f.write("探针世界 run/bg19probe（本轮自建，删前留档）\n")
    f.write("文件数 %d / 合计 %d B\n" % (len(rows), total))
    for r, n in rows:
        f.write("%10d  %s\n" % (n, r))
print("world files", len(rows), total)

# 2) 作者存档跑前/跑后清单（红线：只读不写）
saves = os.path.join("run", "saves")
srows, stotal = tree(saves)
with open(os.path.join(EVID, "02-run-saves-清单.txt"), "w", encoding="utf-8") as f:
    f.write("run/saves 清单（本轮只读；未打开、未由本模组存盘）\n")
    f.write("文件数 %d / 合计 %d B\n" % (len(srows), stotal))
    for r, n in srows:
        f.write("%10d  %s\n" % (n, r))
print("saves files", len(srows), stotal)

# 3) server.properties 逐字节复原
src = os.path.join("run", "server.properties")
bak = os.path.join("run", "server.properties.bg19.bak")
shutil.copyfile(bak, src)
ok = sha(src) == sha(bak) == "a2229937ba8ab7428bc959e87a784890500d6d7061b10fa8302758e46a01d3c4"
print("server.properties restored:", ok, sha(src))

# 4) 删探针世界 + 开关文件
shutil.rmtree(world, ignore_errors=True)
print("world removed:", not os.path.exists(world))
sw = os.path.join("run", "bg19-probe.enabled")
if os.path.exists(sw):
    os.remove(sw)
print("switch removed:", not os.path.exists(sw))
