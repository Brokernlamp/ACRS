import io
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def _to_png(fig) -> bytes:
    try:
        return fig.to_image(format="png", width=900, height=400)
    except Exception as e:
        raise RuntimeError(f"Failed to render chart to PNG: {str(e)}")


def chart_leads_over_time(daily: pd.DataFrame):
    if daily.empty:
        raise ValueError("No data available for leads chart")
    fig = px.line(
        daily, x="date", y="leads",
        title="Leads Over Time",
        labels={"leads": "Leads", "date": "Date"},
        template="plotly_white",
        markers=True,
    )
    fig.update_traces(line_color="#4F46E5", line_width=2.5)
    return fig, _to_png(fig)


def chart_spend_vs_leads(camp: pd.DataFrame):
    if camp.empty:
        raise ValueError("No data available for spend vs leads chart")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Spend ($)", x=camp["campaign"], y=camp["spend"], marker_color="#4F46E5"))
    fig.add_trace(go.Bar(name="Leads", x=camp["campaign"], y=camp["leads"], marker_color="#10B981"))
    fig.update_layout(
        title="Spend vs Leads by Campaign",
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", y=1.1),
    )
    return fig, _to_png(fig)


def chart_campaign_performance(camp: pd.DataFrame):
    if camp.empty:
        raise ValueError("No data available for campaign performance chart")
    valid = camp[camp["cpl"].notna()]
    if valid.empty:
        valid = camp.copy()
        valid["cpl"] = 0
    fig = px.bar(
        valid.sort_values("cpl"),
        x="campaign", y="cpl",
        title="Cost Per Lead (CPL) by Campaign",
        labels={"cpl": "CPL ($)", "campaign": "Campaign"},
        template="plotly_white",
        color="cpl",
        color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
    )
    return fig, _to_png(fig)


def chart_performance_scores(scored: pd.DataFrame):
    if scored.empty:
        raise ValueError("No data available for performance scores chart")
    fig = px.bar(
        scored.sort_values("score", ascending=True),
        x="score", y="campaign",
        orientation="h",
        title="AI Performance Score by Campaign (0–100)",
        labels={"score": "Score", "campaign": "Campaign"},
        template="plotly_white",
        color="score",
        color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
        text="score",
    )
    fig.update_traces(textposition="outside")
    return fig, _to_png(fig)


def chart_budget_allocation(alloc: pd.DataFrame):
    """Current spend vs recommended budget side-by-side bar — replaces pie chart."""
    if alloc.empty:
        raise ValueError("No data available for budget allocation chart")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Spend", x=alloc["campaign"], y=alloc["spend"] if "spend" in alloc.columns else [0]*len(alloc),
        marker_color="#94A3B8",
    ))
    fig.add_trace(go.Bar(
        name="Recommended Budget", x=alloc["campaign"], y=alloc["recommended_budget"],
        marker_color="#4F46E5",
        text=[f"${v:,.0f}" for v in alloc["recommended_budget"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Current Spend vs Recommended Budget",
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", y=1.1),
        yaxis_title="Amount ($)",
    )
    return fig, _to_png(fig)


def chart_leads_forecast(daily: pd.DataFrame, predicted_leads: int, days_ahead: int = 7):
    if daily.empty:
        raise ValueError("No data available for forecast chart")
    daily = daily.sort_values("date").copy()
    last_date = daily["date"].max()
    if pd.isna(last_date):
        raise ValueError("Invalid date data in daily trends")
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days_ahead)
    daily_pred = (predicted_leads or 0) / days_ahead
    # Confidence band: ±20% around forecast
    upper = daily_pred * 1.20
    lower = daily_pred * 0.80

    fig = go.Figure()
    # Confidence band
    fig.add_trace(go.Scatter(
        x=list(future_dates) + list(future_dates[::-1]),
        y=[upper] * days_ahead + [lower] * days_ahead,
        fill="toself", fillcolor="rgba(16,185,129,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Confidence Range", showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["leads"],
        name="Actual", line=dict(color="#4F46E5", width=2.5), mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=future_dates, y=[daily_pred] * days_ahead,
        name="Forecast", line=dict(color="#10B981", width=2, dash="dash"), mode="lines+markers"
    ))
    fig.update_layout(
        title=f"Leads Forecast — Next {days_ahead} Days",
        template="plotly_white",
        legend=dict(orientation="h", y=1.1),
    )
    return fig, _to_png(fig)
