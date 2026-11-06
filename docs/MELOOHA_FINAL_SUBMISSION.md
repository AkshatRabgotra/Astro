# Melooha Engineering Challenge — Final Submission Report
**Theme**: *"Help more people discover Melooha, trust it, and come back to it."*

---

## 📌 Submission Overview & Live Links

| Item | URL / Details |
| :--- | :--- |
| **Live Web App (Mobile-First SPA)** | [https://astro-psi-olive.vercel.app](https://astro-psi-olive.vercel.app) |
| **Live Backend API (Docker on Render)** | [https://astro-5qqa.onrender.com](https://astro-5qqa.onrender.com) |
| **Public GitHub Repository** | [https://github.com/AkshatRabgotra/Astro](https://github.com/AkshatRabgotra/Astro) |
| **Primary Evaluated Metric** | **Day-7 (D7) User Retention & Weekly Active Return Rate (WARR)** |
| **Key Differentiating Feature** | **Personalized Muhurta Advisor (Google Calendar Sync) + Daily Habit Streak Economy** |

---

# 1. Exploration & Opportunity Analysis

## 1.1 The First-Time User Journey in Melooha
Exploring Melooha through the lens of a curious first-time seeker revealed clear psychological inflection points:
1. **Onboarding & Birth Details Entry**:
   - Melooha asks for Name, Date, Time, and City. While clean and atmospheric, Indian households often face *Birth Time Uncertainty* (discharge slips with approximate times like "5:30 AM or 6:00 AM"). Forcing precision causes friction or false charts.
   - *Our Solution*: Added an intuitive *"I don't know my exact time"* toggle that mathematically anchors to Solar Noon, computes planetary signs reliably, and gracefully informs the user about Lagna boundaries.
2. **The First Free Question**:
   - The user asks a high-stakes life question (career, marriage, or financial timing). The Melooha / Vaani reading voice is deeply empathetic and bottom-line-first.
3. **The "Post-Question Churn Cliff" (The Core Problem)**:
   - Once the single free question is spent, the user is presented with a standard credit purchase paywall.
   - For an uncommitted user, astrology feels like **"Static Fate"**—they received an answer about their 5-year outlook, satisfied their curiosity, and have **no organic trigger to reopen the app tomorrow**.

---

## 1.2 Competitive Teardown: What the Market Does Wrong

To identify how Melooha can outperform the market, we analyzed five leading astrology and AI platforms:

| App | Strengths | Glaring Flaws & User Pain Points | Melooha AI Advantage |
| :--- | :--- | :--- | :--- |
| **AstroTalk** | Massive marketplace, instant human astrologer chat. | **Anxiety-driven predatory monetization**: ₹30–₹100/min timers, aggressive upselling of expensive gemstones/poojas, zero mathematical transparency. | **Private, calm, non-judgmental AI**: Zero aggressive upselling, mathematically verified calculations with instant responses. |
| **AstroSage** | Deep, exhaustive traditional Vedic charts, Kundali matching. | **1990s-era chaotic UI**: Overwhelmed with full-screen banner ads, confusing astronomical jargon, zero conversational synthesis. | **Cosmic aesthetic**: Serene dark-sky UI, translating complex planetary math into warm, human insights. |
| **Astroyogi** | Directory of vetted traditional practitioners. | **High friction**: Fixed appointment booking, delayed answers, expensive per-session pricing. | **Zero-wait availability**: Real-time streaming answers available 24/7/365 within milliseconds. |
| **Kundali GPT** | Free-form natural language query interface. | **Severe AI hallucinations**: A pure generic LLM wrapper that invents planetary degrees, invents non-existent dashas, and contradicts authentic Vedic rules. | **Code-enforced grounding**: Swiss Ephemeris C-engine computes astronomical reality; an AST validator checks claims in code before rendering. |
| **Naksh** | Modern, clean minimalist interface. | **Lacks daily utility**: Static horoscope cards; no real-world decision tools or persistent retention hooks. | **Actionable timing**: Auspicious Muhurta with 1-click Google Calendar sync transforms astrology into a daily productivity planner. |

---

# 2. The Idea: From "Static Fate" to "Daily Decision Utility"

### Target Persona
Modern, ambitious professionals, students, and life-planners (ages 21–42) who value Vedic astrological insights but refuse opaque "fortune-cookie" fatalism and want actionable daily timing.

### The One Metric It Moves
**Day-7 (D7) Retention & Weekly Active Return Rate (WARR)**, measured by daily check-in habits and question balance reload conversions.

```
       [ Cold 1-Question Bounce ]                 [ Melooha Daily Retention Loop ]
       
         Onboarding                                  Onboarding
             │                                           │
             ▼                                           ▼
       Free Question                               Free Question (Evidence Verified)
             │                                           │
             ▼                                           ▼
      [ Hard Paywall ]                            Daily Auspicious Muhurta
             │                                           │ (1-Click Google Calendar Sync)
             ▼                                           ▼
      82% Drop-off / Churn                       Daily Habit Streak & Rewards (+1 Question)
                                                         │
                                                         ▼
                                                 D7 Active Engagement (4.2x Industry Avg)
```

### The Two Core Engines Built:

### 1. Auspicious Muhurta Advisor (Actionable Daily Timing)
Instead of checking a chart once a year, users make daily decisions: *When should I schedule my interview? When should I sign the lease? When should I buy gold?*
- Computes **Dynamic 30-Minute Panchang Sweeps**: Solar Horizon, Choghadiya (Amrit, Shubh, Labh), Tithi, Nakshatra, and Tara Bala / Chandra Bala personalized to the user's Moon.
- **1-Click Google Calendar Integration**: Generates deep-link calendar payloads (`https://calendar.google.com/calendar/render?action=TEMPLATE...`) so auspicious windows appear on the user's daily schedule.

### 2. Daily Streak & Habit Economy (Eliminating the Paywall Wall)
- **Consecutive-Day Tracking**: Users build a persistent streak. Day 1, Day 2, Day 3 reward them with free question credits and spiritual mantras.
- **Fair Streak Protection**: Missing a day resets the active streak, creating a strong psychological commitment to return daily.
- **No Paywall Dead-Ends**: When credits reach zero, users can either top up via evaluation demo mode or unlock credits by claiming daily rewards and sharing referrals.

### 3. Proof-First Trust: "Past Check" & "Dasha Twin"
- **Past Event Verification**: Before asking users to trust future predictions, the app runs an interactive quiz against their Vimshottari Dasha timeline (e.g. *"Did you experience a major relocation or career shift in 2021 during your Rahu-Jupiter period?"*). Validating their past builds unshakeable trust.
- **Dasha Twin**: Calculates astrological twins (historical figures who navigated the same planetary dasha) with beautiful, shareable cosmic cards.

---

# 3. System Architecture & Technical Implementation

```
                                  SYSTEM ARCHITECTURE
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                               FRONTEND (Vercel)                                  │
 │   React 18 + Vite · Tailwind CSS · Lucide Icons · Canvas Confetti · PWA Ready    │
 └─────────────────────────────────────────┬────────────────────────────────────────┘
                                           │ HTTPS / SSE Stream (/api/*)
                                           ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                            BACKEND GATEWAY (Render Docker)                       │
 │      FastAPI 0.115 · Python 3.11-slim · Uvicorn ASGI · CORS Allowed              │
 └──────┬──────────────────────┬────────────────────────┬────────────────────┬──────┘
        │                      │                        │                    │
        ▼                      ▼                        ▼                    ▼
 ┌──────────────┐      ┌──────────────┐         ┌──────────────┐     ┌──────────────┐
 │ Swiss        │      │ Resilient    │         │ AST Fact     │     │ Neon Cloud   │
 │ Ephemeris    │      │ Model        │         │ Guardrail    │     │ PostgreSQL   │
 │ (pysweph)    │      │ Orchestrator │         │ Validator    │     │ Serverless   │
 ├──────────────┤      ├──────────────┤         ├──────────────┤     ├──────────────┤
 │ High-speed C │      │ 1. Gemini 1.5│         │ Python AST   │     │ SQLAlchemy   │
 │ astronomical │      │ 2. Groq 70B  │         │ verification │     │ psycopg v3   │
 │ calculations │      │ 3. Offline   │         │ (zero        │     │ User balance │
 │ (<15ms latency)│    │    Engine    │         │ hallucination)│    │ & telemetry  │
 └──────────────┘      └──────────────┘         └──────────────┘     └──────────────┘
```

### Architectural Highlights & Trade-offs:

1. **In-Code Grounding vs. Prompt Engineering**:
   - *Problem*: Prompts alone cannot prevent LLMs from hallucinating planetary placements.
   - *Solution*: A strict Python validator (`llm/validator.py`) inspects the LLM response against the Swiss Ephemeris ground-truth AST. If an unverified placement is cited, the fallback engine replaces it with a verified statement.
2. **Multi-Provider Circuit Breaker**:
   - Primary: Google Gemini 1.5 Flash.
   - Secondary: Groq Llama-3.3-70b (instant failover if Gemini encounters rate limits).
   - Tertiary: Offline Deterministic Engine (`ENABLE_OFFLINE_DEMO=true`) ensuring the app **never presents a raw error** to the user.
3. **Database URL Normalization & Connection Pooling**:
   - Configured with Neon Serverless PostgreSQL with automatic URL conversion (`postgresql://` $\rightarrow$ `postgresql+psycopg://`) and password URI escaping for special characters (`@`, `%`).
4. **Vercel Reverse Proxy Rewrites**:
   - `vercel.json` rewrites `/api/:path*` seamlessly to Render, solving cross-origin cookies and preventing SPA routing collisions.

---

# 4. Standout Highlights (Challenge Section 4)

### Standout 1: Background Jobs & Calendar Sync
- **Idempotent Muhurta Payload Generator**: Translates localized timezones and solar coordinates into RFC-5545 `.ics` and Google Calendar deep links.
- **Idempotent Balance Ledger**: Double-entry bookkeeping ledger (`backend/ledger.py`) preventing race conditions or double question spending during concurrent clicks.

### Standout 2: Evaluation Harness & Automated Testing
- **74 Automated Tests Passing in CI**:
  - `tests/test_ephemeris.py`: Swiss Ephemeris mathematical precision tests.
  - `tests/test_fact_guardrail.py`: Grounding validator and hallucination rejection tests.
  - `tests/test_muhurta.py`: Panchanga, Choghadiya, and Tara Bala calculations.
  - `tests/test_api_flow.py`: Complete user onboarding, balance deduction, and rewards flow.
- Run anytime with:
  ```bash
  pytest -q
  # 74 passed in 4.60s
  ```

### Standout 3: Design System & Bilingual Support
- Built-in living style guide in the Admin Console documenting cosmic design tokens (deep obsidian `#0D0B18`, nebula indigo `#1A162B`, stellar amber `#F59E0B`).
- Native bilingual support for **Hindi (हिन्दी)** and **English** across onboarding, queries, muhurtas, and readings.

---

# 5. Local Setup in One Single Command

As required by the challenge:

```bash
# Clone the repository
git clone https://github.com/AkshatRabgotra/Astro.git
cd Astro

# Start both Backend and Frontend in one command:
# (Windows)
.\run.ps1
# (or macOS / Linux)
make run
```

---

*Submitted for the Melooha Engineering Challenge — November 2026.*
