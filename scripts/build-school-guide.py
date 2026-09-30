#!/usr/bin/env python3
"""Render assets/school-conversation-guide.pdf from scripts/school-conversation-guide.html with headless Chrome.

    python3 scripts/build-school-guide.py

Chrome is the one renderer on hand that prints the guide's CSS faithfully; CHROME_PATH points at another binary.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'scripts' / 'school-conversation-guide.html'
OUT = ROOT / 'assets' / 'school-conversation-guide.pdf'
CHROME = os.environ.get('CHROME_PATH') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

if not Path(CHROME).exists():
    sys.exit(f'build-school-guide: no Chrome at {CHROME}; set CHROME_PATH')
subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--no-first-run',
                f'--print-to-pdf={OUT}', SRC.as_uri()], check=True, capture_output=True)
print(f'wrote  {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)')
