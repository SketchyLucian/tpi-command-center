#!/usr/bin/env python3
"""
TPI GUI Launcher
Runs the True Priority Index Flet cross-platform application.
"""
import sys
import flet as ft
from main import main

if __name__ == "__main__":
    try:
        if hasattr(ft, "run"):
            ft.run(main)
        else:
            ft.app(target=main)
    except KeyboardInterrupt:
        print("\nSession closed safely.")
        sys.exit(0)
