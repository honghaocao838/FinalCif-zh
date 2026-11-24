"""Import the source tree instead of the frozen FinalCif package.

The Windows runtime used for testing ships a preloaded ``finalcif`` package
through ``sitecustomize``; dropping those modules and putting the repository
root first on ``sys.path`` makes the tests exercise the working tree.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
for _name in list(sys.modules):
    if _name == 'finalcif' or _name.startswith('finalcif.'):
        sys.modules.pop(_name, None)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
