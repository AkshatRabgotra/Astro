"""Deterministic safe templated astrological readings built strictly from computed ChartFacts."""

import json
import re
from typing import Any, Dict, List, Optional
from chart.models import ChartFacts


def build_safe_templated_answer(
    chart_facts: ChartFacts,
    question: str,
    user_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a 100% grounded, violation-proof fallback reading built solely from verified facts.
    Supports both English and Hindi questions with a warm, human, personal touch.
    """
    q_lower = question.lower()
    is_hindi = bool(re.search(r"[\u0900-\u097F]", question))
    cited_ids: List[str] = []
    lines: List[str] = []
    display_name = user_name or "Friend"

    # Domain classification
    is_career = any(w in q_lower for w in ["career", "job", "work", "business", "money", "finances", "success", "exam", "करियर", "नौकरी", "व्यापार", "व्यवसाय", "काम", "धन"])
    is_relationship = any(w in q_lower for w in ["love", "marriage", "partner", "relationship", "friend", "divorce", "spouse", "विवाह", "शादी", "प्रेम", "जीवनसाथी"])
    is_timing = any(w in q_lower for w in ["when", "timing", "period", "future", "settle", "years", "time", "date", "कब", "समय", "अवधि"])
    is_remedies = any(w in q_lower for w in ["remedy", "remedies", "balance", "उपाय", "शांति", "संतुलित", "ऊर्जा"])

    planets_by_name = {p.planet: p for p in chart_facts.planets}

    if is_hindi:
        HINDI_SIGNS = {
            "Aries": "मेष", "Taurus": "वृषभ", "Gemini": "मिथुन", "Cancer": "कर्क",
            "Leo": "सिंह", "Virgo": "कन्या", "Libra": "तुला", "Scorpio": "वृश्चिक",
            "Sagittarius": "धनु", "Capricorn": "मकर", "Aquarius": "कुम्भ", "Pisces": "मीन"
        }
        HINDI_PLANETS = {
            "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध",
            "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"
        }
        lines.append(f"नमस्ते {display_name},\n")
        lines.append("आपके इस महत्वपूर्ण प्रश्न पर आपके जन्म चक्र के अनुसार यह आत्मीय और प्रामाणिक ज्योतिषीय मार्गदर्शन प्रस्तुत है:\n")

        if chart_facts.time_known and chart_facts.lagna_sign:
            f01 = chart_facts.get_fact("F01")
            if f01 and f01.is_available:
                hi_lagna = HINDI_SIGNS.get(chart_facts.lagna_sign, chart_facts.lagna_sign)
                lines.append(f"**लग्न आधार**: आपकी कुंडली **{hi_lagna} लग्न (प्रथम भाव) [F01]** पर आधारित है, जो आपकी आंतरिक ऊर्जा और निर्णय शक्ति को संचालित करता है।")
                cited_ids.append("F01")
        else:
            lines.append("**कुंडली आधार**: सटीक जन्म समय उपलब्ध न होने के कारण भाव गणना आरक्षित रखी गई है। हम ग्रह राशियों और महादशा के आधार पर यह विश्लेषण प्रस्तुत कर रहे हैं।")

        if is_remedies:
            lines.append("\n**ऊर्जा संतुलन एवं सात्विक उपाय**:")
            sun = planets_by_name.get("Sun")
            moon = planets_by_name.get("Moon")
            saturn = planets_by_name.get("Saturn")
            if sun:
                hi_sign = HINDI_SIGNS.get(sun.sign, sun.sign)
                lines.append(f"- **सूर्य {hi_sign} राशि में** [F03]: आत्मविश्वास और नेतृत्व ऊर्जा को पोषित करता है। प्रातःकाल सूर्य को जल अर्पित करें।")
                cited_ids.append("F03")
            if moon:
                hi_sign = HINDI_SIGNS.get(moon.sign, moon.sign)
                lines.append(f"- **चन्द्र {hi_sign} राशि में** [F04]: मानसिक शांति और एकाग्रता के लिए नियमित ध्यान और शिव स्मरण हितकारी है।")
                cited_ids.append("F04")
            if saturn:
                hi_sign = HINDI_SIGNS.get(saturn.sign, saturn.sign)
                lines.append(f"- **शनि {hi_sign} राशि में** [F09]: कर्म के प्रति निष्ठा और शनिवार को असहाय लोगों की सहायता से शुभ फल मिलते हैं।")
                cited_ids.append("F09")

        elif is_career:
            lines.append("\n**सर्वोत्तम कार्यक्षेत्र दिशा**: ग्रहों की स्थिति के अनुसार, आप उन क्षेत्रों में श्रेष्ठ प्रदर्शन करते हैं जहाँ आपको रणनीतिक स्वायत्तता और व्यवस्था निर्माण का अवसर मिले।")
            sun = planets_by_name.get("Sun")
            saturn = planets_by_name.get("Saturn")
            if sun:
                hi_sign = HINDI_SIGNS.get(sun.sign, sun.sign)
                h_sun = f", भाव {sun.house}" if (chart_facts.time_known and sun.house is not None) else ""
                lines.append(f"- **सूर्य {hi_sign} राशि में{h_sun}** [F03]: अधिकार क्षेत्र, आत्मबल और नेतृत्व क्षमता को मजबूत करता है।")
                cited_ids.append("F03")
            if saturn:
                hi_sign = HINDI_SIGNS.get(saturn.sign, saturn.sign)
                h_sat = f", भाव {saturn.house}" if (chart_facts.time_known and saturn.house is not None) else ""
                lines.append(f"- **शनि {hi_sign} राशि में{h_sat}** [F09]: कर्म, निरंतर अभ्यास और अनुशासन द्वारा स्थायी सफलता प्रदान करता है।")
                cited_ids.append("F09")

        elif is_relationship:
            venus = planets_by_name.get("Venus")
            moon = planets_by_name.get("Moon")
            if venus:
                hi_sign = HINDI_SIGNS.get(venus.sign, venus.sign)
                h_ven = f", भाव {venus.house}" if (chart_facts.time_known and venus.house is not None) else ""
                lines.append(f"- **शुक्र {hi_sign} राशि में{h_ven}** [F08]: संबंधों में सौहार्द, परस्पर सम्मान और आत्मीय संतुलन को दर्शाता है।")
                cited_ids.append("F08")
            if moon:
                hi_sign = HINDI_SIGNS.get(moon.sign, moon.sign)
                h_moon = f", भाव {moon.house}" if (chart_facts.time_known and moon.house is not None) else ""
                lines.append(f"- **चन्द्र {hi_sign} राशि में{h_moon}** [F04]: भावनात्मक संवेदनशीलता और सुरक्षा की आवश्यकता को इंगित करता है।")
                cited_ids.append("F04")
                if "F02" not in cited_ids:
                    cited_ids.append("F02")

        else:
            sun = planets_by_name.get("Sun")
            moon = planets_by_name.get("Moon")
            if sun:
                hi_sign = HINDI_SIGNS.get(sun.sign, sun.sign)
                lines.append(f"- **सूर्य {hi_sign} राशि में** [F03]: जीवनशक्ति और आत्मबल को ऊर्जा प्रदान करता है।")
                cited_ids.append("F03")
            if moon:
                hi_sign = HINDI_SIGNS.get(moon.sign, moon.sign)
                lines.append(f"- **चन्द्र {hi_sign} राशि में** [F04]: आंतरिक शांति और बौद्धिक विवेक का संवर्धन करता है।")
                cited_ids.append("F04")

        if chart_facts.current_dasha:
            cd = chart_facts.current_dasha
            hi_maha = HINDI_PLANETS.get(cd.mahadasha_lord, cd.mahadasha_lord)
            hi_antar = HINDI_PLANETS.get(cd.antardasha_lord, cd.antardasha_lord)
            lines.append(f"\n**सक्रिय महादशा चक्र [F12]**:")
            lines.append(f"वर्तमान में आप **{hi_maha} महादशा** एवं **{hi_antar} अंतर्दशा** ({cd.start_date} से {cd.end_date}) के प्रभाव में हैं।")
            cited_ids.append("F12")

        lines.append("\n*मार्गदर्शन नोट: वैदिक ज्योतिष आत्म-चिंतन और सचेत निर्णय लेने के लिए प्रतीकात्मक मार्गदर्शन प्रस्तुत करता है।*")

    else:
        # English Template Path
        lines.append(f"Namaste {display_name},\n")
        lines.append("### Grounded Vedic Astrology Reading")
        lines.append("I hear your question deeply. Looking closely into your birth chart, here is your personal astrological guidance:\n")

        if chart_facts.time_known and chart_facts.lagna_sign:
            f01 = chart_facts.get_fact("F01")
            if f01 and f01.is_available:
                lines.append(f"**Ascendant Foundation**: Your chart is anchored with {chart_facts.lagna_sign} Lagna in House 1 [F01], which sets the energetic baseline for your personal agency and worldview.")
                cited_ids.append("F01")
        else:
            lines.append("**Chart Foundation**: Your birth date and place indicate core planetary influences. As your exact birth time was not provided, house placements and exact Ascendant are reserved, focusing our reading on your planetary signs and nakshatras.")

        if is_career:
            lines.append("\n**Core Vocational Alignment**: Based on your astrological profile, your highest vocational fulfillment lies in roles requiring strategic autonomy, systematic execution, and clear structural ownership.")
            sun = planets_by_name.get("Sun")
            saturn = planets_by_name.get("Saturn")
            if sun:
                h_sun = f", House {sun.house}" if (chart_facts.time_known and sun.house is not None) else ""
                lines.append(f"- **Sun in {sun.sign}{h_sun}** [F03]: Governs career authority, purpose, and self-confidence. Placed in Nakshatra {sun.nakshatra.name}.")
                cited_ids.append("F03")
            if saturn:
                h_sat = f", House {saturn.house}" if (chart_facts.time_known and saturn.house is not None) else ""
                dignity = " (Exalted)" if saturn.is_exalted else (" (Debilitated)" if saturn.is_debilitated else "")
                lines.append(f"- **Saturn in {saturn.sign}{h_sat}{dignity}** [F09]: Represents discipline, sustained effort, and career foundation in Nakshatra {saturn.nakshatra.name}.")
                cited_ids.append("F09")

        elif is_relationship:
            venus = planets_by_name.get("Venus")
            moon = planets_by_name.get("Moon")
            if venus:
                h_ven = f", House {venus.house}" if (chart_facts.time_known and venus.house is not None) else ""
                lines.append(f"- **Venus in {venus.sign}{h_ven}** [F08]: Signifies relational harmony, affection, and emotional bonding. Occupies Nakshatra {venus.nakshatra.name}.")
                cited_ids.append("F08")
            if moon:
                h_moon = f", House {moon.house}" if (chart_facts.time_known and moon.house is not None) else ""
                lines.append(f"- **Moon in {moon.sign}{h_moon}** [F04]: Highlights your emotional responsiveness and inner intuition in Nakshatra {moon.nakshatra.name} [F02].")
                cited_ids.append("F04")
                if "F02" not in cited_ids:
                    cited_ids.append("F02")

        else:
            moon = planets_by_name.get("Moon")
            jupiter = planets_by_name.get("Jupiter")
            if moon:
                h_moon = f", House {moon.house}" if (chart_facts.time_known and moon.house is not None) else ""
                lines.append(f"- **Moon in {moon.sign}{h_moon}** [F04]: Nakshatra {moon.nakshatra.name} (Pada {moon.nakshatra.pada}, ruled by {moon.nakshatra.lord}) [F02].")
                cited_ids.append("F04")
                cited_ids.append("F02")
            if jupiter:
                h_jup = f", House {jupiter.house}" if (chart_facts.time_known and jupiter.house is not None) else ""
                lines.append(f"- **Jupiter in {jupiter.sign}{h_jup}** [F07]: Brings wisdom, growth, and optimism in {jupiter.nakshatra.name}.")
                cited_ids.append("F07")

        if chart_facts.current_dasha:
            cd = chart_facts.current_dasha
            lines.append(f"\n**Planetary Timing (Vimshottari Dasha)** [F12]:")
            lines.append(f"You are currently navigating the **{cd.mahadasha_lord} Mahadasha** and **{cd.antardasha_lord} Antardasha** (active from {cd.start_date} to {cd.end_date}). This indicates a focal chapter governed by {cd.mahadasha_lord}'s principles of development.")
            cited_ids.append("F12")

        lines.append("\n*Guidance Note: Astrological readings offer symbolic timing and archetypal insight for self-awareness and life reflection, not guaranteed or fatalistic predictions.*")

    answer_text = "\n".join(lines)
    claims = [{"claim": f"Citing fact {fid}", "fact_id": fid} for fid in cited_ids]
    astro_refs = build_astro_references(chart_facts, cited_ids, question)

    return {
        "answer": answer_text,
        "cited_fact_ids": cited_ids,
        "claims": claims,
        "astro_references": astro_refs,
    }


def build_astro_references(
    chart_facts: ChartFacts,
    cited_fact_ids: List[str],
    question: str = "",
) -> List[Dict[str, str]]:
    """
    Build rich, authentic Melooha-style astrological references with placement and psychological meaning.
    Matches the exact layout seen in real Melooha (Screenshot 5):
    e.g. 'Moon, house 2, Purva Shadha (birth chart): money anxiety reads as family weight'
    """
    q_lower = question.lower()
    is_career = any(w in q_lower for w in ["career", "job", "work", "gate", "intern", "exam", "office", "salary", "पैसा", "काम", "नौकरी"])
    is_rel = any(w in q_lower for w in ["friend", "trust", "love", "marry", "partner", "दोस्त", "मित्र", "शादी", "रिश्ते"])

    planets_map = {p.planet: p for p in chart_facts.planets}
    refs: List[Dict[str, str]] = []
    seen: set = set()

    meanings = {
        ("Sun", "career"): "authoritative leadership and system-building orientation",
        ("Sun", "rel"): "personal ego and expectations of respect in close dynamics",
        ("Moon", "career"): "intuitive adaptability and public service motivation",
        ("Moon", "rel"): "money anxiety reads as family weight; emotional security rooted in lineage",
        ("Mars", "career"): "competitive drive; excels only with undivided, clean execution",
        ("Mars", "rel"): "passionate directness that easily sparks friction if provoked",
        ("Mercury", "career"): "sharp intellect, data processing, and analytical clarity",
        ("Mercury", "rel"): "need for intellectual banter and mental rapport",
        ("Jupiter", "career"): "advisory, mentorship, and high-trust strategic guidance",
        ("Jupiter", "rel"): "generous loyalty and mutual philosophical expansion",
        ("Venus", "career"): "appreciation for elegant design, user experience, and aesthetic harmony",
        ("Venus", "rel"): "desire for warmth, tenderness, and aesthetic harmony in partnership",
        ("Saturn", "career"): "steady, grounded progression where disciplined patience outperforms haste",
        ("Saturn", "rel"): "friend or ally who corrects you realistically outlasts easy praisers",
        ("Rahu", "career"): "unconventional paths, technology, and breakthrough ambitions",
        ("Rahu", "rel"): "intense fascination that requires grounded reality checks",
        ("Ketu", "career"): "desire for deeper mastery behind the system rather than superficial titles",
        ("Ketu", "rel"): "warmest allies may drift first; inner detachment in outer circles",
    }

    for fid in cited_fact_ids:
        if fid in seen:
            continue
        fact = chart_facts.get_fact(fid)
        if not fact:
            continue

        seen.add(fid)
        category = fact.category.lower()
        subj = fact.subject

        if "lagna" in category or "lagna" in subj.lower():
            sign = chart_facts.lagna_sign or "Sidereal"
            deg = f" ({chart_facts.formatted_lagna_degree})" if chart_facts.formatted_lagna_degree else ""
            placement = f"{sign} Ascendant{deg}, house 1 (birth chart)"
            meaning = "core constitutional lens and foundational intellectual orientation"
            refs.append({"placement": placement, "meaning": meaning, "fact_id": fid})

        elif "dasha" in category or "dasha" in subj.lower():
            cd = chart_facts.current_dasha
            if cd:
                placement = f"{cd.mahadasha_lord}/{cd.antardasha_lord} antardasha, until {cd.end_date}"
                if is_career:
                    meaning = "active career window where disciplined effort yields tangible progress"
                elif is_rel:
                    meaning = "interpersonal cycle favoring bonds rooted in constructive honesty"
                else:
                    meaning = "active planetary cycle governing primary life focus and milestone timing"
            else:
                placement = "Active Vimshottari Dasha (birth chart)"
                meaning = "planetary time cycle directing milestone development"
            refs.append({"placement": placement, "meaning": meaning, "fact_id": fid})

        elif subj in planets_map:
            p = planets_map[subj]
            h_str = f", house {p.house}" if (chart_facts.time_known and p.house) else ""
            nak_str = f", {p.nakshatra.name}" if p.nakshatra else ""
            retro = " (retrograde)" if p.is_retrograde else ""
            placement = f"{p.planet}{h_str}{nak_str}{retro} (birth chart)"

            ctx = "career" if is_career else ("rel" if is_rel else "career")
            default_m = f"{p.planet} in {p.sign} directs personal agency and focus"
            meaning = meanings.get((p.planet, ctx), default_m)
            refs.append({"placement": placement, "meaning": meaning, "fact_id": fid})

        else:
            refs.append({
                "placement": f"{fact.subject} (birth chart)",
                "meaning": fact.text,
                "fact_id": fid,
            })

    return refs
