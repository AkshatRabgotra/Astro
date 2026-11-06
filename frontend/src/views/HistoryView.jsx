import React, { useState, useEffect } from "react";
import { History, Compass, Sparkles, Clock, CheckCircle2, ChevronDown, ChevronUp, Sun, Check, X } from "lucide-react";

export default function HistoryView({ user, profile, chartFacts, onOpenEvidence }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [activeAstroModal, setActiveAstroModal] = useState(null);

  const toggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    const url = profile?.id
      ? `/api/user/${user.id}/history?birth_profile_id=${profile.id}`
      : `/api/user/${user.id}/history`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const list = data.history || [];
        // Strictly sort from latest asked (newest) to previously asked (oldest)
        const sorted = [...list].sort((a, b) => {
          const ta = new Date(a.created_at || 0).getTime();
          const tb = new Date(b.created_at || 0).getTime();
          return tb - ta;
        });
        setHistory(sorted);
        // Start completely collapsed so answers are only revealed upon expanding
        setExpandedIds(new Set());
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [user, profile?.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-[#A299BC]">
        <div className="w-6 h-6 border-2 border-[#B21E68] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 pt-3 pb-28 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-white flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-md">
            <History className="w-4 h-4 text-[#FDE68A]" />
          </div>
          <span>{profile?.name ? `${profile.name}'s Reading History` : "Your Reading History"}</span>
        </h2>
        <span className="astro-badge px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-[#DDD5EE]">
          {history.length} {history.length === 1 ? "Record" : "Records"}
        </span>
      </div>

      {history.length === 0 ? (
        <div className="crystal-card p-8 text-center space-y-2">
          <Sparkles className="w-8 h-8 text-[#E5A93C] mx-auto opacity-70 animate-pulse" />
          <h3 className="text-sm font-bold text-white font-serif">No History Yet</h3>
          <p className="text-xs text-[#8E82AA] max-w-xs mx-auto">
            Your astrological consultations and auspicious Muhurta queries will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => {
            const isExpanded = expandedIds.has(item.id);
            const isMuhurta = item.type === "muhurta";

            return (
              <div
                key={item.id}
                onClick={() => toggleExpand(item.id)}
                className={`crystal-card p-4 space-y-3 relative overflow-hidden cursor-pointer transition-all border ${
                  isExpanded ? "border-[#B21E68]/70 shadow-lg" : "hover:border-[#532675]"
                }`}
              >
                {/* Background astrological symbol */}
                <div className="absolute -top-4 -right-4 text-3xl text-white/[0.03] select-none pointer-events-none font-serif">
                  {isMuhurta ? "☉ ⏱ ☽" : "✦ ♈ ♐"}
                </div>

                {/* Header: Distinct Badges & Timestamp */}
                <div className="flex items-center justify-between gap-2">
                  {isMuhurta ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-[#FDE68A] border border-amber-500/40 flex items-center gap-1.5 shrink-0 shadow-sm">
                      <Sun className="w-3 h-3 text-[#E5A93C]" />
                      <span>Auspicious Muhurta</span>
                    </span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#931B58]/25 text-[#F4B8DC] border border-[#B21E68]/50 flex items-center gap-1.5 shrink-0 shadow-sm">
                      <Compass className="w-3 h-3 text-[#E5A93C]" />
                      <span>Vedic Astrology</span>
                    </span>
                  )}

                  <span className="text-[10px] text-[#8E82AA] shrink-0 flex items-center gap-1 astro-badge px-2 py-0.5 rounded-full">
                    <Clock className="w-3 h-3 text-[#E5A93C]" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Question / Activity Title */}
                <div className="flex items-start justify-between gap-3 pt-0.5">
                  <h4 className="text-xs sm:text-sm font-semibold text-white leading-snug">
                    "{item.question_text}"
                  </h4>
                  <div className="p-1 rounded-full bg-[#201035] text-[#A299BC] shrink-0 mt-0.5">
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-[#E5A93C]" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </div>
                </div>

                {/* Only reveal answer when question is explicitly expanded by user */}
                {isExpanded ? (
                  item.answer ? (
                    <div className="space-y-2 pt-2 border-t border-[#291B48] animate-in fade-in duration-150">
                      <div className="p-3.5 rounded-xl bg-[#130C26] border border-[#2B1C48] text-xs text-[#DDD5EE] leading-relaxed">
                        <p className="whitespace-pre-line">
                          {item.answer.answer_text}
                        </p>

                        {/* Authentic Melooha Astrological References Button */}
                        {item.type === "astrology" && (
                          <div className="pt-2.5 mt-2.5 border-t border-[#291B48] flex items-center justify-between gap-2">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                const refs = item.answer.astro_references || [];
                                setActiveAstroModal({
                                  questionText: item.question_text,
                                  references: refs.length > 0 ? refs : (item.answer.cited_fact_ids || []).map((fid) => ({
                                    placement: `${fid} (birth chart)`,
                                    meaning: "astrological foundation and grounded evidence",
                                    fact_id: fid,
                                  })),
                                });
                              }}
                              className="px-3 py-1.5 rounded-full text-xs font-semibold bg-[#210F33] hover:bg-[#32154D] border border-[#B21E68]/50 text-[#F4B8DC] hover:text-white flex items-center gap-1.5 transition-all shadow-sm active:scale-95"
                            >
                              <Sparkles className="w-3.5 h-3.5 text-[#E5A93C]" />
                              <span>Check Astrological References</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-[11px] text-[#A299BC] italic pt-1 border-t border-[#291B48]">
                      Status: {item.status}
                    </div>
                  )
                ) : (
                  <div className="text-[10.5px] text-[#A299BC] group-hover:text-[#F4B8DC] text-right font-medium pr-1 pt-0.5">
                    Tap question to read answer ↓
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Astrological References Bottom-Sheet Modal */}
      {activeAstroModal && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col justify-end p-0 sm:p-4 animate-in fade-in duration-200"
          onClick={() => setActiveAstroModal(null)}
        >
          <div
            className="bg-gradient-to-b from-[#1C0E2F] via-[#140A24] to-[#0D0518] border-t sm:border border-[#B21E68]/60 rounded-t-3xl sm:rounded-3xl p-5 max-w-md mx-auto w-full max-h-[85vh] flex flex-col space-y-4 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 bg-white/25 rounded-full mx-auto -mt-1 mb-1 sm:hidden" />

            <div className="flex items-center justify-between pb-2 border-b border-[#301B4D]">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-[#FDE68A] flex items-center justify-center shadow-md">
                  <Sparkles className="w-4 h-4 text-[#FDE68A]" />
                </div>
                <h3 className="font-serif text-base font-bold text-white tracking-wide">
                  Astrological References
                </h3>
              </div>

              <button
                type="button"
                onClick={() => setActiveAstroModal(null)}
                className="w-7 h-7 rounded-full bg-[#24133F] hover:bg-[#341854] text-[#A299BC] hover:text-white flex items-center justify-center transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {activeAstroModal.questionText && (
              <p className="text-xs sm:text-[13px] text-[#DDD5EE] leading-snug line-clamp-2 italic px-0.5">
                "{activeAstroModal.questionText}"
              </p>
            )}

            <div className="overflow-y-auto space-y-3.5 pr-1 py-1 max-h-[50vh]">
              {activeAstroModal.references && activeAstroModal.references.length > 0 ? (
                activeAstroModal.references.map((ref, idx) => (
                  <div key={idx} className="flex items-start gap-3 text-xs sm:text-[13px] leading-relaxed">
                    <Check className="w-4 h-4 text-[#D8227E] shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white">
                        {ref.placement}:{" "}
                      </span>
                      <span className="text-[#CBBDE2]">
                        {ref.meaning}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-6 text-center text-xs text-[#A299BC]">
                  Standard astrological baseline verified.
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-[#291745]">
              <button
                type="button"
                onClick={() => setActiveAstroModal(null)}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-[#931B58]/40 active:scale-95 transition-all"
              >
                <span>Close and Continue →</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
