"""Deterministic safe templated astrological readings built strictly from computed ChartFacts."""

import json
from typing import Any, Dict, List
from chart.models import ChartFacts


def build_safe_templated_answer(chart_facts: ChartFacts, question: str) -> Dict[str, Any]:
    """
    Generate a 100% grounded, violation-proof fallback reading built solely from verified facts.
    Used when an LLM fails validation after retries.
    """
    q_lower = question.lower()
    cited_ids: List[str] = []
    lines: List[str] = []

    # Domain classification
    is_career = any(w in q_lower for w in ["career", "job", "work", "business", "money", "finances", "success", "exam"])
    is_relationship = any(w in q_lower for w in ["love", "marriage", "partner", "relationship", "friend", "divorce", "spouse"])
    is_timing = any(w in q_lower for w in ["when", "timing", "period", "future", "settle", "years", "time", "date"])

    lines.append("### Grounded Vedic Astrology Reading\n")

    if chart_facts.time_known and chart_facts.lagna_sign:
        f01 = chart_facts.get_fact("F01")
        if f01 and f01.is_available:
            lines.append(f"**Ascendant Foundation**: Your chart is anchored with {chart_facts.lagna_sign} Lagna in House 1 [F01], which sets the energetic baseline for your personal agency and worldview.")
            cited_ids.append("F01")
    else:
        lines.append("**Chart Foundation**: Your birth date and place indicate core planetary influences. As your exact birth time was not provided, house placements and exact Ascendant are reserved, focusing our reading on your planetary signs and nakshatras.")

    # Planetary placements relevant to domain
    planets_by_name = {p.planet: p for p in chart_facts.planets}

    if is_career:
        sun = planets_by_name.get("Sun")
        saturn = planets_by_name.get("Saturn")
        if sun:
            h_sun = f", House {sun.house}" if sun.house is not None else ""
            lines.append(f"- **Sun in {sun.sign}{h_sun}** [F03]: Governs career authority, purpose, and self-confidence. Placed in Nakshatra {sun.nakshatra.name}.")
            cited_ids.append("F03")
        if saturn:
            h_sat = f", House {saturn.house}" if saturn.house is not None else ""
            dignity = " (Exalted)" if saturn.is_exalted else (" (Debilitated)" if saturn.is_debilitated else "")
            lines.append(f"- **Saturn in {saturn.sign}{h_sat}{dignity}** [F09]: Represents discipline, sustained effort, and career foundation in Nakshatra {saturn.nakshatra.name}.")
            cited_ids.append("F09")

    elif is_relationship:
        venus = planets_by_name.get("Venus")
        moon = planets_by_name.get("Moon")
        if venus:
            h_ven = f", House {venus.house}" if venus.house is not None else ""
            lines.append(f"- **Venus in {venus.sign}{h_ven}** [F08]: Signifies relational harmony, affection, and emotional bonding. Occupies Nakshatra {venus.nakshatra.name}.")
            cited_ids.append("F08")
        if moon:
            h_moon = f", House {moon.house}" if moon.house is not None else ""
            lines.append(f"- **Moon in {moon.sign}{h_moon}** [F04]: Highlights your emotional responsiveness and inner intuition in Nakshatra {moon.nakshatra.name} [F02].")
            cited_ids.append("F04")
            if "F02" not in cited_ids:
                cited_ids.append("F02")

    else:
        # General / Timing focus
        moon = planets_by_name.get("Moon")
        jupiter = planets_by_name.get("Jupiter")
        if moon:
            h_moon = f", House {moon.house}" if moon.house is not None else ""
            lines.append(f"- **Moon in {moon.sign}{h_moon}** [F04]: Nakshatra {moon.nakshatra.name} (Pada {moon.nakshatra.pada}, ruled by {moon.nakshatra.lord}) [F02].")
            cited_ids.append("F04")
            cited_ids.append("F02")
        if jupiter:
            h_jup = f", House {jupiter.house}" if jupiter.house is not None else ""
            lines.append(f"- **Jupiter in {jupiter.sign}{h_jup}** [F07]: Brings wisdom, growth, and optimism in {jupiter.nakshatra.name}.")
            cited_ids.append("F07")

    # Current Dasha Timing
    if chart_facts.current_dasha:
        cd = chart_facts.current_dasha
        lines.append(f"\n**Planetary Timing (Vimshottari Dasha)** [F12]:")
        lines.append(f"You are currently navigating the **{cd.mahadasha_lord} Mahadasha** and **{cd.antardasha_lord} Antardasha** (active from {cd.start_date} to {cd.end_date}). This indicates a focal chapter governed by {cd.mahadasha_lord}'s principles of development.")
        cited_ids.append("F12")

    lines.append("\n*Guidance Note: Astrological readings offer symbolic timing and archetypal insight for self-awareness and life reflection, not guaranteed or fatalistic predictions.*")

    answer_text = "\n".join(lines)
    claims = [{"claim": f"Citing fact {fid}", "fact_id": fid} for fid in cited_ids]

    return {
        "answer": answer_text,
        "cited_fact_ids": cited_ids,
        "claims": claims,
    }
