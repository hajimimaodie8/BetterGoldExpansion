# -*- coding: utf-8 -*-
"""第八轮：给 MoneyGremlin 的类注释补一句"音效已换"（bytes 级插入，旧原文不删）。"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'src\main\java\com\hjmmd_8\bettergold\entity\MoneyGremlin.java'
raw = open(P, 'rb').read()
txt = raw.decode('utf-8')
old = '<li><b>音效</b> = 原版僵尸的 ambient / hurt / death（本仓没有 {@code sounds.json}，不新增音频文件）；</li>'
new = (old + '\n'
       ' *   <li>★ <b>第八轮（2026-10-22）已改</b>：上面那条「用原版僵尸音效」<b>按作者要求作废</b>'
       '（「浮空所以不需要走路音效，僵尸音效请给它毙掉」）⇒ ambient / hurt / death 走'
       ' {@code AllSounds.MONEY_GREMLIN_*}（作者 zip 的音轨转 ogg），并且'
       ' {@link #playStepSound} 覆写成空实现（浮空 = 不踩踏）；字幕键 '
       '{@code subtitles.bettergold.money_gremlin_*}。旧原文保留在上面不删。</li>')
if old not in txt:
    print('needle not found'); sys.exit(1)
if '第八轮（2026-10-22）已改' in txt:
    print('already patched'); sys.exit(0)
open(P, 'wb').write(txt.replace(old, new, 1).encode('utf-8'))
print('patched')
