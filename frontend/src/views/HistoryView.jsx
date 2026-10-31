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
    <div className="max-w-md mx-auto px-4 pt-3 pb-24 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-lg font-bold text-white flex items-center gap-2">
          <History className="w-5 h-5 text-[#E5A93C]" />
          Your Reading History
        </h2>
        <span className="text-xs text-[#8E82AA]">
          {history.length} {history.length === 1 ? "Reading" : "Readings"}
        </span>
      </div>

      {history.length === 0 ? (
        <div className="glass-panel p-8 text-center space-y-2">
          <Sparkles className="w-8 h-8 text-[#E5A93C] mx-auto opacity-60" />
          <h3 className="text-sm font-semibold text-white">No Questions Yet</h3>
          <p className="text-xs text-[#8E82AA] max-w-xs mx-auto">
            Your answered questions will appear here with full grounding evidence chips.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div key={item.id} className="glass-panel p-4 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-xs font-semibold text-white leading-snug">
                  "{item.question_text}"
                </h4>
                <span className="text-[10px] text-[#7E7399] shrink-0 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>

              {item.answer ? (
                <div className="p-3 rounded-xl bg-[#17112C] border border-[#2B1F4A] space-y-2 text-xs text-[#D8D1E8] leading-relaxed">
                  <p className="whitespace-pre-line line-clamp-4">
                    {item.answer.answer_text}
                  </p>

                  {item.answer.cited_fact_ids && item.answer.cited_fact_ids.length > 0 && (
                    <div className="pt-2 border-t border-[#291B48] flex flex-wrap gap-1">
                      {item.answer.cited_fact_ids.map((fid) => (
                        <span
                          key={fid}
                          className="px-2 py-0.5 rounded-full text-[10px] bg-[#B21E68]/15 border border-[#B21E68]/30 text-[#F4B8DC]"
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
