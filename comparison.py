"""
Historical comparison utilities
Calculate week-over-week, month-over-month changes
"""

from datetime import datetime, timedelta
import pandas as pd


def calculate_change_percentage(current, previous):
    """Calculate percentage change between two values"""
    try:
        current = float(current)
        previous = float(previous)
    except (TypeError, ValueError):
        return 0.0
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100


def get_trend_indicator(change_pct, reverse=False):
    """
    Get trend arrow and color based on change percentage
    reverse=True for metrics where lower is better (CPL, CPA)
    """
    if abs(change_pct) < 1:
        return "→", "#F59E0B"  # Stable (amber)
    
    if reverse:
        # For CPL, CPA - lower is better
        if change_pct < 0:
            return "↓", "#10B981"  # Down is good (green)
        else:
            return "↑", "#EF4444"  # Up is bad (red)
    else:
        # For Leads, CTR, Revenue - higher is better
        if change_pct > 0:
            return "↑", "#10B981"  # Up is good (green)
        else:
            return "↓", "#EF4444"  # Down is bad (red)


def calculate_period_comparison(current_df, previous_df):
    """
    Compare two dataframes (current period vs previous period)
    Returns dict with changes for all key metrics
    """
    if current_df is None or previous_df is None or current_df.empty or previous_df.empty:
        return None

    try:
        current_metrics = {
            'total_spend': float(current_df['spend'].sum()),
            'total_leads': float(current_df['leads'].sum()),
            'total_clicks': float(current_df['clicks'].sum()),
            'total_impressions': float(current_df['impressions'].sum()),
            'avg_cpl': float(current_df['spend'].sum()) / max(float(current_df['leads'].sum()), 1),
            'avg_ctr': (float(current_df['clicks'].sum()) / max(float(current_df['impressions'].sum()), 1)) * 100,
        }

        previous_metrics = {
            'total_spend': float(previous_df['spend'].sum()),
            'total_leads': float(previous_df['leads'].sum()),
            'total_clicks': float(previous_df['clicks'].sum()),
            'total_impressions': float(previous_df['impressions'].sum()),
            'avg_cpl': float(previous_df['spend'].sum()) / max(float(previous_df['leads'].sum()), 1),
            'avg_ctr': (float(previous_df['clicks'].sum()) / max(float(previous_df['impressions'].sum()), 1)) * 100,
        }

        comparison = {}
        for key in current_metrics:
            current = current_metrics[key]
            previous = previous_metrics[key]
            change_pct = calculate_change_percentage(current, previous)
            reverse = key in ['avg_cpl']
            arrow, color = get_trend_indicator(change_pct, reverse=reverse)
            comparison[key] = {
                'current': current, 'previous': previous,
                'change': current - previous, 'change_pct': change_pct,
                'arrow': arrow, 'color': color
            }
        return comparison
    except Exception:
        return None


def get_date_ranges(end_date=None, period='week'):
    """
    Get current and previous period date ranges
    period: 'week', 'month', or 'custom'
    """
    try:
        if end_date is None:
            end_date = datetime.now().date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        end_date = datetime.now().date()

    if period == 'month':
        current_start = end_date - timedelta(days=29)
        current_end = end_date
        previous_start = current_start - timedelta(days=30)
        previous_end = current_start - timedelta(days=1)
    else:  # default to week
        current_start = end_date - timedelta(days=6)
        current_end = end_date
        previous_start = current_start - timedelta(days=7)
        previous_end = current_start - timedelta(days=1)

    return {
        'current': (current_start, current_end),
        'previous': (previous_start, previous_end)
    }


def format_comparison_html(comparison, metric_name, display_name):
    """Generate HTML for comparison display"""
    if not comparison or metric_name not in comparison:
        return ""
    
    data = comparison[metric_name]
    current = data['current']
    change_pct = data['change_pct']
    arrow = data['arrow']
    color = data['color']
    
    # Format value based on metric type
    if 'cpl' in metric_name or 'spend' in metric_name:
        current_str = f"${current:,.2f}"
    elif 'ctr' in metric_name:
        current_str = f"{current:.2f}%"
    else:
        current_str = f"{int(current):,}"
    
    # Format change
    sign = "+" if change_pct > 0 else ""
    change_str = f"{sign}{change_pct:.1f}%"
    
    return f"""
    <div style="display:inline-block;margin-left:10px;font-size:0.85rem;">
        <span style="color:{color};font-weight:600;">{arrow} {change_str}</span>
        <span style="color:#6B7280;font-size:0.75rem;"> vs prev period</span>
    </div>
    """


def get_comparison_summary(comparison):
    """Generate text summary of comparison"""
    if not comparison:
        return "No comparison data available"
    
    summaries = []
    
    # Leads
    if 'total_leads' in comparison:
        data = comparison['total_leads']
        if abs(data['change_pct']) > 5:
            direction = "increased" if data['change_pct'] > 0 else "decreased"
            summaries.append(f"Leads {direction} by {abs(data['change_pct']):.1f}%")
    
    # CPL
    if 'avg_cpl' in comparison:
        data = comparison['avg_cpl']
        if abs(data['change_pct']) > 5:
            direction = "increased" if data['change_pct'] > 0 else "decreased"
            summaries.append(f"CPL {direction} by {abs(data['change_pct']):.1f}%")
    
    # CTR
    if 'avg_ctr' in comparison:
        data = comparison['avg_ctr']
        if abs(data['change_pct']) > 5:
            direction = "improved" if data['change_pct'] > 0 else "declined"
            summaries.append(f"CTR {direction} by {abs(data['change_pct']):.1f}%")
    
    if not summaries:
        return "Performance is stable compared to previous period"
    
    return " • ".join(summaries)
