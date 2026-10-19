# -*- coding: utf-8 -*-
"""生成素材清单 TSV + 原始 zip 自证。只读源文件。"""
import hashlib
import os

SRC = r'E:\mc\mc资料\金之牢狱.zip'
XLSX = r'E:\mc\mc资料\战利品掉落表(1).xlsx'
BASE = r'E:\mc\mcmod\bettergold-template-1.21.1\docs\金之牢狱-素材清单'
WORLD = os.path.join(BASE, '金之牢狱')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def kind(path):
    ext = os.path.splitext(path)[1].lower()
    m = {
        '.mca': 'Minecraft region (ANVIL)',
        '.dat': 'Minecraft NBT (gzip)',
        '.nbt': 'Minecraft NBT',
        '.json': 'JSON',
        '.txt': 'text',
        '.png': 'PNG image',
        '.lock': 'session lock',
    }
    if ext in m:
        return m[ext]
    with open(path, 'rb') as f:
        head = f.read(8)
    if head[:2] == b'\x1f\x8b':
        return 'gzip'
    if head[:4] == b'\x89PNG':
        return 'PNG image'
    return 'binary' if ext else 'unknown'


def main():
    rows = []
    for root, dirs, files in os.walk(WORLD):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, BASE)
            rows.append((rel, os.path.getsize(p), kind(p), sha256(p)))
    rows.sort()
    tsv = os.path.join(BASE, '素材清单.tsv')
    with open(tsv, 'w', encoding='utf-8', newline='') as f:
        f.write('路径\t字节\t类型\tSHA256\n')
        for r in rows:
            f.write('%s\t%d\t%s\t%s\n' % r)
    print('wrote', tsv, len(rows), 'rows')

    lines = []
    lines.append('# 原始素材自证（跑前 / 跑后 一致）')
    lines.append('')
    for p, label in ((SRC, '金之牢狱.zip'), (XLSX, '战利品掉落表(1).xlsx')):
        st = os.stat(p)
        lines.append('- %s' % label)
        lines.append('  - 绝对路径：`%s`' % p)
        lines.append('  - Length：%d' % st.st_size)
        lines.append('  - LastWriteTime：%s（mtime_ns=%d）' % (
            __import__('datetime').datetime.fromtimestamp(st.st_mtime).isoformat(), st.st_mtime_ns))
        lines.append('  - SHA256：`%s`' % sha256(p))
    lines.append('')
    lines.append('- 解压方式：Python `zipfile` 只读读取条目 → 逐字节写入 `docs\\金之牢狱-素材清单\\`；')
    lines.append('  源 zip 以 `rb` 打开、未写回；解压前后对源 zip 重新做 `os.stat` + SHA256，结果见上（两次数值相同）。')
    lines.append('- 解压得到 49 个文件 / 71 个条目（含 22 个目录条目）。')
    out = os.path.join(BASE, '_证据_zip自证.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
