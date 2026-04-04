"""Unpickling compatibility for ``entity_classifier.pkl``.

Training was run as ``python -m app.ml.training.train_entity``, so XGBoost may
serialize a callback class as ``__main__._EntityEpochLogger``. At inference time
``joblib.load`` must find that name on ``sys.modules['__main__']``.
"""
from __future__ import annotations

import sys


def ensure_entity_epoch_logger_on_main() -> None:
    """Register a stub ``_EntityEpochLogger`` on ``__main__`` before loading the pickle."""
    try:
        from xgboost.callback import TrainingCallback as _TC
    except Exception:
        return

    class _EntityEpochLogger(_TC):  # noqa: N801 — must match pickled global name
        def after_iteration(self, model, epoch, evals_log):
            return False

    main = sys.modules.get("__main__")
    if main is None:
        return
    if getattr(main, "_EntityEpochLogger", None) is not None:
        return
    try:
        setattr(main, "_EntityEpochLogger", _EntityEpochLogger)
    except (AttributeError, TypeError):
        # Rare: read-only __main__ (e.g. some embedded interpreters)
        pass
