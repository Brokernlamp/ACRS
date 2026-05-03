import pandas as pd


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.copy()
        df["ctr"] = (df["clicks"] / df["impressions"].replace(0, float("nan"))) * 100
        df["conversion_rate"] = (df["leads"] / df["clicks"].replace(0, float("nan"))) * 100
        df["cpl"] = df["spend"] / df["leads"].replace(0, float("nan"))
        return df
    except Exception as e:
        raise ValueError(f"Error computing KPIs: {str(e)}")


def summary_kpis(df: pd.DataFrame) -> dict:
    try:
        if df.empty:
            return {
                "Total Spend": "₹0.00", "Total Leads": 0, "Total Clicks": 0,
                "Total Impressions": 0, "Blended CPL ($)": 0.0,
                "Weighted CTR (%)": 0.0, "Conversion Rate (%)": 0.0, "ROAS": 0.0,
            }
        total_spend = df["spend"].sum()
        total_leads = df["leads"].sum()
        total_clicks = df["clicks"].sum()
        total_impressions = df["impressions"].sum()
        total_revenue = df["revenue"].sum() if "revenue" in df.columns else 0.0
        return {
            "Total Spend": f"₹{total_spend:,.2f}",
            "Total Leads": int(total_leads),
            "Total Clicks": int(total_clicks),
            "Total Impressions": int(total_impressions),
            "Blended CPL ($)": round(total_spend / total_leads, 2) if total_leads else 0.0,
            "Weighted CTR (%)": round((total_clicks / total_impressions) * 100, 2) if total_impressions else 0.0,
            "Conversion Rate (%)": round((total_leads / total_clicks) * 100, 2) if total_clicks else 0.0,
            "ROAS": round(total_revenue / total_spend, 2) if total_spend and total_revenue else 0.0,
        }
    except Exception as e:
        raise ValueError(f"Error computing summary KPIs: {str(e)}")


def campaign_summary(df: pd.DataFrame) -> pd.DataFrame:
    try:
        if df.empty:
            return pd.DataFrame()
        grp = df.groupby("campaign").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            spend=("spend", "sum"),
            leads=("leads", "sum"),
        ).reset_index()
        grp["ctr"] = (grp["clicks"] / grp["impressions"].replace(0, float("nan"))) * 100
        grp["cpl"] = grp["spend"] / grp["leads"].replace(0, float("nan"))
        grp["conversion_rate"] = (grp["leads"] / grp["clicks"].replace(0, float("nan"))) * 100
        return grp.round(2)
    except Exception as e:
        raise ValueError(f"Error computing campaign summary: {str(e)}")


def daily_trends(df: pd.DataFrame) -> pd.DataFrame:
    try:
        if df.empty:
            return pd.DataFrame()
        return df.groupby("date").agg(leads=("leads", "sum"), spend=("spend", "sum")).reset_index()
    except Exception as e:
        raise ValueError(f"Error computing daily trends: {str(e)}")


def generate_insights(camp_df: pd.DataFrame, kpis: dict) -> list[str]:
    try:
        insights = []
        if camp_df.empty:
            return ["No campaign data available for insights."]
        
        valid_cpl = camp_df[camp_df["cpl"].notna() & (camp_df["cpl"] > 0)]
        if not valid_cpl.empty:
            best = valid_cpl.loc[valid_cpl["cpl"].idxmin()]
            insights.append(
                f"'{best['campaign']}' is the most efficient campaign with the lowest CPL of ₹{best['cpl']:.2f}."
            )
        
        valid_ctr = camp_df[camp_df["ctr"].notna()]
        if not valid_ctr.empty:
            worst_ctr = valid_ctr.loc[valid_ctr["ctr"].idxmin()]
            if worst_ctr["ctr"] < 1.0:
                insights.append(
                    f"'{worst_ctr['campaign']}' has a CTR of {worst_ctr['ctr']:.2f}% — below 1%, suggesting creative optimization is needed."
                )
        
        if not valid_cpl.empty:
            avg_cpl = valid_cpl["cpl"].mean()
            high_cpl = valid_cpl[valid_cpl["cpl"] > avg_cpl * 1.3]
            for _, row in high_cpl.iterrows():
                insights.append(
                    f"'{row['campaign']}' has a CPL of ₹{row['cpl']:.2f}, which is significantly above average — review targeting and budget allocation."
                )
        
        valid_leads = camp_df[camp_df["leads"] > 0]
        if not valid_leads.empty:
            top = valid_leads.loc[valid_leads["leads"].idxmax()]
            insights.append(f"'{top['campaign']}' generated the most leads ({int(top['leads'])}) — consider scaling this campaign.")
        
        return insights if insights else ["Insufficient data for insights."]
    except Exception as e:
        return [f"Error generating insights: {str(e)}"]
