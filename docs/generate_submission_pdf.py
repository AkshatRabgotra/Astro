import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

def build_pdf():
    pdf_path = "docs/MELOOHA_FINAL_SUBMISSION.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E1B4B"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#312E81"),
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#4338CA"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1F2937"),
        leftIndent=14,
        spaceAfter=3,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    table_cell_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # Title Banner
    story.append(Paragraph("Melooha Engineering Challenge — Final Submission Report", title_style))
    story.append(Paragraph("Theme: <i>'Help more people discover Melooha, trust it, and come back to it.'</i>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=10))

    # Overview Table
    overview_data = [
        [Paragraph("Item", table_cell_header), Paragraph("Details & Live Production URLs", table_cell_header)],
        [Paragraph("Live Web App", table_cell_bold), Paragraph("<b>https://astro-psi-olive.vercel.app</b> (Mobile-First SPA on Vercel)", table_cell)],
        [Paragraph("Live Backend API", table_cell_bold), Paragraph("<b>https://astro-5qqa.onrender.com</b> (FastAPI Docker on Render)", table_cell)],
        [Paragraph("GitHub Repository", table_cell_bold), Paragraph("<b>https://github.com/AkshatRabgotra/Astro</b> (Public, CI passing)", table_cell)],
        [Paragraph("Primary Metric", table_cell_bold), Paragraph("<b>Day-7 (D7) Retention & Weekly Active Return Rate (WARR)</b>", table_cell)],
        [Paragraph("Core Retention Engine", table_cell_bold), Paragraph("<b>Personalized Muhurta Advisor (Google Calendar Sync) + Daily Habit Streak Economy</b>", table_cell)],
    ]
    t_overview = Table(overview_data, colWidths=[120, 410])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#312E81")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(t_overview)
    story.append(Spacer(1, 10))

    # Section 1
    story.append(Paragraph("1. Exploration & Opportunity Analysis", h1_style))
    story.append(Paragraph(
        "<b>The First-Time User Experience in Melooha:</b> Exploring the app reveals an enchanting cosmic onboarding, but also reveals the primary drop-off: <i>Birth Time Anxiety</i> and the <i>Post-Question Churn Cliff</i>. Once a user's single free question is spent, a standard payment paywall appears. For a curious user, a one-off birth chart reading feels like 'Static Fate'—there is no organic trigger to reopen the app tomorrow.",
        body_style
    ))
    story.append(Paragraph("<b>Competitor Teardown & Market Gaps:</b>", h2_style))

    comp_data = [
        [Paragraph("App", table_cell_header), Paragraph("Observed Model & Strengths", table_cell_header), Paragraph("Critical Flaws / Why Users Churn", table_cell_header), Paragraph("Melooha AI Advantage", table_cell_header)],
        [
            Paragraph("<b>AstroTalk</b>", table_cell_bold),
            Paragraph("Human astrologer marketplace; large call volume.", table_cell),
            Paragraph("<b>Predatory monetization</b>: ₹30-100/min anxiety billing, aggressive gemstone/pooja upselling.", table_cell),
            Paragraph("<b>Calm, private AI</b>: Zero fear-mongering, instant responses, complete privacy.", table_cell),
        ],
        [
            Paragraph("<b>AstroSage</b>", table_cell_bold),
            Paragraph("Comprehensive Vedic mathematical tables.", table_cell),
            Paragraph("<b>1990s cluttered UI</b>: Overwhelmed with banner ads, dense astronomical jargon, no chat.", table_cell),
            Paragraph("<b>Serene Cosmic UI</b>: Translates complex math into empathetic, human guidance.", table_cell),
        ],
        [
            Paragraph("<b>Astroyogi</b>", table_cell_bold),
            Paragraph("Curated human consultant directory.", table_cell),
            Paragraph("<b>High friction</b>: Appointment scheduling delays, high per-session fees.", table_cell),
            Paragraph("<b>24/7 Availability</b>: Instant sub-second streaming answers directly to your phone.", table_cell),
        ],
        [
            Paragraph("<b>Kundali GPT</b>", table_cell_bold),
            Paragraph("Free-form conversational natural language.", table_cell),
            Paragraph("<b>Severe AI hallucinations</b>: Invents non-existent dashas and planetary degrees.", table_cell),
            Paragraph("<b>In-Code Guardrails</b>: Swiss Ephemeris C-engine + Python AST verification.", table_cell),
        ],
        [
            Paragraph("<b>Naksh</b>", table_cell_bold),
            Paragraph("Minimalist modern interface.", table_cell),
            Paragraph("<b>Lacks daily utility</b>: Static daily horoscope; no action-oriented tools.", table_cell),
            Paragraph("<b>Actionable Muhurta</b>: 1-click Google Calendar sync for daily life decisions.", table_cell),
        ],
    ]
    t_comp = Table(comp_data, colWidths=[65, 140, 165, 160])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E1B4B")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # Section 2
    story.append(Paragraph("2. The Idea: From 'Static Fate' to 'Daily Decision Utility'", h1_style))
    story.append(Paragraph(
        "<b>Target Persona:</b> Ambitious professionals and seekers (21–42) wanting actionable daily timing for career, wealth, and relationships.<br/>"
        "<b>The One Metric It Moves:</b> <b>Day-7 (D7) Retention & Weekly Active Return Rate (WARR)</b>.<br/>"
        "<b>Why It Works:</b> By transitioning astrology from a yearly static novelty into a <b>daily decision planner</b>, users receive tangible daily value.",
        body_style
    ))
    story.append(Paragraph("<b>The Three Core Value Engines:</b>", h2_style))
    story.append(Paragraph("• <b>Auspicious Muhurta Advisor (1-Click Google Calendar Sync):</b> Computes 30-min window sweeps combining Choghadiya, Tithi, Nakshatra, and Tara Bala personalized to the user's Moon. Directly adds auspicious windows to Google Calendar.", bullet_style))
    story.append(Paragraph("• <b>Daily Habit Streak & Rewards Economy:</b> Consecutive daily check-in rewards (+1 question credit, daily mantra). Eliminates dead-end paywalls and drives habitual daily app opens.", bullet_style))
    story.append(Paragraph("• <b>Proof-First Trust (Past Check & Dasha Twin):</b> Tests the user's chart against known past milestones (career changes, relocations) before predicting the future, creating unshakeable confidence in chart accuracy.", bullet_style))
    story.append(Spacer(1, 8))

    # Section 3
    story.append(Paragraph("3. System Architecture & Technical Implementation", h1_style))
    story.append(Paragraph(
        "• <b>Swiss Ephemeris Core (pysweph):</b> High-precision C astronomical calculation engine executing within Docker in &lt;15ms.<br/>"
        "• <b>Multi-Provider Resilient LLM Orchestrator:</b> Primary Google Gemini 1.5 Flash $\\rightarrow$ secondary Groq Llama-3.3-70b circuit breaker $\\rightarrow$ offline deterministic engine. The user never sees a raw error.<br/>"
        "• <b>In-Code Grounding Validator:</b> Mathematical fact-guardrail in Python that checks generated claims against computed ephemeris placements before streaming.<br/>"
        "• <b>Neon Serverless PostgreSQL:</b> Production database with double-entry question balance ledger and event telemetry.<br/>"
        "• <b>Vercel API Reverse Proxy:</b> Seamlessly proxies /api/* calls to Render Docker container, eliminating CORS hurdles.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Section 4
    story.append(Paragraph("4. Standout Highlights (Challenge Section 4)", h1_style))
    story.append(Paragraph("• <b>Background Jobs & Calendar Sync:</b> Generates RFC-5545 calendar alerts and idempotent streak processing.<br/>"
                           "• <b>Automated Evaluation Harness:</b> 74 unit and integration tests passing in CI (ephemeris, grounding, balance flow).<br/>"
                           "• <b>Living Design System & Bilingual Voice:</b> Authentic Melooha dark-sky theme with complete English and Hindi support.", body_style))

    # Section 5
    story.append(Paragraph("5. One-Command Local Startup", h1_style))
    story.append(Paragraph("Run locally in a single command: <code>.\\run.ps1</code> (Windows) or <code>make run</code> (macOS/Linux).", body_style))

    doc.build(story)
    print("SUCCESS: Generated PDF at", pdf_path)

if __name__ == "__main__":
    build_pdf()
