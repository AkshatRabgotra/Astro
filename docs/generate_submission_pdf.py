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
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E1B4B"),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#312E81"),
        spaceBefore=11,
        spaceAfter=5,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#4338CA"),
        spaceBefore=7,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1F2937"),
        leftIndent=12,
        spaceAfter=2.5,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#111827"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#111827"),
    )
    table_cell_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Melooha Engineering Challenge — Final Submission Report", title_style))
    story.append(Paragraph("Theme: <i>'Help more people discover Melooha, trust it, and come back to it.'</i>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=8))

    # Overview Table
    overview_data = [
        [Paragraph("Deliverable", table_cell_header), Paragraph("Details & Production URLs", table_cell_header)],
        [Paragraph("Live Web Application", table_cell_bold), Paragraph("<b>https://astro-psi-olive.vercel.app</b> (Mobile-First SPA on Vercel)", table_cell)],
        [Paragraph("Backend API Service", table_cell_bold), Paragraph("<b>https://astro-5qqa.onrender.com</b> (FastAPI Docker on Render)", table_cell)],
        [Paragraph("GitHub Repository", table_cell_bold), Paragraph("<b>https://github.com/AkshatRabgotra/Astro</b> (Public repo, 74 tests passing)", table_cell)],
        [Paragraph("Core Target Metric", table_cell_bold), Paragraph("<b>Day-7 (D7) Retention & Weekly Active Return Rate (WARR)</b>", table_cell)],
        [Paragraph("Selected Feature", table_cell_bold), Paragraph("<b>Personalized Muhurta Advisor (Google Calendar Sync) + Daily Rewards Streak</b>", table_cell)],
    ]
    t_overview = Table(overview_data, colWidths=[120, 420])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#312E81")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(t_overview)
    story.append(Spacer(1, 6))

    # Section 1: Exploration
    story.append(Paragraph("1. App Exploration & Problem Identification", h1_style))
    story.append(Paragraph(
        "<b>User Drop-off Points in Melooha:</b> Exploring the user experience highlights two key friction moments: (1) <i>Birth Time Uncertainty</i> during onboarding, and (2) the <i>Single-Question Drop-off</i>. Once a user reads their single free answer, a credit paywall appears. Because a birth chart feels like static information, users feel their questions have been answered and have <b>no daily reason to return tomorrow</b>.",
        body_style
    ))
    story.append(Paragraph("<b>Competitor Analysis & Market Gaps:</b>", h2_style))

    comp_data = [
        [Paragraph("App", table_cell_header), Paragraph("What They Do Well", table_cell_header), Paragraph("Where They Fall Short", table_cell_header), Paragraph("How Our Build Solves It", table_cell_header)],
        [
            Paragraph("<b>AstroTalk</b>", table_cell_bold),
            Paragraph("Instant human astrologer chat.", table_cell),
            Paragraph("Expensive per-minute timers; aggressive sales pushes for poojas and gems.", table_cell),
            Paragraph("<b>Private AI</b>: Immediate readings with zero upsell pressure.", table_cell),
        ],
        [
            Paragraph("<b>AstroSage</b>", table_cell_bold),
            Paragraph("Exhaustive traditional chart tables.", table_cell),
            Paragraph("Outdated 1990s UI cluttered with banner ads; complex jargon.", table_cell),
            Paragraph("<b>Clean modern UI</b>: Translates planetary math into practical advice.", table_cell),
        ],
        [
            Paragraph("<b>Astroyogi</b>", table_cell_bold),
            Paragraph("Directory of verified consultants.", table_cell),
            Paragraph("Requires appointment booking; high friction and slow turnaround.", table_cell),
            Paragraph("<b>Instant answers</b>: Sub-second streaming readings 24/7.", table_cell),
        ],
        [
            Paragraph("<b>Kundali GPT</b>", table_cell_bold),
            Paragraph("Free-form natural language chat.", table_cell),
            Paragraph("High rate of AI hallucinations; invents planetary positions.", table_cell),
            Paragraph("<b>In-code verification</b>: C-engine math + AST code check.", table_cell),
        ],
        [
            Paragraph("<b>Naksh</b>", table_cell_bold),
            Paragraph("Minimalist modern aesthetic.", table_cell),
            Paragraph("Static daily horoscope; lacks practical decision tools.", table_cell),
            Paragraph("<b>Actionable utility</b>: Daily Muhurta with Google Calendar export.", table_cell),
        ],
    ]
    t_comp = Table(comp_data, colWidths=[65, 145, 165, 165])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E1B4B")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 6))

    # Section 2: The Idea
    story.append(Paragraph("2. The Idea: From a One-Time Reading to a Daily Decision Utility", h1_style))
    story.append(Paragraph(
        "<b>Target User:</b> Young professionals, students, and planners who want practical Vedic timing for day-to-day decisions (interviews, signing contracts, travel).<br/>"
        "<b>The Primary Metric:</b> <b>Day-7 (D7) Retention & Weekly Active Return Rate (WARR)</b>.<br/>"
        "<b>The Core Features Built:</b>",
        body_style
    ))
    story.append(Paragraph("• <b>Personalized Muhurta Advisor (1-Click Google Calendar Sync):</b> Computes daily 30-min astronomical windows (Choghadiya, Tithi, Nakshatra, and Tara Bala based on the user's Moon). Users click <i>Add to Google Calendar</i> to schedule auspicious times directly into their day.", bullet_style))
    story.append(Paragraph("• <b>Daily Rewards & Habit Streak:</b> Encourages daily app opens with consecutive check-in streaks (+1 free question credit, daily spiritual mantras), removing the feeling of an abrupt paywall.", bullet_style))
    story.append(Paragraph("• <b>Past Check & Dasha Twin:</b> Builds trust by validating the user's chart against known past life milestones before predicting future periods, and matches historical figures sharing the same planetary dasha.", bullet_style))
    story.append(Spacer(1, 6))

    # Section 3: Architecture
    story.append(Paragraph("3. System Architecture & Engineering Trade-offs", h1_style))
    
    # Architecture Diagram Table
    arch_data = [
        [Paragraph("Layer", table_cell_header), Paragraph("Components & Flow", table_cell_header)],
        [
            Paragraph("<b>Client (Frontend)</b>", table_cell_bold),
            Paragraph("React 18 + Vite SPA · Tailwind CSS · Google Identity Services (One-Tap Login) · Deployed on <b>Vercel</b>", table_cell)
        ],
        [
            Paragraph("<b>API Gateway</b>", table_cell_bold),
            Paragraph("Vercel Reverse Proxy (<code>/api/*</code>) transparently routing requests to the Render backend without CORS friction.", table_cell)
        ],
        [
            Paragraph("<b>Backend Service</b>", table_cell_bold),
            Paragraph("FastAPI in Docker on <b>Render</b> · Python 3.11 · SSE Streaming Engine for instant sub-second text delivery.", table_cell)
        ],
        [
            Paragraph("<b>Calculation & AI</b>", table_cell_bold),
            Paragraph("<b>Swiss Ephemeris (pysweph C-Engine)</b> for exact planetary math (&lt;15ms) · <b>Model Orchestrator</b> (Gemini 1.5 $\\rightarrow$ Groq Llama-3.3 $\\rightarrow$ Offline fallback) · <b>Python AST Guardrail</b> verifying facts before rendering.", table_cell)
        ],
        [
            Paragraph("<b>Data Storage</b>", table_cell_bold),
            Paragraph("<b>Neon Cloud Serverless PostgreSQL</b> · Idempotent question balance ledger · User profile and telemetry storage.", table_cell)
        ],
    ]
    t_arch = Table(arch_data, colWidths=[100, 440])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#312E81")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>Key Engineering Decisions:</b><br/>"
        "1. <i>In-Code Fact Verification</i>: Instead of relying on prompt instructions alone, true placements are calculated in C using Swiss Ephemeris, and generated text is parsed by an AST guardrail in Python.<br/>"
        "2. <i>Multi-Provider Resiliency</i>: Model calls automatically cascade from Gemini 1.5 to Groq to an offline deterministic engine, ensuring the user never sees a raw error.<br/>"
        "3. <i>Double-Entry Balance Ledger</i>: Prevents duplicate deductions or race conditions during rapid clicks.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 4: Standouts
    story.append(Paragraph("4. Challenge Standout Features & Evaluation", h1_style))
    story.append(Paragraph("• <b>Background Jobs & Calendar Sync:</b> Generates RFC-5545 calendar alerts and manages idempotent daily streak tracking.<br/>"
                           "• <b>Automated Evaluation Suite:</b> 74 unit and integration tests passing in CI (<code>pytest -q</code> in 4.6s) across calculations, guardrails, and API flows.<br/>"
                           "• <b>Living Design System & Bilingual Support:</b> Documented cosmic design tokens in the Admin Console; native English and Hindi support across all features.<br/>"
                           "• <b>Single Command Local Setup:</b> Run locally with <code>.\\run.ps1</code> (Windows) or <code>make run</code> (macOS/Linux).", body_style))

    doc.build(story)
    print("SUCCESS: Regenerated professional PDF at", pdf_path)

if __name__ == "__main__":
    build_pdf()
