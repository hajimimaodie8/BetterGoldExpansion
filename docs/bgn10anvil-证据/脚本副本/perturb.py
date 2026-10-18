import sys, os, json, hashlib, subprocess
sys.stdout.reconfigure(errors="replace")

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
MODEL = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "models", "block", "sturdygold_anvil.json")
SCREEN = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "client", "SturdygoldAnvilScreen.java")
VALIDATOR = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")

files = {MODEL: open(MODEL, "rb").read(), SCREEN: open(SCREEN, "rb").read()}
shas = {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}
env = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_validator():
    r = subprocess.run([sys.executable, VALIDATOR], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=ROOT)
    out = r.stdout + r.stderr
    anvil = [l for l in out.splitlines() if "bg-n10anvil" in l and "问题" in l]
    total = [l for l in out.splitlines() if l.startswith("[bg-data-")]
    return r.returncode, (anvil[-1] if anvil else "?"), (total[-1] if total else "?")


def restore():
    for p, b in files.items():
        open(p, "wb").write(b)
    ok = all(hashlib.sha256(open(p, "rb").read()).hexdigest() == shas[p] for p in files)
    return ok


results = []

# baseline
code, anvil, total = run_validator()
results.append(("baseline", code, anvil, total))

# P1: one face's texture swapped (top-block/north: #ew -> #ns)
m = json.loads(files[MODEL].decode("utf-8"))
for e in m["elements"]:
    if e["from"] == [3, 10, 0] and e["to"] == [13, 16, 16]:
        e["faces"]["north"]["texture"] = "#ns"
open(MODEL, "wb").write((json.dumps(m, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
code, anvil, total = run_validator()
results.append(("P1 one face texture -> wrong slot", code, anvil, total))
results.append(("P1 restore_sha_ok", restore(), "", ""))

# P2: delete the title drawString (one of the three texts)
s = files[SCREEN].decode("utf-8")
line = "        guiGraphics.drawString(this.font, this.title, 60, 6, 4210752, false);\n"
assert s.count(line) == 1
open(SCREEN, "wb").write(s.replace(line, "").encode("utf-8"))
code, anvil, total = run_validator()
results.append(("P2 delete title drawString", code, anvil, total))
results.append(("P2 restore_sha_ok", restore(), "", ""))

# P3: add COST_BAR back (old self-made element)
s = files[SCREEN].decode("utf-8")
anchor = "    /** 金色主面板：贴图 (0,0) 起 176×166（与原版砧同一块区域、同尺寸） */"
assert s.count(anchor) == 1
open(SCREEN, "wb").write(s.replace(anchor, "    private static final int COST_BAR_X = 60;\n" + anchor).encode("utf-8"))
code, anvil, total = run_validator()
results.append(("P3 add COST_BAR back", code, anvil, total))
results.append(("P3 restore_sha_ok", restore(), "", ""))

# P4: comment-only change -> must stay green
s = files[SCREEN].decode("utf-8")
anchor = "public class SturdygoldAnvilScreen"
assert s.count(anchor) == 1
open(SCREEN, "wb").write(s.replace(anchor, "// perturbation: comment only\n" + anchor).encode("utf-8"))
code, anvil, total = run_validator()
results.append(("P4 comment only", code, anvil, total))
results.append(("P4 restore_sha_ok", restore(), "", ""))

print("=== perturbation matrix ===")
for name, code, anvil, total in results:
    print("%-36s exit=%s | %s | %s" % (name, code, anvil, total))
print("=== final sha256 ===")
for p in files:
    print(os.path.basename(p), hashlib.sha256(open(p, "rb").read()).hexdigest())
