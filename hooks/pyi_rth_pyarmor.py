# Runtime hook pour PyArmor
import sys
import os

if getattr(sys, 'frozen', False):
    runtime_path = os.path.join(sys._MEIPASS, 'pyarmor_runtime_009306')
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)
    try:
        from pyarmor_runtime_009306 import pyarmor_runtime
    except:
        pass
