#!/usr/bin/env python3
# Vellum library / series-layer engine entry point (library-spec.md §8).
# Python >= 3.8, stdlib only, zero pip dependencies.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vellum_lib.series_cli import main

if __name__ == "__main__":
    sys.exit(main())
