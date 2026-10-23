import re

paths = [
    r'docs\金之牢狱-第九轮收尾-证据\GpoProbe.java.txt',
    r'docs\金之牢狱-第九轮-证据\脚本副本\Gp9Probe.java.txt',
    r'docs\金之牢狱-实现-证据\GpProbe.java.txt',
    r'docs\金之牢狱-实现-证据\GpRateProbe.java.txt',
    r'docs\金之牢狱-实现-证据\GpFinalProbe.java.txt',
    r'docs\金之牢狱-实现-证据\GphProbe.java.txt',
]
out = []
for p in paths:
    s = open(p, encoding='utf-8', errors='replace').read()
    out.append('===== %s %d' % (p, len(s)))
    for m in re.finditer(r'.*(?:generate|JigsawPlacement|StructureStart|GenerationContext|PoolElementStructurePiece).*', s):
        t = m.group(0).strip()
        if t.startswith('import') or t.startswith('*'):
            continue
        out.append('    ' + t[:170])
open(r'probe\gpr\gen_scan.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(len(out))
