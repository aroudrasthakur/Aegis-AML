# Aegis AML Pipeline Audit

**Last verified:** 2026-04-09  
**Scope:** current state review of the run-scoped scoring pipeline, persistence layer, and investigation UI.

## Executive summary

The pipeline is materially stronger than the earlier audit snapshot. Several high-risk gaps have been addressed in code:

- suspicious selection now preserves `medium-low`, label-driven, and heuristic-driven rows
- cluster risk is now based on mean transaction `meta_score` rather than raw risky-wallet density
- Cytoscape snapshots are annotated at the wallet-node level with risk metadata
- run-scoped heuristic metadata is exposed back to the frontend through enriched suspicious rows
- wallet aggregation no longer relies on a fragile foreign-key join filter for member lookup
- wallet timelines are now populated from run suspicious data

The main remaining documentation-worthy caveat is artifact availability: trained `metrics_report.json` and `threshold_config.json` are still generated outputs rather than committed defaults.

## Findings status

| # | Prior issue | Current status | Notes |
| --- | --- | --- | --- |
| 1 | Suspicious-selection inconsistency | Resolved | `execute_pipeline_run()` now calls `_collect_suspicious_transactions()` |
| 2 | Missing threshold artifact in repo | Open | backend falls back safely, but `/api/runs/model/threshold` can still return `null` |
| 3 | Fallback meta weights undocumented | Partially resolved | weights are now documented in `README.md`, still hardcoded in inference |
| 4 | Heuristic data not exposed to UI | Resolved | enriched suspicious rows now include `heuristic_triggered`, labels, count, and top typology/confidence |
| 5 | Fragile wallet membership query | Resolved | `get_run_wallets()` now fetches cluster IDs then uses `in_("cluster_id", cluster_ids)` |
| 6 | Simplistic cluster typology logic | Improved | `infer_cluster_typology()` now mixes ground truth, heuristic voting, cross-chain detection, adaptive structure, and off-ramp evidence |
| 7 | Cluster risk was density, not risk | Resolved | cluster `risk_score` is mean `meta_score` across cluster transactions when available |
| 8 | Graph snapshots lacked wallet annotations | Resolved | `_annotate_cytoscape()` adds `meta_score`, `risk_level`, and suspicious flags to wallet nodes |
| 9 | Wallet timeline rendered no data | Resolved | `WalletPage.tsx` passes `walletTxs` into `FlowTimeline` |
| 10 | Artifact endpoint path fragility | Open | route still probes cwd-relative locations before returning artifact JSON |

## Current architecture

```text
Upload CSVs
  -> create pending run
  -> start background pipeline
  -> merge + clean data
  -> persist run_transactions
  -> build NetworkX wallet graph
  -> compute transaction, graph, and subgraph features
  -> run 185 heuristics per transaction
  -> run 5 batched ML lenses
  -> stack scores into meta-learner or fallback fusion
  -> assign risk tiers
  -> collect suspicious rows
  -> detect suspicious wallet clusters
  -> persist clusters, members, suspicious rows, graph snapshots, and report
```

## Verified technical details

### Suspicious selection logic

A transaction is currently retained for clustering and reporting if any of the following is true:

- `meta_score >= decision_threshold`
- `risk_level` is `high`, `medium`, or `medium-low`
- the source CSV label indicates illicit or suspicious behavior
- at least one heuristic fired and `heuristic_top_confidence >= 0.15`

This closes the most important recall gap from the prior audit.

### Cluster scoring and typology

Current cluster behavior in `backend/app/services/pipeline_run_service.py` and `backend/app/ml/typology_taxonomy.py`:

- suspicious wallets are grouped from connected components in the undirected transaction graph
- cluster risk defaults to mean transaction `meta_score` when cluster scoring rows exist
- typology inference prioritizes uploaded ground truth when present
- cross-chain activity is detected from chain diversity fields
- weighted heuristic voting is used before falling back to graph-only structure rules
- off-ramp pressure can override peel or layering defaults when exit behavior is strong

### Heuristic persistence and UI availability

`run_scores` now stores and the API now exposes:

- `heuristic_triggered`
- `heuristic_triggered_count`
- `heuristic_explanations`
- `heuristic_top_typo`
- `heuristic_top_conf`

`get_enriched_suspicious_txns()` additionally resolves heuristic IDs to display labels for the frontend.

## Remaining risks

### 1. Threshold artifacts are optional at runtime

If training artifacts are absent:

- backend inference falls back to `settings.fallback_risk_threshold` plus default high and low cutoffs
- `/api/runs/model/threshold` returns `{ "threshold": null }`
- frontend views can still render, but trained threshold metadata is unavailable

### 2. Artifact lookup is cwd-sensitive

`routes_runs.py` still searches both:

- `models/artifacts/...`
- `../models/artifacts/...`

This works in common local setups but remains more brittle than resolving from a single repo-root path helper.

### 3. Fallback fusion is still static

The weighted fallback meta score is now documented, but it is still a static coefficient mix rather than a configurable policy or learned calibration artifact.

## Recommended next steps

1. Commit a safe default `threshold_config.json` or generate one during bootstrap.
2. Resolve artifact loading through `app.ml.model_paths.MODELS_DIR` everywhere, including route handlers.
3. Move fallback fusion weights into explicit config to make scoring behavior easier to tune and test.
4. Add one regression test that asserts suspicious selection keeps heuristic-only and `medium-low` rows.

## File map

- `backend/app/services/pipeline_run_service.py`
- `backend/app/repositories/runs_repo.py`
- `backend/app/ml/infer_pipeline.py`
- `backend/app/ml/typology_taxonomy.py`
- `backend/app/api/routes_runs.py`
- `frontend/src/pages/WalletPage.tsx`
- `frontend/src/utils/flowExplorerFromRun.ts`
