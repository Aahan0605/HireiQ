import io
import logging
import csv
from fpdf import FPDF
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.core.rbac import require_tenant
from db.supabase_client import fetch_all_candidates

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(require_tenant)]
)

class CandidateReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 24)
        self.set_text_color(33, 37, 41) # Dark gray
        self.cell(0, 20, 'HireIQ ATS Report', border=False, align='L')
        
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
async def export_candidates_pdf(tenant_id: str = Depends(require_tenant)):
    """
    Generate and return a professional PDF report of all candidates for the tenant.
    """
    try:
        all_candidates = await fetch_all_candidates(tenant_id)
    except Exception as e:
        logger.error("Supabase fetch failed during PDF export: %s", e)
        all_candidates = []

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
async def export_candidates_csv(tenant_id: str = Depends(require_tenant)):
    """
    Generate and stream a CSV report of all candidates for the tenant.
    """
    try:
        all_candidates = await fetch_all_candidates(tenant_id)
    except Exception as e:
        logger.error("Supabase fetch failed during CSV export: %s", e)
        all_candidates = []

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow(["Name", "Role", "Score", "Status", "Skills", "Location", "Experience (Years)"])
    
    for c in all_candidates:
        score = c.get("final_score") or c.get("score") or 0
        status = c.get("status", "Match")
        skills_str = ", ".join(c.get("skills", []))
        experience_years = len(c.get("experience", []))
        
        writer.writerow([
            c.get("name", "N/A"),
            c.get("role", "N/A"),
            score,
            status,
            skills_str,
            c.get("location", "Remote"),
            experience_years
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=HireIQ_Candidates_Report.csv"}
    )
