"""Explanation endpoints."""
from fastapi import APIRouter, HTTPException
from app.services.explanation_service import explain_transaction, explain_case
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{transaction_id}")
async def get_transaction_explanation(transaction_id: str):
    try:
        explanation = explain_transaction(transaction_id)
        if not explanation:
            raise HTTPException(404, "No explanation available")
        return explanation
    except HTTPException:
        raise
    except Exception:
        logger.exception("Explanation failed for transaction %s", transaction_id)
        raise HTTPException(500, "Internal server error")


@router.get("/case/{case_id}")
async def get_case_explanation(case_id: str):
    try:
        explanation = explain_case(case_id)
        if not explanation:
            raise HTTPException(404, "No explanation available")
        return explanation
    except HTTPException:
        raise
    except Exception:
        logger.exception("Explanation failed for case %s", case_id)
        raise HTTPException(500, "Internal server error")
