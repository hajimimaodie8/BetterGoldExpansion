# -*- coding: utf-8 -*-
"""第八轮 ⑤：语言文件加了 3 条字幕键 ⇒ 更新 validate_metal_data.py 里的冻结 SHA / 键数（旧值留注释）。"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
P = os.path.join(ROOT, r'tools\asset-generator\validate_metal_data.py')
LANG = os.path.join(ROOT, r'src\main\resources\assets\bettergold\lang')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


zh_sha = sha(os.path.join(LANG, 'zh_cn.json'))
en_sha = sha(os.path.join(LANG, 'en_us.json'))
txt = open(P, 'rb').read().decode('utf-8')

OLD_ZH = '65C45198982830B343543F1A27D668CF7E125E4CC25C30427E96C3105FC00643'
OLD_EN = 'E606504A7F663C6EE05E2CD4D2F220F9A2F705D18FC50FB0037343C9F637E58B'
OLD_N = '_BGN10_NEW_LANG_KEYS = 113'
NEW_N = ('# ★★ 第八轮（2026-10-22）：金钱妖音效 3 条字幕键（subtitles.bettergold.money_gremlin_*）\n'
         '#   ⇒ 113 + 3 = **116**。旧期望原文留档：_BGN10_NEW_LANG_KEYS = 113\n'
         '_BGN10_NEW_LANG_KEYS = 116')

assert OLD_ZH in txt and OLD_EN in txt and OLD_N in txt
txt = txt.replace('_BGN10_ZH_AFTER_SHA = "%s"' % OLD_ZH,
                  ('# 旧期望原文留档（bg-n10up 轮）：_BGN10_ZH_AFTER_SHA = "%s"\n'
                   '# ★★ 第八轮（2026-10-22）：+3 条金钱妖字幕键 ⇒ 新 SHA（下面这行）\n'
                   '_BGN10_ZH_AFTER_SHA = "%s"') % (OLD_ZH, zh_sha), 1)
txt = txt.replace('_BGN10_EN_AFTER_SHA = "%s"' % OLD_EN,
                  ('# 旧期望原文留档（bg-n10up 轮）：_BGN10_EN_AFTER_SHA = "%s"\n'
                   '# ★★ 第八轮（2026-10-22）：+3 条金钱妖字幕键 ⇒ 新 SHA（下面这行）\n'
                   '_BGN10_EN_AFTER_SHA = "%s"') % (OLD_EN, en_sha), 1)
txt = txt.replace(OLD_N, NEW_N, 1)
open(P, 'wb').write(txt.encode('utf-8'))
print('zh', zh_sha)
print('en', en_sha)
