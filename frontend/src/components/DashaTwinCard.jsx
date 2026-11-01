import React, { useState, useEffect } from "react";
import { Share2, RefreshCw, MessageSquare, ExternalLink, Check, Download, Sparkles, X } from "lucide-react";
import { t } from "../i18n";

export default function DashaTwinCard({ userId, lang, onAskQuestion }) {
  const [twin, setTwin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [includeFirstName, setIncludeFirstName] = useState(false);
  const [creatingShare, setCreatingShare] = useState(false);
  const [shareData, setShareData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchTwin = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setErrorMsg(null);

      const url = `/api/user/${userId}/dasha-twin?lang=${lang}&refresh=${isRefresh}&level=pratyantar`;
      const res = await fetch(url);
      if (!res.ok) {
        if (res.status === 429) {
          setErrorMsg(lang === "hi" ? "आज के लिए रीफ्रेश सीमा समाप्त। आप वर्तमान समानता देख सकते हैं।" : "Daily refresh limit reached. Showing current match.");
          return;
        }
        throw new Error("Failed to fetch Dasha Twin");
      }
      const data = await res.json();
      setTwin(data);
    } catch (err) {
      console.error(err);
      setErrorMsg(lang === "hi" ? "दशा ट्विन लोड करने में त्रुटि।" : "Could not load Dasha Twin parallel.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchTwin(false);
    }
  }, [userId, lang]);

  const handleOpenShare = async () => {
    if (!twin) return;
    setShareModalOpen(true);
    setCreatingShare(true);

    try {
      const payload = {
        user_id: userId,
        headline: twin.headline,
        body: twin.body,
        figure_name: twin.figure?.display_name || "Notable Figure",
        figure_field: twin.figure?.field || "Achiever",
        lord: twin.lord || "Moon",
        theme: twin.lord || "Moon",
        include_first_name: includeFirstName,
        source_url: twin.source_url || twin.event?.source_url,
      };

      const res = await fetch("/api/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Failed to create share card");
      const data = await res.json();
      setShareData(data);
    } catch (err) {
      console.error("Error creating share card:", err);
    } finally {
      setCreatingShare(false);
    }
  };

  const handleWebShare = async () => {
    if (!shareData) return;
    const shareUrl = `${window.location.origin}${shareData.share_url}`;
    const text = `${twin.headline}\n${twin.figure?.display_name} (${twin.figure?.field}) shared this milestone during their ${twin.lord} phase.\n\nDiscover your own cosmic parallel:`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: "Melooha Dasha Twin",
          text: text,
          url: shareUrl,
        });
        return;
      } catch (err) {
        if (err.name !== "AbortError") {
          console.warn("Native Web Share failed, falling back to clipboard", err);
        }
      }
    }

    // Fallback: Copy link
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleWhatsAppShare = () => {
    if (!shareData) return;
    const shareUrl = `${window.location.origin}${shareData.share_url}`;
    const text = encodeURIComponent(
      `✦ Melooha Dasha Twin ✦\n${twin.headline}\n${twin.body}\n\nSee who mirrors your current dasha phase:\n${shareUrl}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  };

  const handleCopyLink = () => {
    if (!shareData) return;
    const shareUrl = `${window.location.origin}${shareData.share_url}`;
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="crystal-card p-5 rounded-3xl animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-5 w-40 bg-purple-900/40 rounded-full" />
          <div className="h-5 w-16 bg-pink-900/40 rounded-full" />
        </div>
        <div className="flex items-center gap-3">
          <div className="w-14 h-14 rounded-full bg-purple-950/60" />
          <div className="space-y-2 flex-1">
            <div className="h-4 w-32 bg-purple-900/40 rounded" />
            <div className="h-3 w-20 bg-purple-950/60 rounded" />
          </div>
        </div>
        <div className="space-y-2 pt-2">
          <div className="h-3 w-full bg-purple-900/30 rounded" />
          <div className="h-3 w-5/6 bg-purple-900/30 rounded" />
        </div>
      </div>
    );
  }

  if (!twin) return null;

  return (
    <div className="crystal-card p-5 rounded-3xl space-y-4 border border-[#B21E68]/40 shadow-xl relative overflow-hidden group">
      {/* Astrological watermark glyph */}
      <div className="absolute -right-6 -bottom-6 text-6xl text-[#E5A93C]/5 font-serif select-none pointer-events-none">
        ☽
      </div>

      {/* Top Header & Lord Chip */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-serif text-lg font-bold text-white tracking-wide leading-snug">
            {twin.headline}
          </h3>
          {twin.is_approximate && (
            <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] bg-amber-500/20 text-[#FDE68A] border border-amber-400/40">
              {t("approximateTimeBadge", lang)}
            </span>
          )}
        </div>

        {/* Lord Pill Badge */}
        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#B21E68] text-white shadow-md shrink-0">
          {twin.lord}
        </span>
      </div>

      {/* Person Monogram & Details */}
      {twin.figure && (
        <div className="flex items-center gap-3.5 pt-1">
          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-tr from-[#25133E] via-[#52133A] to-[#E5A93C] p-0.5 shadow-md shrink-0">
            <div className="w-full h-full rounded-[14px] bg-[#120725] flex items-center justify-center font-serif font-bold text-base text-[#FDE68A]">
              {twin.figure.monogram || twin.figure.display_name?.slice(0, 2).toUpperCase()}
            </div>
          </div>
          <div>
            <h4 className="font-serif text-base font-bold text-white">
              {twin.figure.display_name}
            </h4>
            <p className="text-xs text-[#A299BC] font-medium">
              {twin.figure.field}
            </p>
          </div>
        </div>
      )}

      {/* Body Copy */}
      <p className="text-xs sm:text-sm text-[#DDD5EE] leading-relaxed pt-1">
        {twin.body}
      </p>

      {/* Disclaimer and Source */}
      <div className="flex items-center justify-between text-[11px] text-[#A299BC] pt-1 border-t border-[#2B1B47]">
        <span>{twin.disclaimer}</span>
        {twin.source_url && (
          <a
            href={twin.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[#E5A93C] hover:underline"
          >
            <span>{t("source", lang)}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Error / Rate limit notification */}
      {errorMsg && (
        <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Bottom Action Buttons (44px touch-friendly) */}
      <div className="flex flex-wrap items-center gap-2 pt-2">
        {/* 1. Share Button */}
        <button
          onClick={handleOpenShare}
          className="flex-1 min-h-[44px] py-2.5 px-3.5 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white text-xs font-bold transition-all shadow-md active:scale-95 flex items-center justify-center gap-1.5 hover:brightness-110"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>{t("shareTwin", lang)}</span>
        </button>

        {/* 2. Another Parallel Button */}
        <button
          onClick={() => fetchTwin(true)}
          disabled={refreshing}
          className="min-h-[44px] py-2.5 px-3.5 rounded-xl bg-[#20123A] hover:bg-[#2C1950] border border-[#3A2464] text-white text-xs font-semibold transition-all active:scale-95 flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-[#E5A93C]" : ""}`} />
          <span>{t("anotherParallel", lang)}</span>
        </button>

        {/* 3. Ask About This Button */}
        <button
          onClick={() => onAskQuestion && onAskQuestion(twin.ask_prompt)}
          className="w-full min-h-[44px] py-2 px-3 rounded-xl bg-[#160B29] hover:bg-[#23123F] border border-[#352158] text-[#E5A93C] text-xs font-semibold transition-all active:scale-95 flex items-center justify-between"
        >
          <span className="truncate pr-2">"{twin.ask_prompt}"</span>
          <MessageSquare className="w-3.5 h-3.5 shrink-0" />
        </button>
      </div>

      {/* Share Modal */}
      {shareModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="crystal-card p-5 rounded-3xl max-w-sm w-full space-y-4 border border-[#E5A93C]/40 text-left relative">
            <div className="flex items-center justify-between pb-2 border-b border-[#2B1B47]">
              <div className="flex items-center gap-1.5 text-xs uppercase tracking-widest text-[#E5A93C] font-bold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t("dashaTwin", lang)}</span>
              </div>
              <button
                onClick={() => setShareModalOpen(false)}
                className="w-8 h-8 rounded-full bg-[#24133F] text-[#DDD5EE] flex items-center justify-center hover:bg-[#341C5A]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Privacy Toggle: Include first name */}
            <label className="flex items-center gap-2.5 p-2 rounded-xl bg-[#170B2E] border border-[#321C58] cursor-pointer">
              <input
                type="checkbox"
                checked={includeFirstName}
                onChange={(e) => {
                  setIncludeFirstName(e.target.checked);
                  // Refresh share with first name
                  setTimeout(handleOpenShare, 50);
                }}
                className="w-4 h-4 rounded text-[#B21E68] focus:ring-0 bg-[#251347]"
              />
              <span className="text-xs text-[#DDD5EE]">
                {t("includeFirstName", lang)}
              </span>
            </label>

            {creatingShare ? (
              <div className="p-8 text-center text-xs text-[#A299BC] animate-pulse">
                {t("generatingCard", lang)}
              </div>
            ) : shareData ? (
              <div className="space-y-3">
                {/* 1-Tap WhatsApp Share */}
                <button
                  onClick={handleWhatsAppShare}
                  className="w-full min-h-[44px] py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-all active:scale-95"
                >
                  <span>💬</span>
                  <span>{t("shareOnWhatsApp", lang)}</span>
                </button>

                {/* Native Share / Copy Link */}
                <button
                  onClick={handleWebShare}
                  className="w-full min-h-[44px] py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-all active:scale-95"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Share2 className="w-4 h-4" />}
                  <span>{copied ? t("copiedLink", lang) : t("shareTwin", lang)}</span>
                </button>

                {/* Download Options */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <a
                    href={shareData.card_image_url}
                    download={`melooha-twin-${shareData.token}.png`}
                    className="min-h-[40px] py-2 px-2.5 rounded-xl bg-[#23123E] hover:bg-[#321959] border border-[#3E226E] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all text-center"
                  >
                    <Download className="w-3.5 h-3.5 text-[#E5A93C]" />
                    <span>Card (4:5)</span>
                  </a>
                  <a
                    href={shareData.story_image_url}
                    download={`melooha-twin-story-${shareData.token}.png`}
                    className="min-h-[40px] py-2 px-2.5 rounded-xl bg-[#23123E] hover:bg-[#321959] border border-[#3E226E] text-white text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-all text-center"
                  >
                    <Download className="w-3.5 h-3.5 text-[#B21E68]" />
                    <span>Story (9:16)</span>
                  </a>
                </div>

                <button
                  onClick={handleCopyLink}
                  className="w-full py-2 text-center text-xs text-[#A299BC] hover:text-[#E5A93C] transition-colors"
                >
                  {copied ? t("copiedLink", lang) : "Copy Link"}
                </button>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
