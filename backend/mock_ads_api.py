"""
Mock Ads API — simulates real Google Ads v23+ and Meta Graph API v22+ responses.
Used for demos, testing, and development without real credentials.
"""

import random
from datetime import date, timedelta

random.seed(99)

# ── Shared helpers ─────────────────────────────────────────────────────────────
def _days_back(n: int) -> list[str]:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


MOCK_CLIENTS = {
    "ajay": {
        "google_customer_id": "1234567890",
        "meta_account_id": "act_111222333",
        "campaigns": {
            "google": ["Brand Search", "Competitor Keywords", "Display Retargeting"],
            "meta": ["Lead Gen - Lookalike", "Retargeting - Website Visitors", "Awareness - Broad"],
        },
    },
    "techstartup": {
        "google_customer_id": "9876543210",
        "meta_account_id": "act_444555666",
        "campaigns": {
            "google": ["SaaS - Trial Signups", "Brand Protection"],
            "meta": ["Demo Requests - IT Managers", "Retargeting - Pricing Page"],
        },
    },
    "ecommercebrand": {
        "google_customer_id": "1122334455",
        "meta_account_id": "act_777888999",
        "campaigns": {
            "google": ["Shopping - All Products", "Search - High Intent", "YouTube Awareness"],
            "meta": ["Catalog Sales - Retargeting", "New Customer Acquisition", "Seasonal Promo"],
        },
    },
}


def _google_metrics(seed_offset: int = 0) -> dict:
    r = random.Random(seed_offset)
    impressions = r.randint(8000, 45000)
    ctr = r.uniform(0.008, 0.032)
    clicks = int(impressions * ctr)
    cpc_micros = int(r.uniform(800000, 3500000))   # $0.80 – $3.50 in micros
    cost_micros = clicks * cpc_micros
    cvr = r.uniform(0.03, 0.15)
    conversions = max(1, int(clicks * cvr))
    return {
        "impressions": str(impressions),
        "clicks": str(clicks),
        "cost_micros": str(cost_micros),
        "conversions": str(conversions),
        "conversions_value": str(round(conversions * r.uniform(80, 400), 2)),
        "ctr": str(round(ctr * 100, 4)),
        "average_cpc": str(cpc_micros),
        "cost_per_conversion": str(round(cost_micros / max(conversions, 1) / 1_000_000, 2)),
    }


def _meta_insights(seed_offset: int = 0) -> dict:
    r = random.Random(seed_offset)
    impressions = r.randint(10000, 60000)
    ctr = r.uniform(0.005, 0.025)
    clicks = int(impressions * ctr)
    spend = round(clicks * r.uniform(0.5, 2.8), 2)
    leads = max(1, int(clicks * r.uniform(0.04, 0.18)))
    return {
        "impressions": str(impressions),
        "clicks": str(clicks),
        "spend": str(spend),
        "reach": str(int(impressions * 0.7)),
        "frequency": str(round(impressions / max(int(impressions * 0.7), 1), 2)),
        "ctr": str(round(ctr * 100, 4)),
        "cpm": str(round(spend / impressions * 1000, 2)),
        "cpp": str(round(spend / max(leads, 1), 2)),
        "actions": [
            {"action_type": "lead", "value": str(leads)},
            {"action_type": "link_click", "value": str(clicks)},
            {"action_type": "post_engagement", "value": str(int(clicks * 1.4))},
        ],
    }


# ── Google Ads mock ────────────────────────────────────────────────────────────
def get_mock_google_ads_campaigns(account_id: str, days: int = 30) -> dict:
    """
    Returns mock Google Ads API response matching GAQL v23+ structure.
    cost_micros = spend * 1,000,000 (real API quirk preserved).
    """
    # Find client by google_customer_id
    client_key = next(
        (k for k, v in MOCK_CLIENTS.items() if v["google_customer_id"] == account_id),
        "ajay"
    )
    client = MOCK_CLIENTS[client_key]
    campaign_names = client["campaigns"]["google"]

    results = []
    for i, camp_name in enumerate(campaign_names):
        for day_offset, day_str in enumerate(_days_back(days)):
            m = _google_metrics(seed_offset=hash(f"{account_id}{camp_name}{day_str}") % 10000)
            results.append({
                "campaign": {
                    "resource_name": f"customers/{account_id}/campaigns/{1000 + i}",
                    "id": str(1000 + i),
                    "name": camp_name,
                    "status": "ENABLED",
                    "advertising_channel_type": "SEARCH" if i < 2 else "DISPLAY",
                },
                "metrics": {**m},
                "segments": {
                    "date": day_str,
                },
            })

    return {
        "results": results,
        "fieldMask": "campaign.id,campaign.name,metrics.impressions,metrics.clicks,metrics.cost_micros,metrics.conversions",
        "requestId": f"mock-{account_id[:8]}",
    }


# ── Meta Ads mock ──────────────────────────────────────────────────────────────
def get_mock_meta_ads_campaigns(account_id: str, days: int = 30) -> dict:
    """
    Returns mock Meta Graph API v22+ response matching /act_{id}/campaigns?fields=insights structure.
    Leads extracted from actions array (action_type == 'lead').
    """
    client_key = next(
        (k for k, v in MOCK_CLIENTS.items() if v["meta_account_id"] == account_id),
        "ajay"
    )
    client = MOCK_CLIENTS[client_key]
    campaign_names = client["campaigns"]["meta"]

    data = []
    for i, camp_name in enumerate(campaign_names):
        daily_insights = []
        for day_str in _days_back(days):
            ins = _meta_insights(seed_offset=hash(f"{account_id}{camp_name}{day_str}") % 10000)
            daily_insights.append({
                "date_start": day_str,
                "date_stop": day_str,
                **ins,
            })

        data.append({
            "id": f"{20000 + i}",
            "name": camp_name,
            "status": "ACTIVE",
            "objective": "LEAD_GENERATION" if i < 2 else "BRAND_AWARENESS",
            "insights": {
                "data": daily_insights,
                "paging": {"cursors": {"before": "mock", "after": "mock"}},
            },
        })

    return {
        "data": data,
        "paging": {"cursors": {"before": "mock_before", "after": "mock_after"}},
    }


def get_mock_clients_list() -> list[dict]:
    """Return all mock clients for demo discovery."""
    return [
        {
            "name": k.title().replace("brand", "Brand").replace("startup", "Startup"),
            "google_customer_id": v["google_customer_id"],
            "meta_account_id": v["meta_account_id"],
        }
        for k, v in MOCK_CLIENTS.items()
    ]
