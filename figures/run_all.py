# -*- coding: utf-8 -*-
"""Regenerate all main-text figures from packaged panel data."""
from __future__ import annotations

import runpy
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = [ROOT / f"plot_fig{i:02d}.py" for i in range(1, 8)]


def main() -> None:
    ok, bad = [], []
    for script in SCRIPTS:
        print("=" * 60)
        print("RUN", script.name)
        try:
            runpy.run_path(str(script), run_name="__main__")
            ok.append(script.name)
        except Exception:
            traceback.print_exc()
            bad.append(script.name)
    print("=" * 60)
    print("OK:", ok)
    print("FAIL:", bad)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
