# -*- coding: utf-8 -*-
"""只读：金钱妖声音.zip 清单（不解压到仓库，只打印）。"""
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
Z = r'E:\mc\mc资料\金钱妖声音.zip'
z = zipfile.ZipFile(Z)
print('entries =', len(z.infolist()))
for info in z.infolist():
    print('%-60s %8d  %s' % (info.filename, info.file_size, info.date_time))
