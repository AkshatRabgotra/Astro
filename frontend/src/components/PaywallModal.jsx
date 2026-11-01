import React, { useState } from "react";
import { X, Sparkles, Zap, CheckCircle2, Shield } from "lucide-react";
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
            particleCount: 100,
            spread: 80,
            origin: { y: 0.6 },
            colors: ["#B21E68", "#E5A93C", "#F4B8DC", "#FFD700"]
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
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/85 backdrop-blur-md p-0 sm:p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md crystal-card border-[#B21E68]/70 rounded-t-3xl sm:rounded-3xl p-6 sm:p-8 shadow-2xl relative space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Subtle Watermark */}
        <div className="absolute -top-6 -right-6 text-6xl text-white/[0.03] select-none pointer-events-none font-serif">
          ✦ ♈ ♌
        </div>

        <div className="w-12 h-1 bg-[#43355F] rounded-full mx-auto mb-2 sm:hidden" />

        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-[#A299BC] hover:text-white hover:bg-white/10 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon Header */}
        <div className="text-center pt-1">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#D8227E] text-white shadow-xl shadow-[#B21E68]/40 mb-3 cosmic-glow">
            <Sparkles className="w-7 h-7 text-[#FDE68A]" />
          </div>
          <span className="block text-xs font-bold uppercase tracking-wider text-[#F4B8DC] mb-1">
            Melooha Challenge Demo Mode
          </span>
          <h2 className="font-serif text-2xl font-bold text-white">
            Add 5 Free Questions
          </h2>
          <p className="text-xs text-[#A299BC] mt-1 max-w-xs mx-auto">
            Your question balance is currently 0. Add instant credits with no real payment to keep exploring your chart.
          </p>
        </div>

        {/* Value Proposition Cards */}
        <div className="space-y-2.5 pt-1">
          <div className="flex items-center gap-3 p-3 rounded-xl astro-badge">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <span className="text-xs text-[#E1DBEF]">
              <strong>100% Grounded in Your Facts:</strong> Verified against Swiss Ephemeris data.
            </span>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl astro-badge">
            <Zap className="w-5 h-5 text-[#E5A93C] shrink-0" />
            <span className="text-xs text-[#E1DBEF]">
              <strong>Streaming SSE Delivery:</strong> Instant answers with full evidence chips.
            </span>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-xl astro-badge">
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
          className="w-full py-3.5 px-6 rounded-2xl font-bold text-white bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] hover:brightness-110 active:scale-[0.98] transition-all shadow-xl shadow-[#B21E68]/40 flex items-center justify-center gap-2"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-[#FDE68A]" />
              <span>Add 5 Questions Free</span>
            </>
          )}
        </button>

        <p className="text-center text-[10.5px] text-[#8E82AA] font-medium">
          Hiring Challenge Demo Mode • No payment method required
        </p>
      </div>
    </div>
  );
}
