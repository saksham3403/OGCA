"""Premium PDF report generator for OG CA."""
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, Flowable


class ColorBand(Flowable):
    """Simple decorative color band."""

    def __init__(self, width, height, fill_color):
        super().__init__()
        self.width = width
        self.height = height
        self.fill_color = fill_color

    def draw(self):
        self.canv.setFillColor(self.fill_color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class AccountingReportGenerator:
    """Generate premium accounting reports."""

    DEFAULT_SIGNATURE = "SAKSHAM SINGH"

    def __init__(self, filename="report.pdf"):
        self.filename = filename
        self.page_width, self.page_height = A4
        self._setup_palette()
        self._setup_styles()

    def _setup_palette(self):
        self.primary = colors.HexColor("#0f172a")
        self.secondary = colors.HexColor("#1d4ed8")
        self.accent = colors.HexColor("#0f766e")
        self.success = colors.HexColor("#15803d")
        self.warning = colors.HexColor("#b45309")
        self.danger = colors.HexColor("#b91c1c")
        self.surface = colors.HexColor("#ffffff")
        self.surface_alt = colors.HexColor("#f8fafc")
        self.border = colors.HexColor("#cbd5e1")
        self.text = colors.HexColor("#111827")
        self.muted = colors.HexColor("#64748b")

    def _setup_styles(self):
        styles = getSampleStyleSheet()
        self.styles = styles

        styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=23,
                leading=27,
                alignment=TA_CENTER,
                textColor=self.primary,
                spaceAfter=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="SubTitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                alignment=TA_CENTER,
                textColor=self.muted,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Section",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=16,
                textColor=self.primary,
                spaceBefore=14,
                spaceAfter=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Body",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=self.text,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Muted",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=11,
                textColor=self.muted,
                alignment=TA_CENTER,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Signature",
                parent=styles["Normal"],
                fontName="Helvetica-BoldOblique",
                fontSize=12,
                textColor=self.primary,
                alignment=TA_LEFT,
            )
        )

    @staticmethod
    def _fmt_currency(value):
        return f"Rs. {float(value or 0):,.2f}"

    @staticmethod
    def _category_breakdown(expenses):
        grouped = {}
        for exp in expenses or []:
            cat = exp.get("category") or "Uncategorized"
            grouped.setdefault(cat, {"category": cat, "total": 0.0, "count": 0})
            grouped[cat]["total"] += float(exp.get("amount", 0) or 0)
            grouped[cat]["count"] += 1
        return sorted(grouped.values(), key=lambda x: x["total"], reverse=True)

    def _doc(self, title):
        return SimpleDocTemplate(
            self.filename,
            pagesize=A4,
            leftMargin=0.55 * inch,
            rightMargin=0.55 * inch,
            topMargin=0.55 * inch,
            bottomMargin=0.55 * inch,
            title=title,
        )

    def _page_decor(self, can, doc):
        can.saveState()
        can.setFillColor(self.secondary)
        can.rect(0.4 * inch, self.page_height - 0.35 * inch, self.page_width - 0.8 * inch, 0.04 * inch, fill=1, stroke=0)
        can.setFillColor(self.surface_alt)
        can.rect(0.4 * inch, 0.35 * inch, self.page_width - 0.8 * inch, 0.22 * inch, fill=1, stroke=0)
        can.setFont("Helvetica", 8)
        can.setFillColor(self.muted)
        can.drawString(0.55 * inch, 0.44 * inch, f"OG CA Premium Report | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        can.drawRightString(self.page_width - 0.55 * inch, 0.44 * inch, f"Page {doc.page}")
        can.restoreState()

    def _header(self, user_data, report_name, subtitle):
        full_name = user_data.get("full_name") or user_data.get("username") or "OG CA"
        contact_parts = []
        if user_data.get("email"):
            contact_parts.append(user_data["email"])
        if user_data.get("phone"):
            contact_parts.append(user_data["phone"])
        city = user_data.get("city")
        state = user_data.get("state")
        if city and state:
            contact_parts.append(f"{city}, {state}")
        elif city:
            contact_parts.append(city)

        contact_line = " | ".join(contact_parts) if contact_parts else "Confidential Internal Financial Statement"

        return [
            ColorBand(7.2 * inch, 6, self.primary),
            Spacer(1, 0.05 * inch),
            ColorBand(7.2 * inch, 2.5, self.secondary),
            Spacer(1, 0.08 * inch),
            Paragraph(full_name.upper(), self.styles["ReportTitle"]),
            Paragraph(report_name, self.styles["SubTitle"]),
            Paragraph(subtitle, self.styles["SubTitle"]),
            Paragraph(contact_line, self.styles["SubTitle"]),
            Spacer(1, 0.08 * inch),
        ]

    def _kpi_cards(self, pairs):
        data = []
        row = []
        for idx, (label, value, tone) in enumerate(pairs):
            row.extend([label, value])
            if idx % 2 == 1:
                data.append(row)
                row = []
        if row:
            while len(row) < 4:
                row.extend(["", ""])
            data.append(row)

        t = Table(data, colWidths=[1.65 * inch, 1.9 * inch, 1.65 * inch, 1.9 * inch])
        style = [
            ("BACKGROUND", (0, 0), (-1, -1), self.surface),
            ("GRID", (0, 0), (-1, -1), 0.6, self.border),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), self.text),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [self.surface, self.surface_alt]),
        ]
        for r, pair_row in enumerate(data):
            for c in (0, 2):
                label = pair_row[c]
                tone = next((p[2] for p in pairs if p[0] == label), "primary")
                col = self.primary
                if tone == "success":
                    col = self.success
                elif tone == "warning":
                    col = self.warning
                elif tone == "danger":
                    col = self.danger
                style.append(("TEXTCOLOR", (c, r), (c, r), col))
                style.append(("FONTNAME", (c, r), (c, r), "Helvetica-Bold"))
                style.append(("FONTNAME", (c + 1, r), (c + 1, r), "Helvetica-Bold"))
        t.setStyle(TableStyle(style))
        return [t]

    def _expense_table(self, expenses):
        if not expenses:
            return [Paragraph("No expenses in the selected period.", self.styles["Body"])]

        data = [["Date", "Category", "Description", "Method", "Amount", "Notes"]]
        for row in expenses[:120]:
            data.append([
                str(row.get("date", "")),
                str(row.get("category", ""))[:22],
                str(row.get("description", ""))[:30],
                str(row.get("payment_method", ""))[:15],
                self._fmt_currency(row.get("amount", 0)),
                str(row.get("notes", ""))[:24],
            ])

        t = Table(data, colWidths=[0.8 * inch, 1.2 * inch, 1.65 * inch, 0.9 * inch, 1.0 * inch, 1.45 * inch], repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [self.surface, self.surface_alt]),
                    ("GRID", (0, 0), (-1, -1), 0.45, self.border),
                    ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [t]

    def _category_table(self, category_rows):
        if not category_rows:
            return [Paragraph("No category analytics available.", self.styles["Body"])]

        total = sum(float(r["total"]) for r in category_rows)
        data = [["Rank", "Category", "Transactions", "Amount", "Share %"]]
        for i, row in enumerate(category_rows[:20], start=1):
            pct = (float(row["total"]) / total * 100) if total else 0
            data.append([str(i), row["category"], str(row["count"]), self._fmt_currency(row["total"]), f"{pct:.1f}%"])
        data.append(["", "TOTAL", str(sum(r["count"] for r in category_rows)), self._fmt_currency(total), "100.0%"])

        t = Table(data, colWidths=[0.6 * inch, 2.7 * inch, 1.2 * inch, 1.6 * inch, 1.0 * inch], repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.secondary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [self.surface, self.surface_alt]),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), self.primary),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.45, self.border),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [t]

    def _signature_block(self, user_data):
        signer = self.DEFAULT_SIGNATURE
        approver = user_data.get("full_name") or user_data.get("username") or "Authorized User"
        now = datetime.now().strftime("%d %B %Y")

        rows = [
            ["Prepared By", "Approved By", "Signature"],
            [signer, approver, signer],
            ["Date", now, "Digitally Signed"],
        ]
        t = Table(rows, colWidths=[2.2 * inch, 2.3 * inch, 2.2 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (2, 1), (2, 1), self.secondary),
                    ("BACKGROUND", (0, 1), (-1, -1), self.surface),
                    ("GRID", (0, 0), (-1, -1), 0.6, self.border),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [
            Paragraph("Certification & Signature", self.styles["Section"]),
            Paragraph("This report is system-generated and validated for internal accounting use.", self.styles["Body"]),
            Spacer(1, 0.08 * inch),
            t,
            Spacer(1, 0.08 * inch),
            Paragraph("Signature: SAKSHAM SINGH", self.styles["Signature"]),
        ]

    def generate_expense_report(self, user_data, expenses, summary, start_date, end_date):
        doc = self._doc("Expense Report")
        elements = []

        elements.extend(
            self._header(
                user_data,
                "Extreme Premium Expense Intelligence Report",
                f"Reporting Window: {start_date} to {end_date}",
            )
        )

        elements.append(Paragraph("Executive Snapshot", self.styles["Section"]))
        total_expenses = float(summary.get("total_expenses", 0) or 0)
        total_income = float(summary.get("total_income", 0) or 0)
        balance = float(summary.get("balance", 0) or 0)
        txn_count = len(expenses or [])
        avg_txn = (total_expenses / txn_count) if txn_count else 0
        ratio = (total_expenses / total_income * 100) if total_income > 0 else 0

        elements.extend(
            self._kpi_cards(
                [
                    ("Total Income", self._fmt_currency(total_income), "success"),
                    ("Total Expense", self._fmt_currency(total_expenses), "danger"),
                    ("Net Balance", self._fmt_currency(balance), "primary"),
                    ("Expense Ratio", f"{ratio:.1f}%", "warning"),
                    ("Transactions", str(txn_count), "primary"),
                    ("Avg Transaction", self._fmt_currency(avg_txn), "primary"),
                ]
            )
        )

        cat_rows = self._category_breakdown(expenses)
        if cat_rows:
            top_cat = cat_rows[0]
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(
                Paragraph(
                    f"Top Spend Driver: <b>{top_cat['category']}</b> at <b>{self._fmt_currency(top_cat['total'])}</b>. "
                    f"Maintain control on this segment for stronger monthly surplus.",
                    self.styles["Body"],
                )
            )

        elements.append(Spacer(1, 0.12 * inch))
        elements.append(Paragraph("Detailed Transactions", self.styles["Section"]))
        elements.extend(self._expense_table(expenses))

        elements.append(Spacer(1, 0.12 * inch))
        elements.append(Paragraph("Category Intelligence", self.styles["Section"]))
        elements.extend(self._category_table(cat_rows))

        elements.append(PageBreak())
        elements.append(Paragraph("Audit & Authorization", self.styles["Section"]))
        elements.extend(self._signature_block(user_data))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Footer Signature: SAKSHAM SINGH", self.styles["Muted"]))

        doc.build(elements, onFirstPage=self._page_decor, onLaterPages=self._page_decor)

    def generate_balance_sheet(self, user_data, income_data, expense_data, summary):
        doc = self._doc("Balance Sheet")
        elements = []

        elements.extend(
            self._header(
                user_data,
                "Extreme Premium Financial Statement & Balance Sheet",
                f"Statement Date: {datetime.now().strftime('%d %B %Y')}",
            )
        )

        total_income = float(summary.get("total_income", 0) or 0)
        total_expenses = float(summary.get("total_expenses", 0) or 0)
        balance = float(summary.get("balance", 0) or 0)
        margin = ((balance / total_income) * 100) if total_income > 0 else 0

        elements.append(Paragraph("Balance Summary", self.styles["Section"]))
        elements.extend(
            self._kpi_cards(
                [
                    ("Gross Income", self._fmt_currency(total_income), "success"),
                    ("Gross Expenses", self._fmt_currency(total_expenses), "danger"),
                    ("Net Balance", self._fmt_currency(balance), "primary"),
                    ("Net Margin", f"{margin:.1f}%", "warning"),
                ]
            )
        )

        statement_data = [
            ["Line Item", "Amount"],
            ["Revenue / Income", self._fmt_currency(total_income)],
            ["Less: Expenses", self._fmt_currency(total_expenses)],
            ["Net Profit / (Loss)", self._fmt_currency(balance)],
        ]
        st = Table(statement_data, colWidths=[4.6 * inch, 2.2 * inch])
        st.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#dcfce7")),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fee2e2")),
                    ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#dbeafe")),
                    ("TEXTCOLOR", (0, 3), (-1, 3), self.primary),
                    ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.6, self.border),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(st)

        elements.append(Spacer(1, 0.12 * inch))
        cat_rows = self._category_breakdown(expense_data)
        elements.append(Paragraph("Expense Category Mix", self.styles["Section"]))
        elements.extend(self._category_table(cat_rows))

        elements.append(Spacer(1, 0.12 * inch))
        elements.extend(self._signature_block(user_data))
        elements.append(Paragraph("Footer Signature: SAKSHAM SINGH", self.styles["Muted"]))

        doc.build(elements, onFirstPage=self._page_decor, onLaterPages=self._page_decor)
