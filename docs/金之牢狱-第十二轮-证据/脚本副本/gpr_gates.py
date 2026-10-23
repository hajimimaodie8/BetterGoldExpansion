# -*- coding: utf-8 -*-
"""第十二轮：八关卡一起跑，输出「exit + 关键计数行」两列，并写 build/gpr_gates.txt。

跑法（工作区自带 python，禁用 py -3）：
  <python> probe\\gpr\\gpr_gates.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TG = os.path.join(ROOT, 'tools', 'asset-generator')
OUT = os.path.join(ROOT, 'build', 'gpr_gates.txt')

GATES = [
    ('validate_metal_assets.py', ('[bg-assets-ok]', '[bg-assets-fail]')),
    ('validate_metal_data.py', ('[bg-data-ok]', '[bg-data-fail]')),
    ('validate_trim_assets.py', ('[bgfinal3-ok]', '[bgfinal3-fail]')),
    ('validate_advancements.py', ('[bgach-ok]', '[bgach-fail]')),
    ('validate_bg17_textures.py', ('[bg17tex-ok]', '[bg17tex-fail]')),
    ('check_jar_clean.py', ('[jar-clean-ok]', '[jar-clean-fail]')),
    ('check_forced_chunks.py', ('[chunks-forced-ok]', '[chunks-forced-fail]')),
    ('validate_golden_prison.py', ('[bgp-ok]', '[bgp-fail]')),
]


def run_one(name, keys):
    p = subprocess.run([sys.executable, os.path.join(TG, name)], cwd=ROOT, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    line = ''
    for l in out.splitlines():
        if any(k in l for k in keys):
            line = l.strip()
    if not line:
        tail = out.strip().splitlines()
        line = '(no key line) ' + (tail[-1][:100] if tail else '(no output)')
    return p.returncode, line


def main():
    rows = []
    worst = 0
    env_note = 'PYTHONIOENCODING=%s' % os.environ.get('PYTHONIOENCODING', '(unset)')
    for name, keys in GATES:
        rc, line = run_one(name, keys)
        rows.append((name, rc, line))
        worst = max(worst, rc)
        print('%-30s exit=%d  %s' % (name, rc, line))
    lines = ['', '| 关卡 | exit | 关键计数行 |', '|---|---|---|']
    lines += ['| `%s` | **%d** | `%s` |' % (n, rc, l) for n, rc, l in rows]
    lines.append('')
    lines.append('worst exit = %d（%s）' % (worst, env_note))
    text = '\n'.join(lines) + '\n'
    print(text)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    return 0 if worst == 0 else (2 if worst == 2 else 1)


if __name__ == '__main__':
    sys.exit(main())
