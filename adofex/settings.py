import os.path
import glob


# This project's root directory.
# Default: The place where manage.py is run.
try:
    PROJECT_PATH
except NameError:
    PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

conf_files_path = os.path.join(PROJECT_PATH, 'settings', '*.conf')
conffiles = glob.glob(conf_files_path)
conffiles.sort()

for f in conffiles:
    execfile(os.path.abspath(f))
