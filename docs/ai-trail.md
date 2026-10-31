# AI Trail Log: Melooha Engineering Challenge

## Challenge Overview
- **Domain**: Melooha-style Vedic Astrology AI Q&A Application
- **Stack**:
  - Backend: Python (FastAPI), Swiss Ephemeris (`pysweph`), Postgres (SQLAlchemy/Alembic)
  - Frontend: Next.js / React (mobile-first, Melooha dark cosmic theme)
  - LLM: Dual-provider failover (Gemini primary -> Groq fallback)
  - Core Focus: Grounded facts, verifiable citations, atomic credit ledger, reliable streaming SSE
- **Rules**:
  - Work one phase at a time.
  - Commit after each phase.
  - Write tests before moving on.
  - Free tools only, honest limits, no secret leakage.

---

## Log Entry 1: Project Initialization & Environment Setup
- **Date/Time**: 2026-10-31
- **Prompt Received**: Master Build Prompt for 7-10 day hiring challenge.
- **Key Decisions**:
  1. **Python Ephemeris Library**: Discovered that `pyswisseph` lacks Python 3.12 pre-built wheels on Windows and fails C++ compilation without MSVC build tools. Evaluated alternatives and installed `pysweph` (2.10.3.6), the active Swiss Ephemeris Python 3.12 wheel providing identical `swisseph` C bindings and functions (`swe.calc_ut`, `swe.houses_ex`, `swe.set_sid_mode`).
  2. **Phase Order**: Strictly adhering to Phase 1 first (Chart Engine as pure Python module with stable fact IDs and golden tests).
  3. **Repository Init**: Initialized Git repository.

---

## Log Entry 2: Phase 1 — Chart Engine Architecture & Design
- **Objective**: Build pure-Python module `chart/` turning `(date, time, place, timezone)` into structured `ChartFacts` with stable IDs (`F01`, `F02`, etc.).
- **Vedic Specifications**:
  - Zodiac: Sidereal (Nirayana) with Lahiri Ayanamsa (`swe.SIDM_LAHIRI`).
  - Houses: Whole-Sign House System (Bhava 1 = entire sign of Ascendant).
  - Planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu (mean node), Ketu (true opposite).
  - Nakshatras: 27 nakshatras, 4 padas each, mapped to their Vimshottari lords.
  - Dashas: Vimshottari 120-year cycle (Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury), calculating birth balance and active Mahadasha/Antardasha for any query date.
  - Aspects (Drishti): 7th full aspect for all planets; special Parashari aspects for Mars (4, 7, 8), Jupiter (5, 7, 9), Saturn (3, 7, 10).
  - Unknown Birth Time: Ascendant and whole-sign houses are flagged as `is_time_dependent: True` and marked unavailable (`is_available: False`). No guessing or hallucinating coordinates.

## Log Entry 3: Phase 1 — Implementation & Verification Summary
- **Files Created**:
  - `chart/models.py`: Pydantic models for `BirthInput`, `PlanetPosition`, `NakshatraDetail`, `DashaPeriod`, `AspectRelation`, `ChartFact`, and `ChartFacts`.
  - `chart/nakshatra.py`: Accurate 27 Nakshatra mathematical boundaries ($13^\circ 20'$ each), 4 padas ($3^\circ 20'$ each), and Vimshottari lord mappings.
  - `chart/dasha.py`: 120-year Vimshottari cycle calculation, birth balance, active Mahadasha and Antardasha calculation with start/end dates.
  - `chart/aspects.py`: Parashari aspects (mutual 7th aspect for all planets, special 4th/7th/8th for Mars, 5th/7th/9th for Jupiter, 3rd/7th/10th for Saturn, and Rahu/Ketu aspects).
  - `chart/engine.py`: Core pure-Python Vedic chart engine wrapping Swiss Ephemeris (`pysweph`), sidereal Lahiri ayanamsa, whole-sign houses, unknown-time handling, and stable facts generation (`F01` to `F21`).
  - `tests/test_chart_engine.py`: 7 automated tests including 3 golden charts (New Delhi 1980, Mumbai 1995, Bengaluru 2000), degree formatters, timezone parsing, unknown birth time constraints, and LLM context formatting.
- **Test Status**: All 7 tests PASSED in 0.26s.
- **Commit**: Completed Phase 1.

## Log Entry 4: Phase 2 — Q&A with a Question Balance & Ledger
- **Objective**: Implement database persistence layer, 7 relational tables, append-only credit ledger (+1 signup grant, +N top-up, -1 spend, +1 refund), atomic idempotent spending with multi-threaded concurrency safety, and FastAPI REST endpoints.
- **Files Created / Updated**:
  - `backend/config.py`: Application settings using Pydantic Settings and environment configuration.
  - `backend/database.py`: SQLAlchemy database connection with SQLite WAL mode and PostgreSQL compatibility.
  - `backend/models.py`: 7 relational tables (`users`, `birth_profiles`, `charts`, `balance_ledger`, `questions`, `answers`, `events`).
  - `backend/ledger.py`: Atomic ledger operations:
    - `get_balance`: `SUM(amount)` over append-only ledger entries.
    - `grant_signup_credit`: Idempotent +1 credit on user registration.
    - `spend_question_credit`: Atomic check-and-decrement with per-user mutex and row locking.
    - `topup_credits`: Idempotent +N credit top-up without real payment.
    - `refund_question_credit`: Idempotent automatic +1 refund on generation failure.
  - `backend/service.py`: High-level business logic orchestrating onboarding, birth chart calculation caching, atomic question spending, answer logging, and conversion events.
  - `backend/main.py`: REST API endpoints for onboarding, balance checking, top-up, asking questions, history, chart retrieval, and `/api/metrics` computing second-question retention rate.
  - `tests/test_ledger_and_qa.py`: 6 automated tests including idempotency, zero-balance blocking, automatic refund, and high-concurrency 10-thread parallel spend stress test.
  - `tests/test_api_endpoints.py`: End-to-end integration tests verifying HTTP endpoints, 402 status codes, top-ups, and metrics.
- **Test Status**: All 15 tests PASSED in 2.46s.
- **Commit**: Completed Phase 2.

## Log Entry 5: Phase 3 — Grounded Answers Enforced in Code
- **Objective**: Implement strict prompt building, schema enforcement, algorithmic grounding validator (Rule 1: citation existence & availability; Rule 2: regex + dictionary checks for planets, signs, houses, dashas, dates; Rule 3: retry and fallback generator), and streaming trade-off design.
- **Files Created / Updated**:
  - `llm/prompts.py`: System prompt prohibiting hallucinations and prompt builder incorporating `ChartFacts` context.
  - `llm/validator.py`: `AnswerValidator` with regex entity extraction and cross-referencing against calculated chart ground truth. Catches invalid fact IDs, unavailable citations, hallucinated signs, hallucinated houses, and false dasha claims.
  - `llm/fallback.py`: Deterministic, domain-aware safe templated generator built exclusively from verified facts with zero hallucination risk.
  - `tests/test_grounding_validator.py`: 8 unit tests covering all violation types (non-existent IDs, unavailable citations, sign hallucination, house hallucination, dasha hallucination, unknown time violations, and fallback validity).
- **Streaming Trade-off Documented**:
  - Tokens stream over SSE for instant user responsiveness (<500ms TTFT).
  - Validation occurs upon complete message reception.
  - If valid: emits `event: verified` with fact evidence chips.
  - If invalid: emits `event: replace` with corrected safe fallback text.
- **Test Status**: All 23 tests PASSED in 2.83s.
- **Commit**: Completed Phase 3.
