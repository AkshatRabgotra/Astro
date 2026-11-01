# Dasha Twin: Feature Architecture & Documentation

## 1. Overview & Who It Is For
**Dasha Twin** is a viral retention and acquisition engine that connects a user's active Vedic planetary phase (default: **Pratyantar Dasha**) with a real, verified career milestone achieved by a notable historical or cultural figure during the **same Mahadasha lord**.

- **Target Audience**: Curious everyday astrology seekers, social media story sharers, and cultural enthusiasts who find traditional Vedic astrology predictive claims intimidating or obscure, but resonate deeply with inspirational life parallels.
- **Tone**: A reflective mirror for contemplation and fun, strictly **never a prediction**.

---

## 2. Core Metrics
- **Primary North-Star Metric**: **Shares per Weekly Active User (WAU)**  
  $$\text{Shares per WAU} = \frac{\text{Total Shares Generated in Last 7 Days}}{\text{Weekly Active Users (WAU)}}$$
- **Secondary Metric**: **Share Link Opened to Signup Conversion Rate**  
  $$\text{Share-to-Signup Rate} = \frac{\text{Signups Attributed to } ?ref=\text{token}}{\text{Total Unique } /s/\text{token Views}}$$

### Why This Feature Moves the Metrics:
1. **Low Friction & High Relatability**: Comparing one's current phase to Dilip Kumar, Sachin Tendulkar, Marie Curie, or Steve Jobs creates an immediate screenshot-and-share reflex.
2. **Organic Social Proof**: When users share cards to Instagram Stories, WhatsApp Status, or X, their followers see a branded, visually stunning cosmic artifact with a clear CTA to find their own parallel.
3. **Daily Habit Loop**: Because matching is day-seeded, users return daily to see if their sub-period or parallel has evolved.

---

## 3. Data Integrity & Hand-Curated Dataset
- Stored deterministically in `data/figures.json`.
- **Zero Hallucination Guarantee**: The LLM is never allowed to invent dates, milestones, awards, or celebrities.
- **Rigorous Ingestion Criteria**:
  - **30 Verified Figures**: Diverse representation across cinema, cricket, science, astronautics, technology, literature, music, and athletics.
  - **Rodden Rating**: Strictly **AA** (Official Birth Certificate / Registry) or **A** (Direct autobiographical or subject-quoted memory). Unverified or approximate times are excluded from high-level matching.
  - **Milestones**: 89 events strictly categorized into `career`, `creative`, and `achievement`. All illnesses, deaths, legal scandals, crimes, and minor-related events are categorically excluded.
  - **Rights-Safe**: Celebrity photographs are excluded to respect image rights; stylish monogram initials and planetary glyphs are used on all renderers.

---

## 4. Grounded Card Copy & Code-Enforced Validator
- **Word Limit**: The parallel body copy is strictly capped at **60 words**.
- **Predictive Language Filter**: Any phrase promising the future (`"you will"`, `"guaranteed to"`, `"fortune"`) is rejected.
- **Causal Astrology Filter**: Any claim asserting direct planetary physical causality (`"because of the Moon"`, `"Saturn forces you"`) is rejected.
- **Retry & Fallback**: Retries once on validation failure with programmatic feedback, then falls back to a verified deterministic template in both **English** and **Hindi**.
- **Disclaimer**: Every card and public link displays: *"For reflection and fun, not prediction."*

---

## 5. Sharing Architecture & Privacy
1. **Zero Birth Data Leak**: The `/api/share` endpoint creates a 128-bit random token (`secrets.token_hex(16)`). The snapshot strictly omits birth date, birth time, coordinates, and natal houses.
2. **First Name Privacy Toggle**: User's first name is omitted by default and only appears if explicitly opted in.
3. **Dual Social Image Generation**:
   - **Portrait Card (1080x1350)** for social feed and WhatsApp share.
   - **Story Version (1080x1920)** for 9:16 Instagram and WhatsApp Stories.
   - Generated idempotently in background tasks using Pillow and cached on disk.
4. **90-Day Expiry & Revocation**: Every token automatically expires after 90 days. A dedicated revocation endpoint (`POST /api/share/{token}/revoke`) immediately invalidates cards and returns HTTP 404.

---

## 6. Trade-Offs & Architectural Decisions
| Decision | Chosen Approach | Alternative Considered | Trade-Off Rationale |
| :--- | :--- | :--- | :--- |
| **Dasha Matching Level** | User's Pratyantar vs. Figure's Mahadasha | Matching at same level only | Mahadasha spans years, making it rich in notable milestones. Users experience Pratyantar shifts every few weeks/months, providing fresh parallels. |
| **Image Generation** | Server-side Python Pillow | Client-side html2canvas | Headless server-side Pillow guarantees pixel-perfect Open Graph previews on WhatsApp/Twitter and works flawlessly on low-power mobile devices. |
| **Celebrity Imagery** | Monogram Badges & Planet Glyphs | Scraped Celebrity Photos | Prevents intellectual property & image right liabilities while aligning with Melooha's cosmic dark-plum aesthetic. |
