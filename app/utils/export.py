"""
Professional export utilities for dashboard data.

Supports PDF and Excel export formats with professional styling.
"""

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = structlog.get_logger()


class DashboardPDFExporter:
    """Export dashboard data to professional PDF format."""

    def __init__(self, dashboard_data: Dict[str, Any]):
        self.data = dashboard_data
        self.buffer = io.BytesIO()

    def generate(self) -> io.BytesIO:
        """Generate PDF and return as BytesIO buffer."""
        try:
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=landscape(A4),
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.5 * inch,
            )

            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#EDEDED"),
                spaceAfter=12,
                fontName="Helvetica-Bold",
            )

            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#888888"),
                spaceAfter=10,
                fontName="Helvetica-Bold",
            )

            # Title
            story.append(Paragraph("Dashboard Metrics Report", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Metadata
            overview = self.data.get("overview", {})
            created_at = self.data.get("created_at", "")
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    date_str = date_obj.strftime("%B %d, %Y")
                except Exception:
                    date_str = created_at

                story.append(Paragraph(f"<b>Generated:</b> {date_str}", styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

            if overview.get("domain"):
                story.append(Paragraph(f"<b>Domain:</b> {overview['domain']}", styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

            if overview.get("summary"):
                story.append(Paragraph(f"<b>Summary:</b> {overview['summary']}", styles["Normal"]))
                story.append(Spacer(1, 0.3 * inch))

            # KPIs Section
            kpis = self.data.get("kpis", [])
            if kpis:
                story.append(Paragraph("Key Performance Indicators", heading_style))
                story.append(Spacer(1, 0.1 * inch))

                kpi_table_data = [["Metric", "Value", "Priority", "Formula"]]
                for kpi in kpis:
                    value = kpi.get("value", "N/A")
                    unit = kpi.get("unit", "")
                    value_str = f"{value} {unit}".strip() if value != "N/A" else "N/A"

                    kpi_table_data.append([
                        kpi.get("label", "Unnamed"),
                        value_str,
                        kpi.get("priority", "low").upper(),
                        kpi.get("formula", "N/A"),
                    ])

                kpi_table = Table(kpi_table_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 3 * inch])
                kpi_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#111111")),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#EDEDED")),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 1), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                    ])
                )
                story.append(kpi_table)
                story.append(Spacer(1, 0.3 * inch))

            # Insights Section
            insights = self.data.get("insights", [])
            if insights:
                story.append(PageBreak())
                story.append(Paragraph("Key Insights", heading_style))
                story.append(Spacer(1, 0.1 * inch))

                for idx, insight in enumerate(insights, 1):
                    text = insight.get("text", "")
                    category = insight.get("category", "general")
                    story.append(Paragraph(f"<b>{idx}. [{category.upper()}]</b> {text}", styles["Normal"]))
                    story.append(Spacer(1, 0.15 * inch))

            # Charts Section
            charts = self.data.get("charts", [])
            if charts:
                story.append(PageBreak())
                story.append(Paragraph("Visualizations", heading_style))
                story.append(Spacer(1, 0.1 * inch))

                for chart in charts:
                    title = chart.get("title", "Unnamed Chart")
                    chart_type = chart.get("type", "unknown")
                    description = chart.get("description", "")

                    story.append(Paragraph(f"<b>{title}</b> ({chart_type.capitalize()})", styles["Normal"]))
                    if description:
                        story.append(Paragraph(description, styles["Normal"]))
                    story.append(Spacer(1, 0.2 * inch))

            # Build PDF
            doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

            self.buffer.seek(0)
            logger.info("pdf_export_generated", kpi_count=len(kpis), chart_count=len(charts))
            return self.buffer

        except Exception as e:
            logger.error("pdf_export_failed", error=str(e))
            raise

    def _add_footer(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate):
        """Add footer to each page."""
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#888888"))
        canvas_obj.drawString(
            0.5 * inch,
            0.3 * inch,
            f"ExcellentInsight | Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        )
        canvas_obj.drawRightString(
            doc.pagesize[0] - 0.5 * inch, 0.3 * inch, f"Page {doc.page}"
        )
        canvas_obj.restoreState()


class DashboardExcelExporter:
    """Export dashboard data to professional Excel format."""

    def __init__(self, dashboard_data: Dict[str, Any]):
        self.data = dashboard_data
        self.buffer = io.BytesIO()

    def generate(self) -> io.BytesIO:
        """Generate Excel and return as BytesIO buffer."""
        try:
            workbook = xlsxwriter.Workbook(self.buffer, {"in_memory": True})

            # Define formats
            header_format = workbook.add_format({
                "bold": True,
                "bg_color": "#333333",
                "font_color": "#EDEDED",
                "border": 1,
                "align": "left",
                "valign": "vcenter",
            })

            cell_format = workbook.add_format({
                "border": 1,
                "align": "left",
                "valign": "vcenter",
            })

            title_format = workbook.add_format({
                "bold": True,
                "font_size": 16,
                "font_color": "#000000",
            })

            # Overview Sheet
            overview_sheet = workbook.add_worksheet("Overview")
            overview_sheet.set_column("A:A", 20)
            overview_sheet.set_column("B:B", 50)

            row = 0
            overview_sheet.write(row, 0, "Dashboard Overview", title_format)
            row += 2

            overview = self.data.get("overview", {})
            created_at = self.data.get("created_at", "")

            if created_at:
                overview_sheet.write(row, 0, "Generated", header_format)
                overview_sheet.write(row, 1, created_at, cell_format)
                row += 1

            if overview.get("domain"):
                overview_sheet.write(row, 0, "Domain", header_format)
                overview_sheet.write(row, 1, overview["domain"], cell_format)
                row += 1

            if overview.get("summary"):
                overview_sheet.write(row, 0, "Summary", header_format)
                overview_sheet.write(row, 1, overview["summary"], cell_format)
                row += 1

            if overview.get("sheet_count"):
                overview_sheet.write(row, 0, "Sheets Analyzed", header_format)
                overview_sheet.write(row, 1, overview["sheet_count"], cell_format)
                row += 1

            if overview.get("total_rows"):
                overview_sheet.write(row, 0, "Total Rows", header_format)
                overview_sheet.write(row, 1, overview["total_rows"], cell_format)
                row += 1

            # KPIs Sheet
            kpis = self.data.get("kpis", [])
            if kpis:
                kpi_sheet = workbook.add_worksheet("KPIs")
                kpi_sheet.set_column("A:A", 30)
                kpi_sheet.set_column("B:B", 20)
                kpi_sheet.set_column("C:C", 15)
                kpi_sheet.set_column("D:D", 40)
                kpi_sheet.set_column("E:E", 15)

                headers = ["Metric", "Value", "Priority", "Formula", "Coverage"]
                for col, header in enumerate(headers):
                    kpi_sheet.write(0, col, header, header_format)

                for row_idx, kpi in enumerate(kpis, start=1):
                    value = kpi.get("value", "N/A")
                    unit = kpi.get("unit", "")
                    value_str = f"{value} {unit}".strip() if value != "N/A" else "N/A"

                    kpi_sheet.write(row_idx, 0, kpi.get("label", "Unnamed"), cell_format)
                    kpi_sheet.write(row_idx, 1, value_str, cell_format)
                    kpi_sheet.write(row_idx, 2, kpi.get("priority", "low").upper(), cell_format)
                    kpi_sheet.write(row_idx, 3, kpi.get("formula", "N/A"), cell_format)

                    coverage = kpi.get("coverage")
                    if coverage is not None:
                        kpi_sheet.write(row_idx, 4, f"{int(coverage * 100)}%", cell_format)
                    else:
                        kpi_sheet.write(row_idx, 4, "N/A", cell_format)

            # Insights Sheet
            insights = self.data.get("insights", [])
            if insights:
                insights_sheet = workbook.add_worksheet("Insights")
                insights_sheet.set_column("A:A", 15)
                insights_sheet.set_column("B:B", 80)

                insights_sheet.write(0, 0, "Category", header_format)
                insights_sheet.write(0, 1, "Insight", header_format)

                for row_idx, insight in enumerate(insights, start=1):
                    insights_sheet.write(row_idx, 0, insight.get("category", "general").upper(), cell_format)
                    insights_sheet.write(row_idx, 1, insight.get("text", ""), cell_format)

            # Charts Summary Sheet
            charts = self.data.get("charts", [])
            if charts:
                charts_sheet = workbook.add_worksheet("Charts")
                charts_sheet.set_column("A:A", 30)
                charts_sheet.set_column("B:B", 15)
                charts_sheet.set_column("C:C", 50)

                charts_sheet.write(0, 0, "Chart Title", header_format)
                charts_sheet.write(0, 1, "Type", header_format)
                charts_sheet.write(0, 2, "Description", header_format)

                for row_idx, chart in enumerate(charts, start=1):
                    charts_sheet.write(row_idx, 0, chart.get("title", "Unnamed"), cell_format)
                    charts_sheet.write(row_idx, 1, chart.get("type", "unknown").upper(), cell_format)
                    charts_sheet.write(row_idx, 2, chart.get("description", ""), cell_format)

            workbook.close()
            self.buffer.seek(0)

            logger.info("excel_export_generated", kpi_count=len(kpis), insights_count=len(insights))
            return self.buffer

        except Exception as e:
            logger.error("excel_export_failed", error=str(e))
            raise


def export_dashboard_pdf(dashboard_data: Dict[str, Any]) -> io.BytesIO:
    """Export dashboard to PDF format."""
    exporter = DashboardPDFExporter(dashboard_data)
    return exporter.generate()


def export_dashboard_excel(dashboard_data: Dict[str, Any]) -> io.BytesIO:
    """Export dashboard to Excel format."""
    exporter = DashboardExcelExporter(dashboard_data)
    return exporter.generate()
