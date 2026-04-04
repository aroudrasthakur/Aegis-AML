from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes_ingest import router as ingest_router
from app.api.routes_transactions import router as transactions_router
from app.api.routes_wallets import router as wallets_router
from app.api.routes_heuristics import router as heuristics_router
from app.api.routes_networks import router as networks_router
from app.api.routes_explanations import router as explanations_router
from app.api.routes_reports import router as reports_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_policies import router as policies_router
from app.api.routes_runs import router as runs_router

app = FastAPI(
    title="Cicada AML",
    description="AI-Powered Blockchain Laundering Detection and Investigation Dashboard",
    version="0.1.0",
)

_ALLOWED_ORIGINS = [
    f"http://localhost:{settings.frontend_port}",
    f"http://127.0.0.1:{settings.frontend_port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(wallets_router, prefix="/api/wallets", tags=["Wallets"])
app.include_router(heuristics_router, prefix="/api/heuristics", tags=["Heuristics"])
app.include_router(networks_router, prefix="/api/networks", tags=["Networks"])
app.include_router(explanations_router, prefix="/api/explanations", tags=["Explanations"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(policies_router, prefix="/api/policies", tags=["Policies"])
app.include_router(runs_router, prefix="/api/runs", tags=["Pipeline Runs"])


@app.get("/health")
async def health():
    return {"status": "ok"}
