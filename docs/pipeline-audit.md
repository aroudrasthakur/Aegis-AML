# Cicada AML Risk Pipeline Audit

**Date:** 2026-04-04  
**Scope:** Read-only architecture review of the scoring pipeline, data model, API layer, and UI wiring.

---

## Findings Summary

| # | Severity | Area | Finding |
|---|----------|------|---------|
| 1 | **P0** | Scoring | `execute_pipeline_run` step 6 uses a narrower suspicious-selection filter than `_collect_suspicious_transactions`, dropping `medium-low` rows and heuristic-only triggers. |
| 2 | **P0** | Threshold | `threshold_config.json` is not committed to the repo. The `GET /runs/model/threshold` endpoint returns `null` when artifacts don't exist, which causes the frontend to have no risk tier boundaries until a model is trained. |
| 3 | **P1** | Scoring | The meta-learner fallback (weighted average) uses fixed weights (0.225 behavioral, 0.175 graph/temporal, etc.) that are not documented or configurable. In the absence of a trained meta model, risk scores are driven by arbitrary coefficients. |
| 4 | **P1** | Storage | `run_scores` stores `heuristic_triggered` as a JSON string, but `heuristic_top_typo` and `heuristic_top_conf` are separate columns. The frontend has no API to query individual heuristic results per transaction. |
| 5 | **P1** | API | `get_run_wallets` (newly added) joins `run_cluster_members` via cluster, but the Supabase query `eq("cluster_id.run_id", run_id)` relies on a foreign-key join filter that may not work as expected with the Supabase JS client. Needs testing. |
| 6 | **P2** | Scoring | `_classify_typology` assigns typology labels based on simple degree thresholds (fan-in/fan-out > 10, cycles > 3). These are heuristic and not calibrated against ground truth. |
| 7 | **P2** | Pipeline | Cluster `risk_score` is computed as `len(risky_wallets) / len(component)`, which is a density metric rather than an actual risk score. A cluster with 2 risky wallets out of 2 total gets risk 1.0, while one with 50 risky out of 100 gets 0.5. |
| 8 | **P2** | Storage | `run_graph_snapshots.elements` stores Cytoscape elements, but `_annotate_cytoscape` only annotates nodes matching `transaction_id` — wallet-level nodes are not annotated with risk scores. |
| 9 | **P2** | UI | FlowTimeline passes empty `transactions=[]` on the wallet detail page, so the timeline chart never renders actual data. |
| 10 | **P3** | API | The `GET /runs/model/metrics` and `GET /runs/model/threshold` endpoints search for files in `models/artifacts/` and `../models/artifacts/` — the fallback path depends on the CWD of the FastAPI process, which is fragile. |

---

## Architecture Overview

```
Upload CSVs → create_run (pending)
                  ↓
              start_run → execute_pipeline_run (background)
                  ↓
         1. Merge + clean DataFrames
         2. Persist run_transactions
         3. Build wallet graph (NetworkX DiGraph)
         4. Score transactions (InferencePipeline)
            ├─ Feature extraction (compute_all_features)
            ├─ Heuristics (185 registered, run_all)
            ├─ Parallel lenses: behavioral, graph, temporal, offramp
            ├─ Entity lens (depends on graph embeddings)
            ├─ Meta-learner (XGBoost or weighted fallback)
            └─ Threshold decision
         5. Persist run_scores
         6. Identify suspicious transactions
         7. Detect clusters (connected components in undirected graph)
         8. Persist clusters, members, suspicious_txns
         9. Cytoscape graph snapshots per cluster
        10. Generate structured report (run_reports)
        11. Mark run completed
```

### Scoring Flow (per transaction)

1. **Features:** `compute_all_features(transactions, graph)` returns transaction-level and combined feature matrices.
2. **Heuristics:** `run_all(tx, wallet, graph, features, context)` evaluates all 185 registered heuristics. Returns a confidence vector, applicability vector, triggered IDs, and top typology.
3. **Lenses:** Four lenses run in parallel via `ThreadPoolExecutor(max_workers=4)`:
   - **Behavioral:** XGBoost + autoencoder anomaly score
   - **Graph:** GNN/GCN on wallet graph node features
   - **Temporal:** Time-series features per wallet
   - **Offramp:** Classifies likely off-ramp patterns
4. **Entity lens:** Runs after graph (needs embeddings). Classifies entity-level risk.
5. **Meta-learner:** Stacks all 6 lens scores + heuristic aggregates + data availability flags. Uses `predict_proba` from trained model, or a weighted average fallback.
6. **Threshold:** Maps `meta_score` to `risk_level` using `threshold_config`:
   - `>= high_risk_threshold` → `high`
   - `>= decision_threshold` → `medium`
   - `<= low_risk_ceiling` → `low`
   - else → `medium-low`

### Data Model (run-scoped tables)

| Table | Key columns | Notes |
|-------|-------------|-------|
| `pipeline_runs` | id, user_id, status, total_txns, suspicious_tx_count, suspicious_cluster_count | Parent record |
| `run_transactions` | run_id, transaction_id, sender_wallet, receiver_wallet, amount, timestamp | Raw uploaded data |
| `run_scores` | run_id, transaction_id, meta_score, risk_level, behavioral_score, graph_score, entity_score, temporal_score, offramp_score | Per-tx scoring output |
| `run_suspicious_txns` | run_id, transaction_id, meta_score, risk_level, typology, cluster_id | Filtered subset |
| `run_clusters` | run_id, label, typology, risk_score, total_amount, wallet_count, tx_count | Cluster-level aggregation |
| `run_cluster_members` | cluster_id, wallet_address | Wallet membership |
| `run_reports` | run_id, title, content (JSONB) | Structured report |
| `run_graph_snapshots` | run_id, cluster_id, elements (JSONB) | Cytoscape visualization data |

### Threshold Configuration

The backend loads thresholds from `models/artifacts/threshold_config.json`. Expected shape:

```json
{
  "decision_threshold": 0.45,
  "high_risk_threshold": 0.85,
  "low_risk_ceiling": 0.25,
  "optimal_threshold": 0.45,
  "optimal_f1": 0.72,
  "precision_at_threshold": 0.68,
  "recall_at_threshold": 0.78,
  "min_recall_target": 0.60
}
```

When absent, the pipeline falls back to `{"decision_threshold": 0.5, "high_risk_threshold": 0.9, "low_risk_ceiling": 0.3}` from `settings.fallback_risk_threshold`.

---

## Detailed Findings

### P0-1: Suspicious Selection Inconsistency

`pipeline_run_service.py` defines `_collect_suspicious_transactions()` which correctly includes:
- Scores above decision threshold
- Non-low risk levels (including `medium-low`)
- Rows with illicit/suspicious CSV labels
- Heuristic triggers with confidence >= 0.15

However, `execute_pipeline_run` step 6 **does not call this function**. Instead, it uses an inline filter:

```python
suspicious = [
    r for r in results
    if (r.get("meta_score") or 0) >= threshold
    or r.get("risk_level") in ("medium", "high")
]
```

This drops all `medium-low` rows and ignores heuristic-only triggers. When the trained `decision_threshold` is high (e.g., 0.7+), many elevated transactions are silently excluded from the suspicious set, clusters, and reports.

**Recommendation:** Replace the inline filter with `_collect_suspicious_transactions(results, threshold, tx_by_id)`.

### P0-2: Missing Threshold Artifacts

`threshold_config.json` is not committed to the repository. The frontend `ThresholdProvider` fetches `GET /runs/model/threshold` which returns `{threshold: null}`. Without this config:
- The frontend shows no risk tier badges (correct behavior per Phase 1)
- The backend uses hardcoded fallback thresholds

**Recommendation:** Either commit a default `threshold_config.json` to the repo or ensure the training pipeline always produces one. Document the expected shape.

### P1-3: Meta-Learner Fallback Weights

When no trained meta-model exists, the pipeline uses:

```python
weights = {
    "behavioral_score": 0.225, "graph_score": 0.175,
    "entity_score": 0.125, "temporal_score": 0.175,
    "offramp_score": 0.125, "heuristic_max": 0.175,
}
```

These weights are not documented, configurable, or derived from any calibration. They could be moved to a config file or at minimum documented with rationale.

### P1-4: Heuristic Data Not Exposed

`run_scores.heuristic_triggered` stores a JSON array of triggered heuristic IDs, but there is no API endpoint to query this data. The frontend currently shows `heuristics_count: 0` for all transactions because the count is never populated from the stored data.

**Recommendation:** Add `heuristic_triggered` and `heuristic_top_typo` to the `GET /runs/{id}/scores` response, and populate `heuristics_count` in the suspicious-transactions mapping.

### P2-7: Cluster Risk Score is Density, Not Risk

`_detect_clusters` computes:

```python
"risk_score": len(risky) / max(len(component), 1)
```

This is the fraction of high-risk wallets in the connected component, not an actual risk aggregation. A 2-wallet cluster where both are suspicious gets risk 1.0, while a 100-wallet cluster with 50 suspicious wallets gets 0.5.

**Recommendation:** Consider using `max(meta_score)` or `mean(meta_score)` of constituent suspicious transactions as the cluster risk score.

---

## Appendix: File Impact Map

### Backend (scoring)
- `backend/app/ml/infer_pipeline.py` — Core pipeline orchestration
- `backend/app/services/pipeline_run_service.py` — Run execution and persistence
- `backend/app/ml/heuristics/` — 185 heuristic implementations (5 modules)
- `backend/app/ml/lenses/` — 5 lens models (behavioral, graph, entity, temporal, offramp)
- `backend/app/services/feature_service.py` — Feature extraction
- `backend/app/services/graph_service.py` — Graph construction and node features

### Backend (API)
- `backend/app/api/routes_runs.py` — All run-scoped endpoints
- `backend/app/repositories/runs_repo.py` — Database operations

### Frontend (consumers)
- `frontend/src/utils/riskTiers.ts` — Centralized tier mapping from API config
- `frontend/src/contexts/ThresholdProvider.tsx` — Threshold context
- `frontend/src/pages/DashboardPage.tsx` — Run-scoped dashboard
- `frontend/src/pages/TransactionsPage.tsx` — Run-scoped transactions
- `frontend/src/pages/WalletPage.tsx` — Wallet listing and detail
- `frontend/src/pages/FlowExplorerPage.tsx` — API-driven cluster visualization
- `frontend/src/components/flow-explorer/NodeInspectPanel.tsx` — Node detail from run data

### Data
- `supabase/migrations/018_create_pipeline_runs.sql` — Run-scoped schema
- `supabase/migrations/019_pipeline_runs_user_scoping.sql` — RLS policies
- `models/artifacts/threshold_config.json` — **Missing from repo** (produced by training)
