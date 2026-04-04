"""Off-ramp Lens: conversion and exit pattern detection."""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OfframpLens:
    LENS_TAGS = ["offramp"]

    def __init__(self):
        self.classifier = None

    def _select_features(self, features_df: pd.DataFrame, heuristic_scores: np.ndarray = None) -> np.ndarray:
        """Select the same offramp features used during training.

        Training uses 8 offramp columns + 4 heuristic aggregate columns.
        The raw 185-element heuristic vector is intentionally excluded to keep
        the feature space aligned with training.
        """
        offramp_cols = [c for c in features_df.columns if c in {
            "fan_in_ratio", "weighted_in", "in_degree",
            "suspicious_neighbor_ratio_1hop", "suspicious_neighbor_ratio_2hop",
            "amount", "log_amount", "relay_pattern_score",
        }]
        feat = features_df[offramp_cols].fillna(0).values if offramp_cols else np.zeros((len(features_df), 1))
        return feat.astype(np.float32)

    def predict(self, features_df: pd.DataFrame, heuristic_scores: np.ndarray = None, context: dict = None) -> dict:
        X = self._select_features(features_df, heuristic_scores)
        if self.classifier is not None:
            scores = self.classifier.predict_proba(X)[:, 1] if hasattr(self.classifier, 'predict_proba') else self.classifier.predict(X)
        else:
            scores = np.zeros(X.shape[0])
        return {"offramp_score": scores}

    def load(self, model_path: str):
        p = Path(model_path)
        if p.exists():
            self.classifier = joblib.load(p)
            logger.info(f"Loaded off-ramp classifier from {p}")
