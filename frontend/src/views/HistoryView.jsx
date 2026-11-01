import React, { useState, useEffect } from "react";
import { History, Compass, Sparkles, Clock, CheckCircle2 } from "lucide-react";

export default function HistoryView({ user, onOpenEvidence }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    fetch(`/api/user/${user.id}/history`)
      .then((res) => res.json())
      .then((data) => {
        setHistory(data.history || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [user]);

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
          <span>Your Reading History</span>
        </h2>
        <span className="astro-badge px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-[#DDD5EE]">
          {history.length} {history.length === 1 ? "Reading" : "Readings"}
        </span>
      </div>

      {history.length === 0 ? (
        <div className="crystal-card p-8 text-center space-y-2">
          <Sparkles className="w-8 h-8 text-[#E5A93C] mx-auto opacity-70 animate-pulse" />
          <h3 className="text-sm font-bold text-white font-serif">No Questions Yet</h3>
          <p className="text-xs text-[#8E82AA] max-w-xs mx-auto">
            Your answered questions will appear here with full grounding evidence chips.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div key={item.id} className="crystal-card p-4 space-y-3 relative overflow-hidden">
              <div className="absolute -top-4 -right-4 text-3xl text-white/[0.03] select-none pointer-events-none font-serif">
                ✦ ♈ ♐
              </div>

              <div className="flex items-start justify-between gap-2">
                <h4 className="text-xs sm:text-sm font-semibold text-white leading-snug">
                  "{item.question_text}"
                </h4>
                <span className="text-[10px] text-[#8E82AA] shrink-0 flex items-center gap-1 astro-badge px-2 py-0.5 rounded-full">
                  <Clock className="w-3 h-3 text-[#E5A93C]" />
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>

              {item.answer ? (
                <div className="p-3.5 rounded-xl bg-[#130C26] border border-[#2B1C48] space-y-2 text-xs text-[#DDD5EE] leading-relaxed">
                  <p className="whitespace-pre-line line-clamp-4">
                    {item.answer.answer_text}
                  </p>

                  {item.answer.cited_fact_ids && item.answer.cited_fact_ids.length > 0 && (
                    <div className="pt-2 border-t border-[#291B48] flex flex-wrap gap-1.5 items-center">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-[#9E90BC]">
                        Facts:
                      </span>
                      {item.answer.cited_fact_ids.map((fid) => (
                        <span
                          key={fid}
                          className="px-2 py-0.5 rounded-full text-[10.5px] font-mono font-bold bg-[#B21E68]/20 border border-[#B21E68]/50 text-[#F4B8DC]"
                        >
                          {fid}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-[11px] text-[#A299BC] italic">
                  Status: {item.status}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
