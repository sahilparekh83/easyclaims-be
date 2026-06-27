from io import BytesIO
from fpdf import FPDF


NAVY = (10, 34, 87)
WHITE = (255, 255, 255)
LIGHT_BLUE = (240, 244, 255)
DARK_GRAY = (80, 80, 100)
MID_GRAY = (100, 116, 139)


class _Card(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 6, "EasyClaims - Your Health Benefits, Simplified", align="C")


class PdfService:
    def generate_membership_card_pdf(
        self,
        member_name: str,
        member_email: str,
        partner_name: str,
        partner_type: str,
        plan_name: str,
        plan,
    ) -> bytes:
        pdf = _Card(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        W = pdf.w - 2 * pdf.l_margin  # usable width

        # ── Header banner ──────────────────────────────────────────────────────
        pdf.set_fill_color(*NAVY)
        pdf.rect(pdf.l_margin, 10, W, 18, "F")
        pdf.set_xy(pdf.l_margin + 4, 13)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*WHITE)
        pdf.cell(W - 8, 7, "EasyClaims", ln=0)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(147, 197, 253)
        pdf.set_xy(pdf.l_margin + 4, 20)
        pdf.cell(W - 8, 5, "Your Health Benefits, Simplified", ln=0)

        # Badge
        pdf.set_fill_color(30, 64, 175)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8)
        badge_w = 38
        pdf.set_xy(pdf.w - pdf.r_margin - badge_w, 15)
        pdf.cell(badge_w, 6, "MEMBERSHIP CARD", align="C", fill=True)

        # ── Section: Member & Partner ──────────────────────────────────────────
        y = 36
        pdf.set_xy(pdf.l_margin, y)
        self._section_title(pdf, W, "Member Details")
        y += 8
        rows = [
            ("Member Name", member_name or member_email),
            ("Email", member_email),
            ("Partner", f"{partner_name}  ({partner_type})"),
        ]
        y = self._info_table(pdf, y, W, rows)

        # ── Section: Plan ──────────────────────────────────────────────────────
        y += 4
        self._section_title(pdf, W, "Plan Details", y=y)
        y += 8
        rows = [("Plan Name", plan_name)]
        y = self._info_table(pdf, y, W, rows)

        # ── Section: Benefits ─────────────────────────────────────────────────
        y += 4
        self._section_title(pdf, W, "Plan Benefits", y=y)
        y += 8
        benefits = [
            ("Family Members Covered", str(getattr(plan, "benefit_family", 0))),
            ("Policy Upload Slots", str(getattr(plan, "benefit_slots", 0))),
            ("Claim Support", str(getattr(plan, "benefit_claim", ""))),
        ]
        if getattr(plan, "benefit_aiqa", False):
            benefits.append(("AI Health Query Assistant", "Included"))
        tc = getattr(plan, "benefit_teleconsult_sessions", 0)
        if tc:
            benefits.append(("Tele-consultation", f"{tc} sessions"))
        wc = getattr(plan, "benefit_wellness_sessions", 0)
        if wc:
            benefits.append(("Wellness Sessions", f"{wc} sessions"))
        if getattr(plan, "benefit_hospital_cash", False):
            benefits.append(("Hospital Cash Benefit", "Included"))
        if getattr(plan, "benefit_emergency_assist", False):
            benefits.append(("Emergency Assistance", "Included"))
        self._info_table(pdf, y, W, benefits)

        buf = BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _section_title(self, pdf: FPDF, W: float, title: str, y: float = None):
        if y is not None:
            pdf.set_xy(pdf.l_margin, y)
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(W, 6, f"  {title.upper()}", fill=True, ln=True)

    def _info_table(self, pdf: FPDF, y: float, W: float, rows: list) -> float:
        col_w = W * 0.42
        for i, (label, value) in enumerate(rows):
            bg = LIGHT_BLUE if i % 2 == 0 else WHITE
            pdf.set_xy(pdf.l_margin, y)
            pdf.set_fill_color(*bg)
            pdf.set_text_color(*DARK_GRAY)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(col_w, 7, f"  {label}", fill=True)
            pdf.set_text_color(10, 34, 87)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(W - col_w, 7, value, fill=True, ln=True)
            y += 7
        return y
