import io
import logging
from fpdf import FPDF
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from .candidates import candidates_db as SEEDED_CANDIDATES
from db.supabase_client import fetch_all_candidates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])

class CandidateReport(FPDF):
    def header(self):
        # Logo placeholder or Title
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(33, 37, 41) # Dark gray
        self.cell(0, 20, 'HireIQ ATS Report', border=False, align='L')
        
        # Date on the right
        self.set_font('helvetica', '', 10)
        self.set_text_color(108, 117, 125) # Muted gray
        self.cell(0, 20, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", border=False, align='R')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(108, 117, 125)
        self.cell(0, 10, f'Page {self.page_no()} | HireIQ Intelligence Systems', align='C')

@router.get("/candidates/pdf")
async def export_candidates_pdf():
    """
    Generate and return a professional PDF report of all candidates.
    """
    try:
        db_candidates = await fetch_all_candidates()
        db_ids = {c["id"] for c in db_candidates}
        all_candidates = db_candidates + [c for c in SEEDED_CANDIDATES if c["id"] not in db_ids]
    except Exception as e:
        logger.warning("Supabase fetch failed during PDF export: %s", e)
        all_candidates = SEEDED_CANDIDATES

    # Create PDF object
    pdf = CandidateReport()
    pdf.add_page()
    
    # Table Header
    pdf.set_fill_color(248, 249, 250)
    pdf.set_text_color(33, 37, 41)
    pdf.set_font('helvetica', 'B', 11)
    
    col_widths = [60, 60, 25, 45]
    headers = ["Name", "Role", "Score", "Category"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 12, header, border=1, align='C', fill=True)
    pdf.ln()

    # Table Rows
    pdf.set_font('helvetica', '', 10)
    for c in all_candidates:
        score = c.get("final_score") or c.get("score") or 0
        category = "Strong Match" if score >= 85 else "Match" if score >= 60 else "Weak"
        
        # Color based on category
        if category == "Strong Match":
            pdf.set_text_color(25, 135, 84) # Green
        elif category == "Match":
            pdf.set_text_color(13, 110, 253) # Blue
        else:
            pdf.set_text_color(220, 53, 69) # Red

        pdf.cell(col_widths[0], 10, str(c.get("name", "N/A")), border=1)
        pdf.cell(col_widths[1], 10, str(c.get("role", "N/A")), border=1)
        pdf.cell(col_widths[2], 10, str(score), border=1, align='C')
        pdf.cell(col_widths[3], 10, category, border=1, align='C')
        pdf.ln()

    # Output headers
    pdf_bytes = pdf.output()
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=HireIQ_Candidates_Report.pdf"}
    )


@router.get("/candidates/csv")
async def export_candidates_csv():
    # Keeping CSV for fallback if needed, but the primary is now PDF
    import csv
    import io
    # ... existing implementation ...

