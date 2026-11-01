import subprocess
import sys
import os

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
os.chdir(ROOT)
sys.stdout.reconfigure(errors="replace")

SCRIPTS = [
    "validate_metal_assets.py",
    "validate_metal_data.py",
    "validate_advancements.py",
    "validate_trim_assets.py",
    "validate_bg17_textures.py",
    "validate_golden_prison.py",
    "check_jar_clean.py",
    "check_forced_chunks.py",
]
out_path = os.path.join("build", "bg19-8gates.txt")
env = dict(os.environ, PYTHONIOENCODING="utf-8")
rows = []
with open(out_path, "w", encoding="utf-8") as f:
    for name in SCRIPTS:
        p = os.path.join("tools", "asset-generator", name)
        r = subprocess.run([sys.executable, p], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        tail = [ln for ln in (r.stdout or "").splitlines() if ln.strip()][-3:]
        rows.append((name, r.returncode, tail))
        f.write("===== %s  exit=%d\n" % (name, r.returncode))
        f.write((r.stdout or "")[-4000:])
        if r.stderr:
            f.write("\n--stderr--\n" + r.stderr[-1500:])
        f.write("\n")
        print("== %-32s exit=%d" % (name, r.returncode))
        for ln in tail:
            print("   ", ln[:200])
print("written", out_path)
