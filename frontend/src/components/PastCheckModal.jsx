import React, { useState, useEffect } from "react";
import { Check, X, HelpCircle, Sparkles, ArrowRight, ShieldCheck, RefreshCw } from "lucide-react";
import { t } from "../i18n";

export default function PastCheckModal({
  userId,
  balance,
  lang = "en",
  onComplete,
  onOpenPaywall,
  onPreFillQuestion,
}) {
  const [loading, setLoading] = useState(true);
  const [pastCheck, setPastCheck] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState(null);

  const fetchPastCheck = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`/api/user/${userId}/past-check?lang=${lang}`);
      if (!res.ok) throw new Error("Failed to load Past Check");
      const data = await res.json();

      // If control arm or skipped, proceed directly
      if (!data.should_show) {
        onComplete();
        return;
      }

      setPastCheck(data);
      if (data.is_completed) {
        setShowResult(true);
      } else {
        // Find first unanswered statement
        const firstUnanswered = data.statements.findIndex((s) => !s.is_answered);
        setCurrentIndex(firstUnanswered !== -1 ? firstUnanswered : 0);
      }
    } catch (err) {
      console.error(err);
      setError(lang === "hi" ? "अतीत सत्यापन लोड नहीं हो सका।" : "Could not load Past Check statements.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchPastCheck();
    }
  }, [userId, lang]);

  const handleAnswer = async (answer) => {
    if (!pastCheck || submitting) return;
    const currentItem = pastCheck.statements[currentIndex];
    if (!currentItem) return;

    setSubmitting(true);
    try {
      const res = await fetch(`/api/user/${userId}/past-check/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: currentItem.id, answer }),
      });
      if (!res.ok) throw new Error("Failed to record answer");
      const data = await res.json();

      // Update local state
      const updatedStatements = [...pastCheck.statements];
      updatedStatements[currentIndex] = {
        ...updatedStatements[currentIndex],
        answer,
        is_answered: true,
      };

      setPastCheck({
        ...pastCheck,
        statements: updatedStatements,
        recognized_count: data.recognized_count,
        is_completed: data.is_completed,
      });

      if (currentIndex + 1 < pastCheck.statements.length) {
        setCurrentIndex(currentIndex + 1);
      } else {
        setShowResult(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
        <div className="crystal-card p-6 rounded-3xl max-w-sm w-full space-y-4 text-center animate-pulse">
          <div className="w-12 h-12 rounded-full bg-purple-900/40 mx-auto" />
          <div className="h-4 w-40 bg-purple-900/40 rounded mx-auto" />
          <div className="h-16 w-full bg-purple-900/30 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
        <div className="crystal-card p-6 rounded-3xl max-w-sm w-full space-y-4 text-center">
          <p className="text-xs text-rose-300">{error}</p>
          <div className="flex gap-2">
            <button
              onClick={fetchPastCheck}
              className="flex-1 py-2 px-3 rounded-xl bg-[#251342] text-xs font-semibold text-white flex items-center justify-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{lang === "hi" ? "पुनः प्रयास करें" : "Retry"}</span>
            </button>
            <button
              onClick={onComplete}
              className="flex-1 py-2 px-3 rounded-xl bg-purple-900/50 text-xs text-[#A299BC]"
            >
              {lang === "hi" ? "छोड़ें" : "Skip"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!pastCheck || !pastCheck.should_show) {
    return null;
  }

  const statements = pastCheck.statements || [];
  const currentItem = statements[currentIndex];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="crystal-card p-6 rounded-3xl max-w-md w-full space-y-5 border border-[#E5A93C]/40 relative text-left">
        {/* Top Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#E5A93C]" />
            <span className="text-xs uppercase tracking-widest font-bold text-[#E5A93C]">
              {lang === "hi" ? "अतीत का सत्यापन" : "Past Check"}
            </span>
          </div>
          <span className="text-[10px] text-[#A299BC] px-2 py-0.5 rounded-full bg-[#1A0E30] border border-[#2D1B50]">
            {lang === "hi" ? "प्रतिबिंब, प्रमाण नहीं" : "Reflection, Not Proof"}
          </span>
        </div>

        {/* Result Screen */}
        {showResult ? (
          <div className="space-y-4 text-center py-2 animate-in fade-in">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] flex items-center justify-center text-white font-serif font-bold text-2xl mx-auto shadow-xl cosmic-glow">
              {pastCheck.recognized_count}/{statements.length}
            </div>

            <div className="space-y-1">
              <h3 className="font-serif text-lg font-bold text-white">
                {lang === "hi"
                  ? `आपने ${statements.length} में से ${pastCheck.recognized_count} बदलावों को पहचाना।`
                  : `You recognised ${pastCheck.recognized_count} of ${statements.length} life parallels.`}
              </h3>
              <p className="text-xs text-[#A299BC] max-w-xs mx-auto leading-relaxed">
                {pastCheck.disclaimer}
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="pt-2 space-y-2">
              {balance <= 0 ? (
                <button
                  onClick={() => {
                    try {
                      fetch("/api/events", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                          user_id: userId,
                          event_name: "topup_clicked",
                          payload: { arm: pastCheck?.arm },
                        }),
                      });
                    } catch (e) {
                      console.error(e);
                    }
                    onComplete();
                    if (onOpenPaywall) onOpenPaywall();
                  }}
                  className="w-full min-h-[44px] py-3 px-5 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-bold text-sm shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{lang === "hi" ? "प्रश्न जोड़ें (+5 निःशुल्क)" : "Add Questions Free (+5 Credits)"}</span>
                </button>
              ) : (
                <button
                  onClick={() => {
                    onComplete();
                    if (onPreFillQuestion && currentItem) {
                      const dateStr = currentItem.event_date.slice(0, 7);
                      const q = lang === "hi"
                        ? `मेरे जीवन में ${dateStr} के आसपास आए ग्रहीय बदलाव का क्या अर्थ था?`
                        : `What did my planetary shift around ${dateStr} indicate?`;
                      onPreFillQuestion(q);
                    }
                  }}
                  className="w-full min-h-[44px] py-3 px-5 rounded-2xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-bold text-sm shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{lang === "hi" ? "इस अवधि के बारे में पूछें" : "Ask about this period"}</span>
                </button>
              )}

              <button
                onClick={onComplete}
                className="w-full py-2 text-xs text-[#A299BC] hover:text-white transition-colors"
              >
                {lang === "hi" ? "आगे बढ़ें" : "Continue to App"}
              </button>
            </div>
          </div>
        ) : currentItem ? (
          /* Step Screen (One card at a time with 3 buttons) */
          <div className="space-y-4">
            {/* Progress Dots */}
            <div className="flex items-center justify-center gap-2">
              {statements.map((s, idx) => (
                <div
                  key={idx}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    idx === currentIndex
                      ? "w-7 bg-[#E5A93C]"
                      : s.is_answered
                      ? "w-2 bg-emerald-400"
                      : "w-2 bg-[#2B1B47]"
                  }`}
                />
              ))}
            </div>

            {/* Statement Card */}
            <div className="p-4 rounded-2xl bg-[#140B28] border border-[#2D1B50] space-y-3">
              <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#B21E68]/30 border border-[#B21E68]/50 text-[#F4B8DC]">
                {currentItem.theme}
              </span>
              <p className="font-serif text-sm sm:text-base text-white leading-relaxed font-semibold">
                "{currentItem.statement}"
              </p>
            </div>

            {/* 3 Action Buttons (Min 44px Touch Targets) */}
            <div className="grid grid-cols-3 gap-2 pt-1">
              <button
                onClick={() => handleAnswer("yes")}
                disabled={submitting}
                className="min-h-[44px] py-2 px-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 font-bold text-xs flex flex-col items-center justify-center gap-1 active:scale-95 transition-all disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                <span>{lang === "hi" ? "हाँ" : "Yes"}</span>
              </button>

              <button
                onClick={() => handleAnswer("not_really")}
                disabled={submitting}
                className="min-h-[44px] py-2 px-2 rounded-xl bg-purple-950/40 hover:bg-purple-900/40 border border-purple-800/40 text-[#DDD5EE] font-semibold text-xs flex flex-col items-center justify-center gap-1 active:scale-95 transition-all disabled:opacity-50"
              >
                <X className="w-4 h-4 text-rose-400" />
                <span>{lang === "hi" ? "विशेष नहीं" : "Not really"}</span>
              </button>

              <button
                onClick={() => handleAnswer("cant_recall")}
                disabled={submitting}
                className="min-h-[44px] py-2 px-2 rounded-xl bg-[#180E2E] hover:bg-[#251545] border border-[#352158] text-[#A299BC] font-medium text-xs flex flex-col items-center justify-center gap-1 active:scale-95 transition-all disabled:opacity-50"
              >
                <HelpCircle className="w-4 h-4 text-amber-400" />
                <span>{lang === "hi" ? "याद नहीं" : "Can't recall"}</span>
              </button>
            </div>

            <div className="text-center pt-1">
              <span className="text-[10px] text-[#7B6E96]">
                {lang === "hi" ? "प्रश्न " : "Statement "}
                {currentIndex + 1} of {statements.length}
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
