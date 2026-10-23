import hashlib
import shutil
import sys

src = r'run\server.properties'
bak = r'run\server.properties.gpr.bak'
shutil.copyfile(src, bak)
d = open(src, 'rb').read()
print('backup bytes=%d sha256=%s' % (len(d), hashlib.sha256(d).hexdigest()))
print('bak    bytes=%d sha256=%s' % (len(open(bak, 'rb').read()), hashlib.sha256(open(bak, 'rb').read()).hexdigest()))
