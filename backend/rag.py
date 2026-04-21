import hashlib
import logging
import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

log = logging.getLogger("rag")

_COLLECTION = "campaign_data"

# ── ChromaDB client ───────────────────────────────────────────────────────────
try:
    _client = chromadb.EphemeralClient()
    log.info("[RAG] ChromaDB EphemeralClient initialised")
except AttributeError:
    _client = chromadb.Client()
    log.info("[RAG] ChromaDB Client (legacy) initialised")
except Exception as e:
    log.error(f"[RAG] ChromaDB init FAILED: {e}")
    raise

# ── Embedding function — lightweight default (~50MB vs 400MB for MiniLM) ──────
try:
    _ef = DefaultEmbeddingFunction()
    log.info("[RAG] DefaultEmbeddingFunction loaded")
except Exception as e:
    log.error(f"[RAG] Embedding function init FAILED: {e}")
    raise


def _get_or_create() -> chromadb.Collection:
    try:
        col = _client.get_collection(_COLLECTION, embedding_function=_ef)
        log.debug(f"[RAG] Got existing collection '{_COLLECTION}' ({col.count()} docs)")
        return col
    except Exception:
        col = _client.create_collection(_COLLECTION, embedding_function=_ef)
        log.info(f"[RAG] Created new collection '{_COLLECTION}'")
        return col


def _reset() -> chromadb.Collection:
    try:
        _client.delete_collection(_COLLECTION)
        log.info(f"[RAG] Deleted old collection '{_COLLECTION}'")
    except Exception:
        pass
    col = _client.create_collection(_COLLECTION, embedding_function=_ef)
    log.info(f"[RAG] Created fresh collection '{_COLLECTION}'")
    return col


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
    log.info(f"[RAG] build_index called — df rows={len(df)}, campaigns={len(camp_summary)}")
    col = _reset()
    docs, ids = [], []

    # KPI summary
    kpi_text = "Overall KPI Summary: " + ", ".join(f"{k}: {v}" for k, v in kpis.items())
    docs.append(kpi_text); ids.append(_doc_id(kpi_text))

    # Daily rows
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

    # Campaign aggregates
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

    for ins in insights:
        docs.append(f"Insight: {ins}"); ids.append(_doc_id(ins))
    for act in actions:
        docs.append(f"Recommended action: {act}"); ids.append(_doc_id(act))
    for pat in patterns:
        docs.append(f"Detected pattern: {pat}"); ids.append(_doc_id(pat))

    waste_text = (
        f"Financial impact: estimated wasted spend=${waste.get('total_wasted', 0):.2f}, "
        f"worst campaign='{waste.get('worst_campaign', 'N/A')}', "
        f"recoverable savings=${waste.get('savings_opportunity', 0):.2f}"
    )
    docs.append(waste_text); ids.append(_doc_id(waste_text))

    for row in allocation:
        text = (
            f"Budget allocation for '{row.get('campaign')}': "
            f"score={row.get('score', 0)}, "
            f"share={row.get('budget_share_pct', 0)}%, "
            f"recommended budget=${row.get('recommended_budget', 0):.2f}"
        )
        docs.append(text); ids.append(_doc_id(text))

    pred_text = (
        f"7-day predictions: expected leads={predictions.get('predicted_leads', 0)}, "
        f"trend={predictions.get('trend', 'N/A')}, "
        f"growth rate={predictions.get('growth_rate_pct', 0)}%"
    )
    docs.append(pred_text); ids.append(_doc_id(pred_text))

    # Deduplicate
    seen, unique_docs, unique_ids = set(), [], []
    for d, i in zip(docs, ids):
        if i not in seen:
            seen.add(i); unique_docs.append(d); unique_ids.append(i)

    log.info(f"[RAG] Upserting {len(unique_docs)} unique documents into ChromaDB")
    BATCH = 100
    for start in range(0, len(unique_docs), BATCH):
        try:
            col.upsert(
                documents=unique_docs[start:start + BATCH],
                ids=unique_ids[start:start + BATCH],
            )
        except Exception as e:
            log.error(f"[RAG] Upsert batch {start}–{start+BATCH} FAILED: {e}")
            raise

    log.info(f"[RAG] Index built successfully — {col.count()} documents indexed")


def query_rag(question: str, n_results: int = 6) -> str:
    try:
        col = _get_or_create()
        count = col.count()
        log.info(f"[RAG] query_rag called — collection has {count} docs, question='{question[:60]}'")
        if count == 0:
            log.warning("[RAG] Collection is empty — no context will be returned")
            return ""
        n = min(n_results, count)
        results = col.query(query_texts=[question], n_results=n)
        chunks = results.get("documents", [[]])[0]
        log.info(f"[RAG] Retrieved {len(chunks)} chunks")
        return "\n".join(chunks)
    except Exception as e:
        log.error(f"[RAG] query_rag FAILED: {e}")
        return ""
