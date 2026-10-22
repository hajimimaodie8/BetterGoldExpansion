# -*- coding: utf-8 -*-
"""八关卡：逐个跑，打印 exit + 关键计数行（供 docs 的两列表）。"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
PY = r'C:\Users\Lenovo\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
GATES = [
    ('validate_metal_assets.py', r'\[bg-assets-ok\]|\[bg-assets-fail\]|问题合计'),
    ('validate_metal_data.py', r'\[bg-data-ok\]|\[bg-data-fail\]|\[bgsnd-ok\]|\[bgsnd-summary\]'),
    ('validate_trim_assets.py', r'\[bgfinal3-ok\]|\[bgfinal3-fail\]'),
    ('validate_advancements.py', r'\[bgach-ok\]|\[bgach-fail\]'),
    ('validate_bg17_textures.py', r'\[bg17tex-ok\]|\[bg17tex-fail\]'),
    ('check_jar_clean.py', r'\[jar-clean-ok\]|\[jar-clean-fail\]'),
    ('check_forced_chunks.py', r'\[chunks-forced-ok\]|\[chunks-forced-fail\]'),
    ('validate_golden_prison.py', r'\[bgp-ok\]|\[bgp-fail\]|\[bgp-counter\]'),
]
out = []
for fn, pat in GATES:
    p = os.path.join(ROOT, 'tools', 'asset-generator', fn)
    r = subprocess.run([PY, p], cwd=ROOT, capture_output=True)
    txt = (r.stdout or b'').decode('utf-8', 'replace') + (r.stderr or b'').decode('utf-8', 'replace')
    hits = [l for l in txt.split('\n') if re.search(pat, l)]
    out.append((fn, r.returncode, hits))
    print('%-28s exit=%d' % (fn, r.returncode))
    for h in hits[:4]:
        print('    ' + h.strip())
    sys.stdout.flush()
print()
print('== 两列表 ==')
for fn, rc, hits in out:
    key = (hits[0].strip() if hits else '(no key line)')
    print('| `%s` | **%d** | `%s` |' % (fn, rc, key.replace('|', '\\|')))
bad = [fn for fn, rc, _ in out if rc != 0]
print('\nALL GREEN' if not bad else '\nNOT GREEN: %s' % bad)
