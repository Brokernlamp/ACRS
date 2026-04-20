import google.generativeai as genai
from config import config
from typing import Optional

# Configure Gemini
try:
    if config.GEMINI_API_KEY:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
    else:
        model = None
except Exception:
    model = None


def generate_executive_summary(kpis: dict, predictions: dict, actions: list) -> str:
    """Generate executive summary using Gemini"""
    if not model:
        return _fallback_executive_summary(kpis, predictions, actions)
    if not kpis or not isinstance(kpis, dict):
        return _fallback_executive_summary({}, predictions or {}, actions or [])

    prompt = f"""
You are a senior marketing strategist. Write a concise 3-sentence executive summary for a client report.

Current Performance:
- Total Spend: {kpis.get('Total Spend', 'N/A')}
- Total Leads: {kpis.get('Total Leads', 'N/A')}
- Avg CPL: {kpis.get('Avg CPL ($)', 'N/A')}
- Avg CTR: {kpis.get('Avg CTR (%)', 'N/A')}%

Predictions (Next 7 Days):
- Expected Leads: {predictions.get('predicted_leads', 'N/A')}
- Trend: {predictions.get('trend', 'N/A')}
- Growth Rate: {predictions.get('growth_rate_pct', 'N/A')}%

Top Recommendation: {actions[0] if actions else 'Continue monitoring'}

Write a professional, data-driven summary that a CMO would appreciate. Focus on outcomes and next steps.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else _fallback_executive_summary(kpis, predictions, actions)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_executive_summary(kpis, predictions, actions)


def generate_insight_narrative(insight: str, context: dict = None) -> str:
    """Enhance a technical insight with client-friendly explanation"""
    if not model or not insight:
        return insight or ""

    prompt = f"""
You are a marketing consultant explaining data to a client. 
Rewrite this technical insight in a clear, actionable way:

"{insight}"

Make it:
1. Client-friendly (no jargon)
2. Actionable (what should they do?)
3. Concise (1-2 sentences max)

Return only the rewritten insight, nothing else.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else insight
    except Exception:
        return insight


def generate_recommendation_explanation(recommendation: str, data: dict) -> str:
    """Explain WHY a recommendation was made"""
    if not model or not recommendation:
        return recommendation or ""

    prompt = f"""
You are a marketing strategist. Explain WHY this recommendation makes sense:

Recommendation: {recommendation}

Supporting Data:
{data}

Write a 2-sentence explanation that justifies this recommendation with data.
Be specific and persuasive.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else recommendation
    except Exception:
        return recommendation


def _fallback_executive_summary(kpis: dict, predictions: dict, actions: list) -> str:
    """Fallback summary when Gemini API is not available"""
    trend = predictions.get('trend', '➡️ Stable')
    growth = predictions.get('growth_rate_pct', 0)
    
    if growth > 5:
        outlook = "showing strong momentum"
    elif growth < -5:
        outlook = "facing headwinds"
    else:
        outlook = "maintaining steady performance"
    
    return (
        f"Campaign performance is {outlook} with {kpis.get('Total Leads', 'N/A')} leads generated "
        f"at an average CPL of {kpis.get('Avg CPL ($)', 'N/A')}. "
        f"Forecasts indicate {trend.lower()} trajectory for the next 7 days. "
        f"Primary recommendation: {actions[0] if actions else 'Continue current strategy and monitor closely.'}"
    )


def enhance_insights_with_ai(insights: list, kpis: dict = None) -> list:
    """Enhance all insights with AI narratives (batch processing)"""
    if not model or not insights:
        return insights
    
    # For now, return original insights
    # In production, you'd batch process these through Gemini
    return insights
