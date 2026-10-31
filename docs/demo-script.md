# 2-Minute Demo Video Script: Melooha AI Vedic Astrology

**Target Duration**: 2 minutes (120 seconds)  
**Presenter**: Solo Engineer  
**Focus**: Engineering excellence, strict grounding, the "Evidence Behind Every Answer" concept, and production polish.

---

### Segment 1: Onboarding & Honest Limits (0:00 – 0:25)
- **Visual**: Start on the mobile-first browser screen showing the Melooha Onboarding Modal (`http://localhost:8000`).
- **Action**: 
  1. Enter name: *"Akshat"*, date of birth: *1995-05-24*, and place: *Mumbai, India*.
  2. Toggle the **"I don't know my exact time"** switch on and off to show the explicit design:
- **Spoken**:
  > *"Hi everyone! Welcome to our Melooha Vedic Astrology application. When users don't know their exact birth time, most apps guess coordinates or hallucinate an ascendant. In our pure-Python chart engine, we handle this honestly: time-dependent houses and Lagna are explicitly marked unavailable, computing only verifiable noon planetary signs without guessing."*
- **Action**: Leave time as `14:15` and tap **"Calculate My Chart & Get 1 Free Question"**.

---

### Segment 2: Home Screen & First Free Question (0:25 – 0:50)
- **Visual**: The Melooha Home View appears with the dark cosmic gradient, plum accents, 99% horoscope ring, "Labh" Choghadiya window, and birth chart summary.
- **Action**: Point out the top header badge showing `1 Question left`, then tap the suggested question: *"When will my career enter its strongest period?"*.
- **Spoken**:
  > *"We land on the mobile-first Home screen styled in Melooha's cosmic visual language. Notice our top header shows 1 free question credit from our append-only ledger. Let's ask our first career question."*

---

### Segment 3: Streaming & "Evidence Behind Every Answer" (0:50 – 1:20)
- **Visual**: The Ask screen streams tokens smoothly over SSE.
- **Action**: 
  1. Watch words stream in real-time.
  2. As the stream finishes, highlight the **Evidence Chips** appearing underneath: `[F01: Lagna]`, `[F03: Sun in Taurus]`, `[F12: Current Dasha]`.
  3. Tap `[F01: Lagna]`. The **Evidence Drawer** opens, showing: *Virgo, House 1, 2°03'*.
  4. Tap `[F12: Current Dasha]`. Shows *Venus Mahadasha / Venus Antardasha*.
- **Spoken**:
  > *"The response streams over Server-Sent Events for instant responsiveness. When generation finishes, our code fact validator verifies every cited ID and planet placement. Here is our primary concept: **Evidence Behind Every Answer**. Tapping any chip opens the exact computed astronomical coordinates from Swiss Ephemeris. The LLM didn't invent this—every claim is grounded in code."*

---

### Segment 4: Zero-Balance Paywall & Free Top-Up (1:20 – 1:40)
- **Visual**: Balance badge now shows `0 Question left` in plum.
- **Action**:
  1. Type a second question: *"Will I buy a house in 2027?"* and press Send.
  2. The **Zero Balance Paywall Modal** immediately appears.
  3. Tap **"Add 5 Questions Free"**.
  4. Confetti bursts across the screen! The balance updates to `5 Questions left`.
  5. The question automatically submits and streams!
- **Spoken**:
  > *"Because each question is atomic, our balance is now 0. Attempting a second question safely blocks and brings up our clear paywall. For this hiring challenge, evaluators can tap 'Add 5 Questions Free'—confetti fires, 5 credits are atomically appended to the ledger, and the second reading streams immediately."*

---

### Segment 5: Multilingual (Hindi) & Metrics Dashboard (1:40 – 2:00)
- **Visual**: Switch to Hindi and then open `/metrics`.
- **Action**:
  1. Tap the **"हिन्दी"** button in the header. The UI instantly flips to Hindi: *दैनिक राशिफल*, *शुभ मुहूर्त*, and Hindi entity verification.
  2. Tap the **Metrics** tab on the bottom navigation.
  3. Show the live **Second-Question Retention Rate KPI (100%)**, total questions asked, and evidence chips opened.
- **Spoken**:
  > *"We also built full Hindi multilingual support with cross-language entity grounding. Finally, on our live Metrics screen, we track the challenge target metric: the share of free users who ask a second question, driven directly by the trust created by our Evidence Chips. Everything runs with one command: `docker compose up` or `make dev`. Thank you!"*
