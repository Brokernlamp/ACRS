"""
Platform integrations — fetches campaign data from Google Ads and Meta Ads.
Controlled by DEMO_MODE env var:
  DEMO_MODE=true  → returns mock data (default, no credentials needed)
  DEMO_MODE=false → calls real APIs (requires OAuth tokens)
"""

import os
import logging
from typing import Optional
from mock_ads_api import get_mock_google_ads_campaigns, get_mock_meta_ads_campaigns
from platform_merger import parse_google_response, parse_meta_response

log = logging.getLogger("integrations")

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# ── Google Ads ─────────────────────────────────────────────────────────────────

def fetch_google_ads_campaigns(
    customer_id: str,
    access_token: Optional[str] = None,
    days: int = 30,
) -> list[dict]:
    """
    Fetch and normalise Google Ads campaigns.
    Demo mode: returns mock data.
    Real mode: calls Google Ads API v23+ via GAQL.
    """
    if DEMO_MODE or not access_token:
        log.info(f"[INTEGRATIONS] Google Ads DEMO mode — customer_id={customer_id}")
        raw = get_mock_google_ads_campaigns(customer_id, days=days)
        return parse_google_response(raw)

    # ── Real Google Ads API ────────────────────────────────────────────────────
    log.info(f"[INTEGRATIONS] Google Ads REAL mode — customer_id={customer_id}")
    try:
        import requests
        from datetime import date, timedelta
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days)).isoformat()

        query = f"""
            SELECT
              campaign.id,
              campaign.name,
              campaign.status,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value,
              segments.date
            FROM campaign
            WHERE segments.date BETWEEN '{start}' AND '{end}'
              AND campaign.status = 'ENABLED'
            ORDER BY segments.date DESC
        """
        url = f"https://googleads.googleapis.com/v14/customers/{customer_id}/googleAds:searchStream"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "developer-token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json={"query": query}, headers=headers, timeout=30)
        resp.raise_for_status()
        # searchStream returns newline-delimited JSON objects
        import json
        results = []
        for line in resp.text.strip().split("\n"):
            if line:
                chunk = json.loads(line)
                results.extend(chunk.get("results", []))
        return parse_google_response({"results": results})
    except Exception as e:
        log.error(f"[INTEGRATIONS] Google Ads real API failed: {e} — falling back to demo")
        raw = get_mock_google_ads_campaigns(customer_id, days=days)
        return parse_google_response(raw)


# ── Meta Ads ───────────────────────────────────────────────────────────────────

def fetch_meta_ads_campaigns(
    account_id: str,
    access_token: Optional[str] = None,
    days: int = 30,
) -> list[dict]:
    """
    Fetch and normalise Meta Ads campaigns.
    Demo mode: returns mock data.
    Real mode: calls Meta Graph API v22+.
    """
    if DEMO_MODE or not access_token:
        log.info(f"[INTEGRATIONS] Meta Ads DEMO mode — account_id={account_id}")
        raw = get_mock_meta_ads_campaigns(account_id, days=days)
        return parse_meta_response(raw)

    # ── Real Meta Graph API ────────────────────────────────────────────────────
    log.info(f"[INTEGRATIONS] Meta Ads REAL mode — account_id={account_id}")
    try:
        import requests
        from datetime import date, timedelta
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=days)).isoformat()

        # Normalise account_id — ensure it starts with act_
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        url = f"https://graph.facebook.com/v22.0/{account_id}/campaigns"
        params = {
            "access_token": access_token,
            "fields": "id,name,status,objective,insights.time_range({'since':'" + start + "','until':'" + end + "'}){impressions,clicks,spend,actions,ctr,cpm,cpp,reach,frequency}",
            "limit": 100,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return parse_meta_response(resp.json())
    except Exception as e:
        log.error(f"[INTEGRATIONS] Meta Ads real API failed: {e} — falling back to demo")
        raw = get_mock_meta_ads_campaigns(account_id, days=days)
        return parse_meta_response(raw)


# ── Combined sync ──────────────────────────────────────────────────────────────

def sync_all_platforms(
    google_customer_id: Optional[str] = None,
    meta_account_id: Optional[str] = None,
    google_token: Optional[str] = None,
    meta_token: Optional[str] = None,
    days: int = 30,
) -> dict:
    """
    Fetch from all configured platforms and return combined normalised rows.
    """
    all_campaigns: list[list[dict]] = []
    sources = []

    if google_customer_id:
        g_camps = fetch_google_ads_campaigns(google_customer_id, google_token, days)
        all_campaigns.append(g_camps)
        sources.append("google_ads")
        log.info(f"[INTEGRATIONS] Google: {len(g_camps)} rows")

    if meta_account_id:
        m_camps = fetch_meta_ads_campaigns(meta_account_id, meta_token, days)
        all_campaigns.append(m_camps)
        sources.append("meta_ads")
        log.info(f"[INTEGRATIONS] Meta: {len(m_camps)} rows")

    return {
        "campaigns": [row for platform in all_campaigns for row in platform],
        "sources": sources,
    }
