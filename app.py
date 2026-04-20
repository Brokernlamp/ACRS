import tempfile
import gradio as gr
import pandas as pd
from datetime import datetime, timedelta
import uuid

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
    create_campaign, upsert_campaign_data, get_campaign_data, get_client_data_summary
)
from comparison import (
    calculate_period_comparison, get_date_ranges, format_comparison_html, get_comparison_summary
)

# Global state for UI
_state: dict = {}
_current_user_id = 1  # Default user ID
_current_client_id = None  # Current selected client

# ── CSS ────────────────────────────────────────────────────────────────────────
# Load enterprise CSS
import os

CSS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enterprise_ui.css")
print(f"[DEBUG] Looking for CSS at: {CSS_FILE}")
print(f"[DEBUG] CSS file exists: {os.path.exists(CSS_FILE)}")

if os.path.exists(CSS_FILE):
    with open(CSS_FILE, 'r', encoding='utf-8') as f:
        CSS = f.read()
    print(f"[DEBUG] CSS loaded successfully: {len(CSS)} characters")
else:
    print("[WARNING] enterprise_ui.css not found, using fallback CSS")
    # Fallback minimal CSS if file not found
    CSS = """
    :root {
        --gray-50: #F9FAFB;
        --gray-200: #E5E7EB;
        --gray-600: #4B5563;
        --gray-900: #111827;
        --blue-500: #3B82F6;
    }
    body, .gradio-container { 
        background: var(--gray-50) !important; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    """


def _kpi_cards_html(kpis: dict) -> str:
    icons   = ["💰", "🎯", "📊", "💡"]
    classes = ["purple", "green", "amber", "red"]
    items   = list(kpis.items())
    cards   = ""
    for i, (label, value) in enumerate(items):
        cards += f"""
        <div class="kpi-card {classes[i]}">
            <div class="kpi-label">{icons[i]} {label}</div>
            <div class="kpi-value">{value}</div>
        </div>"""
    return f'<div class="kpi-grid">{cards}</div>'


def _predictions_html(lp, cp, ctr_p) -> str:
    trend_color = "#10B981" if "Improving" in lp["trend"] else ("#EF4444" if "Declining" in lp["trend"] else "#F59E0B")
    refresh_badge = '<span style="background:#FEF2F2;color:#EF4444;padding:2px 8px;border-radius:20px;font-size:0.75rem;font-weight:600;">⚠️ Refresh Needed</span>' if ctr_p["refresh_needed"] else '<span style="background:#ECFDF5;color:#10B981;padding:2px 8px;border-radius:20px;font-size:0.75rem;font-weight:600;">✅ Healthy</span>'
    return f"""
    <div class="pred-grid">
        <div class="pred-card">
            <div class="pred-icon">🎯</div>
            <div class="pred-label">Expected Leads (7d)</div>
            <div class="pred-val">{lp['predicted_leads']}</div>
            <div class="pred-sub" style="color:{trend_color};font-weight:600;">{lp['trend']} &nbsp;·&nbsp; {lp['growth_rate_pct']:+}%</div>
        </div>
        <div class="pred-card">
            <div class="pred-icon">💸</div>
            <div class="pred-label">Expected CPL</div>
            <div class="pred-val">${cp['predicted_cpl']}</div>
            <div class="pred-sub">Will <strong>{cp['direction']}</strong> at current budget</div>
        </div>
        <div class="pred-card">
            <div class="pred-icon">👁️</div>
            <div class="pred-label">Expected CTR</div>
            <div class="pred-val">{ctr_p['predicted_ctr']}%</div>
            <div class="pred-sub">Fatigue drop: {ctr_p['drop_pct']}% &nbsp; {refresh_badge}</div>
        </div>
    </div>"""


def _actions_html(actions: list) -> str:
    color_map = {"🚀": ("scale", "#10B981"), "⚠️": ("review", "#F59E0B"), "💸": ("cut", "#4F46E5"), "✂️": ("cut", "#EF4444")}
    html = ""
    for a in actions:
        first_char = a[:2].strip()
        cls, color = color_map.get(first_char, ("", "#4F46E5"))
        html += f'<div class="action-card {cls}" style="border-left-color:{color}">{a}</div>'
    return html


def _finance_html(waste: dict) -> str:
    return f"""
    <div class="finance-grid">
        <div class="finance-card waste">
            <div class="f-label">🔥 Wasted Spend</div>
            <div class="f-val">${waste['total_wasted']:,.2f}</div>
        </div>
        <div class="finance-card worst">
            <div class="f-label">⚠️ Worst Offender</div>
            <div class="f-val">{waste['worst_campaign']}</div>
        </div>
        <div class="finance-card save">
            <div class="f-label">💰 Recoverable</div>
            <div class="f-val">${waste['savings_opportunity']:,.2f}</div>
        </div>
    </div>"""


def _alloc_html(alloc: pd.DataFrame) -> str:
    rows = ""
    max_score = alloc["score"].max()
    for _, r in alloc.iterrows():
        bar_w = int(r["score"] / max_score * 120)
        rows += f"""<tr>
            <td><strong>{r['campaign']}</strong></td>
            <td><span class="score-bar" style="width:{bar_w}px"></span> <strong>{r['score']}</strong></td>
            <td>{r['budget_share_pct']}%</td>
            <td><strong>${r['recommended_budget']:,.2f}</strong></td>
        </tr>"""
    return f"""
    <table class="alloc-table">
        <thead><tr><th>Campaign</th><th>Score</th><th>Share</th><th>Recommended Budget</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>"""


def _patterns_html(patterns: list) -> str:
    icons = ["📅", "📈", "⚡", "🏆", "🔍"]
    html = ""
    for i, p in enumerate(patterns):
        icon = icons[i % len(icons)]
        cls = "green" if any(w in p for w in ["Best", "improving", "spike"]) else ("red" if any(w in p for w in ["drops", "Declining", "drop"]) else "amber")
        html += f'<div class="insight-card {cls}">{icon} {p}</div>'
    return html


# ── Processing ─────────────────────────────────────────────────────────────────
def load_data_from_db(client_id, start_date=None, end_date=None):
    """Load campaign data from database for a client"""
    db = SessionLocal()
    try:
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get all campaign data for client
        from database.models import CampaignData, Campaign
        query = db.query(CampaignData).join(Campaign).filter(Campaign.client_id == client_id)
        
        if start_date:
            query = query.filter(CampaignData.date >= start_date)
        if end_date:
            query = query.filter(CampaignData.date <= end_date)
        
        data = query.order_by(CampaignData.date).all()
        
        if not data:
            return None
        
        # Convert to DataFrame
        rows = []
        for d in data:
            campaign = db.query(Campaign).filter(Campaign.id == d.campaign_id).first()
            rows.append({
                'date': d.date,
                'campaign': campaign.campaign_name,
                'impressions': d.impressions,
                'clicks': d.clicks,
                'spend': d.spend,
                'leads': d.leads,
                'ctr': d.ctr,
                'cpl': d.cpl
            })
        
        df = pd.DataFrame(rows)
        return df
        
    finally:
        db.close()

def process_upload(file, client_name_val):
    empty = [gr.update(visible=False)] * 3 + [""] * 6 + [None] * 6 + ["", gr.update(choices=[])]

    if file is None:
        return empty + ["<p class='status-err'>⚠️ Please upload a CSV file.</p>"]

    try:
        df = pd.read_csv(file.name)
    except Exception as e:
        return empty + [f"<p class='status-err'> Could not read file: {e}</p>"]

    ok, msg = validate_csv(df)
    if not ok:
        return empty + [f"<p class='status-err'>{msg}</p>"]

    df = sanitize(df)
    df = compute_kpis(df)
    
    # Save to database
    db = SessionLocal()
    try:
        # Get or create client
        client = None
        for c in get_clients_by_user(db, _current_user_id):
            if c.name == client_name_val:
                client = c
                break
        
        if not client:
            client = create_client(db, user_id=_current_user_id, name=client_name_val, industry="Unknown")
        
        # Set current client
        global _current_client_id
        _current_client_id = client.id
        
        # Save campaign data to database
        for _, row in df.iterrows():
            # Get or create campaign
            campaign = None
            for c in get_campaigns_by_client(db, client.id):
                if c.campaign_name == row['campaign']:
                    campaign = c
                    break
            
            if not campaign:
                campaign = create_campaign(db, client_id=client.id, campaign_name=row['campaign'])
            
            # Upsert campaign data
            upsert_campaign_data(
                db,
                campaign_id=campaign.id,
                date=row['date'],
                impressions=int(row['impressions']),
                clicks=int(row['clicks']),
                spend=float(row['spend']),
                leads=int(row['leads']),
                ctr=row['ctr'],
                cpl=row['cpl'],
                conversion_rate=row.get('conversion_rate', 0.0)
            )
        
    except Exception as e:
        return empty + [f"<p class='status-err'>❌ Database error: {e}</p>"]
    finally:
        db.close()
    camp  = campaign_summary(df)
    daily = daily_trends(df)
    kpis  = summary_kpis(df)
    insights = generate_insights(camp, kpis)

    fig1, png1 = chart_leads_over_time(daily)
    fig2, png2 = chart_spend_vs_leads(camp)
    fig3, png3 = chart_campaign_performance(camp)

    intel  = run_intelligence(camp, daily)
    fig4, png4 = chart_performance_scores(intel["scored"])
    fig5, png5 = chart_budget_allocation(intel["allocation"])
    fig6, png6 = chart_leads_forecast(daily, intel["leads_prediction"]["predicted_leads"])

    _state.update(
        df=df, camp=camp, daily=daily, kpis=kpis,
        insights=insights, pngs=[png1, png2, png3],
        intel=intel, ai_pngs=[png4, png5, png6],
    )

    lp    = intel["leads_prediction"]
    cp    = intel["cpl_prediction"]
    ctr_p = intel["ctr_prediction"]
    waste = intel["waste"]
    alloc = intel["allocation"]

    kpi_html      = _kpi_cards_html(kpis)
    pred_html     = _predictions_html(lp, cp, ctr_p)
    actions_html  = _actions_html(intel["actions"])
    finance_html  = _finance_html(waste)
    alloc_html    = _alloc_html(alloc)
    patterns_html = _patterns_html(intel["patterns"])

    insight_html = "".join(
        f'<div class="insight-card">{ins}</div>' for ins in insights
    )

    campaigns = camp["campaign"].tolist()

    return (
        gr.update(visible=True),   # charts_tab
        gr.update(visible=True),   # ai_tab
        gr.update(visible=True),   # actions_tab
        kpi_html,
        insight_html,
        pred_html,
        actions_html,
        finance_html + alloc_html,
        patterns_html,
        fig1, fig2, fig3, fig4, fig5, fig6,
        "<p class='status-ok'>✅ Intelligence engine activated successfully.</p>",
        gr.update(choices=campaigns, value=campaigns[0] if campaigns else None),
    )


def run_simulation(campaign, delta_pct):
    if "camp" not in _state:
        return "<p class='status-err'>⚠️ Upload data first.</p>"
    result = simulate_budget_change(_state["camp"], campaign, delta_pct / 100.0)
    sign   = "+" if result["leads_change"] >= 0 else ""
    cls    = "" if result["leads_change"] >= 0 else "negative"
    return f"""
    <div class="sim-result {cls}">
        <strong>📊 {result['action']} — {campaign}</strong><br><br>
        💰 Spend Change: <strong>${result['spend_change']:+,.2f}</strong><br>
        🎯 Leads Change: <strong>{sign}{result['leads_change']}</strong><br>
        📉 CPL Change: <strong>${result['cpl_change']:+.2f}</strong><br><br>
        <em>{result['summary']}</em>
    </div>"""


def run_pause_simulation(campaign):
    if "camp" not in _state:
        return "<p class='status-err'>⚠️ Upload data first.</p>"
    result = simulate_budget_change(_state["camp"], campaign, -1.0)
    return f"""
    <div class="sim-result negative">
        <strong>⏸️ Pause Simulation — {campaign}</strong><br><br>
        💰 Spend Saved: <strong>${abs(result['spend_change']):,.2f}</strong><br>
        🎯 Leads Lost: <strong>{abs(int(result['leads_change']))}</strong><br><br>
        <em>{result['summary']}</em>
    </div>"""


def download_pdf(client_name):
    if not _state:
        return None, "<p class='status-err'>⚠️ Upload data first.</p>"
    date_range = f"{_state['df']['date'].min().date()} → {_state['df']['date'].max().date()}"
    pdf_bytes = generate_pdf(
        client_name=client_name, date_range=date_range,
        kpis=_state["kpis"], camp_df=_state["camp"],
        insights=_state["insights"], chart_pngs=_state["pngs"],
    )
    _state["pdf_bytes"] = pdf_bytes
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes); tmp.flush()
    return tmp.name, "<p class='status-ok'>✅ Standard report ready.</p>"


def download_growth_pdf(client_name):
    if not _state:
        return None, "<p class='status-err'>⚠️ Upload data first.</p>"
    date_range = f"{_state['df']['date'].min().date()} → {_state['df']['date'].max().date()}"
    pdf_bytes = generate_growth_pdf(
        client_name=client_name, date_range=date_range,
        kpis=_state["kpis"], camp_df=_state["camp"],
        insights=_state["insights"], chart_pngs=_state["pngs"],
        intelligence=_state["intel"], ai_chart_pngs=_state["ai_pngs"],
    )
    _state["pdf_bytes"] = pdf_bytes
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes); tmp.flush()
    return tmp.name, "<p class='status-ok'>✅ AI Growth Strategy PDF ready.</p>"


def send_email_fn(client_name, sender_email, sender_password, recipient_email):
    if "pdf_bytes" not in _state:
        download_growth_pdf(client_name)
    ok, msg = send_report(sender_email, sender_password, recipient_email, client_name, _state.get("pdf_bytes", b""))
    cls = "status-ok" if ok else "status-err"
    return f"<p class='{cls}'>{'✅' if ok else '❌'} {msg}</p>"


def refresh_data(start_date, end_date, comparison_period):
    """Refresh data from database"""
    global _current_client_id
    
    if not _current_client_id:
        return [
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            "", "", "", "", "", "", None, None, None, None, None, None,
            "<p class='status-err'>⚠️ Please upload data first to select a client.</p>",
            gr.update(choices=[]),
            "<p class='status-err'>No client selected</p>"
        ]
    
    # Load data from database
    df = load_data_from_db(_current_client_id, start_date, end_date)
    
    if df is None or df.empty:
        return [
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            "", "", "", "", "", "", None, None, None, None, None, None,
            "<p class='status-err'>⚠️ No data found for selected date range.</p>",
            gr.update(choices=[]),
            "<p class='status-err'>No data available</p>"
        ]
    
    # Process data
    df = compute_kpis(df)
    camp = campaign_summary(df)
    daily = daily_trends(df)
    kpis = summary_kpis(df)
    insights = generate_insights(camp, kpis)
    
    # Generate charts
    fig1, png1 = chart_leads_over_time(daily)
    fig2, png2 = chart_spend_vs_leads(camp)
    fig3, png3 = chart_campaign_performance(camp)
    
    # Run intelligence
    intel = run_intelligence(camp, daily)
    fig4, png4 = chart_performance_scores(intel["scored"])
    fig5, png5 = chart_budget_allocation(intel["allocation"])
    fig6, png6 = chart_leads_forecast(daily, intel["leads_prediction"]["predicted_leads"])
    
    # Store in state
    _state.update(
        df=df, camp=camp, daily=daily, kpis=kpis,
        insights=insights, pngs=[png1, png2, png3],
        intel=intel, ai_pngs=[png4, png5, png6],
    )
    
    # Generate HTML
    lp = intel["leads_prediction"]
    cp = intel["cpl_prediction"]
    ctr_p = intel["ctr_prediction"]
    waste = intel["waste"]
    alloc = intel["allocation"]
    
    kpi_html = _kpi_cards_html(kpis)
    pred_html = _predictions_html(lp, cp, ctr_p)
    actions_html = _actions_html(intel["actions"])
    finance_html = _finance_html(waste)
    alloc_html = _alloc_html(alloc)
    patterns_html = _patterns_html(intel["patterns"])
    insight_html = "".join(f'<div class="insight-card">{ins}</div>' for ins in insights)
    
    campaigns = camp["campaign"].tolist()
    
    # Handle comparison
    comparison_html = ""
    if comparison_period != "None":
        period = 'week' if 'Week' in comparison_period else 'month'
        ranges = get_date_ranges(end_date, period)
        
        # Load previous period data
        prev_start, prev_end = ranges['previous']
        prev_df = load_data_from_db(_current_client_id, prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
        
        if prev_df is not None and not prev_df.empty:
            prev_df = compute_kpis(prev_df)
            comparison = calculate_period_comparison(df, prev_df)
            comparison_html = f"<p style='padding:10px;background:#FAFAFA;border:1px solid #E0E0E0;'>{get_comparison_summary(comparison)}</p>"
    
    return (
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        kpi_html,
        insight_html,
        pred_html,
        actions_html,
        finance_html + alloc_html,
        patterns_html,
        fig1, fig2, fig3, fig4, fig5, fig6,
        "<p class='status-ok'>✅ Data refreshed from database.</p>",
        gr.update(choices=campaigns, value=campaigns[0] if campaigns else None),
        comparison_html
    )


def get_clients_list():
    """Get list of all clients with stats"""
    db = SessionLocal()
    try:
        clients = get_clients_by_user(db, _current_user_id)
        
        if not clients:
            return []
        
        rows = []
        for client in clients:
            campaigns = get_campaigns_by_client(db, client.id)
            
            # Get stats
            df = load_data_from_db(client.id)
            if df is not None and not df.empty:
                total_spend = df['spend'].sum()
                total_leads = df['leads'].sum()
                avg_cpl = total_spend / max(total_leads, 1)
            else:
                total_spend = 0
                total_leads = 0
                avg_cpl = 0
            
            rows.append([
                client.name,
                client.industry or "N/A",
                len(campaigns),
                f"${total_spend:,.2f}",
                int(total_leads),
                f"${avg_cpl:.2f}"
            ])
        
        return rows
    finally:
        db.close()


def add_new_client(name, industry, target_cpl, budget):
    """Add a new client"""
    if not name:
        return gr.update(), "<p class='status-err'>❌ Client name required</p>"
    
    db = SessionLocal()
    try:
        # Check if exists
        existing = get_clients_by_user(db, _current_user_id)
        for c in existing:
            if c.name.lower() == name.lower():
                return gr.update(), "<p class='status-err'>❌ Client already exists</p>"
        
        # Create client
        client = create_client(
            db,
            user_id=_current_user_id,
            name=name,
            industry=industry or "Unknown",
            target_cpl=float(target_cpl) if target_cpl else None,
            monthly_budget=float(budget) if budget else None
        )
        
        # Refresh list
        new_list = get_clients_list()
        return new_list, f"<p class='status-ok'>✅ Client '{name}' added successfully</p>"
        
    except Exception as e:
        return gr.update(), f"<p class='status-err'>❌ Error: {e}</p>"
    finally:
        db.close()
    """Refresh data from database"""
    global _current_client_id
    
    if not _current_client_id:
        return [
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            "", "", "", "", "", "", None, None, None, None, None, None,
            "<p class='status-err'>⚠️ Please upload data first to select a client.</p>",
            gr.update(choices=[]),
            "<p class='status-err'>No client selected</p>"
        ]
    
    # Load data from database
    df = load_data_from_db(_current_client_id, start_date, end_date)
    
    if df is None or df.empty:
        return [
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            "", "", "", "", "", "", None, None, None, None, None, None,
            "<p class='status-err'>⚠️ No data found for selected date range.</p>",
            gr.update(choices=[]),
            "<p class='status-err'>No data available</p>"
        ]
    
    # Process data
    df = compute_kpis(df)
    camp = campaign_summary(df)
    daily = daily_trends(df)
    kpis = summary_kpis(df)
    insights = generate_insights(camp, kpis)
    
    # Generate charts
    fig1, png1 = chart_leads_over_time(daily)
    fig2, png2 = chart_spend_vs_leads(camp)
    fig3, png3 = chart_campaign_performance(camp)
    
    # Run intelligence
    intel = run_intelligence(camp, daily)
    fig4, png4 = chart_performance_scores(intel["scored"])
    fig5, png5 = chart_budget_allocation(intel["allocation"])
    fig6, png6 = chart_leads_forecast(daily, intel["leads_prediction"]["predicted_leads"])
    
    # Store in state
    _state.update(
        df=df, camp=camp, daily=daily, kpis=kpis,
        insights=insights, pngs=[png1, png2, png3],
        intel=intel, ai_pngs=[png4, png5, png6],
    )
    
    # Generate HTML
    lp = intel["leads_prediction"]
    cp = intel["cpl_prediction"]
    ctr_p = intel["ctr_prediction"]
    waste = intel["waste"]
    alloc = intel["allocation"]
    
    kpi_html = _kpi_cards_html(kpis)
    pred_html = _predictions_html(lp, cp, ctr_p)
    actions_html = _actions_html(intel["actions"])
    finance_html = _finance_html(waste)
    alloc_html = _alloc_html(alloc)
    patterns_html = _patterns_html(intel["patterns"])
    insight_html = "".join(f'<div class="insight-card">{ins}</div>' for ins in insights)
    
    campaigns = camp["campaign"].tolist()
    
    # Handle comparison
    comparison_html = ""
    if comparison_period != "None":
        period = 'week' if 'Week' in comparison_period else 'month'
        ranges = get_date_ranges(end_date, period)
        
        # Load previous period data
        prev_start, prev_end = ranges['previous']
        prev_df = load_data_from_db(_current_client_id, prev_start.strftime('%Y-%m-%d'), prev_end.strftime('%Y-%m-%d'))
        
        if prev_df is not None and not prev_df.empty:
            prev_df = compute_kpis(prev_df)
            comparison = calculate_period_comparison(df, prev_df)
            comparison_html = f"<p style='padding:10px;background:#FAFAFA;border:1px solid #E0E0E0;'>{get_comparison_summary(comparison)}</p>"
    
    return (
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        kpi_html,
        insight_html,
        pred_html,
        actions_html,
        finance_html + alloc_html,
        patterns_html,
        fig1, fig2, fig3, fig4, fig5, fig6,
        "<p class='status-ok'>✅ Data refreshed from database.</p>",
        gr.update(choices=campaigns, value=campaigns[0] if campaigns else None),
        comparison_html
    )


# ── UI ─────────────────────────────────────────────────────────────────────────
with gr.Blocks(title="AI Growth Operator", css=CSS, theme=gr.themes.Base()) as demo:
    
    # Header
    gr.HTML("""
    <div class="app-header">
        <h1>AI Growth Operator</h1>
        <p>Marketing analytics platform for agencies — Predictive insights, budget optimization, automated reporting</p>
    </div>
    """)
    
    # Date Range & Comparison Controls
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Row():
                start_date = gr.Textbox(
                    label="Start Date",
                    value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    placeholder="YYYY-MM-DD"
                )
                end_date = gr.Textbox(
                    label="End Date",
                    value=datetime.now().strftime('%Y-%m-%d'),
                    placeholder="YYYY-MM-DD"
                )
        with gr.Column(scale=1):
            comparison_period = gr.Radio(
                label="Compare To",
                choices=["None", "Previous Week", "Previous Month"],
                value="None"
            )
        with gr.Column(scale=1):
            refresh_data_btn = gr.Button("🔄 Refresh Data", variant="secondary")
    
    comparison_summary = gr.HTML("")
    
    # Upload row
    with gr.Group(elem_classes="upload-card"):
        with gr.Row():
            with gr.Column(scale=3):
                csv_input = gr.File(label="📂 Upload Campaign CSV", file_types=[".csv"])
            with gr.Column(scale=2):
                client_name = gr.Textbox(label="Client Name", placeholder="e.g. Acme Corp", lines=1)
                upload_btn  = gr.Button("⚡ Activate Intelligence Engine", variant="primary", elem_classes="primary-btn")

    status_html = gr.HTML("")

    # KPI cards
    kpi_html = gr.HTML("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    with gr.Tabs(elem_classes="tab-nav") as tabs:

        # ── Tab 1: Dashboard ──
        with gr.TabItem("📊 Dashboard", id="charts") as charts_tab:
            with gr.Row():
                chart1 = gr.Plot(show_label=False)
                chart2 = gr.Plot(show_label=False)
            chart3 = gr.Plot(show_label=False)

            with gr.Accordion("💡 Diagnostic Insights", open=True):
                insights_html = gr.HTML("")

        # ── Tab 2: AI Growth Engine ──
        with gr.TabItem("🧠 AI Growth Engine", id="ai") as ai_tab:

            gr.HTML('<div class="section-title">📈 Predictions — Next 7 Days</div>')
            pred_html = gr.HTML("")

            with gr.Row():
                chart4 = gr.Plot(show_label=False)
                chart6 = gr.Plot(show_label=False)

            gr.HTML('<div class="section-title">🎯 Recommended Actions</div>')
            actions_html = gr.HTML("")

            gr.HTML('<div class="section-title">💸 Financial Impact & Budget Plan</div>')
            finance_alloc_html = gr.HTML("")

            with gr.Row():
                chart5 = gr.Plot(show_label=False)

            gr.HTML('<div class="section-title">🔍 Detected Patterns</div>')
            patterns_html = gr.HTML("")

            # Scenario Simulator
            gr.HTML('<div class="section-title">🧪 Scenario Simulator</div>')
            with gr.Row():
                with gr.Column():
                    sim_campaign = gr.Dropdown(label="Select Campaign", choices=[], interactive=True)
                    sim_delta    = gr.Slider(label="Budget Change (%)", minimum=-80, maximum=100, step=10, value=20)
                    sim_btn      = gr.Button("▶ Run Budget Simulation", variant="secondary")
                    sim_result   = gr.HTML("")
                with gr.Column():
                    pause_campaign = gr.Dropdown(label="Campaign to Pause", choices=[], interactive=True)
                    pause_btn      = gr.Button("⏸ Simulate Pause", variant="secondary")
                    pause_result   = gr.HTML("")

        # ── Tab 3: Clients ──
        with gr.TabItem("💼 Clients", id="clients") as clients_tab:
            
            gr.HTML('<div class="section-title">Client Management</div>')
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Client list
                    client_list = gr.Dataframe(
                        headers=["Client Name", "Industry", "Campaigns", "Total Spend", "Total Leads", "Avg CPL"],
                        label="Your Clients",
                        interactive=False
                    )
                    refresh_clients_list_btn = gr.Button("🔄 Refresh Client List")
                
                with gr.Column(scale=1):
                    # Add new client
                    gr.HTML('<div class="section-title">Add New Client</div>')
                    new_client_name = gr.Textbox(label="Client Name", placeholder="Acme Corp")
                    new_client_industry = gr.Textbox(label="Industry", placeholder="SaaS")
                    new_client_target_cpl = gr.Number(label="Target CPL ($)", value=50.0)
                    new_client_budget = gr.Number(label="Monthly Budget ($)", value=10000.0)
                    add_client_btn = gr.Button("➕ Add Client", variant="primary")
                    add_client_status = gr.HTML("")
        
        # ── Tab 4: Reports & Email ──
        with gr.TabItem("📄 Reports & Email", id="actions") as actions_tab:
            with gr.Row():
                with gr.Column():
                    gr.HTML('<div class="section-title">📄 Download Reports</div>')
                    pdf_btn          = gr.Button("📥 Standard Report (PDF)", variant="secondary")
                    pdf_output       = gr.File(label="")
                    pdf_status       = gr.HTML("")
                    growth_pdf_btn   = gr.Button("🚀 AI Growth Strategy Report (PDF)", variant="primary", elem_classes="primary-btn")
                    growth_pdf_output = gr.File(label="")
                    growth_pdf_status = gr.HTML("")

                with gr.Column():
                    gr.HTML('<div class="section-title">📧 Email Report</div>')
                    sender_email  = gr.Textbox(label="Your Gmail Address", placeholder="you@gmail.com")
                    sender_pass   = gr.Textbox(label="Gmail App Password", type="password", placeholder="xxxx xxxx xxxx xxxx")
                    gr.HTML('<p style="font-size:0.78rem;color:#6B7280;margin:-8px 0 8px 0;">Generate an App Password at myaccount.google.com → Security → App Passwords</p>')
                    recipient     = gr.Textbox(label="Recipient Email", placeholder="client@example.com")
                    email_btn     = gr.Button("📨 Send AI Growth Report", variant="secondary")
                    email_status  = gr.HTML("")

    # ── Wire Events ───────────────────────────────────────────────────────────
    
    upload_btn.click(
        process_upload,
        inputs=[csv_input, client_name],
        outputs=[
            charts_tab, ai_tab, actions_tab,
            kpi_html, insights_html,
            pred_html, actions_html, finance_alloc_html, patterns_html,
            chart1, chart2, chart3, chart4, chart5, chart6,
            status_html, sim_campaign,
        ],
    )
    
    refresh_data_btn.click(
        refresh_data,
        inputs=[start_date, end_date, comparison_period],
        outputs=[
            charts_tab, ai_tab, actions_tab,
            kpi_html, insights_html,
            pred_html, actions_html, finance_alloc_html, patterns_html,
            chart1, chart2, chart3, chart4, chart5, chart6,
            status_html, sim_campaign,
            comparison_summary
        ],
    )
    
    # Client management
    refresh_clients_list_btn.click(
        get_clients_list,
        outputs=[client_list]
    )
    
    add_client_btn.click(
        add_new_client,
        inputs=[new_client_name, new_client_industry, new_client_target_cpl, new_client_budget],
        outputs=[client_list, add_client_status]
    )

    sim_campaign.change(lambda x: gr.update(value=x), inputs=[sim_campaign], outputs=[pause_campaign])
    sim_btn.click(run_simulation, inputs=[sim_campaign, sim_delta], outputs=[sim_result])
    pause_btn.click(run_pause_simulation, inputs=[pause_campaign], outputs=[pause_result])

    pdf_btn.click(download_pdf, inputs=[client_name], outputs=[pdf_output, pdf_status])
    growth_pdf_btn.click(download_growth_pdf, inputs=[client_name], outputs=[growth_pdf_output, growth_pdf_status])
    email_btn.click(send_email_fn, inputs=[client_name, sender_email, sender_pass, recipient], outputs=[email_status])

if __name__ == "__main__":
    demo.launch()
