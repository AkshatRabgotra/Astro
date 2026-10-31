# Feature Concept: Evidence Behind Every Answer

## 1. Who It Is For
This feature is designed for **the curious seeker and the discerning skeptic**—first-time Vedic astrology users who are intrigued by personal readings but skeptical of generic "fortune cookie" advice or hallucinated AI answers.

In traditional astrology apps (e.g. AstroTalk, AstroSage), readings either come from expensive human astrologers with varying credibility, or from automated scripts that dump dense, incomprehensible jargon. Generic LLM astrology chat apps hallucinate planet placements, inventing ascendants or dasha periods out of thin air.

**Evidence Behind Every Answer** bridges this gap: users get accessible, natural-language readings, accompanied by interactive, tappable **Evidence Chips** citing the exact astronomical facts (planet, sign, whole-sign house, nakshatra, and dasha window) calculated for their birth moment.

---

## 2. The Target Metric
**Primary Metric**: **Share of free-question users who ask a second question** (Second-Question Retention Rate).

$$\text{Second-Question Retention Rate} = \frac{\text{Users who ask } \ge 2 \text{ questions}}{\text{Users who ask } \ge 1 \text{ question}} \times 100\%$$

### Secondary Supporting Metrics:
- **Evidence Engagement Rate**: % of users who tap at least one Evidence Chip on their first reading.
- **Top-up Conversion Rate**: % of zero-balance users who tap "Add Questions" to continue their reading.

---

## 3. Why It Will Move The Metric
1. **Demystifying AI Trust**: When users see that their reading isn't generic boilerplate, but is visibly grounded in `Saturn in Aries, House 5 (Debilitated)` [F09] and `Venus Mahadasha` [F12], their trust in the engine spikes.
2. **Curiosity Spiral**: Tapping a fact chip reveals new planetary dynamics (e.g., discovering their Moon Nakshatra or an unexpected retrograde planet). This immediately triggers follow-up curiosity: *"What does my Saturn in House 5 mean for long-term investments?"*
3. **Transparency over Fatalism**: By showing the raw facts behind the interpretation, the user feels empowered rather than judged, motivating them to explore other life domains (career, relationships, health).

---

## 4. How The Build Tracks It
Every interaction is instrumented in the append-only `events` table:
1. `user_onboarded`: Triggered when birth profile and chart are computed.
2. `question_asked`: Triggered on initial question submission.
3. `answer_viewed`: Triggered when reading is streamed and verified.
4. `evidence_opened`: Triggered whenever a user taps an Evidence Chip to inspect the underlying chart fact.
5. `second_question_asked`: Triggered automatically on the user's second inquiry.
6. `topup_clicked` / `topup_completed`: Triggered on balance replenishment.

The live `/metrics` dashboard and `/api/metrics` endpoint compute the retention rate in real time directly from the database.
