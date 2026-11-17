#!/usr/bin/env python3
"""Build the static Zeebo archive. Python standard library; no network needed."""
from pathlib import Path
import sys
from archive_pages import render

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
render(ROOT)
