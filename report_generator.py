import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
)


W, H = A4
BRAND = colors.HexColor("#4F46E5")
LIGHT = colors.HexColor("#F3F4F6")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Brand", fontSize=26, textColor=BRAND, spaceAfter=4, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Sub", fontSize=12, textColor=colors.grey, spaceAfter=2))
    s.add(ParagraphStyle("SectionHead", fontSize=13, textColor=BRAND, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Insight", fontSize=10, leftIndent=10, spaceAfter=4, bulletIndent=0))
    return s


def generate_pdf(
    client_name: str,
    date_range: str,
    kpis: dict,
    camp_df,
    insights: list[str],
    chart_pngs: list[bytes],
) -> bytes:
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        s = _styles()
        story = []

        story.append(Paragraph("Campaign Performance Report", s["Brand"]))
        story.append(Paragraph(f"Client: {client_name or 'N/A'}  |  Period: {date_range}", s["Sub"]))
        story.append(Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", s["Sub"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=12))

        story.append(Paragraph("KPI Summary", s["SectionHead"]))
        kpi_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in kpis.items()]
        t = Table(kpi_data, colWidths=[9*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph("Campaign Breakdown", s["SectionHead"]))
        cols = [c for c in ["campaign", "impressions", "clicks", "spend", "leads", "ctr", "cpl", "conversion_rate"] if c in camp_df.columns]
        headers_map = {"campaign": "Campaign", "impressions": "Impressions", "clicks": "Clicks",
                       "spend": "Spend ($)", "leads": "Leads", "ctr": "CTR (%)", "cpl": "CPL ($)", "conversion_rate": "Conv. Rate (%)"}
        headers = [headers_map.get(c, c) for c in cols]
        rows = [headers] + [[str(row[c]) for c in cols] for _, row in camp_df[cols].iterrows()]
        ct = Table(rows, repeatRows=1)
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(ct)

        chart_titles = ["Leads Over Time", "Spend vs Leads by Campaign", "CPL by Campaign"]
        for title, png in zip(chart_titles, chart_pngs):
            if png:
                story.append(Paragraph(title, s["SectionHead"]))
                story.append(Image(io.BytesIO(png), width=16*cm, height=7*cm))
                story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("AI-Generated Insights", s["SectionHead"]))
        for ins in (insights or ["No insights available."]):
            story.append(Paragraph(f"• {ins}", s["Insight"]))

        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f"Failed to generate PDF: {str(e)}")


def generate_growth_pdf(
    client_name: str,
    date_range: str,
    kpis: dict,
    camp_df,
    insights: list[str],
    chart_pngs: list[bytes],
    intelligence: dict,
    ai_chart_pngs: list[bytes],
) -> bytes:
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        s = _styles()
        story = []

        story.append(Paragraph("AI Growth Strategy Report", s["Brand"]))
        story.append(Paragraph(f"Client: {client_name or 'N/A'}  |  Period: {date_range}", s["Sub"]))
        story.append(Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", s["Sub"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=12))

        story.append(Paragraph("KPI Summary", s["SectionHead"]))
        kpi_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in kpis.items()]
        t = Table(kpi_data, colWidths=[9*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        scored = intelligence.get("scored", camp_df)
        if not scored.empty and "score" in scored.columns:
            story.append(Paragraph("AI Performance Scores", s["SectionHead"]))
            score_cols = [c for c in ["campaign", "score", "ctr", "cpl", "conversion_rate"] if c in scored.columns]
            score_data = [[c.replace("_", " ").title() for c in score_cols]]
            for _, row in scored.iterrows():
                score_data.append([str(row[c]) for c in score_cols])
            st = Table(score_data, repeatRows=1)
            st.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(st)
            story.append(Spacer(1, 0.3*cm))

        lp = intelligence.get("leads_prediction", {})
        cp = intelligence.get("cpl_prediction", {})
        ctr_p = intelligence.get("ctr_prediction", {})
        story.append(Paragraph("Predictions (Next 7 Days)", s["SectionHead"]))
        pred_data = [
            ["Metric", "Prediction"],
            ["Expected Leads", str(lp.get("predicted_leads", "N/A"))],
            ["Growth Rate", f"{lp.get('growth_rate_pct', 0)}%"],
            ["Trend", lp.get("trend", "N/A")],
            ["Expected CPL", f"${cp.get('predicted_cpl', 0)}"],
            ["CPL Direction", str(cp.get("direction", "N/A")).capitalize()],
            ["Expected CTR", f"{ctr_p.get('predicted_ctr', 0)}%"],
            ["CTR Drop", f"{ctr_p.get('drop_pct', 0)}%"],
            ["Creative Refresh Needed", "Yes" if ctr_p.get("refresh_needed") else "No"],
        ]
        pt = Table(pred_data, colWidths=[9*cm, 7*cm])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.3*cm))

        waste = intelligence.get("waste", {})
        story.append(Paragraph("Financial Impact", s["SectionHead"]))
        fin_data = [
            ["Item", "Amount"],
            ["Estimated Wasted Spend", f"${waste.get('total_wasted', 0):,.2f}"],
            ["Worst Offender", waste.get("worst_campaign", "N/A")],
            ["Recoverable Savings", f"${waste.get('savings_opportunity', 0):,.2f}"],
        ]
        ft = Table(fin_data, colWidths=[9*cm, 7*cm])
        ft.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ft)
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("Recommended Actions", s["SectionHead"]))
        for action in (intelligence.get("actions") or ["No actions available."]):
            story.append(Paragraph(f"• {action}", s["Insight"]))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("Detected Patterns", s["SectionHead"]))
        for p in (intelligence.get("patterns") or ["No patterns detected."]):
            story.append(Paragraph(f"• {p}", s["Insight"]))
        story.append(Spacer(1, 0.3*cm))

        alloc = intelligence.get("allocation")
        if alloc is not None and not alloc.empty:
            story.append(Paragraph("Optimal Budget Plan", s["SectionHead"]))
            alloc_data = [["Campaign", "Score", "Budget Share (%)", "Recommended Budget ($)"]]
            for _, row in alloc.iterrows():
                alloc_data.append([row["campaign"], str(row.get("score", "N/A")),
                                   f"{row.get('budget_share_pct', 0)}%", f"${row.get('recommended_budget', 0):,.2f}"])
            at = Table(alloc_data, repeatRows=1)
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(at)
        story.append(PageBreak())

        all_titles = ["Leads Over Time", "Spend vs Leads", "CPL by Campaign",
                      "AI Performance Scores", "Budget Allocation", "Leads Forecast"]
        all_pngs = list(chart_pngs or []) + list(ai_chart_pngs or [])
        for title, png in zip(all_titles, all_pngs):
            if png:
                story.append(Paragraph(title, s["SectionHead"]))
                story.append(Image(io.BytesIO(png), width=16*cm, height=7*cm))
                story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("Diagnostic Insights", s["SectionHead"]))
        for ins in (insights or ["No insights available."]):
            story.append(Paragraph(f"• {ins}", s["Insight"]))

        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f"Failed to generate growth PDF: {str(e)}")
