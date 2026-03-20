# Copyright (c) 2026 Dossenge
# Released under the MIT License (see LICENSE file for details)

import subprocess
import sys
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
