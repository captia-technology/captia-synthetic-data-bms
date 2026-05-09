"""Generador de los 42 notebooks didácticos del proyecto.

Ejecutar como módulo desde la raíz del repo:

    uv run python -m scripts.build_notebooks

Cada caso vive en un módulo aparte (`case_overview.py`, `case_a.py`, ...).
Re-ejecuciones son idempotentes y deterministas (`seed=42`).
"""
