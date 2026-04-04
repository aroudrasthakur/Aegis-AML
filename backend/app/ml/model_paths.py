"""Stable paths to repository-root ``models/`` (independent of process cwd)."""
from __future__ import annotations

from pathlib import Path

# backend/app/ml/model_paths.py → parents[3] = repo root (…/Aegis-AML)
_REPO_ROOT = Path(__file__).resolve().parents[3]

MODELS_DIR: Path = _REPO_ROOT / "models"
