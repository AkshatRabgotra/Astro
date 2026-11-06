# Melooha AI — Vedic Astrology Q&A & Auspicious Timing

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-74%20Passing-success.svg)](https://pytest.org)

**Melooha Engineering Challenge Submission** — *"Help more people discover Melooha, trust it, and come back to it."*

---

## 🚀 Live Production Links & Deliverables

| Deliverable | Link / Location |
| :--- | :--- |
| **Live Web App (Mobile-First SPA)** | **[https://astro-psi-olive.vercel.app](https://astro-psi-olive.vercel.app)** |
| **Live Backend API (Docker)** | **[https://astro-5qqa.onrender.com](https://astro-5qqa.onrender.com)** |
| **Public GitHub Repository** | **[https://github.com/AkshatRabgotra/Astro](https://github.com/AkshatRabgotra/Astro)** |
| **Final Submission Report (PDF)** | **[Download PDF](https://astro-psi-olive.vercel.app/MELOOHA_FINAL_SUBMISSION.pdf)** |
| **Target Evaluated Metric** | **Day-7 (D7) Retention & Weekly Active Return Rate (WARR)** |
| **Core Differentiating Feature** | **Personalized Muhurta Advisor (Google Calendar Sync) + Daily Rewards Habit Streak** |

---

## 📌 Executive Summary
A standalone, mobile-first, authentic Melooha-style AI Vedic astrology platform designed to solve the **post-question drop-off**:
1. **Evidence-Grounded Readings**: Answers stream over SSE using an empathetic conversational voice (bottom-line first), strictly validated against precomputed Swiss Ephemeris astronomical facts with zero hallucinations. Includes an interactive **Astrological References** modal (`{Placement} ({Chart}): {Meaning}`).
2. **Personalized Auspicious Muhurta**: Computes 30-minute astrological windows (Choghadiya, Tithi, Nakshatra, and Tara Bala) with **1-click Google Calendar integration**.
3. **Daily Habit Streak Economy**: Consecutive-day check-in rewards (+1 free question credit and daily spiritual mantras) that keep users engaged beyond the single free question.
4. **Past Check & Dasha Twin**: Verifies past life milestones against Vimshottari Dasha to build unshakeable trust, and matches historical figures navigating the same planetary period.

---

## ⚡ Quickstart (One Command to Run Everything)

```bash
# Clone the repository
git clone https://github.com/AkshatRabgotra/Astro.git
cd Astro

# Start both Backend and Frontend with one command:
# On Windows:
.\run.ps1

# On macOS / Linux:
make run
```

Or run via Docker:
```bash
docker compose up --build
```

---

## 🧪 Automated Test Suite (74 Passing Tests)

Run the automated test harness:
```bash
pytest -q
# 74 passed in 4.60s
```
Covers:
- Swiss Ephemeris astronomical precision calculations
- AST fact-guardrail and hallucination rejection
- Panchanga, Choghadiya, and Tara Bala rules
- User onboarding, atomic credit balance ledger, and reward streak flows

---

*Submitted for the Melooha Engineering Challenge — November 2026.*
