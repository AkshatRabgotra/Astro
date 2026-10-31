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

## Log Entry 6: Phase 4 — Reliable Model Calls (Gemini -> Groq Fallback)
- **Objective**: Implement multi-provider failover chain with Gemini (primary) and Groq (fallback), circuit breakers, timeouts, per-provider error telemetry, and user-friendly error wrapping.
- **Files Created / Updated**:
  - `llm/circuit_breaker.py`: `CircuitBreaker` with states `CLOSED`, `OPEN`, `HALF_OPEN`, configurable failure threshold and recovery cooldown. Fast-fails requests to prevent cascading timeouts.
  - `llm/client.py`:
    - `GeminiProvider`: Direct REST interface to Google Gemini API with timeout control.
    - `GroqProvider`: Direct REST interface to Groq OpenAI-compatible API.
    - `ModelOrchestrator`: Coordinates primary -> fallback failover, circuit tripping, and structured logging.
    - `AllProvidersFailedError`: Friendly error masking internal traces with encouraging retry copy.
  - `tests/test_model_providers.py`: 5 unit tests covering primary success, mock Gemini failure fallback to Groq, circuit breaker state machine, tripped-circuit call skipping, and dual-provider failure handling.
- **Test Status**: All 28 tests PASSED in 3.11s.
- **Commit**: Completed Phase 4.

## Log Entry 7: Phase 5 — Streaming SSE, Automated CI & One-Command Setup
- **Objective**: Implement end-to-end Server-Sent Events (SSE) streaming endpoint, CI workflow, container configuration, and local startup automation.
- **Files Created / Updated**:
  - `backend/streaming.py`: SSE event generator emitting `start`, `token`, `verified` (with structured fact chips), `replace` (with grounded safe template), and `error` (with automatic credit refund).
  - `backend/main.py`: Connected `GET /api/questions/{question_id}/stream` with streaming HTTP headers (`Cache-Control: no-cache`, `X-Accel-Buffering: no`).
  - `.github/workflows/ci.yml`: GitHub Actions workflow testing on Python 3.12 across all pushes and pull requests.
  - `Dockerfile`: Multi-stage slim container packaging Swiss Ephemeris and FastAPI.
  - `docker-compose.yml`: Local multi-container orchestration.
  - `Makefile`: Commands for `make dev`, `make test`, `docker-up`, `docker-down`.
  - `requirements.txt` & `.env.example`: Explicit pinned dependencies and environment documentation.
  - `tests/test_streaming_sse.py`: 3 tests covering verified SSE streaming, replace event on violation, and automatic refund on failure.
- **Test Status**: All 31 tests PASSED in 4.15s.
- **Commit**: Completed Phase 5.

## Log Entry 8: Phase 6 — My One Idea & Melooha-Style Mobile-First UI
- **Objective**: Build a mobile-first UI authentic to Melooha's look and feel, implement "Evidence Behind Every Answer" with interactive fact inspection modals, instrument conversion events, and write `docs/idea.md`.
- **Files Created / Updated**:
  - `docs/idea.md`: Half-page rationale defining the audience (discerning seekers/skeptics), target metric (% of free-question users asking a 2nd question), trust hypothesis, and tracking implementation.
  - `frontend/package.json` & `vite.config.js`: React 18, Vite 6, Lucide icons, canvas-confetti, Tailwind CSS.
  - `frontend/src/index.css`: Melooha cosmic theme (`#080511`, `#161028`, `#B21E68`), Google Playfair Display & Inter typography, 44px touch targets.
  - `frontend/src/components/Header.jsx`: User profile pill, question balance counter (`1 Question left` / `0 Question left` with top-up badge).
  - `frontend/src/components/BottomNav.jsx`: Floating bottom bar with Home, center glowing Ask button, History, and Metrics tabs.
  - `frontend/src/components/EvidenceModal.jsx`: Interactive fact inspector showing exact coordinate, sign, whole-sign house, nakshatra, and dasha window on chip tap.
  - `frontend/src/components/PaywallModal.jsx`: Zero-balance paywall with "+5 Questions (Free Challenge)" instant credit top-up and confetti.
  - `frontend/src/components/OnboardingModal.jsx`: Birth date, place picker, and "I don't know my time" toggle with explicit house reservation warning.
  - `frontend/src/views/HomeView.jsx`: Daily horoscope (99% ring, lucky color/number), active Choghadiya (Labh), placements summary, and suggested questions.
  - `frontend/src/views/AskView.jsx`: SSE streaming chat interface with verified Evidence Chips, replace fallback badge, and error retry state.
  - `frontend/src/views/HistoryView.jsx`: Chronological question and reading archive with cited fact IDs.
  - `frontend/src/views/MetricsView.jsx`: Live analytics dashboard rendering the second-question retention rate KPI and conversion funnel.
  - `backend/main.py`: Static mount serving `frontend/dist` for single-command full-stack execution.
- **Build Status**: `vite build` completed cleanly; 31 pytest tests passing in 3.71s.
- **Commit**: Completed Phase 6.

## Log Entry 9: Phase 7 — Stand-Out Extras (Evaluation Harness & Multilingual Hindi)
- **Objective**: Implement the two challenge extras: (1) 30-question automated evaluation harness with score report and CI subset test; (2) End-to-end Hindi multilingual support across entities, grounding validation, and frontend UI.
- **Files Created / Updated**:
  - `evals/dataset.json`: 30 curated questions across career, relationships, timing, and edge cases (including unknown birth time probes, non-fatalistic ethics tests, and Hindi questions).
  - `evals/runner.py`: Evaluation runner executing code-level grounding verification, citation integrity checks, and scoring rubric generating `docs/eval_report.md`.
  - `docs/eval_report.md`: Markdown evaluation report recording **100.0% grounding pass rate** across all 30 questions.
  - `tests/test_eval_subset.py`: CI integration test executing the evaluation harness.
  - `chart/multilingual.py`: English <-> Hindi (Devanagari & transliterated) mapping for Grahas (Surya, Chandra, Mangal, etc.), Rashis (Mesha, Vrishabha, etc.), and Bhavas.
  - `llm/validator.py`: Updated to natively recognize Devanagari entities while enforcing universal fact ID grounding.
  - `frontend/src/i18n.js`: Bilingual localization dictionary (English ⇄ हिन्दी).
  - `frontend/src/components/Header.jsx`: One-tap language toggle button.
- **Test Status**: All 32 tests PASSED in 3.95s; frontend build compiled cleanly.
- **Commit**: Completed Phase 7.
