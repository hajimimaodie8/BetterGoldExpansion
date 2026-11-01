import hashlib
import os
import shutil
import sys

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")

src = os.path.join("run", "server.properties")
bak = os.path.join("run", "server.properties.bg19.bak")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

print("before", sha(src), len(open(src, "rb").read()))
shutil.copyfile(src, bak)
print("bak   ", sha(bak))
assert sha(src) == sha(bak)

raw = open(src, "rb").read()
assert b"level-name=world\n" in raw or b"level-name=world\r\n" in raw, "level-name literal not found"
new = raw.replace(b"level-name=world\r\n", b"level-name=bg19probe\r\n").replace(
    b"level-name=world\n", b"level-name=bg19probe\n")
open(src, "wb").write(new)
print("after ", sha(src), b"bg19probe" in open(src, "rb").read())

# 开关文件（相对 run/ 的工作目录）
open(os.path.join("run", "bg19-probe.enabled"), "w", encoding="utf-8").write("bg19\n")
print("switch", os.path.isfile(os.path.join("run", "bg19-probe.enabled")))

# 旧的 session.lock
for d in ("run/world", "run/saves"):
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, d)):
        if "session.lock" in filenames:
            p = os.path.join(dirpath, "session.lock")
            print("removing", p)
            os.remove(p)
