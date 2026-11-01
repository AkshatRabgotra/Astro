import React, { useState, useEffect } from "react";
import { Gift, Flame, Share2, Copy, Check, Volume2, Play, Pause, Sparkles, ChevronRight, CheckCircle2, ArrowRight } from "lucide-react";
import confetti from "canvas-confetti";

export default function RewardsView({ user, balance, onRefreshBalance, onOpenPaywall }) {
  const [rewardsState, setRewardsState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);
  const [friendCode, setFriendCode] = useState("");
  const [redeemStatus, setRedeemStatus] = useState(null);
  const [activeMantra, setActiveMantra] = useState(null);
  const [chantCount, setChantCount] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  useEffect(() => {
    if (!user?.id) return;
    loadRewards();
  }, [user]);

  const loadRewards = async () => {
    try {
      const res = await fetch(`/api/user/${user.id}/rewards`);
      if (res.ok) {
        const data = await res.json();
        setRewardsState(data);
      }
    } catch (err) {
      console.error("Error loading rewards:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClaimStreak = async () => {
    if (!user?.id) return;
    try {
      const res = await fetch(`/api/user/${user.id}/rewards/claim-streak`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.success) {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ["#E5A93C", "#B21E68", "#F4B8DC", "#FFD700"],
        });
        setRewardsState(data.state);
        onRefreshBalance();
      }
    } catch (err) {
      console.error("Error claiming streak:", err);
    }
  };

  const handleCopyReferral = () => {
    if (!rewardsState?.referral_code) return;
    navigator.clipboard.writeText(rewardsState.referral_code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const handleShareWhatsApp = () => {
    if (!rewardsState?.referral_code) return;
    const text = encodeURIComponent(
      `Hey! I'm using Melooha to get 100% grounded Vedic astrology readings. Use my referral code *${rewardsState.referral_code}* to get 5 free questions! 🪐✨`
    );
    window.open(`https://api.whatsapp.com/send?text=${text}`, "_blank");
  };

  const handleRedeemCode = async () => {
    if (!friendCode.trim() || !user?.id) return;
    try {
      const res = await fetch(`/api/user/${user.id}/rewards/redeem-referral`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: friendCode.trim() }),
      });
      const data = await res.json();
      if (data.success) {
        confetti({ particleCount: 100, spread: 80, origin: { y: 0.6 } });
        setRedeemStatus({ type: "success", text: data.message });
        setRewardsState(data.state);
        setFriendCode("");
        onRefreshBalance();
      } else {
        setRedeemStatus({ type: "error", text: data.message });
      }
    } catch (err) {
      setRedeemStatus({ type: "error", text: "Failed to redeem code. Please try again." });
    }
  };

  const handleClaimMantraReward = async (planet) => {
    if (!user?.id) return;
    try {
      const res = await fetch(`/api/user/${user.id}/rewards/claim-mantra`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ planet }),
      });
      const data = await res.json();
      if (data.success) {
        confetti({ particleCount: 60, spread: 60, origin: { y: 0.7 } });
        setRewardsState(data.state);
        setChantCount(0);
        setIsPlayingAudio(false);
        onRefreshBalance();
      }
    } catch (err) {
      console.error("Error claiming mantra:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-[#9F93BF] gap-3">
        <div className="w-6 h-6 border-2 border-[#B21E68] border-t-transparent rounded-full animate-spin" />
        <span className="text-xs">Loading Cosmic Rewards...</span>
      </div>
    );
  }

  const streakDays = rewardsState?.streak_days || [
    { day: 1, reward_coins: 5 },
    { day: 2, reward_coins: 7 },
    { day: 3, reward_coins: 9 },
    { day: 4, reward_coins: 11 },
    { day: 5, reward_coins: 13 },
    { day: 6, reward_coins: 15 },
    { day: 7, reward_coins: 17 },
  ];

  const currentDay = rewardsState?.streak_count || 1;
  const canClaim = rewardsState?.can_claim_today;

  return (
    <div className="space-y-4 pb-28 max-w-md mx-auto px-4 pt-3">
      {/* Top Header Bar with Wallet (Screenshot 1) */}
      <div className="flex items-center justify-between pb-1">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center shadow-lg shadow-[#B21E68]/30">
            <Gift className="w-4 h-4 text-[#FDE68A]" />
          </div>
          <h1 className="font-serif text-2xl font-bold text-white tracking-wide">
            Rewards
          </h1>
        </div>

        {/* Wallet Pill */}
        <div 
          onClick={onOpenPaywall}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#18112C] border border-[#3E2963] cursor-pointer hover:border-[#B21E68] transition-all shadow-md group"
        >
          <span className="text-xs text-[#A299BC] font-medium">Wallet</span>
          <div className="flex items-center gap-1">
            <span className="w-3.5 h-3.5 rounded-full gold-coin inline-block shrink-0" />
            <span className="text-sm font-bold text-white group-hover:text-[#FDE68A] transition-colors">
              ₹{rewardsState?.wallet_coins || 5}
            </span>
          </div>
          <div className="w-4 h-4 rounded-full bg-[#B21E68] text-white flex items-center justify-center text-[11px] font-bold">
            +
          </div>
        </div>
      </div>

      {/* Card 1: 7-Day Daily Streak (Screenshot 1) */}
      <div className="crystal-card p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full gold-coin flex items-center justify-center shadow-md shrink-0">
            <Sparkles className="w-5 h-5 text-amber-950" />
          </div>
          <div>
            <h3 className="font-serif text-base font-bold text-white flex items-center gap-2">
              Keep Your Streak Alive!
              <Flame className="w-4 h-4 text-orange-400 fill-orange-400" />
            </h3>
            <p className="text-xs text-[#A299BC]">
              Collect your daily rewards here
            </p>
          </div>
        </div>

        {/* 7-Day Progress Circles */}
        <div className="grid grid-cols-7 gap-1.5 pt-1">
          {streakDays.map((item) => {
            const isCompleted = item.day < currentDay || (item.day === currentDay && !canClaim);
            const isCurrentActive = item.day === currentDay && canClaim;

            return (
              <div key={item.day} className="flex flex-col items-center gap-1.5">
                <span className="text-[10px] text-[#8E82AA] font-semibold">
                  Day {item.day}
                </span>

                <div
                  className={`w-10 h-12 rounded-xl flex flex-col items-center justify-center transition-all ${
                    isCompleted
                      ? "bg-emerald-950/60 border-2 border-emerald-500/80 shadow-md text-emerald-300"
                      : isCurrentActive
                      ? "bg-gradient-to-b from-[#B21E68]/40 to-[#1D1338] border-2 border-[#E5A93C] gold-glow text-white scale-105"
                      : "bg-[#18102C] border border-[#2F214F] text-[#8478A0] opacity-80"
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full gold-coin flex items-center justify-center text-[8px] font-black text-amber-950">
                      ✦
                    </div>
                  )}
                  <span className="text-[11px] font-bold mt-1">
                    ₹{item.reward_coins}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Streak Action CTA Button */}
        <div>
          {canClaim ? (
            <button
              onClick={handleClaimStreak}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg hover:brightness-110 active:scale-95 transition-all cosmic-glow"
            >
              <Sparkles className="w-4 h-4 text-[#FDE68A]" />
              <span>Claim ₹{rewardsState?.today_reward_coins} Today (Adds +{rewardsState?.today_reward_questions} Question)</span>
            </button>
          ) : (
            <div className="w-full py-2.5 px-4 rounded-xl bg-[#17102A] border border-[#302150] text-[#A299BC] text-xs text-center font-medium flex items-center justify-center gap-2">
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>Claimed today! Get ₹{rewardsState?.next_reward_coins} more tomorrow</span>
            </div>
          )}
        </div>
      </div>

      {/* Card 2: Refer a Friend (Screenshot 1) */}
      <div className="crystal-card p-5 relative overflow-hidden space-y-4">
        {/* Background glow circle */}
        <div className="absolute -top-12 -right-12 w-32 h-32 rounded-full bg-amber-500/10 blur-2xl pointer-events-none" />

        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-serif text-base font-bold text-white flex items-center gap-1.5">
              Refer a friend & both earn <span className="text-[#E5A93C]">🪙 ₹50</span>
            </h3>
            <p className="text-xs text-[#A299BC] mt-0.5">
              Give 5 free questions. You earn 5 questions when they ask their first reading.
            </p>
          </div>

          <div className="w-12 h-12 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center shrink-0">
            <span className="text-2xl">🪙</span>
          </div>
        </div>

        {/* WhatsApp & Referral Code Buttons */}
        <div className="space-y-2.5">
          <button
            onClick={handleShareWhatsApp}
            className="w-full py-2.5 px-4 rounded-xl bg-[#25D366] hover:bg-[#20BE5A] text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md active:scale-95 transition-all"
          >
            <Share2 className="w-4 h-4" />
            <span>Refer a friend via WhatsApp</span>
          </button>

          <div className="flex items-center justify-between p-2 pl-3 rounded-xl bg-[#140D26] border border-[#352554]">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[#8E82AA]">Your Referral Code:</span>
              <span className="font-mono font-bold text-[#F4B8DC] text-sm tracking-widest">
                {rewardsState?.referral_code || "MELOO-9X47"}
              </span>
            </div>

            <button
              onClick={handleCopyReferral}
              className="px-3 py-1.5 rounded-lg bg-[#271A45] hover:bg-[#B21E68] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors active:scale-95"
            >
              {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCode ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>

        {/* Redeem friend code input */}
        <div className="pt-2 border-t border-[#291B45]">
          <span className="text-[11px] text-[#8E82AA] block mb-1.5 font-medium">
            Have a friend's referral code?
          </span>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={friendCode}
              onChange={(e) => setFriendCode(e.target.value.toUpperCase())}
              placeholder="Enter Code (e.g. 9X47WP)"
              className="flex-1 bg-[#150E28] border border-[#352554] rounded-xl px-3 py-2 text-xs text-white placeholder-[#685B85] focus:outline-none focus:border-[#B21E68]"
            />
            <button
              onClick={handleRedeemCode}
              disabled={!friendCode.trim()}
              className="px-3.5 py-2 rounded-xl bg-[#B21E68] hover:bg-[#931B58] text-white text-xs font-semibold disabled:opacity-40 transition-all active:scale-95"
            >
              Redeem
            </button>
          </div>
          {redeemStatus && (
            <p className={`text-[11px] mt-1.5 font-medium ${redeemStatus.type === "success" ? "text-emerald-400" : "text-rose-400"}`}>
              {redeemStatus.text}
            </p>
          )}
        </div>
      </div>

      {/* Card 3: MANTRA JAAP (Remedial Sound & Peace Chanting) */}
      <div className="crystal-card p-5 space-y-4">
        <div className="text-center space-y-1">
          <div className="flex items-center justify-center gap-2 text-xs font-serif font-bold text-[#E5A93C] tracking-widest uppercase">
            <span>✦</span>
            <span>MANTRA JAAP</span>
            <span>✦</span>
          </div>
          <p className="text-xs text-[#A299BC] max-w-xs mx-auto">
            Chant mantras and find peace, earn rewards as you stay consistent.
          </p>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#1A1230] border border-[#382759] text-[11px] text-[#E5A93C] font-semibold mt-1">
            <span className="w-2 h-2 rounded-full gold-coin inline-block" />
            <span>Claimed: {rewardsState?.mantra_claims_today || 0}/14</span>
          </div>
        </div>

        {/* Selected or Default Mantra (Mars Mantra - Screenshot 1) */}
        {rewardsState?.mantras?.map((m) => {
          const isSelected = activeMantra?.planet === m.planet;

          return (
            <div
              key={m.planet}
              className={`p-4 rounded-2xl border transition-all ${
                isSelected
                  ? "bg-[#1F143B] border-[#B21E68] shadow-lg"
                  : "bg-[#150E28] border-[#2E204B] hover:border-[#3F2B64]"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {/* Planet Visual Circle */}
                  <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-amber-700 via-rose-800 to-rose-600 flex items-center justify-center text-white font-serif font-bold shadow-md shadow-rose-900/40 shrink-0">
                    ♂
                  </div>
                  <div>
                    <h4 className="font-serif text-sm font-bold text-white">
                      {m.title}
                    </h4>
                    <p className="font-serif text-xs text-[#E5A93C] italic mt-0.5">
                      {m.transliteration}
                    </p>
                    <p className="text-[10px] text-[#8E82AA] mt-0.5 line-clamp-1">
                      {m.significance}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setActiveMantra(m);
                    setChantCount((prev) => prev + 1);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/20 to-[#B21E68]/30 border border-[#E5A93C]/40 text-[#FDE68A] text-xs font-semibold hover:border-[#E5A93C] transition-all flex items-center gap-1 active:scale-95 shrink-0"
                >
                  <span>Claim 🪙 ₹1</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Active Chanting Drawer */}
              {isSelected && (
                <div className="mt-3 pt-3 border-t border-[#312250] space-y-3">
                  <div className="p-3 rounded-xl bg-[#0F0A1E] text-center space-y-1">
                    <span className="font-serif text-base text-[#F4B8DC] font-bold block">
                      {m.sanskrit}
                    </span>
                    <span className="text-[11px] text-[#A299BC] block">
                      "{m.transliteration}"
                    </span>
                  </div>

                  {/* Audio Waveform Player Simulation */}
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#140D26] border border-[#2D1F49]">
                    <button
                      onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                      className="w-8 h-8 rounded-full bg-[#B21E68] text-white flex items-center justify-center shadow-md active:scale-95"
                    >
                      {isPlayingAudio ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
                    </button>

                    {/* Waveform bars */}
                    <div className="flex items-center gap-1 h-5 px-3 flex-1 justify-center">
                      <div className={`w-1 bg-[#E5A93C] rounded-full ${isPlayingAudio ? "wave-bar" : "h-2"}`} />
                      <div className={`w-1 bg-[#B21E68] rounded-full ${isPlayingAudio ? "wave-bar" : "h-4"}`} />
                      <div className={`w-1 bg-[#F4B8DC] rounded-full ${isPlayingAudio ? "wave-bar" : "h-3"}`} />
                      <div className={`w-1 bg-[#E5A93C] rounded-full ${isPlayingAudio ? "wave-bar" : "h-5"}`} />
                      <div className={`w-1 bg-[#B21E68] rounded-full ${isPlayingAudio ? "wave-bar" : "h-2"}`} />
                    </div>

                    <div className="text-[11px] font-mono text-[#A299BC]">
                      Chants: <strong className="text-white">{chantCount}/14</strong>
                    </div>
                  </div>

                  {/* Complete & Claim Button */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setChantCount((c) => c + 1)}
                      className="flex-1 py-2 px-3 rounded-xl bg-[#281A49] hover:bg-[#342260] text-white text-xs font-semibold transition-all active:scale-95"
                    >
                      ✦ Chant Mala Bead (+1)
                    </button>
                    <button
                      onClick={() => handleClaimMantraReward(m.planet)}
                      className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white text-xs font-bold transition-all shadow-md active:scale-95 hover:brightness-110"
                    >
                      Claim +1 Question Free
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
