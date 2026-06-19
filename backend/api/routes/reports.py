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

class SingleCandidateReport(FPDF):
    def header(self):
        self.set_fill_color(30, 41, 59)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, 10)
        self.cell(0, 10, 'HireIQ Candidate Dossier', border=False, align='L')
        
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(226, 232, 240)
        self.set_xy(15, 20)
        self.cell(0, 10, 'Automated Screening & Evaluation Summary', border=False, align='L')
        
        self.set_font('helvetica', '', 9)
        self.set_text_color(226, 232, 240)
        self.set_xy(15, 20)
        self.cell(180, 10, f"Generated: {datetime.now().strftime('%b %d, %Y')}", border=False, align='R')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()} | Confidential Candidate Assessment', align='C')

@router.get("/candidates/{candidate_id}/pdf")
async def export_candidate_pdf(candidate_id: str, tenant_id: str = Depends(require_tenant)):
    from db.supabase_client import fetch_candidate_by_id, _candidate_to_dict
    from fastapi import HTTPException
    import re
    
    candidate_raw = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate_raw:
        raise HTTPException(status_code=404, detail="Candidate not found.")
        
    c = _candidate_to_dict(candidate_raw)
    
    pdf = SingleCandidateReport()
    pdf.add_page()
    
    pdf.set_xy(10, 45)
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, c.get("name", "Unknown Candidate"))
    pdf.ln(10)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 6, f"Target Role: {c.get('role', 'N/A')}")
    pdf.ln(6)
    
    pdf.set_font('helvetica', '', 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, f"Email: {c.get('email', 'N/A')}   |   Phone: {c.get('phone', 'N/A')}   |   Location: {c.get('location', 'N/A')}")
    pdf.ln(5)
    
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y() + 3, 200, pdf.get_y() + 3)
    pdf.ln(8)
    
    score = c.get("score") or 0
    verdict = c.get("insights", {}).get("ai_summary", {}).get("verdict") or "Hire"
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 8, "Evaluation Score:")
    
    pdf.set_font('helvetica', 'B', 18)
    if score >= 85:
        pdf.set_text_color(16, 185, 129)
    elif score >= 60:
        pdf.set_text_color(59, 130, 246)
    else:
        pdf.set_text_color(239, 68, 68)
    pdf.cell(30, 8, f"{score}%")
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(30, 8, "Verdict:")
    
    pdf.set_font('helvetica', 'B', 12)
    if "No" in verdict:
        pdf.set_text_color(239, 68, 68)
    else:
        pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 8, verdict)
    pdf.ln(12)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Executive AI Summary")
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(51, 65, 85)
    summary_text = c.get("insights", {}).get("executive_summary") or c.get("summary") or "No summary available."
    pdf.multi_cell(0, 5, summary_text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 8, "Key Strengths")
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(51, 65, 85)
    strengths = c.get("insights", {}).get("strengths") or []
    if strengths:
        for str_item in strengths:
            pdf.multi_cell(0, 5, f"- {str_item}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "No specific strengths logged.")
        pdf.ln(5)
    pdf.ln(4)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(225, 29, 72)
    pdf.cell(0, 8, "Development Gaps & Concerns")
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(51, 65, 85)
    concerns = c.get("insights", {}).get("concerns") or c.get("insights", {}).get("weaknesses") or []
    if concerns:
        for con_item in concerns:
            pdf.multi_cell(0, 5, f"- {con_item}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "No major concerns identified.")
        pdf.ln(5)
    pdf.ln(4)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Core Technical Skills")
    pdf.ln(8)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(51, 65, 85)
    skills = c.get("skills") or []
    if skills:
        pdf.multi_cell(0, 5, ", ".join(skills), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "None specified.")
        pdf.ln(5)
    pdf.ln(4)
    
    focus_areas = c.get("insights", {}).get("ai_summary", {}).get("interview_focus") or []
    if focus_areas:
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Recommended Interview Focus Areas")
        pdf.ln(8)
        
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(51, 65, 85)
        for fa in focus_areas:
            pdf.multi_cell(0, 5, f"- {fa}", new_x="LMARGIN", new_y="NEXT")
            
    pdf_bytes = pdf.output()
    
    safe_name = "".join([char for char in c.get("name", "Candidate") if char.isalnum() or char in ["-", "_"]])
    filename = f"HireIQ_Report_{safe_name}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
