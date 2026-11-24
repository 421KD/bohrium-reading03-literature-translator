#!/usr/bin/env python3
"""ARM entrypoint for the literature-translator Skill.

Delegates to the scaffold extractor in translate_pdf.py so the bundle exposes
the canonical `src/reproduce.py` entrypoint expected by the ARM manifest.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translate_pdf import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
