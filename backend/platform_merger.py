"""
Platform merger — normalises Google Ads and Meta Ads API responses into a
unified campaign format, deduplicates, and provides fuzzy client matching.
"""

from __future__ import annotations
from typing import Optional


# ── Normalisation ──────────────────────────────────────────────────────────────

def normalise_google_campaign(result: dict, date_str: Optional[str] = None) -> dict:
    """
    Convert a single Google Ads GAQL result row into unified format.
    Handles cost_micros → spend conversion and string → number coercion.
    """
    camp = result.get("campaign", {})
    metrics = result.get("metrics", {})
    seg = result.get("segments", {})

    cost_micros = int(metrics.get("cost_micros", 0) or 0)
    spend = round(cost_micros / 1_000_000, 2)
    impressions = int(metrics.get("impressions", 0) or 0)
    clicks = int(metrics.get("clicks", 0) or 0)
    conversions = float(metrics.get("conversions", 0) or 0)
    leads = int(conversions)

    return {
        "platform": "google_ads",
        "platform_campaign_id": str(camp.get("id", "")),
        "campaign_name": camp.get("name", "Unknown"),
        "date": date_str or seg.get("date", ""),
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "leads": leads,
        "revenue": float(metrics.get("conversions_value", 0) or 0),
        "ctr": round(clicks / impressions * 100, 4) if impressions else 0.0,
        "cpl": round(spend / leads, 2) if leads else 0.0,
        "conversion_rate": round(leads / clicks * 100, 2) if clicks else 0.0,
    }


def normalise_meta_campaign(campaign: dict, insight: dict) -> dict:
    """
    Convert a Meta Graph API campaign + insight row into unified format.
    Extracts leads from actions array (action_type == 'lead').
    """
    actions = insight.get("actions", [])
    leads = next(
        (int(a.get("value", 0)) for a in actions if a.get("action_type") == "lead"),
        0
    )
    impressions = int(insight.get("impressions", 0) or 0)
    clicks = int(insight.get("clicks", 0) or 0)
    spend = float(insight.get("spend", 0) or 0)

    return {
        "platform": "meta_ads",
        "platform_campaign_id": str(campaign.get("id", "")),
        "campaign_name": campaign.get("name", "Unknown"),
        "date": insight.get("date_start", ""),
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "leads": leads,
        "revenue": 0.0,  # Meta doesn't return revenue directly without pixel
        "ctr": round(clicks / impressions * 100, 4) if impressions else 0.0,
        "cpl": round(spend / leads, 2) if leads else 0.0,
        "conversion_rate": round(leads / clicks * 100, 2) if clicks else 0.0,
    }


def parse_google_response(response: dict) -> list[dict]:
    """Parse full Google Ads API response into list of normalised rows."""
    rows = []
    for result in response.get("results", []):
        rows.append(normalise_google_campaign(result))
    return rows


def parse_meta_response(response: dict) -> list[dict]:
    """Parse full Meta Graph API response into list of normalised rows."""
    rows = []
    for campaign in response.get("data", []):
        insights_data = campaign.get("insights", {}).get("data", [])
        for insight in insights_data:
            rows.append(normalise_meta_campaign(campaign, insight))
    return rows


# ── Merge ──────────────────────────────────────────────────────────────────────

def merge_platform_campaigns(client_name: str, campaigns_list: list[list[dict]]) -> dict:
    """
    Merge normalised campaign rows from multiple platforms.
    Deduplicates by (platform, platform_campaign_id, date).

    campaigns_list: list of lists — each inner list is from one platform.
    """
    seen: set[tuple] = set()
    merged: list[dict] = []

    for platform_campaigns in campaigns_list:
        for row in platform_campaigns:
            key = (row["platform"], row["platform_campaign_id"], row["date"])
            if key not in seen:
                seen.add(key)
                merged.append(row)

    # Aggregate totals
    total_spend = sum(r["spend"] for r in merged)
    total_leads = sum(r["leads"] for r in merged)
    total_impressions = sum(r["impressions"] for r in merged)
    total_clicks = sum(r["clicks"] for r in merged)
    total_revenue = sum(r["revenue"] for r in merged)
    sources = list({r["platform"] for r in merged})

    return {
        "client": client_name,
        "campaigns": merged,
        "aggregated": {
            "total_spend": round(total_spend, 2),
            "total_leads": total_leads,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_revenue": round(total_revenue, 2),
            "blended_cpl": round(total_spend / total_leads, 2) if total_leads else 0.0,
            "blended_ctr": round(total_clicks / total_impressions * 100, 4) if total_impressions else 0.0,
            "roas": round(total_revenue / total_spend, 2) if total_spend and total_revenue else 0.0,
            "sources": sources,
        },
    }


# ── Fuzzy client matching ──────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> int:
    """
    Token-sort ratio similarity between two strings (0-100).
    Falls back to simple overlap if fuzzywuzzy not installed.
    """
    try:
        from fuzzywuzzy import fuzz
        return fuzz.token_sort_ratio(a.lower(), b.lower())
    except ImportError:
        # Simple fallback: character overlap ratio
        a, b = a.lower(), b.lower()
        if a == b:
            return 100
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        matches = sum(1 for c in shorter if c in longer)
        return int(matches / max(len(longer), 1) * 100)


def fuzzy_match_clients(
    platform_clients_a: list[dict],
    platform_clients_b: list[dict],
    threshold: int = 85,
) -> list[dict]:
    """
    Suggest client merges across two platforms using fuzzy name matching.

    platform_clients_a / _b: list of {"id": ..., "name": ...}
    Returns matches above threshold with confidence and recommendation.
    """
    suggestions = []
    for ca in platform_clients_a:
        best_score = 0
        best_match = None
        for cb in platform_clients_b:
            score = _similarity(ca["name"], cb["name"])
            if score > best_score:
                best_score = score
                best_match = cb

        if best_match and best_score >= threshold:
            suggestions.append({
                "client_a": ca,
                "client_b": best_match,
                "confidence": best_score,
                "recommendation": "MERGE" if best_score >= 90 else "REVIEW",
            })

    # Sort by confidence descending
    return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)
