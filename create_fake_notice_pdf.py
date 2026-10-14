"""
Generates a realistic "fishy" / scam recruitment circular PDF
to test FormFix AI's ML Authenticity & Urgency models.
"""

import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_fake_job_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=1, # Center
        textColor=colors.HexColor('#991B1B')
    )

    sub_header_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1, # Center
        textColor=colors.HexColor('#1E293B')
    )

    memo_style = ParagraphStyle(
        'MemoStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#1F2937')
    )

    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    urgent_box_style = ParagraphStyle(
        'UrgentBoxStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#991B1B')
    )

    elements = []

    # Fake Bureaucratic Header
    elements.append(Paragraph("CENTRAL PUBLIC EMPLOYMENT & RECRUITMENT CELL", header_style))
    elements.append(Paragraph("DIRECT FAST-TRACK VACANCY MISSION 2026-2027", sub_header_style))
    elements.append(Paragraph("MINISTRY OF CITIZEN OPPORTUNITY & SOCIAL WELFARE", sub_header_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#991B1B'), spaceBefore=2, spaceAfter=8))

    # Memo Reference and Date
    memo_table_data = [
        [
            Paragraph("<b>Memo Ref No:</b> CPRA/DIRECT-SEL/2026/8842-X", memo_style),
            Paragraph("<b>Dated:</b> Immediate Release (October 2026)", ParagraphStyle('RAlign', parent=memo_style, alignment=2))
        ]
    ]
    t_memo = Table(memo_table_data, colWidths=[280, 240])
    t_memo.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_memo)
    elements.append(Spacer(1, 10))

    # Urgent Callout Box
    alert_data = [[
        Paragraph("⚠️ URGENT PUBLIC NOTICE: FAST-TRACK SELECTION FOR 12,450 VACANCIES — NO WRITTEN EXAM! APPLY BEFORE TOMORROW MIDNIGHT!", urgent_box_style)
    ]]
    alert_table = Table(alert_data, colWidths=[520])
    alert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEE2E2')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#DC2626')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(alert_table)
    elements.append(Spacer(1, 12))

    # Section 1: Overview & Suspicious Direct Selection
    elements.append(Paragraph("<b>1. VACANCY DETAILS & EXAM EXEMPTION</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Applications are invited from eligible male and female candidates nationwide for 12,450 posts "
        "of Junior Data Entry Specialist, Field Administrative Executive, and Postal Logistics Associate. "
        "<b>In order to ensure immediate fast-track hiring, the conventional written examination and physical test "
        "have been 100% waived.</b> Direct final allotment letters will be issued based solely on high school aggregate "
        "and a 10-minute online screening conducted over WhatsApp video call.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Section 2: Salary & Perks
    elements.append(Paragraph("<b>2. SALARY AND ALLOWANCES</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Fixed monthly remuneration of <b>₹42,500/- per month</b> plus government accommodation allowance. "
        "Positions are permanent with immediate joining letters dispatched within 48 hours of verification.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Section 3: Red Flag Payment & UPI solicitation
    elements.append(Paragraph("<b>3. REGISTRATION CHARGE & CLEARANCE FEE (MANDATORY)</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Every applicant must submit a non-refundable application clearance and processing charge of <b>₹799/-</b>. "
        "Due to temporary scheduled maintenance on the central payment gateway, all candidates must transfer the "
        "processing fee directly via <b>Google Pay / PhonePe UPI</b> to the designated verification ID: "
        "<b>central-recruitment@upi</b>. Applications submitted without proof of ₹799 UPI transaction will be "
        "summarily rejected without any further notice.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Section 4: Tight Deadline & Penalty
    elements.append(Paragraph("<b>4. CRITICAL DEADLINE & STRICT FORFEITURE</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<b>Application Deadline: 2 days remaining (Tomorrow, 11:59 PM IST).</b> "
        "Any application received past this cutoff will be rejected and the candidate will be permanently "
        "debarred from government recruitment drives for 3 consecutive years. Late registration penalty of ₹1,500 applies.",
        body_style
    ))
    elements.append(Spacer(1, 10))

    # Section 5: Document Requirement (Sensitive data harvest)
    elements.append(Paragraph("<b>5. MANDATORY DOCUMENTS TO ATTACH</b>", bold_body))
    elements.append(Spacer(1, 4))
    doc_items = [
        "1. High School (10th/12th) Marksheet copy",
        "2. Clear scanned photo of Aadhaar Card (Front and Back)",
        "3. Bank Passbook and Debit Card front copy for salary DBT direct transfer setup",
        "4. Screenshot / Transaction receipt of ₹799 UPI fee transfer",
        "5. Signed physical declaration form sent via speed post within 3 days"
    ]
    for d in doc_items:
        elements.append(Paragraph(f"• {d}", body_style))
        elements.append(Spacer(1, 2))
    elements.append(Spacer(1, 8))

    # Section 6: Social Media Redirection
    elements.append(Paragraph("<b>6. HOW TO CONFIRM YOUR SELECTION</b>", bold_body))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Immediately after completing the UPI fee transfer, send the payment screenshot along with your documents "
        "to our official Chief Coordinator on <b>WhatsApp at +91 98765-43210</b>. Candidates must also join "
        "our official Telegram channel <b>t.me/central_recruitment_2026_officials</b> to view the instant merit list.",
        body_style
    ))
    elements.append(Spacer(1, 18))

    # Signature Block
    sig_data = [
        [
            Paragraph("Official Seal / Stamp:<br/><i>[RECRUITMENT DIRECTORATE SEAL]</i>", memo_style),
            Paragraph("<b>By Order of the Central Selection Board</b><br/>Dr. S. K. Sharma<br/>Joint Director (Direct Allotment Cell)", ParagraphStyle('Sig', parent=memo_style, alignment=2))
        ]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    elements.append(t_sig)

    doc.build(elements)
    print(f"PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    local_path = os.path.abspath("Fake_Govt_Job_Recruitment_Notice.pdf")
    generate_fake_job_pdf(local_path)

    # Also copy to Downloads folder if accessible
    downloads_path = os.path.expanduser(r"~\Downloads\Fake_Govt_Job_Recruitment_Notice.pdf")
    try:
        shutil.copy(local_path, downloads_path)
        print(f"Copied to user's Downloads: {downloads_path}")
    except Exception as e:
        print(f"Could not copy to Downloads: {e}")
