import React, { useState } from "react";
import { Compass, Sparkles, Clock, Shield, Moon, Printer, Download, X, FileText, CheckCircle2 } from "lucide-react";
import KundliChart, { NORTH_HOUSES, PLANET_SHORT } from "../components/KundliChart";
import DashaTimeline from "../components/DashaTimeline";
import TransitsCard from "../components/TransitsCard";
import { t } from "../i18n";

export default function ChartView({ chartFacts, profile, lang = "en", onSelectQuestion }) {
  const [activeSegment, setActiveSegment] = useState("chart"); // "chart" | "dasha" | "transits"
  const [showPrintModal, setShowPrintModal] = useState(false);

  const segments = [
    { id: "chart", label: lang === "hi" ? "कुंडली चक्र" : "Kundli Chart" },
    { id: "dasha", label: lang === "hi" ? "दशा चक्र" : "Dasha" },
    { id: "transits", label: lang === "hi" ? "गोचर आज" : "Transits" },
  ];

  const moonPlanet = chartFacts?.planets?.find((p) => p.planet === "Moon");
  const activeName = profile?.name || "Melooha Member";
  const lagnaNum = chartFacts?.lagna_sign_number || 1;
  const timeKnown = chartFacts?.time_known;

  const planetsByHouse = {};
  for (let h = 1; h <= 12; h++) {
    planetsByHouse[h] = [];
  }
  chartFacts?.planets?.forEach((p) => {
    if (p.house && p.house >= 1 && p.house <= 12) {
      planetsByHouse[p.house].push(p);
    }
  });

  const getSignNumForHouse = (h) => {
    return ((lagnaNum - 1 + (h - 1)) % 12) + 1;
  };

  return (
    <div className="pb-28 max-w-md mx-auto px-4 pt-3">
      {/* Main Screen Interface (Hidden when printing so it never bleeds into PDF) */}
      <div className="chart-view-main space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between no-print">
          <div>
            <span className="text-[10px] font-bold text-[#E5A93C] uppercase tracking-wider block">
              {lang === "hi" ? "वैदिक जन्म पत्रिका" : "Vedic Birth Horary"}
            </span>
            <h2 className="font-serif text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-[#E5A93C]" />
              <span>{lang === "hi" ? "कुंडली एवं समय चक्र" : "Chart & Planetary Cycles"}</span>
            </h2>
          </div>

          {/* 1-Click Print / PDF Export Button */}
          <button
            onClick={() => setShowPrintModal(true)}
            className="px-2.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/20 to-[#B21E68]/30 border border-[#E5A93C]/40 hover:border-[#E5A93C] text-[#FDE68A] text-xs font-semibold flex items-center gap-1.5 shadow-sm active:scale-95 transition-all"
            title="Print or Save PDF Kundli Dossier"
          >
            <Printer className="w-3.5 h-3.5 text-[#E5A93C]" />
            <span>{lang === "hi" ? "प्रिंट / PDF" : "Print PDF"}</span>
          </button>
        </div>

        {/* Segmented Control */}
        <div className="grid grid-cols-3 p-1 rounded-2xl bg-[#140C28] border border-[#2B1B47]">
          {segments.map((seg) => {
            const isActive = activeSegment === seg.id;
            return (
              <button
                key={seg.id}
                onClick={() => setActiveSegment(seg.id)}
                className={`min-h-[40px] rounded-xl text-xs font-bold transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white shadow-md cosmic-glow"
                    : "text-[#A299BC] hover:text-white"
                }`}
              >
                {seg.label}
              </button>
            );
          })}
        </div>

        {/* Classical Vedic Placements Summary Banner */}
        {chartFacts && (
          <div className="crystal-card p-3.5 space-y-2">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl astro-badge">
                <span className="text-[#8478A0] block text-[10px] font-medium">{t("ascendantLagna", lang)}</span>
                <span className="font-bold text-white text-xs mt-0.5 block truncate">
                  {chartFacts.lagna_sign || chartFacts.lagna?.sign || (chartFacts.time_known ? "Aries" : t("unavailable", lang))}
                  {chartFacts.formatted_lagna_degree ? ` (${chartFacts.formatted_lagna_degree})` : ""}
                </span>
              </div>
              <div className="p-2.5 rounded-xl astro-badge">
                <span className="text-[#8478A0] block text-[10px] font-medium">{t("moonNakshatra", lang)}</span>
                <span className="font-bold text-white text-xs mt-0.5 block truncate">
                  {chartFacts.planets?.find((p) => p.planet === "Moon")?.nakshatra?.name || "Moon"}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Segment Content */}
        {activeSegment === "chart" && chartFacts && (
          <div className="space-y-3 animate-in fade-in duration-200">
            <KundliChart
              chartFacts={chartFacts}
              lang={lang}
              onSelectHouseQuestion={onSelectQuestion}
            />
          </div>
        )}

        {activeSegment === "dasha" && (
          <div className="space-y-3 animate-in fade-in duration-200">
            <DashaTimeline
              chartFacts={chartFacts}
              currentDasha={chartFacts?.current_dasha}
              allMahadashas={chartFacts?.all_dashas || chartFacts?.all_mahadashas || []}
              lang={lang}
              onSelectDashaQuestion={onSelectQuestion}
            />
          </div>
        )}

        {activeSegment === "transits" && (
          <div className="space-y-3 animate-in fade-in duration-200">
            <TransitsCard
              profile={profile}
              birthProfileId={profile?.id}
              chartFacts={chartFacts}
              lang={lang}
              onSelectTransitQuestion={onSelectQuestion}
            />
          </div>
        )}
      </div>

      {/* Printable PDF Kundli Dossier Modal */}
      {showPrintModal && (
        <div className="print-modal-overlay fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
          <div className="print-modal-container bg-[#140C24] border border-[#5A1C46] rounded-3xl max-w-lg w-full max-h-[92vh] overflow-y-auto shadow-2xl space-y-4 p-5 relative">
            {/* Modal Controls Bar (Hidden during actual print) */}
            <div className="flex items-center justify-between pb-3 border-b border-[#2C1948] no-print sticky top-0 bg-[#140C24] z-20">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#E5A93C]" />
                <h3 className="font-serif text-base font-bold text-white">
                  {lang === "hi" ? "वैदिक पत्रिका दस्तावेज़ (PDF)" : "Vedic Horoscope Dossier"}
                </h3>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-[#931B58] to-[#E5A93C] text-white text-xs font-bold shadow-md hover:brightness-110 active:scale-95 flex items-center gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>{lang === "hi" ? "प्रिंट / PDF सहेजें" : "Print / Save PDF"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setShowPrintModal(false)}
                  className="p-1.5 rounded-xl bg-[#251540] hover:bg-[#351C5A] text-[#A299BC] hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Print Dossier Document Body (Strict 2-Page Structure) */}
            <div id="print-dossier-root" className="print-dossier space-y-6 text-xs">
              {/* ================= PAGE 1: Visual Diagrammatic Kundli Chart & Native Details ================= */}
              <div className="print-page print-page-1 space-y-3.5">
                {/* Document Header */}
                <div className="text-center space-y-1 pb-2 border-b border-[#3D1E60]">
                  <div className="flex items-center justify-center gap-2 font-serif text-lg font-bold text-[#F5C842]">
                    <span>✦ MELOOHA VEDIC ASTROLOGY ✦</span>
                  </div>
                  <p className="text-[11px] font-mono text-[#DDD5EE]">
                    Mathematically Grounded via Swiss Ephemeris • Lahiri Sidereal Zodiac
                  </p>
                </div>

                {/* Native Personal Details Box */}
                <div className="grid grid-cols-2 gap-2.5 p-3.5 rounded-2xl bg-[#1A0D30] border border-[#482075] text-[#EDE9FE]">
                  <div>
                    <span className="text-[9.5px] text-[#A299BC] block uppercase font-mono tracking-wider">Native Name</span>
                    <strong className="text-white text-base font-serif block">{activeName}</strong>
                  </div>
                  <div>
                    <span className="text-[9.5px] text-[#A299BC] block uppercase font-mono tracking-wider">Ascendant (Lagna)</span>
                    <strong className="text-[#F5C842] text-sm font-bold block">
                      {chartFacts?.lagna_sign} ({chartFacts?.formatted_lagna_degree || "00°00'"})
                    </strong>
                  </div>
                  <div>
                    <span className="text-[9.5px] text-[#A299BC] block uppercase font-mono tracking-wider">Birth Date & Time</span>
                    <span className="text-white font-medium block">
                      {profile?.birth_date || "Recorded"} • {profile?.birth_time || "Solar Noon"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9.5px] text-[#A299BC] block uppercase font-mono tracking-wider">Moon Nakshatra</span>
                    <span className="text-[#F4B8DC] font-bold block">
                      {moonPlanet?.nakshatra?.name || "Moon"} (Pada {moonPlanet?.nakshatra?.pada || 1})
                    </span>
                  </div>
                  <div className="col-span-2 pt-1.5 border-t border-[#341858]">
                    <span className="text-[9.5px] text-[#A299BC] block uppercase font-mono tracking-wider">Birth Location</span>
                    <span className="text-white font-medium block">{profile?.place_name || "India"}</span>
                  </div>
                </div>

                {/* Visual Diagrammatic Kundli Chart (North Indian SVG Diamond) */}
                <div className="space-y-2 flex flex-col items-center">
                  <span className="text-[11px] uppercase font-bold text-[#F5C842] tracking-wider block text-center">
                    Visual Kundli Chart (D1 Rashi)
                  </span>

                  <div className="w-[310px] aspect-square rounded-2xl border-2 border-[#582A8E] bg-[#120824] p-1.5 flex items-center justify-center shadow-md">
                    <svg viewBox="0 0 400 400" className="w-full h-full select-none">
                      {/* Outer boundary */}
                      <rect x="2" y="2" width="396" height="396" fill="#120824" stroke="#4C3073" strokeWidth="2.5" rx="6" />

                      {/* 12 House Polygons */}
                      {NORTH_HOUSES.map((house) => {
                        const signNum = getSignNumForHouse(house.id);
                        const planets = planetsByHouse[house.id] || [];
                        const isLagnaHouse = house.id === 1;

                        return (
                          <g key={house.id}>
                            <polygon
                              points={house.points}
                              fill={isLagnaHouse ? "#221035" : "#160A2B"}
                              stroke="#4D2577"
                              strokeWidth="1.2"
                            />

                            {/* Sign Number */}
                            {timeKnown && (
                              <text
                                x={house.labelPos.x}
                                y={house.labelPos.y}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fill="#CBB6E8"
                                fontSize="12"
                                fontWeight="bold"
                                fontFamily="monospace"
                              >
                                {signNum}
                              </text>
                            )}

                            {/* Occupying Planets */}
                            {planets.length > 0 && (
                              <g>
                                {planets.map((p, pIdx) => {
                                  const count = planets.length;
                                  const offset = (pIdx - (count - 1) / 2) * 14;
                                  return (
                                    <text
                                      key={p.planet}
                                      x={house.center.x}
                                      y={house.center.y + offset + (timeKnown ? 3 : 0)}
                                      textAnchor="middle"
                                      dominantBaseline="middle"
                                      fill="#F5C842"
                                      fontSize="12.5"
                                      fontWeight="bold"
                                      fontFamily="sans-serif"
                                    >
                                      {PLANET_SHORT[p.planet] || p.planet.slice(0, 2)}
                                      {p.is_retrograde && "®"}
                                    </text>
                                  );
                                })}
                              </g>
                            )}

                            {/* Lagna Tag */}
                            {isLagnaHouse && timeKnown && (
                              <text
                                x={house.center.x}
                                y={house.center.y - 18}
                                textAnchor="middle"
                                fill="#E5A93C"
                                fontSize="10"
                                fontWeight="bold"
                              >
                                ASC
                              </text>
                            )}
                          </g>
                        );
                      })}

                      {/* Center Bindu */}
                      <circle cx="200" cy="200" r="3.5" fill="#E5A93C" />
                    </svg>
                  </div>
                </div>

                {/* Page 1 Footer */}
                <div className="pt-2 text-center text-[10px] text-[#A299BC] border-t border-[#341858]">
                  ✦ Page 1 of 2 • Visual Kundli Chart & Native Birth Details ✦
                </div>
              </div>

              {/* ================= PAGE 2: Complete List of Placements & Dasha ================= */}
              <div className="print-page print-page-2 space-y-3.5">
                {/* Header */}
                <div className="text-center space-y-1 pb-2 border-b border-[#3D1E60]">
                  <div className="flex items-center justify-center gap-2 font-serif text-base font-bold text-[#F5C842]">
                    <span>✦ PLANETARY POSITIONS & ACTIVE DASHA ✦</span>
                  </div>
                  <p className="text-[10.5px] font-mono text-[#DDD5EE]">
                    Native: {activeName} • Ascendant: {chartFacts?.lagna_sign} ({chartFacts?.formatted_lagna_degree || "00°00'"})
                  </p>
                </div>

                {/* Complete 9 Planets Astrological Table */}
                <div className="space-y-1.5">
                  <span className="text-[10.5px] uppercase font-bold text-[#F5C842] tracking-wider block">
                    Planetary Positions (Nirayana Longitudes)
                  </span>
                  <div className="overflow-x-auto rounded-xl border border-[#482075] bg-[#160A2B]">
                    <table className="w-full text-left border-collapse text-[11px]">
                      <thead>
                        <tr className="bg-[#241142] text-[#FDE68A] border-b border-[#482075]">
                          <th className="p-2.5 font-bold">Planet</th>
                          <th className="p-2.5 font-bold">Rashi (Sign)</th>
                          <th className="p-2.5 font-bold">Degree</th>
                          <th className="p-2.5 font-bold">House</th>
                          <th className="p-2.5 font-bold">Nakshatra</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#32175A]">
                        {chartFacts?.planets?.map((p) => (
                          <tr key={p.planet} className="bg-[#160A2B] text-white">
                            <td className="p-2.5 font-bold text-white flex items-center gap-1">
                              <span>{p.planet}</span>
                              {p.is_retrograde && <span className="text-[9px] text-[#FDE68A]">®</span>}
                            </td>
                            <td className="p-2.5 text-[#EDE9FE] font-medium">{p.sign}</td>
                            <td className="p-2.5 font-mono text-[11px] text-[#FDE68A]">{p.formatted_sign_degree}</td>
                            <td className="p-2.5 font-bold text-[#F5A623]">H{p.house || 1}</td>
                            <td className="p-2.5 text-[#F4B8DC] font-medium">{p.nakshatra?.name || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Active Vimshottari Dasha Box */}
                {chartFacts?.current_dasha && (
                  <div className="p-3.5 rounded-2xl bg-[#1A0D30] border border-[#B21E68]/70 space-y-1">
                    <span className="text-[10px] font-bold text-[#F4B8DC] uppercase tracking-wider block">
                      Active Vimshottari Dasha Window
                    </span>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-white text-sm">
                        {chartFacts.current_dasha.mahadasha_lord} Mahadasha • {chartFacts.current_dasha.antardasha_lord} Antardasha
                      </span>
                      <span className="text-[#F5C842] font-mono text-[11px] font-bold">
                        Until {chartFacts.current_dasha.end_date}
                      </span>
                    </div>
                  </div>
                )}

                {/* Astrological Seal & Footer */}
                <div className="pt-2 text-center text-[10px] text-[#A299BC] border-t border-[#341858] space-y-1">
                  <div>Certified Mathematical Ephemeris Computation • Melooha Planetary Engine</div>
                  <div>✦ Page 2 of 2 • Planetary Positions & Vimshottari Dasha ✦</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
