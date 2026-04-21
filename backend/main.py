import io
import base64
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state (per-process; replace with Redis for multi-worker)
_state: dict = {}
_current_user_id = 1
_current_client_id: Optional[int] = None


def _fig_to_b64(png: bytes) -> str:
    return base64.b64encode(png).decode()


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

    _, png1 = chart_leads_over_time(daily)
    _, png2 = chart_spend_vs_leads(camp)
    _, png3 = chart_campaign_performance(camp)

    intel = run_intelligence(camp, daily)
    _, png4 = chart_performance_scores(intel["scored"])
    _, png5 = chart_budget_allocation(intel["allocation"])
    _, png6 = chart_leads_forecast(daily, intel["leads_prediction"]["predicted_leads"])

    _state.update(
        df=df, camp=camp, daily=daily, kpis=kpis,
        insights=insights, pngs=[png1, png2, png3],
        intel=intel, ai_pngs=[png4, png5, png6],
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
        "predictions": intel["leads_prediction"],
        "cpl_prediction": intel["cpl_prediction"],
        "ctr_prediction": intel["ctr_prediction"],
        "actions": intel["actions"],
        "waste": waste,
        "allocation": alloc_records,
        "patterns": intel["patterns"],
        "charts": {
            "leads_over_time": _fig_to_b64(png1),
            "spend_vs_leads": _fig_to_b64(png2),
            "campaign_performance": _fig_to_b64(png3),
            "performance_scores": _fig_to_b64(png4),
            "budget_allocation": _fig_to_b64(png5),
            "leads_forecast": _fig_to_b64(png6),
        },
    }
    return _safe(result)


# ── Upload ────────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), client_name: str = Form(...)):
    global _current_client_id
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


@app.post("/api/refresh")
def refresh_data(req: RefreshRequest):
    if not _current_client_id:
        raise HTTPException(400, "No client selected. Upload data first.")

    df = _load_data_from_db(_current_client_id, req.start_date, req.end_date)
    if df is None or df.empty:
        raise HTTPException(404, "No data found for selected date range.")

    result = _process_df(df)

    if req.comparison_period and req.comparison_period != "None":
        period = "week" if "Week" in req.comparison_period else "month"
        ranges = get_date_ranges(req.end_date, period)
        prev_start, prev_end = ranges["previous"]
        prev_df = _load_data_from_db(_current_client_id, prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d"))
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
        insights=_state["insights"], chart_pngs=_state["pngs"],
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
        insights=_state["insights"], chart_pngs=_state["pngs"],
        intelligence=_state["intel"], ai_chart_pngs=_state["ai_pngs"],
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
            insights=_state["insights"], chart_pngs=_state["pngs"],
            intelligence=_state["intel"], ai_chart_pngs=_state["ai_pngs"],
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


@app.post("/api/clients")
def add_client(req: NewClientRequest):
    if not req.name:
        raise HTTPException(400, "Client name is required.")
    db = SessionLocal()
    try:
        existing = get_clients_by_user(db, _current_user_id)
        if any(c.name.lower() == req.name.lower() for c in existing):
            raise HTTPException(409, f"Client '{req.name}' already exists.")
        client = create_client(
            db, user_id=_current_user_id, name=req.name,
            industry=req.industry, target_cpl=req.target_cpl, monthly_budget=req.monthly_budget,
        )
        return {"id": client.id, "name": client.name, "industry": client.industry}
    finally:
        db.close()


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Settings ─────────────────────────────────────────────────────────────────
@app.get("/api/settings")
def get_settings():
    """Return current non-secret settings."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY", "")
    return {
        "gemini_api_key_set": bool(key),
        "gemini_api_key_preview": f"{key[:8]}...{key[-4:]}" if len(key) > 12 else ("set" if key else ""),
        "gemini_model": "gemini-2.0-flash-lite",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./acrs.db"),
    }


class SettingsUpdateRequest(BaseModel):
    gemini_api_key: str = ""


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    """Write GEMINI_API_KEY to backend/.env at runtime."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        # Read existing lines
        lines = open(env_path).readlines() if os.path.exists(env_path) else []
        key_line = f"GEMINI_API_KEY={req.gemini_api_key}\n"
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("GEMINI_API_KEY="):
                new_lines.append(key_line)
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(key_line)
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        # Reload env in process
        from dotenv import load_dotenv
        load_dotenv(override=True)
        log.info(f"[SETTINGS] GEMINI_API_KEY updated")
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(500, f"Failed to save settings: {e}")


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


# ── Chatbot ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


@app.get("/api/chat/status")
def chat_status():
    from rag import _client, _COLLECTION
    key = os.getenv("GEMINI_API_KEY", "").strip()
    try:
        col = _client.get_collection(_COLLECTION)
        indexed = col.count()
    except Exception:
        indexed = 0
    return {
        "gemini_configured": bool(key),
        "rag_documents_indexed": indexed,
        "ready": indexed > 0,
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty.")
    log.info(f"[MAIN] /api/chat received: '{req.message[:80]}'")
    reply = chatbot_chat(req.message.strip())
    log.info(f"[MAIN] /api/chat reply: '{reply[:80]}'")
    return {"reply": reply, "history": get_history()}


@app.post("/api/chat/reset")
def chat_reset():
    reset_history()
    return {"status": "history cleared"}


@app.get("/api/chat/history")
def chat_history():
    return {"history": get_history()}
