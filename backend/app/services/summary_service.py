"""LLM-powered report summary generation using OpenAI."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.config import settings
from app.repositories import runs_repo
from app.supabase_client import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are an AML compliance analyst assistant. Given a structured pipeline run report in JSON format, produce a concise, professional summary suitable for a Suspicious Activity Report (SAR) narrative.

Focus on:
- Key findings: how many transactions were flagged, cluster patterns, dominant typologies
- Risk assessment: what risk levels were observed and their distribution
- Actionable items: which clusters or transactions warrant immediate investigation
- Keep the summary under 500 words
- Use plain language suitable for compliance officers
- Do NOT include raw numbers from the JSON — synthesize and interpret"""


def _get_openai_client():
    """Lazy-import openai to avoid startup failure when key is not set."""
    try:
        import openai
    except ImportError:
        raise RuntimeError("openai package is not installed. Run: pip install openai")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return openai.OpenAI(**kwargs)


def _truncate_content(content: dict, max_chars: int = 12000) -> str:
    """Serialize report content to JSON, truncating if too long for the prompt."""
    text = json.dumps(content, indent=2, default=str)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n... [truncated]"
    return text


def generate_run_report_summary(
    run_id: str,
    *,
    force: bool = False,
) -> dict:
    """Generate (or return cached) an LLM summary for a run report.

    Returns dict with summary_text, summary_model, summary_generated_at.
    """
    report = runs_repo.get_run_report(run_id)
    if not report:
        raise ValueError(f"No report found for run {run_id}")

    if not force and report.get("summary_text"):
        return {
            "summary_text": report["summary_text"],
            "summary_model": report.get("summary_model"),
            "summary_generated_at": report.get("summary_generated_at"),
            "cached": True,
        }

    content = report.get("content", {})
    content_str = _truncate_content(content)

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize this pipeline run report:\n\n{content_str}"},
        ],
        max_tokens=800,
        temperature=0.3,
    )

    summary_text = response.choices[0].message.content or ""
    model_used = response.model or settings.openai_model
    generated_at = datetime.now(timezone.utc).isoformat()

    sb = get_supabase()
    sb.table("run_reports").update({
        "summary_text": summary_text,
        "summary_model": model_used,
        "summary_generated_at": generated_at,
        "summary_prompt_version": PROMPT_VERSION,
    }).eq("id", report["id"]).execute()

    logger.info("Generated summary for run %s report %s (%d chars)",
                run_id, report["id"], len(summary_text))

    return {
        "summary_text": summary_text,
        "summary_model": model_used,
        "summary_generated_at": generated_at,
        "cached": False,
    }


def get_run_report_summary(run_id: str) -> dict | None:
    """Return cached summary for a run report, or None if not generated."""
    report = runs_repo.get_run_report(run_id)
    if not report or not report.get("summary_text"):
        return None
    return {
        "summary_text": report["summary_text"],
        "summary_model": report.get("summary_model"),
        "summary_generated_at": report.get("summary_generated_at"),
    }
