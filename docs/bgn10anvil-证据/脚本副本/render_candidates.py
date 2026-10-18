import sys, os
sys.path.insert(0, r"E:\mc\mcmod\bettergold-template-1.21.1\build\bgn10anvil")
sys.stdout.reconfigure(errors="replace")
import render_model as R

ROOT = r"E:\mc\mcmod\bettergold-template-1.21.1"
OUT = os.path.join(ROOT, "build", "bgn10anvil", "preview")
os.makedirs(OUT, exist_ok=True)

renders = [
    ("candidate_A", "candidate_A.json", 0),
    ("candidate_A_back", "candidate_A.json", 180),
    ("candidate_A_top0", "candidate_A_top0.json", 0),
    ("candidate_A_top0_back", "candidate_A_top0.json", 180),
    ("candidate_A_side_mirror", "candidate_A_side_mirror.json", 0),
]
for name, f, ang in renders:
    R.render(os.path.join(ROOT, "build", "bgn10anvil", f),
             os.path.join(OUT, "render_%s.png" % name), rot_y=ang)
