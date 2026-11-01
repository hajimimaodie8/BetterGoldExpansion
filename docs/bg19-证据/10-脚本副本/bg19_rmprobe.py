import hashlib
import os
import shutil
import sys

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")
EVID = os.path.join("docs", "bg19-证据")
os.makedirs(EVID, exist_ok=True)

# 1) 探针源码留档（删前）
src_dir = os.path.join("src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bg19")
dst_dir = os.path.join(EVID, "03-探针源码副本")
os.makedirs(dst_dir, exist_ok=True)
for fn in sorted(os.listdir(src_dir)):
    shutil.copyfile(os.path.join(src_dir, fn), os.path.join(dst_dir, fn))
    print("archived", fn, os.path.getsize(os.path.join(dst_dir, fn)),
          hashlib.sha256(open(os.path.join(dst_dir, fn), "rb").read()).hexdigest()[:16])

# 2) 服务端探针日志原文（只摘 [bg19-s] 行）
log = open(os.path.join("run", "logs", "latest.log"), "rb").read().decode("utf-8", errors="replace")
lines = [ln.split("]: ", 1)[-1] for ln in log.splitlines() if "[bg19-s]" in ln]
with open(os.path.join(EVID, "04-服务端探针原文.txt"), "w", encoding="utf-8") as f:
    f.write("bg19 服务端探针（第 4 次跑 = 最终读数；前三次的失败读数见 05-探针迭代记录.txt）\n")
    f.write("\n".join(lines) + "\n")
print("log lines", len(lines))

# 3) 删探针（整块删除，不是注释掉）
shutil.rmtree(src_dir, ignore_errors=True)
print("probe removed:", not os.path.exists(src_dir))
print("probe dir empty parent:", os.listdir(os.path.dirname(src_dir)))
