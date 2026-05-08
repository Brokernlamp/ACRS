import io
import os
import math
import logging
from typing import Optional, Any

# ── Logging setup — must be before any module imports ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from utils import validate_csv, sanitize
from data_processor import compute_kpis, summary_kpis, campaign_summary, daily_trends, generate_insights
from visualizer import (
    chart_leads_over_time, chart_spend_vs_leads, chart_campaign_performance,
    chart_performance_scores, chart_budget_allocation, chart_leads_forecast,
)
from report_generator import generate_pdf, generate_growth_pdf
from emailer import send_report
from intelligence import run_intelligence, simulate_budget_change
from database import SessionLocal
from database.crud import (
    create_client, get_clients_by_user, get_campaigns_by_client,
    create_campaign, upsert_campaign_data,
    create_campaign_group, get_campaign_groups,
    assign_campaign_to_group, get_group_performance,
    get_client_cross_platform_summary,
)
from comparison import calculate_period_comparison, get_date_ranges, get_comparison_summary
from rag import build_index
from chatbot import chat as chatbot_chat, reset_history, get_history
from datetime import datetime

# ── Numpy-safe JSON serialiser ────────────────────────────────────────────────
def _safe(obj: Any) -> Any:
    """Recursively convert numpy / pandas scalars to plain Python types."""
    if isinstance(obj, dict):
        return {k: _safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if math.isnan(float(obj)) else float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return _safe(obj.tolist())
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


app = FastAPI(title="AI Growth Operator API")

# CORS — reads allowed origins from env so Vercel URL works in production
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
log.info(f"[MAIN] CORS allowed origins: {_allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state (per-process; replace with Redis for multi-worker)
_state: dict = {}
_current_user_id = 1
_current_client_id: Optional[int] = None


def _load_data_from_db(client_id: int, start_date=None, end_date=None) -> Optional[pd.DataFrame]:
    from database.models import CampaignData, Campaign
    db = SessionLocal()
    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        query = db.query(CampaignData).join(Campaign).filter(Campaign.client_id == client_id)
        if start_date:
            query = query.filter(CampaignData.date >= start_date)
        if end_date:
            query = query.filter(CampaignData.date <= end_date)

        data = query.order_by(CampaignData.date).all()
        if not data:
            return None

        rows = []
        campaign_cache = {}
        for d in data:
            if d.campaign_id not in campaign_cache:
                campaign_cache[d.campaign_id] = db.query(Campaign).filter(Campaign.id == d.campaign_id).first()
            camp = campaign_cache[d.campaign_id]
            rows.append({
                "date": d.date, "campaign": camp.campaign_name,
                "impressions": float(d.impressions or 0), "clicks": float(d.clicks or 0),
                "spend": float(d.spend or 0), "leads": float(d.leads or 0),
                "ctr": float(d.ctr or 0), "cpl": float(d.cpl or 0),
            })
        return pd.DataFrame(rows)
    finally:
        db.close()


def _process_df(df: pd.DataFrame) -> dict:
    """Run full pipeline on a DataFrame and return serialisable result."""
    # Ensure date column is proper datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = compute_kpis(df)
    camp = campaign_summary(df)
    daily = daily_trends(df)
    kpis = summary_kpis(df)
    # Make kpis fully JSON-serialisable
    kpis = {k: (int(v) if isinstance(v, (int,)) else float(v) if hasattr(v, '__float__') and not isinstance(v, str) else v) for k, v in kpis.items()}
    insights = generate_insights(camp, kpis)

    _, json1 = chart_leads_over_time(daily)
    _, json2 = chart_spend_vs_leads(camp)
    _, json3 = chart_campaign_performance(camp)

    intel = run_intelligence(camp, daily)
    _, json4 = chart_performance_scores(intel["scored"])
    _, json5 = chart_budget_allocation(intel["allocation"])
    _, json6 = chart_leads_forecast(daily, intel["leads_prediction"]["predicted_leads"])

    _state.update(
        df=df, camp=camp, daily=daily, kpis=kpis,
        insights=insights,
        intel=intel,
    )

    # Build RAG index from fresh data
    try:
        alloc_list = intel["allocation"].fillna(0).to_dict(orient="records")
        log.info(f"[MAIN] Building RAG index — {len(df)} rows, {len(camp)} campaigns")
        build_index(
            df=df, camp_summary=camp, kpis=kpis,
            insights=insights, actions=intel["actions"],
            patterns=intel["patterns"], waste=intel["waste"],
            allocation=alloc_list, predictions=intel["leads_prediction"],
        )
        log.info("[MAIN] RAG index built successfully")
    except Exception as rag_err:
        log.error(f"[MAIN] RAG index build FAILED: {type(rag_err).__name__}: {rag_err}")

    # Convert allocation DataFrame — replace NaN with 0 for JSON safety
    alloc_records = intel["allocation"].fillna(0).to_dict(orient="records")
    waste = {k: (float(v) if hasattr(v, '__float__') else v) for k, v in intel["waste"].items()}

    result = {
        "kpis": kpis,
        "insights": insights,
        "campaigns": camp["campaign"].tolist(),
        "camp_summary": camp.fillna(0).to_dict(orient="records"),
        "predictions": intel["leads_prediction"],
        "cpl_prediction": intel["cpl_prediction"],
        "ctr_prediction": intel["ctr_prediction"],
        "actions": intel["actions"],
        "waste": waste,
        "allocation": alloc_records,
        "patterns": intel["patterns"],
        "charts": {
            "leads_over_time": json1,
            "spend_vs_leads": json2,
            "campaign_performance": json3,
            "performance_scores": json4,
            "budget_allocation": json5,
            "leads_forecast": json6,
        },
    }
    return _safe(result)


# ── Upload ────────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), client_name: str = Form(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    ok, msg = validate_csv(df)
    if not ok:
        raise HTTPException(400, msg)

    df = sanitize(df)

    db = SessionLocal()
    try:
        client = next((c for c in get_clients_by_user(db, _current_user_id) if c.name == client_name), None)
        if not client:
            client = create_client(db, user_id=_current_user_id, name=client_name, industry="Unknown")
        global _current_client_id
        _current_client_id = client.id

        df_kpi = compute_kpis(df)
        existing_campaigns = {c.campaign_name: c for c in get_campaigns_by_client(db, client.id)}
        for _, row in df_kpi.iterrows():
            camp_name = str(row["campaign"])
            if camp_name not in existing_campaigns:
                existing_campaigns[camp_name] = create_campaign(db, client_id=client.id, campaign_name=camp_name)
            camp_obj = existing_campaigns[camp_name]
            # Convert pandas Timestamp to python date
            row_date = row["date"]
            if hasattr(row_date, "date"):
                row_date = row_date.date()
            upsert_campaign_data(
                db, campaign_id=camp_obj.id, date=row_date,
                impressions=int(row["impressions"]), clicks=int(row["clicks"]),
                spend=float(row["spend"]), leads=int(row["leads"]),
                ctr=float(row.get("ctr") or 0), cpl=float(row.get("cpl") or 0),
                conversion_rate=float(row.get("conversion_rate") or 0),
                revenue=float(row.get("revenue") or 0),
            )
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")
    finally:
        db.close()

    return _process_df(df)


# ── Refresh ───────────────────────────────────────────────────────────────────
class RefreshRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    comparison_period: Optional[str] = "None"
    client_id: Optional[int] = None  # explicit client_id overrides in-memory state


@app.post("/api/refresh")
def refresh_data(req: RefreshRequest):
    global _current_client_id
    # Use explicit client_id if provided, otherwise fall back to in-memory
    target_client_id = req.client_id or _current_client_id
    if not target_client_id:
        raise HTTPException(400, "No client selected. Upload data first.")

    # Update in-memory state so subsequent calls work
    _current_client_id = target_client_id

    df = _load_data_from_db(target_client_id, req.start_date, req.end_date)
    if df is None or df.empty:
        raise HTTPException(404, "No data found for this client yet.")

    result = _process_df(df)

    if req.comparison_period and req.comparison_period != "None":
        period = "week" if "Week" in req.comparison_period else "month"
        ranges = get_date_ranges(req.end_date, period)
        prev_start, prev_end = ranges["previous"]
        prev_df = _load_data_from_db(target_client_id, prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d"))
        if prev_df is not None and not prev_df.empty:
            prev_df = compute_kpis(prev_df)
            comparison = calculate_period_comparison(df, prev_df)
            result["comparison_summary"] = get_comparison_summary(comparison)

    return result


# ── Simulation ────────────────────────────────────────────────────────────────
class SimRequest(BaseModel):
    campaign: str
    delta_pct: float


@app.post("/api/simulate")
def simulate(req: SimRequest):
    if "camp" not in _state:
        raise HTTPException(400, "Upload data first.")
    result = simulate_budget_change(_state["camp"], req.campaign, req.delta_pct / 100.0)
    return result


@app.post("/api/simulate/pause")
def simulate_pause(req: SimRequest):
    if "camp" not in _state:
        raise HTTPException(400, "Upload data first.")
    result = simulate_budget_change(_state["camp"], req.campaign, -1.0)
    return result


# ── Reports ───────────────────────────────────────────────────────────────────
@app.get("/api/report/standard")
def download_standard_report(client_name: str = "Client"):
    if not _state:
        raise HTTPException(400, "Upload data first.")
    df = _state["df"]
    date_range = f"{df['date'].min().date()} → {df['date'].max().date()}"
    pdf_bytes = generate_pdf(
        client_name=client_name, date_range=date_range,
        kpis=_state["kpis"], camp_df=_state["camp"],
        insights=_state["insights"], chart_pngs=[],
    )
    _state["pdf_bytes"] = pdf_bytes
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{client_name}_report.pdf"'},
    )


@app.get("/api/report/growth")
def download_growth_report(client_name: str = "Client"):
    if not _state:
        raise HTTPException(400, "Upload data first.")
    df = _state["df"]
    date_range = f"{df['date'].min().date()} → {df['date'].max().date()}"
    pdf_bytes = generate_growth_pdf(
        client_name=client_name, date_range=date_range,
        kpis=_state["kpis"], camp_df=_state["camp"],
        insights=_state["insights"], chart_pngs=[],
        intelligence=_state["intel"], ai_chart_pngs=[],
    )
    _state["pdf_bytes"] = pdf_bytes
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{client_name}_growth_report.pdf"'},
    )


# ── Email ─────────────────────────────────────────────────────────────────────
class EmailRequest(BaseModel):
    client_name: str
    sender_email: str
    sender_password: str
    recipient_email: str


@app.post("/api/email")
def send_email(req: EmailRequest):
    if "pdf_bytes" not in _state:
        if not _state:
            raise HTTPException(400, "Upload data first.")
        df = _state["df"]
        date_range = f"{df['date'].min().date()} → {df['date'].max().date()}"
        _state["pdf_bytes"] = generate_growth_pdf(
            client_name=req.client_name, date_range=date_range,
            kpis=_state["kpis"], camp_df=_state["camp"],
            insights=_state["insights"], chart_pngs=[],
            intelligence=_state["intel"], ai_chart_pngs=[],
        )
    ok, msg = send_report(req.sender_email, req.sender_password, req.recipient_email, req.client_name, _state["pdf_bytes"])
    if not ok:
        raise HTTPException(500, msg)
    return {"message": msg}


# ── Clients ───────────────────────────────────────────────────────────────────
@app.get("/api/clients")
def list_clients():
    db = SessionLocal()
    try:
        clients = get_clients_by_user(db, _current_user_id)
        rows = []
        for c in clients:
            if not c.name or not c.name.strip():  # skip empty-name test clients
                continue
            campaigns = get_campaigns_by_client(db, c.id)
            df = _load_data_from_db(c.id)
            total_spend = float(df["spend"].sum()) if df is not None and not df.empty else 0
            total_leads = float(df["leads"].sum()) if df is not None and not df.empty else 0
            rows.append({
                "id": c.id, "name": c.name, "industry": c.industry or "N/A",
                "campaigns": len(campaigns),
                "total_spend": total_spend, "total_leads": total_leads,
                "avg_cpl": round(total_spend / max(total_leads, 1), 2),
            })
        return rows
    finally:
        db.close()


class NewClientRequest(BaseModel):
    name: str
    industry: Optional[str] = "Unknown"
    target_cpl: Optional[float] = None
    monthly_budget: Optional[float] = None
    revenue_per_lead: Optional[float] = None


@app.post("/api/clients")
def add_client(req: NewClientRequest):
    if not req.name or not req.name.strip():
        raise HTTPException(400, "Client name is required.")
    db = SessionLocal()
    try:
        existing = get_clients_by_user(db, _current_user_id)
        if any(c.name.lower() == req.name.strip().lower() for c in existing):
            raise HTTPException(409, f"Client '{req.name}' already exists.")
        client = create_client(
            db, user_id=_current_user_id, name=req.name.strip(),
            industry=req.industry, target_cpl=req.target_cpl,
            monthly_budget=req.monthly_budget,
        )
        if req.revenue_per_lead is not None:
            client.revenue_per_lead = req.revenue_per_lead
            db.commit()
            db.refresh(client)
        return {"id": client.id, "name": client.name, "industry": client.industry}
    finally:
        db.close()


@app.delete("/api/clients/{client_id}")
def delete_client_endpoint(client_id: int):
    from database.crud import delete_client
    db = SessionLocal()
    try:
        ok = delete_client(db, client_id)
        if not ok:
            raise HTTPException(404, "Client not found")
        return {"status": "deleted"}
    finally:
        db.close()


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Platform linking & syncing ─────────────────────────────────────────────────────
class LinkPlatformsRequest(BaseModel):
    google_account_id: Optional[str] = None
    meta_account_id: Optional[str] = None
    linkedin_account_id: Optional[str] = None


@app.post("/api/clients/{client_id}/link-platforms")
def link_platforms(client_id: int, req: LinkPlatformsRequest):
    """Store platform account IDs on a client record."""
    db = SessionLocal()
    try:
        from database.crud import get_client_by_id
        client = get_client_by_id(db, client_id)
        if not client:
            raise HTTPException(404, "Client not found")
        if req.google_account_id:
            client.google_ads_customer_id = req.google_account_id
        if req.meta_account_id:
            client.meta_ads_account_id = req.meta_account_id
        if req.linkedin_account_id:
            client.linkedin_account_id = req.linkedin_account_id
        db.commit()
        return {
            "client_id": client_id,
            "google_linked": bool(client.google_ads_customer_id),
            "meta_linked": bool(client.meta_ads_account_id),
            "linkedin_linked": bool(client.linkedin_account_id),
        }
    finally:
        db.close()


@app.post("/api/clients/{client_id}/sync-platforms")
def sync_platforms(client_id: int, days: int = 30):
    """
    Fetch latest campaigns from all linked platforms using stored OAuth tokens.
    """
    from platform_integrations import fetch_google_ads_campaigns, fetch_meta_ads_campaigns
    from platform_merger import merge_platform_campaigns
    from database.crud import get_client_by_id, get_api_connections
    from database.models import Campaign as CampaignModel

    db = SessionLocal()
    try:
        client = get_client_by_id(db, client_id)
        if not client:
            raise HTTPException(404, "Client not found")

        # Get stored OAuth tokens
        connections = {c.platform: c for c in get_api_connections(db, _current_user_id)}
        google_conn = connections.get("google_ads")
        meta_conn = connections.get("meta_ads")

        all_camps: list[list[dict]] = []
        errors: list[str] = []

        if client.google_ads_customer_id:
            if not google_conn or not google_conn.access_token:
                errors.append("Google Ads: No access token stored. Connect your account in Settings.")
            else:
                try:
                    g = fetch_google_ads_campaigns(
                        client.google_ads_customer_id,
                        google_conn.access_token,
                        days=days,
                    )
                    all_camps.append(g)
                    client.last_google_sync = datetime.utcnow()
                    log.info(f"[SYNC] Google: {len(g)} rows")
                except Exception as e:
                    errors.append(f"Google Ads: {e}")
                    log.error(f"[SYNC] Google failed: {e}")

        if client.meta_ads_account_id:
            if not meta_conn or not meta_conn.access_token:
                errors.append("Meta Ads: No access token stored. Connect your account in Settings.")
            else:
                try:
                    m = fetch_meta_ads_campaigns(
                        client.meta_ads_account_id,
                        meta_conn.access_token,
                        days=days,
                    )
                    all_camps.append(m)
                    client.last_meta_sync = datetime.utcnow()
                    log.info(f"[SYNC] Meta: {len(m)} rows")
                except Exception as e:
                    errors.append(f"Meta Ads: {e}")
                    log.error(f"[SYNC] Meta failed: {e}")

        if not all_camps:
            msg = "No data synced."
            if errors:
                msg += " Errors: " + " | ".join(errors)
            elif not client.google_ads_customer_id and not client.meta_ads_account_id:
                msg = "No platforms linked. Use /link-platforms first."
            raise HTTPException(400, msg)

        merged = merge_platform_campaigns(client.name, all_camps)
        db.commit()

        # Save to DB
        campaigns_added = 0
        existing = {
            (c.platform, c.platform_campaign_id): c
            for c in get_campaigns_by_client(db, client_id)
        }

        for row in merged["campaigns"]:
            key = (row["platform"], row["platform_campaign_id"])
            if key not in existing:
                camp = CampaignModel(
                    client_id=client_id,
                    campaign_name=row["campaign_name"],
                    platform=row["platform"],
                    platform_campaign_id=row["platform_campaign_id"],
                    is_auto_synced=True,
                    synced_at=datetime.utcnow(),
                )
                db.add(camp)
                db.flush()
                existing[key] = camp
                campaigns_added += 1

            camp_obj = existing[key]
            if row.get("date"):
                from datetime import datetime as dt
                row_date = dt.strptime(row["date"], "%Y-%m-%d").date()
                upsert_campaign_data(
                    db, campaign_id=camp_obj.id, date=row_date,
                    impressions=row["impressions"], clicks=row["clicks"],
                    spend=row["spend"], leads=row["leads"],
                    revenue=row["revenue"], ctr=row["ctr"],
                    cpl=row["cpl"], conversion_rate=row["conversion_rate"],
                )

        db.commit()
        log.info(f"[SYNC] client={client_id} added={campaigns_added} rows={len(merged['campaigns'])}")

        result = _safe({
            "status": "synced",
            "campaigns_added": campaigns_added,
            "total_rows": len(merged["campaigns"]),
            "aggregated": merged["aggregated"],
            "errors": errors,
        })
        return result
    finally:
        db.close()


@app.get("/api/clients/{client_id}/platform-mapping-suggestions")
def platform_mapping_suggestions(client_id: int):
    """
    Use fuzzy matching to suggest which demo/real platform clients
    match the stored client name.
    """
    from platform_merger import fuzzy_match_clients
    from mock_ads_api import get_mock_clients_list
    from database.crud import get_client_by_id

    db = SessionLocal()
    try:
        client = get_client_by_id(db, client_id)
        if not client:
            raise HTTPException(404, "Client not found")

        mock_clients = get_mock_clients_list()
        platform_clients = [
            {"id": c["google_customer_id"], "name": c["name"], "platform": "google_ads"}
            for c in mock_clients
        ] + [
            {"id": c["meta_account_id"], "name": c["name"], "platform": "meta_ads"}
            for c in mock_clients
        ]

        our_clients = [{"id": str(client.id), "name": client.name}]
        suggestions = fuzzy_match_clients(our_clients, platform_clients, threshold=60)
        return {"client_id": client_id, "suggestions": suggestions}
    finally:
        db.close()


# ── Campaign Groups ─────────────────────────────────────────────────────────────────
class CampaignGroupRequest(BaseModel):
    client_id: int
    name: str
    objective: str = "conversion"
    description: Optional[str] = None


class AssignCampaignRequest(BaseModel):
    campaign_id: int
    group_id: Optional[int] = None


@app.post("/api/campaign-groups")
def create_group(req: CampaignGroupRequest):
    db = SessionLocal()
    try:
        group = create_campaign_group(
            db, client_id=req.client_id, name=req.name,
            objective=req.objective, description=req.description
        )
        return {"id": group.id, "name": group.name, "objective": group.objective}
    except ValueError as e:
        raise HTTPException(409, str(e))
    finally:
        db.close()


@app.post("/api/campaign-groups/assign-campaign")
def assign_to_group(req: AssignCampaignRequest):
    db = SessionLocal()
    try:
        campaign = assign_campaign_to_group(db, req.campaign_id, req.group_id)
        return {"campaign_id": campaign.id, "group_id": campaign.group_id}
    except ValueError as e:
        raise HTTPException(404, str(e))
    finally:
        db.close()


@app.get("/api/group-performance/{group_id}")
def group_performance(group_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    from datetime import datetime as dt
    db = SessionLocal()
    try:
        sd = dt.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        ed = dt.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        result = get_group_performance(db, group_id, sd, ed)
        if not result:
            raise HTTPException(404, "Group not found")
        return _safe(result)
    finally:
        db.close()


# NOTE: parameterised route must come AFTER all specific /campaign-groups/* routes
@app.get("/api/campaign-groups/{client_id}")
def list_groups(client_id: int):
    db = SessionLocal()
    try:
        groups = get_campaign_groups(db, client_id)
        return [
            {"id": g.id, "name": g.name, "objective": g.objective,
             "description": g.description,
             "campaign_count": len([c for c in g.campaigns if c.is_active])}
            for g in groups
        ]
    finally:
        db.close()


@app.get("/api/clients/{client_id}/data-coverage")
def data_coverage(client_id: int):
    """Return the date range and row count of stored data for a client."""
    from database.models import CampaignData, Campaign
    from sqlalchemy import func
    db = SessionLocal()
    try:
        result = db.query(
            func.min(CampaignData.date).label("earliest"),
            func.max(CampaignData.date).label("latest"),
            func.count(CampaignData.id).label("rows"),
        ).join(Campaign).filter(Campaign.client_id == client_id).first()

        if not result or not result.earliest:
            return {"has_data": False, "earliest": None, "latest": None, "rows": 0, "days": 0}

        days = (result.latest - result.earliest).days + 1
        return {
            "has_data": True,
            "earliest": result.earliest.isoformat(),
            "latest": result.latest.isoformat(),
            "rows": result.rows,
            "days": days,
        }
    finally:
        db.close()


@app.get("/api/clients/{client_id}/platform-info")
def get_platform_info(client_id: int):
    """Return linked platform IDs for a client."""
    from database.crud import get_client_by_id
    db = SessionLocal()
    try:
        client = get_client_by_id(db, client_id)
        if not client:
            raise HTTPException(404, "Client not found")
        return {
            "google_ads_customer_id": client.google_ads_customer_id,
            "meta_ads_account_id": client.meta_ads_account_id,
            "linkedin_account_id": client.linkedin_account_id,
            "last_google_sync": client.last_google_sync.isoformat() if client.last_google_sync else None,
            "last_meta_sync": client.last_meta_sync.isoformat() if client.last_meta_sync else None,
        }
    finally:
        db.close()


@app.get("/api/clients/{client_id}/cross-platform")
def cross_platform_summary(client_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """The main multi-platform view — all campaigns grouped, with blended metrics and P&L."""
    from datetime import datetime as dt
    db = SessionLocal()
    try:
        sd = dt.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        ed = dt.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        result = get_client_cross_platform_summary(db, client_id, sd, ed)
        return _safe(result)
    finally:
        db.close()


@app.get("/api/clients/{client_id}/campaigns")
def list_client_campaigns(client_id: int):
    """List all campaigns for a client with their group assignment and platform."""
    db = SessionLocal()
    try:
        campaigns = get_campaigns_by_client(db, client_id)
        return [
            {
                "id": c.id,
                "name": c.campaign_name,
                "platform": c.platform or "manual",
                "group_id": c.group_id,
                "group_name": c.group.name if c.group else None,
            }
            for c in campaigns
        ]
    finally:
        db.close()


# ── Simulation Report ───────────────────────────────────────────────────────
class SimReportRequest(BaseModel):
    client_name: str
    simulations: list  # list of SimResult dicts


@app.post("/api/report/simulation")
def download_simulation_report(req: SimReportRequest):
    from report_generator import generate_simulation_pdf
    if not req.simulations:
        raise HTTPException(400, "No simulation results provided.")
    pdf_bytes = generate_simulation_pdf(
        client_name=req.client_name,
        simulations=req.simulations,
        kpis=_state.get("kpis", {}),
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{req.client_name}_simulation_report.pdf"'},
    )


# ── Settings ─────────────────────────────────────────────────────────────────
@app.get("/api/settings")
def get_settings():
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    active = "groq" if groq_key else ("gemini" if gemini_key else "none")
    return {
        "groq_api_key_set": bool(groq_key),
        "groq_api_key_preview": f"{groq_key[:8]}...{groq_key[-4:]}" if len(groq_key) > 12 else ("set" if groq_key else ""),
        "gemini_api_key_set": bool(gemini_key),
        "gemini_api_key_preview": f"{gemini_key[:8]}...{gemini_key[-4:]}" if len(gemini_key) > 12 else ("set" if gemini_key else ""),
        "active_provider": active,
        "active_model": "llama-3.1-8b-instant" if active == "groq" else ("gemini-2.0-flash-lite" if active == "gemini" else "none"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./acrs.db"),
    }


class SettingsUpdateRequest(BaseModel):
    gemini_api_key: str = ""
    groq_api_key: str = ""


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    """Update API keys — sets env var immediately, persists to .env for local dev."""
    def _persist(key_name: str, value: str):
        os.environ[key_name] = value
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            try:
                lines = open(env_path).readlines()
                new_line = f"{key_name}={value}\n"
                updated, new_lines = False, []
                for line in lines:
                    if line.startswith(f"{key_name}="):
                        new_lines.append(new_line); updated = True
                    else:
                        new_lines.append(line)
                if not updated:
                    new_lines.append(new_line)
                open(env_path, "w").writelines(new_lines)
            except OSError:
                pass

    if req.groq_api_key:
        _persist("GROQ_API_KEY", req.groq_api_key)
        log.info("[SETTINGS] GROQ_API_KEY updated")
    if req.gemini_api_key:
        _persist("GEMINI_API_KEY", req.gemini_api_key)
        log.info("[SETTINGS] GEMINI_API_KEY updated")
    return {"status": "saved"}


@app.get("/api/settings/sample-data")
def download_sample_data():
    """Return a realistic sample CSV for testing."""
    import csv, io as _io
    from datetime import date, timedelta
    import random
    random.seed(42)
    campaigns = ["Google Search", "Meta Retargeting", "LinkedIn Awareness", "Google Display"]
    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "campaign", "impressions", "clicks", "spend", "leads", "revenue"])
    base = date.today() - timedelta(days=60)
    for i in range(60):
        d = base + timedelta(days=i)
        for camp in campaigns:
            impr  = random.randint(8000, 40000)
            ctr   = random.uniform(0.008, 0.035)
            clicks = int(impr * ctr)
            cpc   = random.uniform(0.8, 3.5)
            spend = round(clicks * cpc, 2)
            cvr   = random.uniform(0.04, 0.18)
            leads = max(1, int(clicks * cvr))
            revenue = round(leads * random.uniform(80, 400), 2)
            w.writerow([d.isoformat(), camp, impr, clicks, spend, leads, revenue])
    buf.seek(0)
    from fastapi.responses import Response
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_campaign_data.csv"'},
    )


# ── License proxy ───────────────────────────────────────────────────────────
# These endpoints forward license requests from the frontend to the central
# license server, keeping the server URL server-side only.

import httpx as _httpx

_LICENSE_SERVER = os.getenv("LICENSE_SERVER_URL", "https://license.aigrowthoperator.com")


class LicenseValidateRequest(BaseModel):
    license_key: str
    machine_id: str
    product_name: str = "ai-growth-operator"


class LicensePollRequest(BaseModel):
    token: str
    machine_id: str


@app.post("/api/license/validate")
async def license_validate(req: LicenseValidateRequest):
    """Proxy: desktop → local backend → license server."""
    try:
        async with _httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{_LICENSE_SERVER}/api/license/validate",
                json={"license_key": req.license_key, "machine_id": req.machine_id, "product_name": req.product_name},
            )
        return JSONResponse(status_code=r.status_code, content=r.json())
    except Exception as e:
        raise HTTPException(503, f"License server unreachable: {e}")


@app.post("/api/license/poll")
async def license_poll(req: LicensePollRequest):
    """Proxy: desktop → local backend → license server."""
    try:
        async with _httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{_LICENSE_SERVER}/api/license/poll",
                json={"token": req.token, "machine_id": req.machine_id},
            )
        return JSONResponse(status_code=r.status_code, content=r.json())
    except Exception as e:
        raise HTTPException(503, f"License server unreachable: {e}")


# ── Gemini proxy (Desktop App → License Server → Gemini) ─────────────────────
# The license server holds the real Gemini API key; the desktop app never sees it.

class GeminiProxyRequest(BaseModel):
    prompt: str
    license_token: str  # current lease JWT — server validates before forwarding


@app.post("/api/ai/chat")
async def gemini_proxy(req: GeminiProxyRequest):
    """Route AI requests through the license server so the Gemini key stays server-side."""
    try:
        async with _httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{_LICENSE_SERVER}/api/ai/chat",
                json={"prompt": req.prompt, "token": req.license_token},
            )
        if r.status_code == 402:
            raise HTTPException(402, "License expired. Please renew your subscription.")
        if r.status_code == 403:
            raise HTTPException(403, "License invalid.")
        if r.status_code == 429:
            # Pass rate-limit detail through so the frontend can show reset time
            raise HTTPException(429, detail=r.json())
        return JSONResponse(status_code=r.status_code, content=r.json())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, f"AI service unreachable: {e}")


# ── Chatbot ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    license_token: str = ""  # lease JWT forwarded from desktop app


@app.get("/api/chat/status")
def chat_status():
    from rag import _client, _COLLECTION
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    ai_configured = bool(groq_key or gemini_key)
    active_provider = "groq" if groq_key else ("gemini" if gemini_key else "none")
    try:
        col = _client.get_collection(_COLLECTION)
        indexed = col.count()
    except Exception:
        indexed = 0
    return {
        "gemini_configured": bool(gemini_key),
        "ai_configured": ai_configured,
        "active_provider": active_provider,
        "rag_documents_indexed": indexed,
        "ready": indexed > 0,
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")
    log.info(f"[MAIN] /api/chat received: '{req.message[:80]}'")
    result = chatbot_chat(req.message.strip(), license_token=req.license_token)
    if isinstance(result, dict) and result.get("error") == "credits_exhausted":
        raise HTTPException(402, detail={"error": "credits_exhausted"})
    if isinstance(result, dict) and result.get("error") == "daily_limit_reached":
        raise HTTPException(429, detail=result)
    log.info(f"[MAIN] /api/chat reply: '{result['reply'][:80]}'")
    return {
        "reply": result["reply"],
        "tokens_in": result.get("tokens_in", 0),
        "tokens_out": result.get("tokens_out", 0),
        "tokens_total": result.get("tokens_total", 0),
        "provider": result.get("provider", "unknown"),
        "history": get_history(),
    }


@app.post("/api/chat/reset")
def chat_reset():
    reset_history()
    return {"status": "history cleared"}


@app.get("/api/chat/history")
def chat_history():
    return {"history": get_history()}
