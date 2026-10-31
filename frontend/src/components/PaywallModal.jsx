import React, { useState } from "react";
import { X, Sparkles, Zap, CheckCircle2, Shield, HeartHandshake } from "lucide-react";
import confetti from "canvas-confetti";

export default function PaywallModal({ user, onTopupSuccess, onClose }) {
  const [loading, setLoading] = useState(false);

  const handleTopup = async (count = 5) => {
    if (!user) return;
    setLoading(true);
    try {
      const idempotencyKey = `topup_${user.id}_${Date.now()}`;
      const res = await fetch(`/api/user/${user.id}/topup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count, idempotency_key: idempotencyKey }),
      });
      if (res.ok) {
        const data = await res.json();
        // Fire confetti celebration
        try {
          confetti({
            particleCount: 80,
            spread: 70,
            origin: { y: 0.6 },
            colors: ["#B21E68", "#E5A93C", "#F4B8DC", "#4F46E5"]
          });
        } catch (e) {}

        onTopupSuccess(data.balance);
      }
    } catch (err) {
      console.error("Top-up failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/80 backdrop-blur-md p-0 sm:p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md bg-[#130D24] border border-[#B21E68]/60 rounded-t-3xl sm:rounded-3xl p-6 sm:p-8 shadow-2xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="w-12 h-1 bg-[#43355F] rounded-full mx-auto mb-4 sm:hidden" />

        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-[#A299BC] hover:text-white hover:bg-white/10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon Header */}
        <div className="text-center pt-2">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white shadow-lg shadow-[#B21E68]/30 mb-3">
            <Sparkles className="w-7 h-7 text-[#E5A93C]" />
          </div>
          <span className="block text-xs font-semibold uppercase tracking-wider text-[#F4B8DC] mb-1">
            Melooha Challenge Credit Top-Up
          </span>
          <h2 className="font-serif text-2xl font-bold text-white">
            Get 5 More Questions
          </h2>
          <p className="text-xs text-[#A299BC] mt-1.5 max-w-xs mx-auto">
            Your question balance is currently 0. Add instant credits with no real payment to keep exploring your chart.
          </p>
        </div>

        {/* Value Proposition Cards */}
        <div className="my-5 space-y-2.5">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1B1233] border border-[#352554]">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <span className="text-xs text-[#E1DBEF]">
              <strong>100% Grounded in Your Facts:</strong> Verified against Swiss Ephemeris data.
            </span>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1B1233] border border-[#352554]">
            <Zap className="w-5 h-5 text-[#E5A93C] shrink-0" />
            <span className="text-xs text-[#E1DBEF]">
              <strong>Streaming SSE Delivery:</strong> Instant answers with full evidence chips.
            </span>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1B1233] border border-[#352554]">
            <Shield className="w-5 h-5 text-[#F4B8DC] shrink-0" />
            <span className="text-xs text-[#E1DBEF]">
              <strong>Automatic Failure Refund:</strong> If a model call fails, credits are restored instantly.
            </span>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={() => handleTopup(5)}
          disabled={loading}
          className="w-full py-3.5 px-6 rounded-2xl font-semibold text-white bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] hover:opacity-95 active:scale-[0.98] transition-all shadow-lg shadow-[#B21E68]/40 flex items-center justify-center gap-2"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-[#E5A93C]" />
              <span>Add 5 Questions Free</span>
            </>
          )}
        </button>

        <p className="text-center text-[10px] text-[#7E7399] mt-3">
          Hiring Challenge Demo Mode • No payment method required
        </p>
      </div>
    </div>
  );
}
