import React, { useState, useMemo } from "react";
import {
  Heart,
  Users,
  UserCheck,
  BookOpen,
  Sparkles,
  Diamond,
  Briefcase,
  Compass,
  Lock,
  ArrowRight,
  ShieldCheck,
  X,
  FileText,
  Flame,
  Award,
  Crown,
  Scale,
  Landmark,
  Coins,
} from "lucide-react";
import { t } from "../i18n";

export default function ReportsView({
  user,
  profile,
  profiles = [],
  chartFacts,
  balance,
  lang = "en",
  onOpenPaywall,
  onSelectQuestion,
  onOpenOnboarding,
}) {
  const [selectedReport, setSelectedReport] = useState(null);
  const [showReportPaywall, setShowReportPaywall] = useState(false);
  const [reportsUnlocked, setReportsUnlocked] = useState(() => {
    try {
      return localStorage.getItem(`melooha_reports_unlocked_${user?.id}`) === "true";
    } catch (_) {
      return false;
    }
  });
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);

  const handleUnlockReports = () => {
    setReportsUnlocked(true);
    setPurchaseSuccess(true);
    try {
      localStorage.setItem(`melooha_reports_unlocked_${user?.id}`, "true");
    } catch (_) {}
    setTimeout(() => {
      setPurchaseSuccess(false);
      setShowReportPaywall(false);
    }, 1800);
  };

  // Dynamic astrological placements from chartFacts
  const lagna = chartFacts?.lagna_sign || chartFacts?.lagna?.sign || "Aries";
  const moon = chartFacts?.planets?.find((p) => p.planet === "Moon")?.sign || "Taurus";
  const venus = chartFacts?.planets?.find((p) => p.planet === "Venus")?.sign || "Gemini";
  const jupiter = chartFacts?.planets?.find((p) => p.planet === "Jupiter")?.sign || "Leo";
  const saturn = chartFacts?.planets?.find((p) => p.planet === "Saturn")?.sign || "Aquarius";
  const mahadasha = chartFacts?.current_dasha?.mahadasha_lord || "Venus";

  // Categories & Report Items (Exact matches to real Melooha app screenshots)
  const reportCategories = [
    {
      id: "love",
      title: lang === "hi" ? "प्रेम एवं विवाह" : "Love and Marriage",
      reports: [
        {
          id: "love_style",
          title: lang === "hi" ? "लव स्टाइल" : "Love Style",
          icon: Heart,
          badge: null,
          summary: `Governed by natal Venus in ${venus} and your 7th house axis. Indicates an affectionate, thoughtful expression in intimate bonds.`,
          detail: `Your chart shows Venus placed in ${venus}. In relationships, you value authentic connection, intellectual dialogue, and emotional transparency. You are naturally considerate of your partner's needs, though you need mutual respect and personal freedom to thrive.`,
          evidence: `Venus in ${venus} • Moon in ${moon}`,
          prompt: "What does my Venus placement reveal about my subconscious love style?",
        },
        {
          id: "marriage",
          title: lang === "hi" ? "विवाह समय" : "Marriage",
          icon: Heart,
          badge: "Trending",
          summary: `Analysis of the 7th house and D9 Navamsha. Highlights auspicious timing windows and partner characteristics.`,
          detail: `The 7th lord and Jupiter transit influence your marriage timing. Your ${mahadasha} Mahadasha cycle activates life stabilization, indicating significant partnership milestones during periods of Jupiter aspecting your natal 7th house.`,
          evidence: `7th House from ${lagna} • Active ${mahadasha} Dasha`,
          prompt: "When does my chart indicate auspicious timing for marriage?",
        },
        {
          id: "ideal_partner",
          title: lang === "hi" ? "आदर्श जीवनसाथी" : "Ideal Partner",
          icon: UserCheck,
          badge: null,
          summary: `Qualities, mental temperament, and spiritual alignment of your compatible counterpart.`,
          detail: `Based on your D1 Lagna and 7th house lord, your ideal partner is someone with strong inner purpose, emotional maturity, and an appreciative nature. They balance your analytical tendencies with grounding presence.`,
          evidence: `7th House Karaka • D9 Navamsha Harmony`,
          prompt: "What personality traits will my ideal life partner possess according to Vedic astrology?",
        },
        {
          id: "love_or_arrange",
          title: lang === "hi" ? "लव या अरेंज" : "Love or Arrange",
          icon: Heart,
          badge: "New",
          summary: `Evaluating 5th house (romance) vs 9th/7th houses (traditional union) connection.`,
          detail: `Your 5th lord connection with the 7th house suggests opportunities for romantic self-choice, supported warmly by family blessings. Personal affinity plays the primary role before formal familial ceremonies.`,
          evidence: `5th Lord connection to 7th House • Rahu/Venus axis`,
          prompt: "Does my birth chart favor a love marriage or an arranged marriage?",
        },
        {
          id: "spouse",
          title: lang === "hi" ? "जीवनसाथी का स्वभाव" : "Spouse",
          icon: BookOpen,
          badge: null,
          summary: `Professional domain, background, and demeanor of your future spouse.`,
          detail: `The placement of Jupiter and Venus in your horoscope indicates a spouse who is professionally dedicated, culturally rooted, and intellectually sharp. Mutual support in financial and home life will be strong.`,
          evidence: `Jupiter Karaka • Venus in ${venus}`,
          prompt: "What will be the career and personality background of my spouse?",
        },
        {
          id: "in_laws",
          title: lang === "hi" ? "ससुराल पक्ष" : "In-Laws",
          icon: Users,
          badge: null,
          summary: `The 8th house analysis representing family of spouse and ancestral harmony.`,
          detail: `The 8th house from your ${lagna} ascendant indicates a respectful, cultured in-law relationship. Maintaining clear boundary communication during early marriage establishes lasting mutual goodwill.`,
          evidence: `8th House alignment from ${lagna}`,
          prompt: "How will my relationship with my in-laws be according to my horoscope?",
        },
      ],
    },
    {
      id: "money",
      title: lang === "hi" ? "धन एवं समृद्धि" : "Money",
      reports: [
        {
          id: "billionaire_potential",
          title: lang === "hi" ? "अरबपति योग" : "Billionaire Potential",
          icon: Diamond,
          badge: "Popular",
          summary: `Dhana Yogas, 2nd house (accumulated wealth) and 11th house (gains) evaluation.`,
          detail: `Your horoscope contains favorable Dhana Yogas formed by the lords of wealth and gains. Wealth accumulation accelerates significantly during your ${mahadasha} dasha, particularly through enterprise, equity, and strategic long-term investments.`,
          evidence: `2nd House of Wealth • 11th House of High Gains`,
          prompt: "What Dhana Yogas exist in my chart for extraordinary wealth creation?",
        },
        {
          id: "wealth",
          title: lang === "hi" ? "धन संचय" : "Wealth",
          icon: Coins,
          badge: null,
          summary: `Liquid savings, asset growth curves, and auspicious asset acquisition phases.`,
          detail: `With Jupiter and Mercury influencing your wealth houses, your financial trajectory is steady and cumulative. Avoid impulsive speculative ventures during Saturn retrogrades; focus on real estate and compounding assets.`,
          evidence: `Jupiter Aspect • 2nd House Lord Placement`,
          prompt: "Which investment avenues will yield the greatest financial stability for me?",
        },
        {
          id: "property",
          title: lang === "hi" ? "भूमि एवं वाहन" : "Property & Assets",
          icon: Landmark,
          badge: null,
          summary: `4th house strength for owning real estate, vehicles, and landed property.`,
          detail: `The 4th house from ${lagna} governs fixed assets. Mars and Venus aspects indicate successful property acquisition, with peak purchasing windows emerging over the next 2-3 years.`,
          evidence: `4th House of Real Estate • Mars & Venus strength`,
          prompt: "When does my chart favor purchasing a home or landed property?",
        },
      ],
    },
    {
      id: "work",
      title: lang === "hi" ? "कार्य एवं करियर" : "Work",
      reports: [
        {
          id: "career_path",
          title: lang === "hi" ? "करियर दिशा" : "Career Path",
          icon: Briefcase,
          badge: null,
          summary: `10th house Karma Bhava analysis, optimal industries, and leadership phases.`,
          detail: `Your 10th house is energized by strong planetary aspects. Roles involving strategic leadership, creative technology, advisory, or independent authority align best with your planetary strengths.`,
          evidence: `10th House Karma Bhava from ${lagna}`,
          prompt: "What is my optimal career field and leadership direction according to my Kundli?",
        },
        {
          id: "business_vs_job",
          title: lang === "hi" ? "व्यवसाय बनाम नौकरी" : "Business vs Job",
          icon: Scale,
          badge: null,
          summary: `6th house (service) vs 7th/10th houses (independent enterprise) comparison.`,
          detail: `Your chart shows that while service jobs provided a crucial foundational training ground, your long-term destiny strongly favors autonomous enterprise, consultancy, or partnership businesses.`,
          evidence: `6th vs 7th House Lord Strength`,
          prompt: "Am I better suited for independent entrepreneurship or a corporate job?",
        },
        {
          id: "leadership",
          title: lang === "hi" ? "नेतृत्व शैली" : "Leadership Style",
          icon: Crown,
          badge: null,
          summary: `Sun and Mars authority metrics for commanding teams and public influence.`,
          detail: `The Sun and Mars placements grant executive instinct and high perseverance. You lead best by setting clear visionary standards while empowering team members with operational autonomy.`,
          evidence: `Sun & Mars Authority Index`,
          prompt: "How can I maximize my authority and executive impact at work?",
        },
      ],
    },
  ];

  return (
    <div className="space-y-6 pb-52 max-w-md mx-auto px-4 pt-3 relative">
      {/* Background Starfield Accent */}
      <div className="absolute inset-0 pointer-events-none select-none overflow-hidden opacity-40 -z-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <circle cx="20%" cy="15%" r="1" fill="#FFFFFF" />
          <circle cx="85%" cy="25%" r="1.5" fill="#FDE68A" />
          <circle cx="15%" cy="60%" r="1.2" fill="#F4B8DC" />
          <circle cx="75%" cy="70%" r="1" fill="#FFFFFF" />
        </svg>
      </div>

      {/* Categories & 3-Column Report Cards */}
      {reportCategories.map((cat) => (
        <div key={cat.id} className="space-y-3.5">
          {/* Melooha Winged Category Divider Pill */}
          <div className="flex items-center justify-center gap-3 py-1">
            <div className="h-[1px] w-12 bg-gradient-to-r from-transparent via-[#782855] to-[#B21E68]/60" />
            <span className="px-4 py-1 rounded-full bg-[#1A0E2A]/90 border border-[#4A163B] text-xs font-serif font-bold text-[#F4B8DC] shadow-sm tracking-wide">
              {cat.title}
            </span>
            <div className="h-[1px] w-12 bg-gradient-to-l from-transparent via-[#782855] to-[#B21E68]/60" />
          </div>

          {/* 3-Column Grid matching real Melooha app */}
          <div className="grid grid-cols-3 gap-2.5">
            {cat.reports.map((report) => {
              const Icon = report.icon;
              return (
                <button
                  key={report.id}
                  onClick={() => setSelectedReport(report)}
                  className="p-3.5 rounded-2xl bg-[#180F2A]/90 hover:bg-[#251540] border border-[#3A1B4E]/80 hover:border-[#B21E68] transition-all flex flex-col items-center justify-between min-h-[105px] text-center relative group active:scale-95 shadow-lg overflow-hidden"
                >
                  {/* Trending / New Badge */}
                  {report.badge && (
                    <span
                      className={`absolute top-1.5 right-1.5 text-[8.5px] font-bold px-1.5 py-0.2 rounded-full ${
                        report.badge === "Trending"
                          ? "bg-rose-500/30 text-rose-300 border border-rose-500/40"
                          : "bg-amber-500/30 text-[#FDE68A] border border-amber-500/40"
                      }`}
                    >
                      {report.badge}
                    </span>
                  )}

                  {/* Icon with soft pink tint */}
                  <div className="w-10 h-10 rounded-xl bg-[#231238] flex items-center justify-center text-[#F4B8DC] group-hover:scale-110 transition-transform mt-1">
                    <Icon className="w-5 h-5 text-[#F4B8DC]" />
                  </div>

                  {/* Label */}
                  <span className="text-[11px] font-medium text-[#E8E2F5] leading-tight line-clamp-2 px-0.5 group-hover:text-white transition-colors">
                    {report.title}
                  </span>

                  {/* Lock Indicator in bottom right */}
                  <div className="absolute bottom-1.5 right-2 opacity-50 group-hover:opacity-90 transition-opacity">
                    <Lock className="w-2.5 h-2.5 text-[#A299BC]" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      {/* Floating Bottom Report Status Dock (Elevated cleanly above the center Ask button) */}
      <div className="fixed bottom-[102px] left-0 right-0 z-30 px-4 pointer-events-none">
        <div className="max-w-md mx-auto pointer-events-auto">
          <div className="p-2.5 pl-4 pr-2 rounded-full bg-[#150924]/95 backdrop-blur-2xl border border-[#5A1C46] shadow-[0_12px_36px_rgba(0,0,0,0.95),0_0_20px_rgba(178,30,104,0.35)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full bg-rose-500/25 border border-rose-500/40 text-[9.5px] font-bold text-rose-300 uppercase tracking-wider animate-pulse">
                90% OFF
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-sm font-extrabold text-white">₹499</span>
                <span className="text-[11px] text-[#A299BC] line-through">₹4,999</span>
              </div>
            </div>

            <button
              onClick={() => setShowReportPaywall(true)}
              className="py-2 px-5 rounded-full bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white text-xs font-bold shadow-md hover:brightness-110 active:scale-95 transition-all"
            >
              {reportsUnlocked
                ? lang === "hi" ? "पूर्ण रिपोर्ट अनलॉक है" : "Reports Unlocked ✓"
                : lang === "hi" ? "पूर्ण रिपोर्ट खरीदें" : "Buy Full Report"}
            </button>
          </div>
        </div>
      </div>

      {/* Full Detailed Report Modal with Formatted & Indented Text Area */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="crystal-card p-5 max-w-sm w-full max-h-[85vh] flex flex-col space-y-4 relative border border-[#B21E68]/60 shadow-2xl">
            {/* Close Button */}
            <button
              onClick={() => setSelectedReport(null)}
              className="absolute top-3.5 right-3.5 w-7 h-7 rounded-full bg-[#200E30] text-[#A299BC] hover:text-white flex items-center justify-center transition-colors z-20"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header */}
            <div className="flex items-center gap-3 pt-1 shrink-0">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] flex items-center justify-center text-white shadow-md shrink-0">
                <selectedReport.icon className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-[#E5A93C] tracking-wider block">
                  Vedic Horoscope Report
                </span>
                <h3 className="font-serif text-lg font-bold text-white leading-tight">
                  {selectedReport.title}
                </h3>
              </div>
            </div>

            {/* Scrollable, Formatted & Indented Report Content */}
            <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 text-xs custom-scrollbar">
              {/* Summary Pill Box */}
              <div className="p-3 rounded-xl bg-[#140828] border border-[#2B1745] space-y-1">
                <span className="text-[10px] text-[#A299BC] font-medium block">
                  Astrological Foundation
                </span>
                <p className="text-xs text-[#EAE3F7] leading-relaxed">
                  {selectedReport.summary}
                </p>
              </div>

              {/* Formatted & Indented Astrological Sections */}
              <div className="space-y-3">
                {/* 1. Root Planetary Alignment */}
                <div className="space-y-1">
                  <h4 className="text-[11.5px] font-bold text-[#F4B8DC] flex items-center gap-1.5">
                    <span className="text-[#E5A93C] text-[10px]">✦</span>
                    <span>Natal Chart Grounding</span>
                  </h4>
                  <div className="pl-3.5 border-l-2 border-[#B21E68]/40 py-0.5">
                    <p className="text-xs text-[#DDD5EE] leading-relaxed">
                      {selectedReport.detail}
                    </p>
                  </div>
                </div>

                {/* 2. Key Planetary Indicators */}
                <div className="space-y-1">
                  <h4 className="text-[11.5px] font-bold text-[#F4B8DC] flex items-center gap-1.5">
                    <span className="text-[#E5A93C] text-[10px]">✦</span>
                    <span>Active Planetary Karakas</span>
                  </h4>
                  <div className="pl-3.5 border-l-2 border-[#B21E68]/40 py-0.5 space-y-1 text-xs text-[#DDD5EE]">
                    <div className="flex items-center gap-2">
                      <span className="text-[#A299BC]">Governing Sign:</span>
                      <strong className="text-white">{lagna} Ascendant</strong>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[#A299BC]">Active Dasha Window:</span>
                      <strong className="text-[#FDE68A]">{mahadasha} Mahadasha</strong>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[#A299BC]">Key Placement:</span>
                      <strong className="text-[#F4B8DC]">{selectedReport.evidence}</strong>
                    </div>
                  </div>
                </div>

                {/* 3. Actionable Vedic Reflection */}
                <div className="space-y-1">
                  <h4 className="text-[11.5px] font-bold text-[#F4B8DC] flex items-center gap-1.5">
                    <span className="text-[#E5A93C] text-[10px]">✦</span>
                    <span>Self-Reflection & Guidance</span>
                  </h4>
                  <div className="pl-3.5 border-l-2 border-[#E5A93C]/40 py-0.5">
                    <p className="text-xs text-[#DDD5EE] leading-relaxed">
                      This period invites deeper alignment with your natal strengths. Focus on conscious choices rather than passive prediction.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Modal Actions (Never overlapping content) */}
            <div className="pt-2 space-y-2 shrink-0 border-t border-[#2A1640]">
              <button
                onClick={() => {
                  const prompt = selectedReport.prompt;
                  setSelectedReport(null);
                  if (onSelectQuestion) onSelectQuestion(prompt);
                }}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all"
              >
                <span>{lang === "hi" ? "इस विषय पर प्रश्न पूछें" : "Ask About This Topic"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setSelectedReport(null)}
                className="w-full py-1.5 rounded-xl text-xs text-[#A299BC] hover:text-white transition-colors"
              >
                {lang === "hi" ? "वापस जाएं" : "Close"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dedicated Report Paywall Modal (90% OFF Offer) */}
      {showReportPaywall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
          <div className="crystal-card p-6 max-w-sm w-full relative border border-[#B21E68]/70 shadow-2xl space-y-4">
            {/* Close Button */}
            <button
              onClick={() => setShowReportPaywall(false)}
              className="absolute top-3.5 right-3.5 w-7 h-7 rounded-full bg-[#200E30] text-[#A299BC] hover:text-white flex items-center justify-center transition-colors z-20"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Glowing Offer Header */}
            <div className="text-center pt-2 space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#931B58] to-[#D8227E] flex items-center justify-center text-white mx-auto shadow-lg shadow-[#B21E68]/40">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="px-3 py-0.5 rounded-full bg-rose-500/25 border border-rose-500/40 text-[10px] font-bold text-rose-300 uppercase tracking-wider inline-block">
                  Festive Special • 90% OFF
                </span>
                <h3 className="font-serif text-xl font-bold text-white mt-1.5 leading-tight">
                  Personalized Life Kundali Report
                </h3>
                <p className="text-xs text-[#C5B9DF] mt-1">
                  Comprehensive 45+ Page Vedic Guide for {profile?.name || "You"}
                </p>
              </div>
            </div>

            {/* Price Badge */}
            <div className="p-3 rounded-2xl bg-[#170C28] border border-[#3E1A48] flex items-center justify-between">
              <div>
                <span className="text-[10px] text-[#A299BC] block font-medium">One-Time Lifetime Access</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-white">₹499</span>
                  <span className="text-xs text-[#A299BC] line-through">₹4,999</span>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-[11px] font-bold text-emerald-300">
                Save ₹4,500
              </span>
            </div>

            {/* Included Features */}
            <div className="space-y-2 text-xs text-[#DDD5EE]">
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-[#E5A93C] shrink-0 mt-0.5" />
                <span><strong>12 Domain Reports:</strong> Love, Wealth, Career, Health & Family</span>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-[#E5A93C] shrink-0 mt-0.5" />
                <span><strong>10-Year Mahadasha Timeline:</strong> Key milestones & favorable dates</span>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-[#E5A93C] shrink-0 mt-0.5" />
                <span><strong>Remedial Astrology:</strong> Saturn Sade Sati cures & gemstones</span>
              </div>
            </div>

            {/* Success State or Action CTA */}
            {purchaseSuccess ? (
              <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/60 text-center space-y-1 animate-in zoom-in-95">
                <span className="text-sm font-bold text-emerald-300 block">✨ All Reports Unlocked!</span>
                <span className="text-[11px] text-emerald-200 block">Enjoy full access to your personalized life readings.</span>
              </div>
            ) : (
              <button
                onClick={handleUnlockReports}
                className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white text-sm font-bold shadow-lg shadow-[#B21E68]/40 hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
              >
                <span>Unlock Full Report (Demo ₹499)</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}

            <p className="text-[10px] text-center text-[#8E82AA]">
              100% money-back guarantee • Instant digital in-app access
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
