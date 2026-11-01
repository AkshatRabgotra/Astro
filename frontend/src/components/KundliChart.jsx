import React, { useState } from "react";
import { Sparkles, Eye, Info, ChevronRight, HelpCircle } from "lucide-react";

const HOUSE_THEMES = {
  1: { name: "Tanu Bhava (Self)", significations: "Physical vitality, appearance, self-identity, constitution" },
  2: { name: "Dhana Bhava (Wealth)", significations: "Accumulated wealth, speech, family values, food" },
  3: { name: "Bhratru Bhava (Courage)", significations: "Siblings, courage, initiatives, communication, short travel" },
  4: { name: "Sukha Bhava (Home)", significations: "Mother, inner peace, vehicles, land, home foundation" },
  5: { name: "Putra Bhava (Intellect)", significations: "Children, creativity, intelligence, past-life karma, investments" },
  6: { name: "Ari Bhava (Overcoming)", significations: "Daily work, health, debts, obstacles, competitive resilience" },
  7: { name: "Yuvati Bhava (Partnership)", significations: "Marriage, business partners, public dealings, contracts" },
  8: { name: "Randhra Bhava (Transformation)", significations: "Longevity, occult, research, sudden changes, inheritances" },
  9: { name: "Dharma Bhava (Fortune)", significations: "Higher wisdom, guru, father, luck, long journeys, philosophy" },
  10: { name: "Karma Bhava (Career)", significations: "Profession, public standing, authority, leadership, legacy" },
  11: { name: "Labha Bhava (Gains)", significations: "Income, network circles, aspirations, major life achievements" },
  12: { name: "Vyaya Bhava (Liberation)", significations: "Spiritual liberation, foreign lands, expenditure, sub-conscious" },
};

const PLANET_SHORT = {
  Sun: "Su",
  Moon: "Mo",
  Mars: "Ma",
  Mercury: "Me",
  Jupiter: "Ju",
  Venus: "Ve",
  Saturn: "Sa",
  Rahu: "Ra",
  Ketu: "Ke",
};

// North Indian Diamond Polygon Paths (400x400 SVG viewport)
const NORTH_HOUSES = [
  { id: 1, points: "200,0 100,100 200,200 300,100", center: { x: 200, y: 100 }, labelPos: { x: 200, y: 55 } },
  { id: 2, points: "0,0 200,0 100,100", center: { x: 100, y: 50 }, labelPos: { x: 100, y: 30 } },
  { id: 3, points: "0,0 0,200 100,100", center: { x: 50, y: 100 }, labelPos: { x: 30, y: 100 } },
  { id: 4, points: "0,200 100,100 200,200 100,300", center: { x: 100, y: 200 }, labelPos: { x: 55, y: 200 } },
  { id: 5, points: "0,200 0,400 100,300", center: { x: 50, y: 300 }, labelPos: { x: 30, y: 300 } },
  { id: 6, points: "0,400 200,400 100,300", center: { x: 100, y: 350 }, labelPos: { x: 100, y: 375 } },
  { id: 7, points: "200,400 100,300 200,200 300,300", center: { x: 200, y: 300 }, labelPos: { x: 200, y: 345 } },
  { id: 8, points: "200,400 400,400 300,300", center: { x: 300, y: 350 }, labelPos: { x: 300, y: 375 } },
  { id: 9, points: "400,200 400,400 300,300", center: { x: 350, y: 300 }, labelPos: { x: 370, y: 300 } },
  { id: 10, points: "400,200 300,300 200,200 300,100", center: { x: 300, y: 200 }, labelPos: { x: 345, y: 200 } },
  { id: 11, points: "400,0 400,200 300,100", center: { x: 350, y: 100 }, labelPos: { x: 370, y: 100 } },
  { id: 12, points: "200,0 400,0 300,100", center: { x: 300, y: 50 }, labelPos: { x: 300, y: 30 } },
];

export default function KundliChart({ chartFacts, onSelectHouseQuestion }) {
  const [selectedHouse, setSelectedHouse] = useState(1);
  const [chartStyle, setChartStyle] = useState("north"); // 'north' | 'table'

  if (!chartFacts || !chartFacts.planets) {
    return null;
  }

  const lagnaNum = chartFacts.lagna_sign_number || 1;
  const timeKnown = chartFacts.time_known;

  // Group planets by house
  const planetsByHouse = {};
  for (let h = 1; h <= 12; h++) {
    planetsByHouse[h] = [];
  }

  chartFacts.planets.forEach((p) => {
    if (p.house && p.house >= 1 && p.house <= 12) {
      planetsByHouse[p.house].push(p);
    }
  });

  const getSignNumForHouse = (h) => {
    return ((lagnaNum - 1 + (h - 1)) % 12) + 1;
  };

  const selectedPlanets = planetsByHouse[selectedHouse] || [];
  const selectedTheme = HOUSE_THEMES[selectedHouse] || {};

  return (
    <div className="glass-panel p-4 sm:p-5 relative overflow-hidden space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#E5A93C] animate-pulse" />
            <h3 className="font-serif text-sm sm:text-base font-bold text-white flex items-center gap-1.5">
              Visual Kundli Chart (D1 Rashi)
            </h3>
          </div>
          <p className="text-[11px] text-[#A299BC] mt-0.5">
            {timeKnown
              ? `Lagna: ${chartFacts.lagna_sign || "Aries"} • Lahiri Sidereal`
              : "Solar Noon Reference (Houses reserved without exact time)"}
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-[#17102D] p-1 rounded-xl border border-[#2D1F4D]">
          <button
            onClick={() => setChartStyle("north")}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              chartStyle === "north"
                ? "bg-[#B21E68] text-white shadow-sm"
                : "text-[#8E82AA] hover:text-white"
            }`}
          >
            Chart
          </button>
          <button
            onClick={() => setChartStyle("table")}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
              chartStyle === "table"
                ? "bg-[#B21E68] text-white shadow-sm"
                : "text-[#8E82AA] hover:text-white"
            }`}
          >
            List
          </button>
        </div>
      </div>

      {chartStyle === "north" ? (
        <div className="flex flex-col items-center">
          {/* SVG North Indian Kundli Chart */}
          <div className="relative w-full max-w-[340px] aspect-square">
            <svg
              viewBox="0 0 400 400"
              className="w-full h-full filter drop-shadow-xl select-none"
            >
              {/* Outer border */}
              <rect
                x="2"
                y="2"
                width="396"
                height="396"
                fill="#120B24"
                stroke="#4C3073"
                strokeWidth="2.5"
                rx="6"
              />

              {/* Houses */}
              {NORTH_HOUSES.map((house) => {
                const isSelected = selectedHouse === house.id;
                const signNum = getSignNumForHouse(house.id);
                const planets = planetsByHouse[house.id] || [];

                return (
                  <g
                    key={house.id}
                    onClick={() => setSelectedHouse(house.id)}
                    className="cursor-pointer group"
                  >
                    {/* Polygon House Shape */}
                    <polygon
                      points={house.points}
                      className={`transition-colors duration-200 ${
                        isSelected
                          ? "fill-[#B21E68]/35 stroke-[#F4B8DC] stroke-[2]"
                          : "fill-[#160E2E] stroke-[#382356] hover:fill-[#20143F] stroke-[1.2]"
                      }`}
                    />

                    {/* House Sign Number (Small Corner Marker) */}
                    {timeKnown && (
                      <text
                        x={house.labelPos.x}
                        y={house.labelPos.y}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        className="text-[11px] font-mono font-bold fill-[#8375A2] group-hover:fill-white pointer-events-none"
                      >
                        {signNum}
                      </text>
                    )}

                    {/* Occupying Planets */}
                    {planets.length > 0 && (
                      <g className="pointer-events-none">
                        {planets.map((p, pIdx) => {
                          const count = planets.length;
                          const offset = (pIdx - (count - 1) / 2) * 13;
                          return (
                            <text
                              key={p.planet}
                              x={house.center.x}
                              y={house.center.y + offset + (timeKnown ? 4 : 0)}
                              textAnchor="middle"
                              dominantBaseline="middle"
                              className={`text-[11.5px] font-sans font-bold ${
                                isSelected ? "fill-[#FFE27D]" : "fill-[#F4B8DC]"
                              }`}
                            >
                              {PLANET_SHORT[p.planet] || p.planet.slice(0, 2)}
                              {p.is_retrograde && "®"}
                            </text>
                          );
                        })}
                      </g>
                    )}

                    {/* House 1 Lagna Badge */}
                    {house.id === 1 && timeKnown && (
                      <text
                        x={house.center.x}
                        y={house.center.y - 18}
                        textAnchor="middle"
                        className="text-[10px] font-bold fill-[#E5A93C] uppercase tracking-wider pointer-events-none"
                      >
                        Asc
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Decorative Center Dot */}
              <circle cx="200" cy="200" r="3.5" fill="#E5A93C" />
            </svg>
          </div>

          <span className="text-[10px] text-[#867B9F] mt-2">
            Tap any house to inspect its planetary alignments & significance
          </span>
        </div>
      ) : (
        /* Table View */
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => {
            const planets = planetsByHouse[h] || [];
            const signNum = getSignNumForHouse(h);
            const isSelected = selectedHouse === h;

            return (
              <button
                key={h}
                onClick={() => setSelectedHouse(h)}
                className={`p-2.5 rounded-xl text-left border transition-all ${
                  isSelected
                    ? "bg-[#B21E68]/20 border-[#B21E68] text-white"
                    : "bg-[#160E2C] border-[#2D1F4D] text-[#8A7EA6] hover:border-[#4B3472]"
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">House {h}</span>
                  {timeKnown && <span className="text-[10px] text-[#E5A93C]">Sign {signNum}</span>}
                </div>
                <div className="mt-1 text-[11px] truncate text-[#D9D0EA]">
                  {planets.length > 0 ? (
                    planets.map((p) => p.planet + (p.is_retrograde ? "®" : "")).join(", ")
                  ) : (
                    <span className="text-[#64597C]">Empty</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Selected House Deep Dive Inspector */}
      <div className="p-3.5 rounded-2xl bg-[#17102D] border border-[#342456] space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-md bg-[#B21E68]/30 border border-[#B21E68]/60 text-[#F4B8DC] text-xs font-bold">
              House {selectedHouse}
            </span>
            <h4 className="text-xs sm:text-sm font-semibold text-white">
              {selectedTheme.name}
            </h4>
          </div>
          {timeKnown && (
            <span className="text-[11px] text-[#E5A93C] font-medium">
              Sign: {getSignNumForHouse(selectedHouse)}
            </span>
          )}
        </div>

        <p className="text-xs text-[#A99EC3] leading-relaxed">
          {selectedTheme.significations}
        </p>

        {/* Occupying Planets in Selected House */}
        <div className="pt-2 border-t border-[#291B48]">
          <span className="text-[10px] uppercase tracking-wider text-[#8A7EA6] font-semibold block mb-1">
            Planets in this House ({selectedPlanets.length})
          </span>
          {selectedPlanets.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {selectedPlanets.map((p) => (
                <div
                  key={p.planet}
                  className="px-2.5 py-1 rounded-lg bg-[#21153E] border border-[#442F6B] text-xs text-white flex items-center gap-1.5"
                >
                  <span className="font-bold text-[#E5A93C]">{p.planet}</span>
                  <span className="text-[10px] text-[#A69CC0]">
                    {p.sign} {p.formatted_sign_degree}
                  </span>
                  {p.is_retrograde && (
                    <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-300 font-bold">
                      RETRO
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <span className="text-xs text-[#73688E] italic">
              No planets placed here in your birth chart (acts through its sign lord).
            </span>
          )}
        </div>

        {/* Suggest Question Button */}
        {onSelectHouseQuestion && (
          <button
            onClick={() =>
              onSelectHouseQuestion(
                `Tell me in detail about my House ${selectedHouse} (${selectedTheme.name}) and how its planetary energy shapes my life.`
              )
            }
            className="w-full mt-2 py-2 px-3 rounded-xl bg-[#B21E68]/20 hover:bg-[#B21E68]/40 border border-[#B21E68]/50 text-xs font-semibold text-[#F4B8DC] flex items-center justify-center gap-1.5 transition-all active:scale-[0.98]"
          >
            <span>Ask question about House {selectedHouse}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
