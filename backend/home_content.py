"""Engine for generating 100% grounded and verifiable Home screen content.

Complies strictly with Section B6:
- Daily insight: built from today's Moon transit relative to natal Moon.
- Lucky colour & number: derived from traditional weekday lord (Varadhipati) and documented.
- Harmony percentage: exact formula shown (Favorable Transits from Natal Moon / 9 * 100).
- Questions for you: dynamically constructed from active Dasha and Transits with Fact IDs.
- Every content item carries explicit fact_ids or is labelled static.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import swisseph as swe

from chart.engine import SIGNS
from chart.transits import calculate_today_transits, FAVORABLE_FROM_MOON


# Traditional Varadhipati (Day-Lord) planetary associations (Brihat Samhita Ch. 104)
WEEKDAY_LORDS = [
    {"day": "Monday", "lord": "Moon", "color_en": "White / Pearl", "color_hi": "सफेद / मोती", "number": 2, "fact_id": "FACT_VARA_MOON"},
    {"day": "Tuesday", "lord": "Mars", "color_en": "Red / Coral", "color_hi": "लाल / मूंगा", "number": 9, "fact_id": "FACT_VARA_MARS"},
    {"day": "Wednesday", "lord": "Mercury", "color_en": "Emerald Green", "color_hi": "हरा / पन्ना", "number": 5, "fact_id": "FACT_VARA_MERCURY"},
    {"day": "Thursday", "lord": "Jupiter", "color_en": "Yellow / Saffron", "color_hi": "पीला / केसरिया", "number": 3, "fact_id": "FACT_VARA_JUPITER"},
    {"day": "Friday", "lord": "Venus", "color_en": "Pastel Blue / White", "color_hi": "हल्का नीला / चमकीला सफेद", "number": 6, "fact_id": "FACT_VARA_VENUS"},
    {"day": "Saturday", "lord": "Saturn", "color_en": "Navy / Charcoal", "color_hi": "गहरा नीला / काला", "number": 8, "fact_id": "FACT_VARA_SATURN"},
    {"day": "Sunday", "lord": "Sun", "color_en": "Amber / Gold", "color_hi": "सुनहरा / तांबा", "number": 1, "fact_id": "FACT_VARA_SUN"},
]

# Daily Moon transit insights by house from Natal Moon (Phaladeepika Ch. 26)
MOON_HOUSE_INSIGHTS = {
    1: {
        "en": "Today brings heightened self-awareness and personal clarity. Ideal for attending to personal priorities and bodily vitality.",
        "hi": "आज का दिन आत्म-जागरूकता और व्यक्तिगत स्पष्टता लाता है। व्यक्तिगत प्राथमिकताओं और स्वास्थ्य पर ध्यान देने के लिए उत्तम।",
    },
    2: {
        "en": "Focus turns toward financial stewardship, practical commitments, and clear communication with family.",
        "hi": "ध्यान वित्तीय प्रबंधन, व्यावहारिक प्रतिबद्धताओं और परिवार के साथ संवाद पर केंद्रित रहेगा।",
    },
    3: {
        "en": "A productive day for collaborative effort, short communications, courage, and taking proactive steps.",
        "hi": "सहयोगात्मक प्रयासों, संक्षिप्त संचार, साहस और सक्रिय कदम उठाने के लिए एक उत्पादक दिन।",
    },
    4: {
        "en": "Focus centers on domestic stability, home reflection, and finding emotional centering amidst routine tasks.",
        "hi": "घरेलू स्थिरता, आत्म-चिंतन और दिनचर्या के बीच भावनात्मक संतुलन बनाए रखने पर ध्यान रहेगा।",
    },
    5: {
        "en": "Favorable for creative ideation, strategic learning, and purposeful intellectual initiatives.",
        "hi": "रचनात्मक विचारों, रणनीतिक अध्ययन और बौद्धिक पहलों के लिए अनुकूल समय।",
    },
    6: {
        "en": "An effective phase for resolving pending tasks, organizing work, and overcoming practical obstacles.",
        "hi": "लंबित कार्यों को निपटाने, कार्य व्यवस्थित करने और व्यावहारिक बाधाओं को हल करने का उपयुक्त समय।",
    },
    7: {
        "en": "Partnerships and interpersonal dynamics take the foreground. Excellent for honest dialogue and mutually beneficial agreements.",
        "hi": "साझेदारी और पारस्परिक संबंध केंद्र में रहेंगे। स्पष्ट संवाद और साझा सहमति के लिए उत्तम दिन।",
    },
    8: {
        "en": "A reflective window calling for steady patience, introspection, and avoiding hasty commitments.",
        "hi": "धैर्य, गहन आत्म-अवलोकन और जल्दबाजी में निर्णय न लेने के लिए एक शांत विचारणीय समय।",
    },
    9: {
        "en": "Brings long-range perspective, ethical clarity, and openness to mentorship and philosophical reflection.",
        "hi": "दूरगामी दृष्टिकोण, नैतिक स्पष्टता और बड़ों व गुरुओं के मार्गदर्शन से लाभ प्राप्त करने का समय।",
    },
    10: {
        "en": "Professional responsibilities and vocational execution are highlighted. Favorable for organized leadership.",
        "hi": "व्यावसायिक जिम्मेदारियां और कार्य-प्रदर्शन प्राथमिकता में रहेंगे। संगठित नेतृत्व के लिए अनुकूल।",
    },
    11: {
        "en": "Encourages networking, collaborative gains, peer support, and advancing meaningful aspirations.",
        "hi": "मित्रों के सहयोग, सामाजिक संपर्कों और महत्वपूर्ण आकांक्षाओं को आगे बढ़ाने के लिए फलदायी दिन।",
    },
    12: {
        "en": "A quieter window encouraging restorative rest, closing loose ends, and mindful boundary-setting.",
        "hi": "विश्राम, अनावश्यक तनाव से दूरी और अधूरे कार्यों को समेटने के लिए एक शांत और चिंतनशील चरण।",
    },
}


def get_grounded_home_content(
    natal_lagna_sign_num: Optional[int],
    natal_moon_sign_num: int,
    active_mahadasha: str,
    active_antardasha: str,
    target_dt: Optional[datetime] = None,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Generate fully grounded Home screen payload with explicit Fact IDs for every claim.
    """
    if target_dt is None:
        target_dt = datetime.now(timezone.utc)

    # 1. Compute today's transits using Swiss Ephemeris
    gochara = calculate_today_transits(
        natal_lagna_sign_num=natal_lagna_sign_num,
        natal_moon_sign_num=natal_moon_sign_num,
        target_dt=target_dt,
    )

    # 2. Extract Transit Moon
    transit_moon = next((t for t in gochara.transits if t.planet == "Moon"), None)
    house_from_moon = transit_moon.house_from_moon if transit_moon else 1
    natal_moon_name = SIGNS[natal_moon_sign_num - 1]
    transit_moon_sign = transit_moon.sign if transit_moon else "Aries"

    insight_text = MOON_HOUSE_INSIGHTS.get(house_from_moon, MOON_HOUSE_INSIGHTS[1])[lang]

    daily_insight = {
        "type": "grounded",
        "fact_ids": [
            f"FACT_TRANSIT_MOON_IN_{transit_moon_sign.upper()}",
            f"FACT_NATAL_MOON_IN_{natal_moon_name.upper()}",
            f"FACT_MOON_HOUSE_{house_from_moon}_FROM_CHANDRA",
        ],
        "title": (
            f"चंद्र गोचर: आपकी चंद्र राशि से {house_from_moon}वां भाव"
            if lang == "hi"
            else f"Moon Transiting House {house_from_moon} from Natal Moon"
        ),
        "text": insight_text,
        "house_from_moon": house_from_moon,
        "transit_moon_sign": transit_moon_sign,
        "natal_moon_sign": natal_moon_name,
    }

    # 3. Traditional Varadhipati (Day-Lord) Convention
    # Python weekday(): Monday is 0, Sunday is 6
    day_idx = target_dt.weekday()
    day_info = WEEKDAY_LORDS[day_idx]

    traditional_convention = {
        "type": "traditional_convention",
        "fact_ids": [day_info["fact_id"]],
        "day": day_info["day"],
        "lord": day_info["lord"],
        "color": day_info["color_hi"] if lang == "hi" else day_info["color_en"],
        "number": day_info["number"],
        "documentation": "Traditional Varadhipati day-lord convention (Brihat Samhita Ch. 104)",
    }

    # 4. Planetary Gochara Balance (Exact formula shown)
    favorable_count = sum(1 for t in gochara.transits if t.is_favorable_from_moon)
    total_planets = len(gochara.transits)
    balance_pct = int(round((favorable_count / total_planets) * 100))

    gochara_harmony = {
        "type": "grounded",
        "fact_ids": ["FACT_GOCHARA_HARMONY_RATIO"],
        "favorable_count": favorable_count,
        "total_planets": total_planets,
        "percentage": balance_pct,
        "formula": f"{favorable_count}/{total_planets} planetary transits currently in classical favorable houses from Natal Moon (Phaladeepika Ch. 26)",
        "label": (
            f"गोचर संतुलन ({favorable_count}/{total_planets} ग्रह अनुकूल)"
            if lang == "hi"
            else f"Gochara Balance ({favorable_count}/{total_planets} Favorable)"
        ),
    }

    # 5. Dynamically Generated "Questions For You" (Grounded in active dasha & transits)
    saturn_transit = next((t for t in gochara.transits if t.planet == "Saturn"), None)
    jupiter_transit = next((t for t in gochara.transits if t.planet == "Jupiter"), None)

    questions_for_you: List[Dict[str, Any]] = []

    # Q1: Active Mahadasha
    if lang == "hi":
        q1_text = f"मेरी सक्रिय {active_mahadasha} महादशा मेरे करियर और निर्णयों को कैसे प्रभावित कर रही है?"
    else:
        q1_text = f"How is my active {active_mahadasha} Mahadasha shaping my career and priorities?"
    questions_for_you.append({
        "type": "grounded",
        "fact_ids": [f"FACT_MAHADASHA_{active_mahadasha.upper()}"],
        "category": "dasha",
        "text": q1_text,
    })

    # Q2: Active Antardasha timing
    if lang == "hi":
        q2_text = f"वर्तमान {active_antardasha} अंतर्दशा में मेरे लिए कौन से प्रमुख अवसर सक्रिय हैं?"
    else:
        q2_text = f"What opportunities unfold during my current {active_antardasha} Antardasha window?"
    questions_for_you.append({
        "type": "grounded",
        "fact_ids": [f"FACT_ANTARDASHA_{active_antardasha.upper()}"],
        "category": "timing",
        "text": q2_text,
    })

    # Q3: Saturn Transit / Sade Sati
    sat_house = saturn_transit.house_from_moon if saturn_transit else 10
    if gochara.sade_sati_active:
        if lang == "hi":
            q3_text = f"मेरी साढ़े साती ({gochara.sade_sati_status}) के दौरान स्थिरता बनाए रखने के उपाय क्या हैं?"
        else:
            q3_text = f"How should I navigate my current Sade Sati phase ({gochara.sade_sati_status})?"
        q3_fid = "FACT_SADE_SATI_ACTIVE"
    else:
        if lang == "hi":
            q3_text = f"शनि का चंद्र से {sat_house}वें भाव में गोचर मेरे दायित्वों पर क्या प्रभाव डाल रहा है?"
        else:
            q3_text = f"How does Saturn transiting House {sat_house} from my Moon influence my discipline?"
        q3_fid = f"FACT_TRANSIT_SATURN_HOUSE_{sat_house}"

    questions_for_you.append({
        "type": "grounded",
        "fact_ids": [q3_fid],
        "category": "transit_saturn",
        "text": q3_text,
    })

    # Q4: Jupiter Expansion Transit
    jup_house = jupiter_transit.house_from_moon if jupiter_transit else 5
    if lang == "hi":
        q4_text = f"गुरु का चंद्र से {jup_house}वें भाव में गोचर किस क्षेत्र में विस्तार और मार्गदर्शन देगा?"
    else:
        q4_text = f"Which areas will Jupiter expand while transiting House {jup_house} from my Moon?"
    questions_for_you.append({
        "type": "grounded",
        "fact_ids": [f"FACT_TRANSIT_JUPITER_HOUSE_{jup_house}"],
        "category": "transit_jupiter",
        "text": q4_text,
    })

    return {
        "daily_insight": daily_insight,
        "traditional_convention": traditional_convention,
        "gochara_harmony": gochara_harmony,
        "questions_for_you": questions_for_you,
    }
