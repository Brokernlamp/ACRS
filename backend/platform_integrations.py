"""
Platform integrations — fetches real campaign data from Google Ads and Meta Ads.
Requires valid access tokens stored in the APIConnection table.

Google Ads: GAQL v14 searchStream
Meta Ads:   Graph API v22+ /campaigns?fields=insights
"""

import os
import json
import logging
import requests
from typing import Optional
from datetime import date, timedelta
from platform_merger import parse_google_response, parse_meta_response

log = logging.getLogger("integrations")


# ── Google Ads ─────────────────────────────────────────────────────────────────

def fetch_google_ads_campaigns(
    customer_id: str,
    access_token: str,
    days: int = 30,
) -> list[dict]:
    """
    Fetch and normalise Google Ads campaigns via GAQL v14 searchStream.
    Raises on auth failure so the caller can surface the error to the user.
    """
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
        "login-customer-id": customer_id,
        "Content-Type": "application/json",
    }

    log.info(f"[GOOGLE] Fetching campaigns for customer_id={customer_id} days={days}")
    resp = requests.post(url, json={"query": query}, headers=headers, timeout=30)

    if resp.status_code == 401:
        raise PermissionError("Google Ads token expired or invalid. Please reconnect your account.")
    if resp.status_code == 403:
        raise PermissionError("Google Ads access denied. Check your developer token and account permissions.")
    resp.raise_for_status()

    results = []
    for line in resp.text.strip().split("\n"):
        if line.strip():
            chunk = json.loads(line)
            results.extend(chunk.get("results", []))

    log.info(f"[GOOGLE] Got {len(results)} rows")
    return parse_google_response({"results": results})


# ── Meta Ads ───────────────────────────────────────────────────────────────────

def fetch_meta_ads_campaigns(
    account_id: str,
    access_token: str,
    days: int = 30,
) -> list[dict]:
    """
    Fetch and normalise Meta Ads campaigns via Graph API v22+.
    Leads extracted from actions array (action_type == 'lead').
    Raises on auth failure so the caller can surface the error to the user.
    """
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()

    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    url = f"https://graph.facebook.com/v22.0/{account_id}/campaigns"
    params = {
        "access_token": access_token,
        "fields": (
            "id,name,status,objective,"
            f"insights.time_range({{'since':'{start}','until':'{end}'}})"
            "{impressions,clicks,spend,actions,ctr,cpm,cpp,reach,frequency,date_start,date_stop}"
        ),
        "limit": 100,
    }

    log.info(f"[META] Fetching campaigns for account_id={account_id} days={days}")
    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code == 401:
        raise PermissionError("Meta Ads token expired or invalid. Please reconnect your account.")
    if resp.status_code == 403:
        raise PermissionError("Meta Ads access denied. Check your app permissions.")

    data = resp.json()
    if "error" in data:
        err = data["error"]
        if err.get("code") in (190, 102):
            raise PermissionError(f"Meta token error: {err.get('message', 'Invalid token')}")
        raise RuntimeError(f"Meta API error: {err.get('message', str(err))}")

    log.info(f"[META] Got {len(data.get('data', []))} campaigns")
    return parse_meta_response(data)


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
    Partial success is allowed — if one platform fails, the other still syncs.
    """
    all_campaigns: list[list[dict]] = []
    sources: list[str] = []
    errors: list[str] = []

    if google_customer_id and google_token:
        try:
            g = fetch_google_ads_campaigns(google_customer_id, google_token, days)
            all_campaigns.append(g)
            sources.append("google_ads")
            log.info(f"[SYNC] Google: {len(g)} rows")
        except Exception as e:
            log.error(f"[SYNC] Google failed: {e}")
            errors.append(f"Google Ads: {e}")

    if meta_account_id and meta_token:
        try:
            m = fetch_meta_ads_campaigns(meta_account_id, meta_token, days)
            all_campaigns.append(m)
            sources.append("meta_ads")
            log.info(f"[SYNC] Meta: {len(m)} rows")
        except Exception as e:
            log.error(f"[SYNC] Meta failed: {e}")
            errors.append(f"Meta Ads: {e}")

    return {
        "campaigns": [row for platform in all_campaigns for row in platform],
        "sources": sources,
        "errors": errors,
    }
