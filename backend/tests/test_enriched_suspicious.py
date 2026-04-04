"""Tests for merging suspicious txns with run_transactions and run_scores."""
import json

from app.repositories import runs_repo


def test_parse_triggered_ids():
    assert runs_repo._parse_triggered_ids(None) == []
    assert runs_repo._parse_triggered_ids([]) == []
    assert runs_repo._parse_triggered_ids([91, 92]) == [91, 92]
    assert runs_repo._parse_triggered_ids(json.dumps([1, 2, 3])) == [1, 2, 3]
    assert runs_repo._parse_triggered_ids("not json") == []
    assert runs_repo._parse_triggered_ids("   ") == []
