"""Temporal Lens: LSTM-based temporal anomaly detection."""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from pathlib import Path

from app.ml.ml_device import resolve_torch_device
from app.utils.logger import get_logger

logger = get_logger(__name__)

MAX_SEQ_LEN = 50


class TemporalLSTM(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, dropout=dropout, batch_first=True)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = self.classifier(h_n[-1])
        return out.squeeze(-1)


class TemporalLens:
    LENS_TAGS = ["temporal"]

    def __init__(self):
        self.model = None
        self.input_dim = None
        self._device = None

    def _build_sequence(self, df: pd.DataFrame, wallet: str) -> np.ndarray:
        # Kept for backward compatibility if called directly, but predict() is now vectorized
        pass

    def predict(self, transactions_df: pd.DataFrame, wallets: list[str], heuristic_scores: np.ndarray = None) -> dict:
        """Score temporal risk for all wallets in a single batched GPU call."""
        if not wallets:
            return {"temporal_scores": {}}

        sender_col = "sender_wallet" if "sender_wallet" in transactions_df.columns else "sender"
        receiver_col = "receiver_wallet" if "receiver_wallet" in transactions_df.columns else "receiver"

        work = transactions_df
        if "timestamp" in work.columns:
            work = work.sort_values("timestamp")

        from collections import defaultdict
        wallet_txns = defaultdict(list)

        senders = work[sender_col].astype(str).values if sender_col in work.columns else np.zeros(len(work), dtype=str)
        receivers = work[receiver_col].astype(str).values if receiver_col in work.columns else np.zeros(len(work), dtype=str)

        wallet_set = set(wallets)
        for i in range(len(work)):
            s = senders[i]
            r = receivers[i]
            if s in wallet_set:
                wallet_txns[s].append(i)
            if r in wallet_set and r != s:
                wallet_txns[r].append(i)

        amt = work["amount"].fillna(0).to_numpy(dtype=np.float32) if "amount" in work.columns else np.zeros(len(work), dtype=np.float32)
        tspo = work["time_since_prev_out"].fillna(0).to_numpy(dtype=np.float32) if "time_since_prev_out" in work.columns else np.zeros(len(work), dtype=np.float32)
        burst = work["burstiness_score"].fillna(0).to_numpy(dtype=np.float32) if "burstiness_score" in work.columns else np.zeros(len(work), dtype=np.float32)

        input_dim = self.input_dim if self.input_dim is not None else 4
        batch = np.zeros((len(wallets), MAX_SEQ_LEN, input_dim), dtype=np.float32)

        for wi, w in enumerate(wallets):
            idxs = wallet_txns[w][-MAX_SEQ_LEN:]
            for si, ti in enumerate(idxs):
                offset = MAX_SEQ_LEN - len(idxs) + si
                batch[wi, offset, 0] = amt[ti]
                batch[wi, offset, 1] = tspo[ti]
                batch[wi, offset, 2] = 1.0 if senders[ti] == w else 0.0
                batch[wi, offset, 3] = burst[ti]

        scores: dict[str, float] = {}
        if self.model is not None:
            device = self._device or resolve_torch_device()
            self.model.eval()
            with torch.no_grad():
                tensor = torch.from_numpy(batch).to(device)
                logits = self.model(tensor).cpu().numpy()  # (W,)
                probs = 1.0 / (1.0 + np.exp(-logits))
            for i, w in enumerate(wallets):
                scores[w] = float(probs[i])
        else:
            for w in wallets:
                scores[w] = 0.0

        return {"temporal_scores": scores}

    def load(self, model_path: str):
        p = Path(model_path)
        if p.exists():
            self._device = resolve_torch_device()
            state = torch.load(p, map_location=self._device, weights_only=True)
            input_dim = state.get("input_dim", 4)
            self.input_dim = input_dim
            self.model = TemporalLSTM(input_dim)
            self.model.load_state_dict(state["model_state_dict"])
            self.model.to(self._device)
            logger.info(f"Loaded temporal LSTM from {p} (device={self._device})")
