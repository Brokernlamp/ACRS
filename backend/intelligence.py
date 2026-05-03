import math
import numpy as np
import pandas as pd

# ── Constants ──────────────────────────────────────────────────────────────────
BETA = 0.7       # budget sensitivity for leads
ALPHA = 0.35     # CPL inefficiency factor on budget increase
LAMBDA = 0.08    # CTR fatigue decay constant
GAMMA = 0.7      # budget→leads scaling efficiency
W1, W2, W3 = 0.3, 0.4, 0.3  # performance score weights


# ── 1. Performance Score ───────────────────────────────────────────────────────
def performance_scores(camp: pd.DataFrame) -> pd.DataFrame:
    """Normalised composite score per campaign (0–100)."""
    if camp.empty:
        raise ValueError("Cannot compute performance scores on empty DataFrame")
    df = camp.copy()
    safe_cpl = df["cpl"].replace(0, float("nan"))

    ctr_max = df["ctr"].max()
    ctr_norm = df["ctr"] / ctr_max if ctr_max else pd.Series([0.0] * len(df))

    cpl_inv = (1 / safe_cpl)
    cpl_inv_max = cpl_inv.max()
    cpl_inv_norm = cpl_inv / cpl_inv_max if cpl_inv_max else pd.Series([0.0] * len(df))

    cr_max = df["conversion_rate"].max()
    cr_norm = df["conversion_rate"] / cr_max if cr_max else pd.Series([0.0] * len(df))

    df["score"] = ((W1 * ctr_norm + W2 * cpl_inv_norm + W3 * cr_norm) * 100).fillna(0).round(1)
    return df


# ── 2. Budget Allocation ───────────────────────────────────────────────────────
def optimal_budget_allocation(camp_scored: pd.DataFrame, total_budget: float) -> pd.DataFrame:
    """Redistribute total_budget proportional to performance score."""
    df = camp_scored.copy()
    total_score = df["score"].sum()
    if total_score == 0:
        n = len(df)
        df["budget_share_pct"] = round(100 / n, 1) if n else 0.0
        df["recommended_budget"] = round(total_budget / n, 2) if n else 0.0
    else:
        df["budget_share_pct"] = (df["score"] / total_score * 100).round(1)
        df["recommended_budget"] = (df["score"] / total_score * total_budget).round(2)
    # Keep current spend for comparison chart
    if "spend" not in df.columns:
        df["spend"] = 0.0
    return df


# ── 3. Leads Prediction ────────────────────────────────────────────────────────
def predict_leads(daily: pd.DataFrame, days_ahead: int = 7, budget_delta: float = 0.0) -> dict:
    """
    Weighted moving average + growth factor + budget sensitivity.
    budget_delta: fractional change e.g. 0.20 = +20%
    """
    if daily.empty:
        return {"predicted_leads": 0, "growth_rate_pct": 0.0, "trend": "➡️ Stable", "days_ahead": days_ahead}

    leads = daily.sort_values("date")["leads"].values
    if len(leads) == 0:
        return {"predicted_leads": 0, "growth_rate_pct": 0.0, "trend": "➡️ Stable", "days_ahead": days_ahead}

    if len(leads) < 6:
        recent = leads[-min(3, len(leads)):]
        prev = leads[:max(1, len(leads) - len(recent))]
    else:
        recent = leads[-3:]
        prev = leads[-6:-3]

    recent_avg = float(recent.mean()) if len(recent) > 0 else 0.0
    prev_mean = float(prev.mean()) if len(prev) > 0 else 0.0
    prev_avg = prev_mean if prev_mean != 0 else recent_avg

    g = (recent_avg - prev_avg) / prev_avg if prev_avg != 0 else 0.0
    g = max(-0.5, min(g, 0.5))

    predicted = recent_avg * (1 + g) * (1 + BETA * budget_delta) * days_ahead
    predicted = max(0, round(predicted))

    trend = "📈 Improving" if g > 0.02 else ("📉 Declining" if g < -0.02 else "➡️ Stable")
    return {
        "predicted_leads": predicted,
        "growth_rate_pct": round(g * 100, 1),
        "trend": trend,
        "days_ahead": days_ahead,
    }


# ── 4. CPL Prediction ─────────────────────────────────────────────────────────
def predict_cpl(current_cpl: float, budget_delta: float = 0.0) -> dict:
    """CPL rises non-linearly with budget increase."""
    if not current_cpl or math.isnan(current_cpl):
        current_cpl = 0.0
    predicted = current_cpl * (1 + ALPHA * budget_delta)
    direction = "rise" if budget_delta > 0 else ("fall" if budget_delta < 0 else "stay flat")
    return {
        "predicted_cpl": round(predicted, 2),
        "direction": direction,
    }


# ── 5. CTR Fatigue Prediction ─────────────────────────────────────────────────
def predict_ctr(current_ctr: float, days: int = 7) -> dict:
    """Exponential decay model for ad fatigue."""
    if not current_ctr or math.isnan(current_ctr):
        return {"predicted_ctr": 0.0, "drop_pct": 0.0, "refresh_needed": True}
    predicted = current_ctr * math.exp(-LAMBDA * days)
    drop_pct = round((current_ctr - predicted) / current_ctr * 100, 1)
    return {
        "predicted_ctr": round(predicted, 2),
        "drop_pct": drop_pct,
        "refresh_needed": predicted < 1.0,
    }


# ── 6. Scenario Simulation ────────────────────────────────────────────────────
def simulate_budget_change(camp: pd.DataFrame, campaign_name: str, delta: float) -> dict:
    """
    Simulate impact of budget change on a single campaign.
    delta: fractional e.g. 0.20 = +20%, -1.0 = pause
    """
    matches = camp[camp["campaign"] == campaign_name]
    if matches.empty:
        return {
            "campaign": campaign_name, "action": "Error",
            "spend_change": 0, "leads_change": 0, "cpl_change": 0,
            "summary": f"Campaign '{campaign_name}' not found.",
        }
    row = matches.iloc[0]
    current_leads = row["leads"]
    current_spend = row["spend"]
    current_cpl = row["cpl"] if not (pd.isna(row["cpl"])) else 0.0

    if delta == -1.0:
        return {
            "campaign": campaign_name,
            "action": "Pause",
            "spend_change": -current_spend,
            "leads_change": -current_leads,
            "cpl_change": 0,
            "summary": (
                f"Pausing '{campaign_name}' saves ₹{current_spend:,.2f} "
                f"but eliminates ~{int(current_leads)} leads."
            ),
        }

    new_leads = round(current_leads * (1 + GAMMA * delta))
    new_spend = round(current_spend * (1 + delta), 2)
    new_cpl = round(current_cpl * (1 + ALPHA * delta), 2)
    action = f"{'Increase' if delta > 0 else 'Decrease'} budget by {abs(delta)*100:.0f}%"

    return {
        "campaign": campaign_name,
        "action": action,
        "spend_change": round(new_spend - current_spend, 2),
        "leads_change": new_leads - int(current_leads),
        "cpl_change": round(new_cpl - current_cpl, 2),
        "summary": (
            f"{action} on '{campaign_name}': "
            f"{'+'if new_leads > current_leads else ''}{new_leads - int(current_leads)} leads, "
            f"{'+'if new_spend > current_spend else ''}₹{new_spend - current_spend:,.2f} spend, "
            f"CPL → ₹{new_cpl:.2f}."
        ),
    }


# ── 7. Wasted Spend ───────────────────────────────────────────────────────────
def wasted_spend(camp: pd.DataFrame) -> dict:
    """Partial inefficiency model: proportional waste above avg CPL."""
    if camp.empty:
        return {"total_wasted": 0.0, "worst_campaign": "N/A", "worst_waste": 0.0, "savings_opportunity": 0.0}
    valid = camp[camp["cpl"].notna() & (camp["cpl"] > 0)]
    if valid.empty:
        return {"total_wasted": 0.0, "worst_campaign": camp.iloc[0]["campaign"], "worst_waste": 0.0, "savings_opportunity": 0.0}
    avg_cpl = valid["cpl"].mean()
    camp = camp.copy()
    camp["waste"] = camp.apply(
        lambda r: r["spend"] * (r["cpl"] - avg_cpl) / r["cpl"]
        if pd.notna(r["cpl"]) and r["cpl"] > avg_cpl else 0,
        axis=1,
    )
    total_waste = camp["waste"].sum()
    worst = camp.loc[camp["waste"].idxmax()]
    return {
        "total_wasted": round(total_waste, 2),
        "worst_campaign": worst["campaign"],
        "worst_waste": round(worst["waste"], 2),
        "savings_opportunity": round(total_waste * 0.6, 2),
    }


# ── 8. Pattern Detection ──────────────────────────────────────────────────────
def detect_patterns(daily: pd.DataFrame) -> list[str]:
    """Detect day-of-week fatigue, anomalies, momentum shifts."""
    if daily.empty:
        return ["Insufficient data for pattern detection."]
    patterns = []
    df = daily.copy().sort_values("date")
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return ["Insufficient data for pattern detection."]
    df["dow"] = df["date"].dt.day_name()

    dow_avg = df.groupby("dow")["leads"].mean()
    worst_day = dow_avg.idxmin()
    best_day = dow_avg.idxmax()

    if dow_avg.min() < dow_avg.mean() * 0.75:
        patterns.append(
            f"Performance consistently drops on {worst_day}s "
            f"(avg {dow_avg[worst_day]:.0f} leads vs {dow_avg.mean():.0f} overall) — likely audience fatigue."
        )

    # Week-over-week momentum
    if len(df) >= 14:
        mid = len(df) // 2
        w1_avg = df.iloc[:mid]["leads"].mean()
        w2_avg = df.iloc[mid:]["leads"].mean()
        wow = (w2_avg - w1_avg) / w1_avg * 100 if w1_avg else 0
        direction = "improving" if wow > 0 else "declining"
        patterns.append(
            f"Performance is {direction} week-over-week by {abs(wow):.1f}% "
            f"({w1_avg:.0f} → {w2_avg:.0f} avg daily leads)."
        )

    # Spike/drop anomaly: z-score > 2
    mean, std = df["leads"].mean(), df["leads"].std()
    if std > 0:
        anomalies = df[((df["leads"] - mean) / std).abs() > 2]
        for _, row in anomalies.iterrows():
            direction = "spike" if row["leads"] > mean else "drop"
            patterns.append(
                f"Anomaly detected on {row['date'].date()}: "
                f"leads {direction} to {int(row['leads'])} (avg: {mean:.0f})."
            )

    patterns.append(f"Best performing day of week: {best_day} (avg {dow_avg[best_day]:.0f} leads) — schedule key launches here.")
    return patterns


# ── 9. Recommended Actions ────────────────────────────────────────────────────
def recommended_actions(camp_scored: pd.DataFrame, waste: dict) -> list[str]:
    if camp_scored.empty:
        return ["No campaign data available for recommendations."]
    actions = []
    best = camp_scored.loc[camp_scored["score"].idxmax()]
    worst = camp_scored.loc[camp_scored["score"].idxmin()]

    actions.append(f"🚀 SCALE: Increase budget on '{best['campaign']}' by 20–30% — highest performance score ({best['score']}).")
    if len(camp_scored) > 1:
        actions.append(f"⚠️ REVIEW: '{worst['campaign']}' has the lowest score ({worst['score']}) — audit creatives and targeting.")

    if waste.get("total_wasted", 0) > 0:
        actions.append(
            f"💸 REALLOCATE: ₹{waste['total_wasted']:,.2f} in inefficient spend detected. "
            f"Shift budget from '{waste['worst_campaign']}' → '{best['campaign']}'."
        )

    valid_cpl = camp_scored[camp_scored["cpl"].notna()]
    if not valid_cpl.empty:
        avg_cpl = valid_cpl["cpl"].mean()
        high_cpl = valid_cpl[valid_cpl["cpl"] > avg_cpl * 1.25]
        for _, row in high_cpl.iterrows():
            actions.append(f"✂️ OPTIMISE: '{row['campaign']}' CPL ₹{row['cpl']:.2f} is 25%+ above average — reduce bids or tighten audience.")

    return actions


# ── 10. Full Intelligence Report ──────────────────────────────────────────────
def run_intelligence(camp: pd.DataFrame, daily: pd.DataFrame, total_budget: float = None) -> dict:
    if camp.empty:
        raise ValueError("Cannot run intelligence on empty campaign data")
    if total_budget is None or total_budget <= 0:
        total_budget = float(camp["spend"].sum()) or 1.0

    scored = performance_scores(camp)
    alloc = optimal_budget_allocation(scored, total_budget)
    waste = wasted_spend(camp)
    patterns = detect_patterns(daily)
    actions = recommended_actions(scored, waste)

    leads_pred = predict_leads(daily, days_ahead=7)
    avg_cpl = camp["cpl"].dropna().mean() if not camp["cpl"].dropna().empty else 0.0
    avg_ctr = camp["ctr"].dropna().mean() if not camp["ctr"].dropna().empty else 0.0
    cpl_pred = predict_cpl(avg_cpl, budget_delta=0)
    ctr_pred = predict_ctr(avg_ctr, days=7)

    sims = []
    for _, row in camp.iterrows():
        for delta in [0.20, -0.30]:
            sims.append(simulate_budget_change(camp, row["campaign"], delta))
    pause_sims = [simulate_budget_change(camp, row["campaign"], -1.0) for _, row in camp.iterrows()]

    return {
        "scored": scored,
        "allocation": alloc,
        "waste": waste,
        "patterns": patterns,
        "actions": actions,
        "leads_prediction": leads_pred,
        "cpl_prediction": cpl_pred,
        "ctr_prediction": ctr_pred,
        "simulations": sims,
        "pause_simulations": pause_sims,
    }
