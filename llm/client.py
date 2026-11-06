"""Multi-provider LLM Client with Gemini primary, Groq fallback, circuit breaker, and retry."""

import json
import logging
import time
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple
import httpx
from pydantic import BaseModel

from backend.config import settings
from llm.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger("melooha.llm")
logger.setLevel(logging.INFO)


class AllProvidersFailedError(Exception):
    """Raised when both primary (Gemini) and fallback (Groq) providers fail."""
    def __init__(self, message: str, provider_errors: Dict[str, str]):
        super().__init__(message)
        self.user_friendly_message = (
            "The cosmic servers are experiencing high volume right now. "
            "Your question balance has been preserved. Please tap Retry to try again."
        )
        self.provider_errors = provider_errors


class LLMResponse(BaseModel):
    content: str
    provider: str
    duration_ms: float
    is_fallback: bool = False


class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", timeout_sec: float = 25.0):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.timeout = timeout_sec

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        models_to_try = [
            self.model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3.5-flash-lite",
        ]
        # Deduplicate while preserving order
        unique_models = []
        for m in models_to_try:
            if m and m not in unique_models:
                unique_models.append(m)

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        last_error = ""
        with httpx.Client(timeout=self.timeout) as client:
            for model_name in unique_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
                try:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            part = candidates[0].get("content", {}).get("parts", [{}])[0]
                            text = part.get("text", "")
                            if text:
                                return text
                    last_error = f"Gemini ({model_name}) returned status {resp.status_code}: {resp.text[:200]}"
                except Exception as e:
                    last_error = f"Gemini ({model_name}) error: {str(e)}"
                    continue

        raise RuntimeError(last_error or "All Gemini models failed")


class GroqProvider:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile", timeout_sec: float = 12.0):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model
        self.timeout = timeout_sec

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        # Automatically detect xAI Grok vs Groq Cloud
        if self.api_key.startswith("xai-"):
            url = "https://api.x.ai/v1/chat/completions"
            model = "grok-2-latest" if self.model == "llama-3.3-70b-versatile" else self.model
        else:
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API returned status {resp.status_code}: {resp.text}")

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Groq returned empty choices")

            content = choices[0].get("message", {}).get("content", "")
            return content


class DemoAstrologyProvider:
    """Offline deterministic provider that generates grounded Vedic readings when no API keys are configured or external providers fail."""

    def generate(self, prompt: str, system_prompt: str) -> str:
        import re

        # Extract user question and name
        question = ""
        if "USER QUESTION:" in prompt:
            parts = prompt.split("USER QUESTION:")
            question = parts[1].split('"""')[0].split("\n\n")[0].strip(' "\n')

        user_name = "Friend"
        m_name = re.search(r"USER NAME:\s*([^\n\r]+)", prompt)
        if m_name:
            cand = m_name.group(1).strip()
            if cand and cand != "Seeker":
                user_name = cand

        q_lower = question.lower()
        is_hindi = bool(re.search(r"[\u0900-\u097F]", question))
        is_remedies = any(w in q_lower for w in ["उपाय", "शांति", "संतुलित", "संतुलन", "ऊर्जा", "दोष", "निवारण", "मंत्र", "दान", "रत्न", "remedy", "remedies", "balance"])
        is_career = any(w in q_lower for w in ["career", "job", "work", "profession", "business", "money", "finances", "success", "exam", "vocation", "strongest", "promotion", "field", "income", "wealth", "calling", "fit", "करियर", "नौकरी", "व्यापार", "व्यवसाय", "काम", "पेशा", "धन", "सफलता", "क्षेत्र"])
        is_relationship = any(w in q_lower for w in ["love", "marriage", "marry", "married", "wedding", "partner", "relationship", "spouse", "dating", "husband", "wife", "match", "विवाह", "शादी", "प्रेम", "जीवनसाथी", "संबंध", "पार्टनर", "पति", "पत्नी"])
        is_timing = any(w in q_lower for w in ["when", "timing", "period", "future", "date", "year", "time", "months", "age", "कब", "समय", "अवधि", "वर्ष", "भविष्य", "दिन"])

        # Parse facts from prompt text
        facts = {}
        for line in prompt.split("\n"):
            line = line.strip()
            m = re.match(r"^\[?(F\d+)\]?[\s:|\-\(]+(.*)$", line)
            if m:
                fid = m.group(1)
                facts[fid] = line

        # Check if birth time was known
        time_known = False
        if "F01" in facts:
            f01_text = facts["F01"]
            if "UNAVAILABLE" not in f01_text.upper() and "not provided" not in f01_text.lower():
                time_known = True

        SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

        def get_sign(text: str) -> Optional[str]:
            for s in SIGNS:
                if re.search(rf"\b{s}\b", text):
                    return s
            return None

        def get_house(text: str) -> Optional[int]:
            if not time_known:
                return None
            m = re.search(r"\bHouse\s+(\d{1,2})\b", text)
            if m:
                return int(m.group(1))
            return None

        def get_dasha_details(text: str) -> Tuple[str, str, str]:
            m_maha = re.search(r"Mahadasha:\s*([A-Za-z]+)", text)
            m_antar = re.search(r"Antardasha:\s*([A-Za-z]+)", text)
            m_dates = re.search(r"\((\d{4}-\d{2}-\d{2}\s+to\s+\d{4}-\d{2}-\d{2})\)", text)
            maha = m_maha.group(1) if m_maha else "Active"
            antar = m_antar.group(1) if m_antar else "Current"
            dates = m_dates.group(1) if m_dates else "current cycle"
            return maha, antar, dates

        cited_ids = []
        paragraphs = []

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
            HINDI_HOUSES = {
                1: "प्रथम भाव (लग्न)", 2: "द्वितीय भाव", 3: "तृतीय भाव", 4: "चतुर्थ भाव",
                5: "पंचम भाव", 6: "षष्ठ भाव", 7: "सप्तम भाव", 8: "अष्टम भाव",
                9: "नवम भाव", 10: "दशम भाव", 11: "एकादश भाव", 12: "द्वादश भाव"
            }

            lagna_sign = None
            paragraphs.append(f"नमस्ते {user_name},")
            if time_known and "F01" in facts:
                lagna_sign = get_sign(facts["F01"])
                hi_lagna = HINDI_SIGNS.get(lagna_sign, lagna_sign)
                paragraphs.append(
                    f"### ज्योतिषीय आधार\n"
                    f"आपके इस महत्वपूर्ण प्रश्न पर आपके जन्म चक्र का ध्यानपूर्वक अध्ययन करने के बाद, मैं आपके साथ यह व्यक्तिगत मार्गदर्शन साझा कर रहा हूँ। "
                    f"आपकी कुंडली **{hi_lagna} लग्न (प्रथम भाव) [F01]** पर आधारित है, जो यह दर्शाती है कि आपकी आंतरिक ऊर्जा, विचारशीलता और जीवन में सही निर्णय लेने की क्षमता स्वाभाविक रूप से सुदृढ़ है।"
                )
                cited_ids.append("F01")
            else:
                paragraphs.append(
                    "### ज्योतिषीय आधार\n"
                    "आपके प्रश्न का आदर करते हुए, चूँकि आपका सटीक जन्म समय उपलब्ध नहीं है, इसलिए अनुचित भविष्यवाणियों से बचने के लिए भावों और लग्न की गणना आरक्षित रखी गई है। "
                    "हम आपके मुख्य ग्रहों, राशियों और सक्रिय महादशा के आधार पर यह व्यक्तिगत विश्लेषण प्रस्तुत कर रहे हैं।"
                )

            sun_text = facts.get("F03", "")
            moon_text = facts.get("F04", "")
            sat_text = facts.get("F09", "")
            merc_text = facts.get("F06", "")
            jup_text = facts.get("F07", "")
            ven_text = facts.get("F08", "")

            sun_sign = get_sign(sun_text) or "Leo"
            moon_sign = get_sign(moon_text) or "Aries"
            sat_sign = get_sign(sat_text) or "Capricorn"

            hi_sun_sign = HINDI_SIGNS.get(sun_sign, sun_sign)
            hi_moon_sign = HINDI_SIGNS.get(moon_sign, moon_sign)
            hi_sat_sign = HINDI_SIGNS.get(sat_sign, sat_sign)

            sun_house = get_house(sun_text)
            moon_house = get_house(moon_text)
            sat_house = get_house(sat_text)

            if is_remedies:
                paragraphs.append("### ऊर्जा संतुलन एवं वैदिक उपाय")
                paragraphs.append(
                    "आपकी कुंडली में ऊर्जा को संतुलित और संरेखित करने के लिए ग्रहों के आधार पर यह प्रमुख सात्विक उपाय अत्यंत प्रभावशाली हैं। "
                    "जब आप अपनी आंतरिक ऊर्जा को ग्रहों के अनुकूल ढालते हैं, तो जीवन में स्पष्टता और संतुलन स्वतः स्थापित होता है।"
                )

                paragraphs.append("### प्रमुख ग्रह प्रभाव एवं सात्विक उपाय")
                drivers = []
                if "F03" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(sun_house, f'भाव {sun_house}')}" if (time_known and sun_house) else ""
                    drivers.append(
                        f"- **सूर्य की तेज ऊर्जा [F03]**: सूर्य **{hi_sun_sign} राशि में**{h_str} स्थित है। "
                        f"आत्मविश्वास, जीवनशक्ति और नेतृत्व ऊर्जा को संतुलित रखने के लिए प्रातःकाल तांबे के पात्र से सूर्य को जल अर्पित करें और 'ॐ सूर्याय नमः' का 11 बार स्मरण करें।"
                    )
                    cited_ids.append("F03")

                if "F04" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(moon_house, f'भाव {moon_house}')}" if (time_known and moon_house) else ""
                    drivers.append(
                        f"- **चन्द्रमा की मानसिक शांति [F04]**: चन्द्र **{hi_moon_sign} राशि में**{h_str} मन और भावनाओं का कारक है। "
                        f"भावनात्मक संतुलन और शांत चित्त के लिए नियमित रूप से 10 मिनट ध्यान करें तथा माँ अथवा मातृ-तुल्य स्त्रियों का आशीर्वाद लें।"
                    )
                    cited_ids.append("F04")

                if "F09" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(sat_house, f'भाव {sat_house}')}" if (time_known and sat_house) else ""
                    drivers.append(
                        f"- **शनि की कर्म शुद्धि [F09]**: शनि **{hi_sat_sign} राशि में**{h_str} अनुशासन और धैर्य का प्रतीक है। "
                        f"अपने कर्म में ईमानदारी बनाए रखें, शनिवार को जरूरतमंदों की सहायता करें अथवा पीपल के वृक्ष के समीप दीप प्रज्वलित करें।"
                    )
                    cited_ids.append("F09")

                paragraphs.append("\n".join(drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    hi_maha = HINDI_PLANETS.get(maha, maha)
                    hi_antar = HINDI_PLANETS.get(antar, antar)
                    paragraphs.append(
                        f"### सक्रिय महादशा प्रभाव [F12]\n"
                        f"वर्तमान में आप **{hi_maha} महादशा** एवं **{hi_antar} अंतर्दशा** ({dates}) के प्रभाव में हैं। "
                        f"इस समयावधि में सात्विक जीवनशैली, नियमित योग और संतुलित आहार आपके ऊर्जा चक्रों को सशक्त बनाए रखेगा।"
                    )
                    cited_ids.append("F12")

                paragraphs.append(
                    "### व्यावहारिक दिशा-निर्देश\n"
                    "- **प्रातःकालीन सूर्य वंदन**: सकारात्मक ऊर्जा के साथ दिन की शुरुआत करें।\n"
                    "- **संतुलित दिनचर्या**: कार्य और विश्राम के बीच संतुलन स्थापित करें।\n"
                    "- **कर्म शुद्धि**: अपनी वाणी में मधुरता और दूसरों के प्रति सम्मान बनाए रखें।"
                )

            elif is_career:
                paragraphs.append("### प्रत्यक्ष उत्तर एवं सर्वोत्तम कार्यक्षेत्र")
                ref_sign = lagna_sign or sun_sign
                if ref_sign in ["Aries", "Leo", "Sagittarius"]:
                    hi_domains = "रणनीतिक नेतृत्व, तकनीकी प्रबंधन, उद्यमिता एवं प्रशासनिक दायित्व"
                elif ref_sign in ["Taurus", "Virgo", "Capricorn"]:
                    hi_domains = "डेटा एनालिटिक्स, वित्तीय प्रणालियाँ, संरचनात्मक संचालन एवं तकनीकी इंजीनियरिंग"
                elif ref_sign in ["Gemini", "Libra", "Aquarius"]:
                    hi_domains = "उत्पाद प्रबंधन, नवाचार रणनीति, संचार, मीडिया एवं परामर्श सेवाएं"
                else:
                    hi_domains = "अनुसंधान, परामर्श, शिक्षा, स्वास्थ्य सेवा नवाचार एवं संस्थागत विकास"

                basis_parts = []
                if time_known and lagna_sign:
                    basis_parts.append(f"**{hi_lagna} लग्न [F01]**")
                if "F03" in facts:
                    basis_parts.append(f"**सूर्य {hi_sun_sign} राशि में [F03]**")
                    if "F03" not in cited_ids:
                        cited_ids.append("F03")

                basis_text = " तथा ".join(basis_parts) if basis_parts else "ग्रहों की स्थिति"

                paragraphs.append(
                    f"आपकी जन्म कुंडली में {basis_text} के आधार पर, आपके लिए सबसे अनुकूल क्षेत्र **{hi_domains}** हैं। "
                    f"आप उन भूमिकाओं में सर्वाधिक सफल होते हैं जहाँ आपको स्वतंत्र निर्णय लेने और दीर्घकालिक व्यवस्था निर्माण का अवसर प्राप्त हो।"
                )

                paragraphs.append("### प्रमुख ग्रह प्रभाव")
                drivers = []
                if "F03" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(sun_house, f'भाव {sun_house}')}" if (time_known and sun_house) else ""
                    drivers.append(
                        f"- **सूर्य का अधिकार क्षेत्र [F03]**: सूर्य **{hi_sun_sign} राशि में**{h_str} स्थित है। "
                        f"यह आपके भीतर स्वाभाविक नेतृत्व क्षमता, निर्णय लेने का साहस और सामाजिक मान-प्रतिष्ठा प्रदान करता है।"
                    )
                    if "F03" not in cited_ids:
                        cited_ids.append("F03")

                if "F09" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(sat_house, f'भाव {sat_house}')}" if (time_known and sat_house) else ""
                    drivers.append(
                        f"- **शनि का कर्म आधार [F09]**: शनि **{hi_sat_sign} राशि में**{h_str} स्थित है। "
                        f"कर्म के अधिपति के रूप में शनि निरंतर अभ्यास, धैर्य और अनुशासन से दीर्घकालिक प्रगति सुनिश्चित करता है।"
                    )
                    if "F09" not in cited_ids:
                        cited_ids.append("F09")

                if "F06" in facts:
                    merc_sign = get_sign(merc_text) or "Gemini"
                    hi_merc_sign = HINDI_SIGNS.get(merc_sign, merc_sign)
                    merc_house = get_house(merc_text)
                    h_str = f" एवं {HINDI_HOUSES.get(merc_house, f'भाव {merc_house}')}" if (time_known and merc_house) else ""
                    drivers.append(
                        f"- **बुध का बौद्धिक विवेक [F06]**: बुध **{hi_merc_sign} राशि में**{h_str} स्थित होकर तीक्ष्ण विश्लेषणात्मक क्षमता और व्यापारिक दूरदर्शिता प्रदान करता है।"
                    )
                    if "F06" not in cited_ids:
                        cited_ids.append("F06")

                paragraphs.append("\n".join(drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    hi_maha = HINDI_PLANETS.get(maha, maha)
                    hi_antar = HINDI_PLANETS.get(antar, antar)
                    paragraphs.append(
                        f"### करियर समय चक्र एवं महादशा [F12]\n"
                        f"वर्तमान में आप **{hi_maha} महादशा** एवं **{hi_antar} अंतर्दशा** ({dates}) के प्रभाव में हैं। "
                        f"यह समयावधि अपनी कार्यकुशलता को निखारने और करियर में नई ऊंचाइयाँ प्राप्त करने के लिए अनुकूल है।"
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### व्यावहारिक मार्गदर्शन\n"
                    "- **मुख्य कौशल में निपुणता**: अपनी विशेषज्ञता को निरंतर विस्तार दें।\n"
                    "- **धैर्य और निरंतरता**: तात्कालिक सफलता के स्थान पर सुदृढ़ नींव तैयार करें।"
                )

            elif is_relationship:
                paragraphs.append("### संबंध एवं साझेदारी सामंजस्य")
                ven_sign = get_sign(ven_text) or "Taurus"
                hi_ven_sign = HINDI_SIGNS.get(ven_sign, ven_sign)
                ven_house = get_house(ven_text)

                paragraphs.append(
                    f"आपकी कुंडली में **शुक्र {hi_ven_sign} राशि में [F08]** एवं **चन्द्र {hi_moon_sign} राशि में [F04]** स्थित होकर "
                    f"परस्पर सम्मान, भावनात्मक सच्चाई और सौहार्दपूर्ण साझेदारी को आधार बनाते हैं।"
                )
                if "F08" not in cited_ids and "F08" in facts:
                    cited_ids.append("F08")
                if "F04" not in cited_ids and "F04" in facts:
                    cited_ids.append("F04")

                paragraphs.append("### प्रमुख ग्रह प्रभाव")
                drivers = []
                if "F08" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(ven_house, f'भाव {ven_house}')}" if (time_known and ven_house) else ""
                    drivers.append(
                        f"- **शुक्र का प्रेम एवं सामंजस्य [F08]**: शुक्र **{hi_ven_sign} राशि में**{h_str} स्थित है। "
                        f"यह संबंधों में आदर, कोमलता और भावनात्मक संतुलन की आवश्यकता को दर्शाता है।"
                    )
                if "F04" in facts:
                    h_str = f" एवं {HINDI_HOUSES.get(moon_house, f'भाव {moon_house}')}" if (time_known and moon_house) else ""
                    drivers.append(
                        f"- **चन्द्रमा का भावनात्मक आधार [F04]**: चन्द्र **{hi_moon_sign} राशि में**{h_str} मन की शांति और आत्मीय सुरक्षा को निर्देशित करता है।"
                    )
                paragraphs.append("\n".join(drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    hi_maha = HINDI_PLANETS.get(maha, maha)
                    hi_antar = HINDI_PLANETS.get(antar, antar)
                    paragraphs.append(
                        f"### संबंध समय चक्र एवं दशा [F12]\n"
                        f"आपकी सक्रिय **{hi_maha} महादशा** और **{hi_antar} अंतर्दशा** ({dates}) भावनात्मक परिपक्वता का अवसर प्रदान करती है।"
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### व्यावहारिक मार्गदर्शन\n"
                    "- **खुला संवाद रखें**: अपनी भावनाओं और अपेक्षाओं को स्पष्टता से साझा करें।\n"
                    "- **पारस्परिक सहयोग**: एक-दूसरे की व्यक्तिगत स्वतंत्रता का सम्मान करते हुए साझा लक्ष्य बनाएं।"
                )

            elif is_timing:
                paragraphs.append("### ज्योतिषीय समय चक्र एवं दशा प्रभाव")
                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    hi_maha = HINDI_PLANETS.get(maha, maha)
                    hi_antar = HINDI_PLANETS.get(antar, antar)
                    paragraphs.append(
                        f"आपका मुख्य समय चक्र **{hi_maha} महादशा** एवं **{hi_antar} अंतर्दशा** [F12] द्वारा संचालित है, जो {dates} तक सक्रिय है। "
                        f"वैदिक ज्योतिष में विंशोत्तरी दशा जीवन के इस अध्याय की प्राथमिक प्राथमिकताओं और विकास को इंगित करती है।"
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### व्यावहारिक योजना\n"
                    "- **दशा अनुसार कार्य**: महत्वपूर्ण निर्णयों को अनुकूल ग्रह दशा के साथ संरेखित करें।\n"
                    "- **तैयारी और संयम**: प्रमुख अवसरों के लिए पूर्व-तैयारी पर ध्यान दें।"
                )

            else:
                paragraphs.append("### ग्रह गोचर एवं समग्र विश्लेषण")
                paragraphs.append(
                    f"आपकी जन्म कुंडली में **सूर्य {hi_sun_sign} राशि में [F03]** और **चन्द्र {hi_moon_sign} राशि में [F04]** स्थित होकर "
                    f"आत्मबल और भावनात्मक विवेक का संतुलित सामंजस्य स्थापित करते हैं।"
                )
                if "F03" in facts and "F03" not in cited_ids:
                    cited_ids.append("F03")
                if "F04" in facts and "F04" not in cited_ids:
                    cited_ids.append("F04")

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    hi_maha = HINDI_PLANETS.get(maha, maha)
                    hi_antar = HINDI_PLANETS.get(antar, antar)
                    paragraphs.append(
                        f"### सक्रिय ग्रह दशा [F12]\n"
                        f"वर्तमान में **{hi_maha} महादशा** एवं **{hi_antar} अंतर्दशा** ({dates}) चल रही है।"
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### व्यावहारिक सुझाव\n"
                    "- **दैनिक संतुलन बनाए रखें**: नियमित रूप से ध्यान और सात्विक दिनचर्या अपनाएं।"
                )

            paragraphs.append("\n*नोट: वैदिक ज्योतिष आत्म-जागरूकता और सचेत निर्णय लेने के लिए प्रतीकात्मक मार्गदर्शन प्रस्तुत करता है, न कि कोई भाग्यवादी निश्चितता।*")

        else:
            # English Generation Path
            lagna_sign = None
            paragraphs.append(f"Namaste {user_name},")
            if time_known and "F01" in facts:
                lagna_sign = get_sign(facts["F01"])
                paragraphs.append(
                    f"I hear your question with care and dedication. Looking closely into your personal birth chart, "
                    f"your life journey is anchored by **{lagna_sign or 'computed'} Lagna in House 1 [F01]**. "
                    f"This ascendant gives you a natural inner compass, intellectual discernment, and the patience to navigate life with conscious strength."
                )
                cited_ids.append("F01")
            else:
                paragraphs.append(
                    f"I appreciate your question. As your exact birth time was not provided, house boundaries and exact Ascendant are strictly reserved to prevent ungrounded predictions. "
                    f"We examine your core planetary signs, nakshatras, and planetary periods (Dasha) to provide grounded cosmic guidance."
                )

            # 2. Domain Analysis
            if is_career:
                paragraphs.append("### Direct Answer & Best-Fit Career Path")
                sun_text = facts.get("F03", "")
                sat_text = facts.get("F09", "")
                merc_text = facts.get("F06", "")
                jup_text = facts.get("F07", "")

                sun_sign = get_sign(sun_text) or "Taurus"
                sat_sign = get_sign(sat_text) or "Capricorn"
                sun_house = get_house(sun_text)
                sat_house = get_house(sat_text)

                primary_basis = []
                if time_known and lagna_sign:
                    primary_basis.append(f"**{lagna_sign} Lagna [F01]**")
                if "F03" in facts:
                    primary_basis.append(f"**Sun in {sun_sign} [F03]**")
                    if "F03" not in cited_ids:
                        cited_ids.append("F03")
                if "F09" in facts and not primary_basis:
                    primary_basis.append(f"**Saturn in {sat_sign} [F09]**")
                    if "F09" not in cited_ids:
                        cited_ids.append("F09")

                basis_str = " and ".join(primary_basis) if primary_basis else "your planetary alignment"

                ref_sign = lagna_sign or sun_sign
                if ref_sign in ["Aries", "Leo", "Sagittarius"]:
                    domains = "Executive Leadership, Technology Strategy, Entrepreneurial Operations, and Strategic Administration"
                elif ref_sign in ["Taurus", "Virgo", "Capricorn"]:
                    domains = "Strategic Analytics, Systems Architecture, Finance, Structured Operations, and Enterprise Engineering"
                elif ref_sign in ["Gemini", "Libra", "Aquarius"]:
                    domains = "Product Management, Strategic Advisory, Innovation Strategy, Communications, and Scalable Technology"
                else:
                    domains = "Advisory Consulting, Specialized Research, Healthcare Innovation, Creative Strategy, and People Leadership"

                paragraphs.append(
                    f"Based on {basis_str}, your strongest natural career alignment is in **{domains}**. "
                    f"You excel where you hold structural ownership, intellectual autonomy, and the agency to build enduring, scalable results."
                )

                paragraphs.append("### Key Astrological Drivers")
                drivers = []
                if "F03" in facts:
                    h_str = f" in House {sun_house}" if (time_known and sun_house) else ""
                    drivers.append(
                        f"- **Sun's Authority [F03]**: Placed in **{sun_sign}{h_str}**, the Sun governs professional recognition, inner conviction, and leadership. "
                        f"This placement signals that you perform at your best with executive clarity and decision-making independence."
                    )
                    if "F03" not in cited_ids:
                        cited_ids.append("F03")

                if "F09" in facts:
                    h_str = f" in House {sat_house}" if (time_known and sat_house) else ""
                    drivers.append(
                        f"- **Saturn's Vocational Foundation [F09]**: Positioned in **{sat_sign}{h_str}**, Saturn acts as your vocational anchor, governing discipline, patience, and long-term mastery. "
                        f"It indicates that your professional stature builds steadily through systematic execution and cumulative experience."
                    )
                    if "F09" not in cited_ids:
                        cited_ids.append("F09")

                if "F06" in facts:
                    merc_sign = get_sign(merc_text) or "Gemini"
                    merc_house = get_house(merc_text)
                    h_str = f" in House {merc_house}" if (time_known and merc_house) else ""
                    drivers.append(
                        f"- **Mercury's Intellect & Strategy [F06]**: Placed in **{merc_sign}{h_str}**, Mercury fuels sharp analytical discrimination, strategic negotiation, and commercial problem-solving."
                    )
                    if "F06" not in cited_ids:
                        cited_ids.append("F06")
                elif "F07" in facts:
                    jup_sign = get_sign(jup_text) or "Sagittarius"
                    jup_house = get_house(jup_text)
                    h_str = f" in House {jup_house}" if (time_known and jup_house) else ""
                    drivers.append(
                        f"- **Jupiter's Wisdom & Expansion [F07]**: Located in **{jup_sign}{h_str}**, Jupiter confers higher vision, ethical discernment, and mentorship capacity."
                    )
                    if "F07" not in cited_ids:
                        cited_ids.append("F07")

                paragraphs.append("\n".join(drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    paragraphs.append(
                        f"### Career Timing & Active Dasha Window [F12]\n"
                        f"You are actively navigating the **{maha} Mahadasha** and **{antar} Antardasha** ({dates}). "
                        f"This planetary cycle opens favorable timing for consolidating your expertise, establishing domain authority, and preparing for strategic career expansion."
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### Strategic Actionable Guidance\n"
                    "- **Consolidate High-Leverage Skills**: Focus on cultivating rare and valuable expertise that bridges strategic vision with systematic implementation.\n"
                    "- **Cultivate Long-Term Alliances**: Align with mentors and collaborators who respect substantive competence and reliability.\n"
                    "- **Embrace Compound Progression**: Let Saturn's disciplined cadence work in your favor—steadfast consistency will outperform short-term expedience."
                )

            elif is_relationship:
                paragraphs.append("### Relational Harmony & Partnership Dynamics")
                ven_text = facts.get("F08", "")
                moon_text = facts.get("F04", "")
                ven_sign = get_sign(ven_text) or "Taurus"
                moon_sign = get_sign(moon_text) or "Cancer"
                ven_house = get_house(ven_text)
                moon_house = get_house(moon_text)

                paragraphs.append(
                    f"Your relational blueprint is anchored by **Venus in {ven_sign} [F08]** and **Moon in {moon_sign} [F04]**. "
                    f"You approach close partnerships with a deep need for mutual respect, emotional authenticity, and intellectual compatibility."
                )
                if "F08" not in cited_ids and "F08" in facts:
                    cited_ids.append("F08")
                if "F04" not in cited_ids and "F04" in facts:
                    cited_ids.append("F04")

                paragraphs.append("### Key Relational Significators")
                rel_drivers = []
                if "F08" in facts:
                    h_str = f" in House {ven_house}" if (time_known and ven_house) else ""
                    rel_drivers.append(
                        f"- **Venus Harmony [F08]**: Placed in **{ven_sign}{h_str}**, Venus represents how you express affection and value harmony. "
                        f"It indicates that balance, transparent appreciation, and shared aesthetic values are essential for lasting fulfillment."
                    )
                if "F04" in facts:
                    h_str = f" in House {moon_house}" if (time_known and moon_house) else ""
                    rel_drivers.append(
                        f"- **Moon's Emotional Anchor [F04]**: Located in **{moon_sign}{h_str}**, the Moon shapes your instinctual response and emotional security in deep bonds."
                    )
                    if "F02" in facts and "F02" not in cited_ids:
                        cited_ids.append("F02")
                paragraphs.append("\n".join(rel_drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    paragraphs.append(
                        f"### Partnership Timing & Active Dasha Window [F12]\n"
                        f"Your active **{maha} Mahadasha** and **{antar} Antardasha** ({dates}) highlight an important chapter for deepening emotional bonds and establishing balanced commitments."
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### Strategic Actionable Guidance\n"
                    "- **Prioritize Transparent Communication**: Express your emotional expectations clearly and invite vulnerable reciprocity.\n"
                    "- **Foster Shared Growth**: Build partnerships that allow both individuals independent agency while cultivating common goals."
                )

            elif is_timing:
                paragraphs.append("### Planetary Timing & Active Windows")
                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    paragraphs.append(
                        f"Your primary astrological timing is governed by the **{maha} Mahadasha** and **{antar} Antardasha** [F12], active from {dates}. "
                        f"In Vedic astrology, this Vimshottari cycle indicates the primary evolutionary themes and karmic focus of your current chapter."
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append("### Supporting Planetary Influences")
                drivers = []
                if "F07" in facts:
                    jup_text = facts["F07"]
                    jup_sign = get_sign(jup_text) or "Sagittarius"
                    jup_house = get_house(jup_text)
                    h_str = f" in House {jup_house}" if (time_known and jup_house) else ""
                    drivers.append(f"- **Jupiter's Expansion [F07]**: Placed in **{jup_sign}{h_str}**, Jupiter signals opportune windows for education, mentorship, and expansive progress.")
                    if "F07" not in cited_ids:
                        cited_ids.append("F07")
                if "F09" in facts:
                    sat_text = facts["F09"]
                    sat_sign = get_sign(sat_text) or "Capricorn"
                    sat_house = get_house(sat_text)
                    h_str = f" in House {sat_house}" if (time_known and sat_house) else ""
                    drivers.append(f"- **Saturn's Endurance [F09]**: Placed in **{sat_sign}{h_str}**, Saturn ensures that efforts invested now create lasting structural stability.")
                    if "F09" not in cited_ids:
                        cited_ids.append("F09")
                paragraphs.append("\n".join(drivers))

                paragraphs.append(
                    "### Actionable Roadmap\n"
                    "- **Align Milestones with Active Dasha**: Initiate important transitions during periods ruled by favorable planetary lords.\n"
                    "- **Cultivate Patience**: Use preparatory timing windows to build foundation before major public launches."
                )

            else:
                # General / Cosmic Overview
                paragraphs.append("### Planetary Alignment Overview")
                moon_text = facts.get("F04", "")
                sun_text = facts.get("F03", "")
                moon_sign = get_sign(moon_text) or "Taurus"
                sun_sign = get_sign(sun_text) or "Aries"
                moon_house = get_house(moon_text)
                sun_house = get_house(sun_text)

                paragraphs.append(
                    f"Your birth chart reflects a purposeful balance between inward consciousness and outward agency, "
                    f"anchored by **Sun in {sun_sign} [F03]** and **Moon in {moon_sign} [F04]**."
                )
                if "F03" not in cited_ids and "F03" in facts:
                    cited_ids.append("F03")
                if "F04" not in cited_ids and "F04" in facts:
                    cited_ids.append("F04")

                paragraphs.append("### Core Astrological Influences")
                drivers = []
                if "F03" in facts:
                    h_str = f" in House {sun_house}" if (time_known and sun_house) else ""
                    drivers.append(f"- **Sun's Vitality [F03]**: Sun in **{sun_sign}{h_str}** shapes your outward purpose, vitality, and willpower.")
                if "F04" in facts:
                    h_str = f" in House {moon_house}" if (time_known and moon_house) else ""
                    drivers.append(f"- **Moon's Perception [F04]**: Moon in **{moon_sign}{h_str}** governs intuitive intelligence, emotional calm, and inner resilience.")
                paragraphs.append("\n".join(drivers))

                if "F12" in facts:
                    maha, antar, dates = get_dasha_details(facts["F12"])
                    paragraphs.append(
                        f"### Current Planetary Cycle [F12]\n"
                        f"You are navigating the **{maha} Mahadasha** and **{antar} Antardasha** ({dates}), highlighting personal growth and clarity."
                    )
                    if "F12" not in cited_ids:
                        cited_ids.append("F12")

                paragraphs.append(
                    "### Strategic Actionable Guidance\n"
                    "- **Maintain Daily Equilibrium**: Anchor your daily routine around practices that harmonize mind and focused action.\n"
                    "- **Honor Your Constitutional Baseline**: Make conscious decisions aligned with your natural strengths."
                )

        paragraphs.append("\n*Note: Vedic astrology offers symbolic timing and self-awareness to support conscious decision-making rather than fatalistic certainty.*")

        answer_text = "\n\n".join(paragraphs)
        astro_refs = []
        for fid in cited_ids:
            txt = facts.get(fid, "")
            placement_str = txt.split(":")[1].strip() if ":" in txt else (txt.split(" in ")[0] if " in " in txt else txt[:35])
            if "birth chart" not in placement_str.lower():
                placement_str = f"{placement_str} (birth chart)"
            astro_refs.append({
                "placement": placement_str,
                "meaning": "planetary grounding and active karmic development",
                "fact_id": fid
            })

        return json.dumps({
            "answer": answer_text,
            "cited_fact_ids": cited_ids,
            "astro_references": astro_refs,
            "claims": [{"claim": "Grounded chart analysis", "fact_id": fid} for fid in cited_ids],
        }, ensure_ascii=False)


class ModelOrchestrator:
    """
    Manages provider failover: Gemini (Primary) -> Groq (Fallback).
    Includes circuit breakers, timeouts, retries with backoff, and logging.
    """
    def __init__(
        self,
        gemini_provider: Optional[GeminiProvider] = None,
        groq_provider: Optional[GroqProvider] = None,
        circuit_failure_threshold: int = 3,
        circuit_recovery_seconds: float = 60.0,
    ):
        self.gemini = gemini_provider or GeminiProvider()
        self.groq = groq_provider or GroqProvider()
        self.gemini_circuit = CircuitBreaker(
            "gemini",
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_seconds,
        )
        self.groq_circuit = CircuitBreaker(
            "groq",
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_seconds,
        )

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """
        Execute provider chain:
        1. If no API keys are set in environment, seamlessly serve reading via Grounded Vedic Demo Engine.
        2. Try Gemini if circuit allows.
        3. If Gemini fails or circuit is open, failover to Groq.
        4. If both fail, raise AllProvidersFailedError with friendly message.
        """
        gemini_key = getattr(self.gemini, "api_key", None)
        groq_key = getattr(self.groq, "api_key", None)
        has_gemini_key = bool(gemini_key and not str(gemini_key).startswith("your_"))
        has_groq_key = bool(groq_key and not str(groq_key).startswith("your_"))
        is_mock = "Mock" in type(self.gemini).__name__ or "Mock" in type(self.groq).__name__

        if not is_mock and not has_gemini_key and not has_groq_key and getattr(settings, "ENABLE_OFFLINE_DEMO", True):
            logger.info("No LLM API keys configured in .env. Serving reading via Grounded Vedic Demo Engine.")
            demo = DemoAstrologyProvider()
            raw_json = demo.generate(prompt=prompt, system_prompt=system_prompt)
            return LLMResponse(
                content=raw_json,
                provider="vedic_engine (demo)",
                duration_ms=15.0,
                is_fallback=False,
            )

        provider_errors: Dict[str, str] = {}

        # 1. Primary: Gemini
        if self.gemini_circuit.allow_request():
            start_t = time.time()
            try:
                logger.info("Calling primary provider: Gemini")
                raw_text = self.gemini.generate(prompt=prompt, system_prompt=system_prompt)
                dur = (time.time() - start_t) * 1000.0
                self.gemini_circuit.record_success()
                logger.info(f"Gemini succeeded in {dur:.1f}ms")
                return LLMResponse(
                    content=raw_text,
                    provider="gemini",
                    duration_ms=round(dur, 2),
                    is_fallback=False,
                )
            except Exception as e:
                dur = (time.time() - start_t) * 1000.0
                self.gemini_circuit.record_failure()
                err_msg = str(e)
                provider_errors["gemini"] = err_msg
                logger.warning(f"Gemini call failed ({dur:.1f}ms): {err_msg}. Triggering fallback to Groq.")
        else:
            provider_errors["gemini"] = f"Gemini circuit breaker is OPEN (tripped)."
            logger.warning("Gemini circuit breaker is OPEN; skipping Gemini.")

        # 2. Fallback: Groq
        if self.groq_circuit.allow_request():
            start_t = time.time()
            try:
                logger.info("Calling fallback provider: Groq")
                raw_text = self.groq.generate(prompt=prompt, system_prompt=system_prompt)
                dur = (time.time() - start_t) * 1000.0
                self.groq_circuit.record_success()
                logger.info(f"Groq fallback succeeded in {dur:.1f}ms")
                return LLMResponse(
                    content=raw_text,
                    provider="groq",
                    duration_ms=round(dur, 2),
                    is_fallback=True,
                )
            except Exception as e:
                dur = (time.time() - start_t) * 1000.0
                self.groq_circuit.record_failure()
                err_msg = str(e)
                provider_errors["groq"] = err_msg
                logger.error(f"Groq fallback failed ({dur:.1f}ms): {err_msg}")
        else:
            provider_errors["groq"] = "Groq circuit breaker is OPEN."
            logger.error("Groq circuit breaker is OPEN.")

        # Both failed
        if not is_mock and getattr(settings, "ENABLE_OFFLINE_DEMO", True):
            logger.info("External providers failed at runtime. Serving reading via Grounded Vedic Engine fallback.")
            demo = DemoAstrologyProvider()
            raw_json = demo.generate(prompt=prompt, system_prompt=system_prompt)
            return LLMResponse(
                content=raw_json,
                provider="vedic_engine (safe fallback)",
                duration_ms=10.0,
                is_fallback=True,
            )

        raise AllProvidersFailedError(
            message="Both Gemini and Groq model providers failed.",
            provider_errors=provider_errors,
        )
