"""Tests for heuristic context enrichment and requirement aliases."""
import networkx as nx

from app.ml.heuristics.base import Applicability, BaseHeuristic
from app.ml.infer_pipeline import InferencePipeline


def test_timestamp_requirement_satisfied_via_timestamps_list():
    assert BaseHeuristic._requirement_satisfied(
        "timestamp",
        {"timestamp": None, "timestamps": ["2024-01-01", "2024-01-02"]},
    )
    assert not BaseHeuristic._requirement_satisfied("timestamp", {"timestamps": []})


def test_build_tx_context_includes_timestamp_and_deposit_patterns():
    g = nx.DiGraph()
    g.add_edge("a", "recv", amount=1.0)
    g.add_edge("b", "recv", amount=2.0)
    wp = {
        "address": "recv",
        "amounts": [1.0, 2.0],
        "timestamps": ["t1", "t2"],
        "balances": [0.0],
        "total_in": 3.0,
        "total_out": 0.0,
        "tx_count": 2,
    }
    tx = {"transaction_id": "x", "timestamp": "t2", "sender_wallet": "b", "receiver_wallet": "recv"}
    ctx = InferencePipeline._build_tx_context(tx, wp, {}, g)
    assert ctx["timestamp"] == "t2"
    assert set(ctx["deposit_patterns"]) == {"a", "b"}
    assert ctx["timestamps"] == ["t1", "t2"]


def test_stub_heuristics_have_empty_data_requirements_and_metadata():
    from app.ml.heuristics import registry

    import app.ml.heuristics.traditional  # noqa: F401
    import app.ml.heuristics.blockchain  # noqa: F401
    import app.ml.heuristics.hybrid  # noqa: F401
    import app.ml.heuristics.ai_enabled  # noqa: F401

    h2 = registry.get(2)
    assert h2 is not None
    assert h2.data_requirements == []
    assert getattr(h2, "offchain_requirements", None) == ["revenue_data"]

    h119 = registry.get(119)
    assert h119 is not None
    assert h119.data_requirements == []


def test_real_heuristic_still_inapplicable_without_context():
    from app.ml.heuristics.traditional import CashStructuring

    h = CashStructuring()
    assert h.check_data_requirements(None) == Applicability.INAPPLICABLE_MISSING_DATA
