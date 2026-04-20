"""
RAG engine — builds an in-memory ChromaDB collection from campaign data
and retrieves the most relevant chunks for a user query.

The collection is rebuilt every time new data is loaded (upload / refresh).
Embeddings use a local HuggingFace model — no API key needed.
"""

import hashlib
from typing import Optional
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

# Singleton in-memory client — lives for the process lifetime
_client = chromadb.Client()
_COLLECTION = "campaign_data"
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def _get_or_create() -> chromadb.Collection:
    try:
        return _client.get_collection(_COLLECTION, embedding_function=_ef)
    except Exception:
        return _client.create_collection(_COLLECTION, embedding_function=_ef)


def _reset() -> chromadb.Collection:
    try:
        _client.delete_collection(_COLLECTION)
    except Exception:
        pass
    return _client.create_collection(_COLLECTION, embedding_function=_ef)


def _doc_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def build_index(
    df: pd.DataFrame,
    camp_summary: pd.DataFrame,
    kpis: dict,
    insights: list,
    actions: list,
    patterns: list,
    waste: dict,
    allocation: list,
    predictions: dict,
) -> None:
    """
    Convert all analytics data into text chunks and index them into ChromaDB.
    Called after every upload / refresh so the chatbot always has fresh context.
    """
    col = _reset()
    docs, ids = [], []

    # ── KPI summary ──────────────────────────────────────────────────────────
    kpi_text = "Overall KPI Summary: " + ", ".join(f"{k}: {v}" for k, v in kpis.items())
    docs.append(kpi_text); ids.append(_doc_id(kpi_text))

    # ── Per-campaign daily rows ───────────────────────────────────────────────
    for _, row in df.iterrows():
        text = (
            f"Campaign '{row['campaign']}' on {row['date']}: "
            f"impressions={int(row.get('impressions', 0))}, "
            f"clicks={int(row.get('clicks', 0))}, "
            f"spend=${float(row.get('spend', 0)):.2f}, "
            f"leads={int(row.get('leads', 0))}, "
            f"CTR={float(row.get('ctr', 0) or 0):.2f}%, "
            f"CPL=${float(row.get('cpl', 0) or 0):.2f}"
        )
        docs.append(text); ids.append(_doc_id(text))

    # ── Campaign aggregate summary ────────────────────────────────────────────
    for _, row in camp_summary.iterrows():
        text = (
            f"Campaign aggregate for '{row['campaign']}': "
            f"total spend=${float(row.get('spend', 0)):.2f}, "
            f"total leads={int(row.get('leads', 0))}, "
            f"avg CTR={float(row.get('ctr', 0) or 0):.2f}%, "
            f"avg CPL=${float(row.get('cpl', 0) or 0):.2f}, "
            f"conversion rate={float(row.get('conversion_rate', 0) or 0):.2f}%"
        )
        docs.append(text); ids.append(_doc_id(text))

    # ── Insights ──────────────────────────────────────────────────────────────
    for ins in insights:
        docs.append(f"Insight: {ins}"); ids.append(_doc_id(ins))

    # ── Recommended actions ───────────────────────────────────────────────────
    for act in actions:
        docs.append(f"Recommended action: {act}"); ids.append(_doc_id(act))

    # ── Patterns ──────────────────────────────────────────────────────────────
    for pat in patterns:
        docs.append(f"Detected pattern: {pat}"); ids.append(_doc_id(pat))

    # ── Waste / financial impact ──────────────────────────────────────────────
    waste_text = (
        f"Financial impact: estimated wasted spend=${waste.get('total_wasted', 0):.2f}, "
        f"worst campaign='{waste.get('worst_campaign', 'N/A')}', "
        f"recoverable savings=${waste.get('savings_opportunity', 0):.2f}"
    )
    docs.append(waste_text); ids.append(_doc_id(waste_text))

    # ── Budget allocation ─────────────────────────────────────────────────────
    for row in allocation:
        text = (
            f"Budget allocation for '{row.get('campaign')}': "
            f"score={row.get('score', 0)}, "
            f"share={row.get('budget_share_pct', 0)}%, "
            f"recommended budget=${row.get('recommended_budget', 0):.2f}"
        )
        docs.append(text); ids.append(_doc_id(text))

    # ── Predictions ───────────────────────────────────────────────────────────
    pred_text = (
        f"7-day predictions: expected leads={predictions.get('predicted_leads', 0)}, "
        f"trend={predictions.get('trend', 'N/A')}, "
        f"growth rate={predictions.get('growth_rate_pct', 0)}%"
    )
    docs.append(pred_text); ids.append(_doc_id(pred_text))

    # Deduplicate by id
    seen, unique_docs, unique_ids = set(), [], []
    for d, i in zip(docs, ids):
        if i not in seen:
            seen.add(i); unique_docs.append(d); unique_ids.append(i)

    # Batch upsert
    BATCH = 100
    for start in range(0, len(unique_docs), BATCH):
        col.upsert(
            documents=unique_docs[start:start + BATCH],
            ids=unique_ids[start:start + BATCH],
        )


def query_rag(question: str, n_results: int = 6) -> str:
    """Return the top-n most relevant text chunks for a question."""
    try:
        col = _get_or_create()
        if col.count() == 0:
            return ""
        results = col.query(query_texts=[question], n_results=min(n_results, col.count()))
        chunks = results.get("documents", [[]])[0]
        return "\n".join(chunks)
    except Exception:
        return ""
