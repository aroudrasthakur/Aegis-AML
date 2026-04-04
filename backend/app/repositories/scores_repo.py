from __future__ import annotations

from app.supabase_client import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)


def upsert_transaction_scores(records: list[dict]) -> list[dict]:
    if not records:
        return []
    try:
        sb = get_supabase()
        resp = sb.table("transaction_scores").upsert(
            records, on_conflict="transaction_id"
        ).execute()
        return list(resp.data or [])
    except Exception:
        logger.exception("upsert_transaction_scores failed for %d records", len(records))
        return []


def get_transaction_scores_batch(transaction_ids: list[str]) -> dict[str, dict]:
    """Fetch scores for multiple transactions in a single query."""
    if not transaction_ids:
        return {}
    try:
        sb = get_supabase()
        resp = (
            sb.table("transaction_scores")
            .select("*")
            .in_("transaction_id", transaction_ids)
            .execute()
        )
        return {row["transaction_id"]: row for row in (resp.data or []) if "transaction_id" in row}
    except Exception:
        logger.exception("get_transaction_scores_batch failed for %d ids", len(transaction_ids))
        return {}


def get_transaction_score(transaction_id: str) -> dict | None:
    try:
        sb = get_supabase()
        resp = (
            sb.table("transaction_scores")
            .select("*")
            .eq("transaction_id", transaction_id)
            .maybe_single()
            .execute()
        )
        if resp is None:
            return None
        return resp.data
    except Exception:
        logger.exception("get_transaction_score failed for %s", transaction_id)
        return None


def upsert_wallet_scores(records: list[dict]) -> list[dict]:
    if not records:
        return []
    try:
        sb = get_supabase()
        resp = sb.table("wallet_scores").upsert(
            records, on_conflict="wallet_address"
        ).execute()
        return list(resp.data or [])
    except Exception:
        logger.exception("upsert_wallet_scores failed for %d records", len(records))
        return []


def get_wallet_score(wallet_address: str) -> dict | None:
    try:
        sb = get_supabase()
        resp = (
            sb.table("wallet_scores")
            .select("*")
            .eq("wallet_address", wallet_address)
            .maybe_single()
            .execute()
        )
        if resp is None:
            return None
        return resp.data
    except Exception:
        logger.exception("get_wallet_score failed for %s", wallet_address)
        return None
