import os.path
import glob


try:
    TX_ROOT
except NameError:
    TX_ROOT = os.path.dirname(__file__)

conf_files_path = os.path.join(TX_ROOT, 'settings', '*.conf')
conffiles = glob.glob(conf_files_path)
conffiles.sort()

for f in conffiles:
    execfile(os.path.abspath(f))
