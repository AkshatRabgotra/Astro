import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  RefreshCw,
  AlertCircle,
  ShieldCheck,
  Compass,
  ArrowRight,
  Volume2,
  VolumeX,
  ThumbsUp,
  ThumbsDown,
  Check,
  X,
  Clock,
} from "lucide-react";
import PastCheckModal from "../components/PastCheckModal";
import { useTypewriter } from "../utils/useTypewriter";
import { t } from "../i18n";

const ASK_PHRASES = {
  en: [
    "Ask your astrology question...",
    "Will someone in my close circle betray my trust this year?",
    "When will my career enter its strongest period?",
    "What does my active Antardasha indicate for job change?",
    "When will Saturn Sade Sati ease its pressure?",
    "Is this an auspicious year to buy property or car?",
    "What spiritual remedy will protect my energy right now?",
    "Which gemstone strengthens my Lagna lord?",
  ],
  hi: [
    "अपना ज्योतिषीय प्रश्न यहाँ पूछें...",
    "क्या इस वर्ष कार्यक्षेत्र में पदोन्नति का योग है?",
    "मेरी कुंडली में साढ़े साती का क्या प्रभाव रहेगा?",
    "मेरी ऊर्जा और शांति के लिए कौन सा उपाय श्रेष्ठ है?",
    "क्या साझेदारी में व्यापार शुरू करना लाभदायक होगा?",
    "राहु और केतु मेरी कुंडली में क्या फल दे रहे हैं?",
  ],
};

/**
 * Parses bold text (**text**) and in-text fact chips ([F01]..[F25])
 */
function parseInline(text) {
  if (!text) return "";
  const regex = /(\*\*[^*]+\*\*|\[F\d+\])/g;
  const parts = text.split(regex);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="text-white font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (/^\[F\d+\]$/.test(part)) {
      return (
        <span
          key={i}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-[10.5px] font-mono font-bold bg-[#B21E68]/30 text-[#F4B8DC] border border-[#B21E68]/60 shadow-sm align-baseline"
        >
          {part}
        </span>
      );
    }
    return part;
  });
}

/**
 * Rich, indented markdown formatter for astrological readings
 */
function MarkdownContent({ text }) {
  if (!text) return null;

  const lines = text.split("\n");
  const elements = [];
  let currentList = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="space-y-2.5 my-2.5 pl-1">
          {currentList.map((item, idx) => (
            <li
              key={idx}
              className="relative pl-5 text-xs sm:text-[13px] text-[#DDD5EE] leading-relaxed before:content-['✦'] before:text-[#E5A93C] before:absolute before:left-0 before:top-0.5 before:text-[10px]"
            >
              {parseInline(item)}
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      return;
    }

    // Section headings (### or ##)
    if (line.startsWith("### ") || line.startsWith("## ")) {
      flushList();
      const heading = line.replace(/^#{2,3}\s+/, "");
      elements.push(
        <h4
          key={`h-${idx}`}
          className="font-serif text-[13px] sm:text-sm font-bold text-[#F4B8DC] pt-3 pb-1 border-b border-[#2C1D47] flex items-center gap-2 mb-2"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#E5A93C] inline-block shrink-0" />
          <span>{parseInline(heading)}</span>
        </h4>
      );
      return;
    }

    // Bullet points (- or * or •)
    if (/^[-*•]\s+/.test(line)) {
      currentList.push(line.replace(/^[-*•]\s+/, ""));
      return;
    }

    // Standard paragraph
    flushList();
    elements.push(
      <p key={`p-${idx}`} className="text-xs sm:text-[13px] text-[#DDD5EE] leading-relaxed mb-2.5">
        {parseInline(line)}
      </p>
    );
  });

  flushList();
  return <div className="space-y-0.5">{elements}</div>;
}

export default function AskView({
  user,
  profile,
  chartFacts,
  balance,
  lang = "en",
  onOpenPaywall,
  onOpenEvidence,
  onOpenHistory,
  initialQuestion,
  onQuestionCompleted,
  onStreamingStateChange,
}) {
  const [questionText, setQuestionText] = useState(initialQuestion || "");
  const [lastQuestion, setLastQuestion] = useState(initialQuestion || "");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const [activeAstroModal, setActiveAstroModal] = useState(null);
  const [feedbackState, setFeedbackState] = useState({});

  const handleFeedback = (msgId, type) => {
    setFeedbackState((prev) => ({
      ...prev,
      [msgId]: prev[msgId] === type ? null : type,
    }));
  };

  const handleOpenAstroModal = (msg, questionContext) => {
    let refs = msg.astro_references || [];
    if (!refs || refs.length === 0) {
      if (msg.cited_facts && msg.cited_facts.length > 0) {
        refs = msg.cited_facts.map((f) => ({
          placement: `${f.subject || f.id} (birth chart)`,
          meaning: f.text || "planetary foundation and grounded astrological basis",
          fact_id: f.id,
        }));
      } else if (chartFacts?.planets) {
        refs = chartFacts.planets.slice(0, 4).map((p) => ({
          placement: `${p.planet}${p.house ? `, house ${p.house}` : ""}${p.nakshatra?.name ? `, ${p.nakshatra.name}` : ""} (birth chart)`,
          meaning: `${p.planet} in ${p.sign} directs personal agency and focus`,
        }));
      }
    }
    setActiveAstroModal({
      questionText: questionContext || msg.userQuestion || lastQuestion || "Astrological Consultation",
      references: refs,
    });
  };

  const [messages, setMessages] = useState(() => {
    if (typeof window !== "undefined" && user?.id && profile?.id) {
      try {
        // Clean legacy permanent storage so app re-opens with a fresh ask room
        localStorage.removeItem(`melooha_chat_${user.id}_${profile.id}`);
        const saved = sessionStorage.getItem(`melooha_session_chat_${user.id}_${profile.id}`);
        if (saved) return JSON.parse(saved);
      } catch (_) {}
    }
    return [];
  });
  const [currentStreamAnswer, setCurrentStreamAnswer] = useState("");
  const [errorMessage, setErrorMessage] = useState(null);
  const [showPastCheck, setShowPastCheck] = useState(false);
  const [hasSeenPastCheck, setHasSeenPastCheck] = useState(false);
  const messagesEndRef = useRef(null);

  // Switch or restore active session chat when family member changes
  useEffect(() => {
    if (!user?.id || !profile?.id) return;
    try {
      localStorage.removeItem(`melooha_chat_${user.id}_${profile.id}`);
      const saved = sessionStorage.getItem(`melooha_session_chat_${user.id}_${profile.id}`);
      if (saved) {
        setMessages(JSON.parse(saved));
      } else {
        setMessages([]);
      }
    } catch (_) {
      setMessages([]);
    }
  }, [user?.id, profile?.id]);

  // Persist session messages (cleared when app/browser is closed; permanent records live in HistoryView)
  useEffect(() => {
    if (!user?.id || !profile?.id) return;
    try {
      sessionStorage.setItem(`melooha_session_chat_${user.id}_${profile.id}`, JSON.stringify(messages));
    } catch (_) {}
  }, [messages, user?.id, profile?.id]);

  // Notify parent App of streaming progress so navigation never loses track
  useEffect(() => {
    if (onStreamingStateChange) {
      onStreamingStateChange({
        isStreaming,
        streamStatus,
        lastQuestion,
      });
    }
  }, [isStreaming, streamStatus, lastQuestion]);

  // Animated typewriter for ask placeholder
  const askPhrases = ASK_PHRASES[lang] || ASK_PHRASES.en;
  const animatedAskPlaceholder = useTypewriter(askPhrases, {
    typingSpeed: 60,
    deletingSpeed: 30,
    pauseMs: 2000,
    emptyPauseMs: 400,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamAnswer]);

  // Voice Astrologer: Native browser TTS with bilingual auto-detection
  const [speakingMessageId, setSpeakingMessageId] = useState(null);

  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleToggleVoiceReading = (msgId, rawText) => {
    if (!("speechSynthesis" in window)) {
      alert("Text-to-speech audio is not supported in this browser.");
      return;
    }

    if (speakingMessageId === msgId) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Clean Markdown markers and fact citation tags before vocalizing
    const cleanText = (rawText || "")
      .replace(/\[F\d+\]/g, "")
      .replace(/(\*\*|\*|#|_|`)/g, "")
      .replace(/\[.*?\]/g, "")
      .replace(/[✦•\->]/g, " ")
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.92; // Serene, measured astrologer pacing
    utterance.pitch = 1.0;

    const isHindi = lang === "hi" || /[\u0900-\u097F]/.test(cleanText);
    utterance.lang = isHindi ? "hi-IN" : "en-IN";

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find((v) =>
      isHindi
        ? v.lang.startsWith("hi")
        : v.lang === "en-IN" || v.lang.startsWith("en-GB") || v.lang.startsWith("en")
    );
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onend = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);

    setSpeakingMessageId(msgId);
    window.speechSynthesis.speak(utterance);
  };

  // If initial question was passed from HomeView suggested questions
  useEffect(() => {
    if (initialQuestion && initialQuestion.trim()) {
      setQuestionText(initialQuestion);
      setLastQuestion(initialQuestion);
    }
  }, [initialQuestion]);

  const handleAsk = async (textToSubmit) => {
    const qText = (textToSubmit || questionText || lastQuestion).trim();
    if (!qText || isStreaming) return;

    setLastQuestion(qText);

    if (balance <= 0) {
      onOpenPaywall();
      return;
    }

    setErrorMessage(null);
    setIsStreaming(true);
    setStreamStatus("Consulting planetary positions...");
    setCurrentStreamAnswer("");

    // Add user question message to thread (avoid duplicate on retry)
    const userMsgId = `user_${Date.now()}`;
    setMessages((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].role === "user" && prev[prev.length - 1].text === qText) {
        return prev;
      }
      return [...prev, { id: userMsgId, role: "user", text: qText }];
    });
    setQuestionText("");

    const idempotencyKey = `q_${user.id}_${Date.now()}`;

    try {
      // 1. Spend credit and create pending question
      const createRes = await fetch("/api/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          birth_profile_id: profile.id,
          question_text: qText,
          idempotency_key: idempotencyKey,
        }),
      });

      if (!createRes.ok) {
        if (createRes.status === 402) {
          setIsStreaming(false);
          onOpenPaywall();
          return;
        }
        const errData = await createRes.json();
        throw new Error(errData.detail || "Failed to start question");
      }

      const qData = await createRes.json();
      const questionId = qData.question_id;

      // 2. Open Server-Sent Events (SSE) stream
      setStreamStatus("Connecting to celestial intelligence...");
      const eventSource = new EventSource(`/api/questions/${questionId}/stream`);

      let accumulatedAnswer = "";
      let citedFacts = [];
      let finalProvider = "gemini";
      let replacedReason = null;
      let astroReferences = [];

      eventSource.addEventListener("status", (e) => {
        const d = JSON.parse(e.data);
        setStreamStatus(d.message || "Generating reading...");
      });

      eventSource.addEventListener("token", (e) => {
        const d = JSON.parse(e.data);
        accumulatedAnswer += d.token;
        setCurrentStreamAnswer(accumulatedAnswer);
      });

      eventSource.addEventListener("verified", (e) => {
        const d = JSON.parse(e.data);
        citedFacts = d.cited_facts || [];
        astroReferences = d.astro_references || [];
        finalProvider = d.provider;
      });

      eventSource.addEventListener("replace", (e) => {
        const d = JSON.parse(e.data);
        accumulatedAnswer = d.answer;
        setCurrentStreamAnswer(d.answer);
        citedFacts = d.cited_facts || [];
        astroReferences = d.astro_references || [];
        finalProvider = d.provider;
        replacedReason = d.reason;
      });

      eventSource.addEventListener("error", (e) => {
        try {
          const d = JSON.parse(e.data);
          setErrorMessage(d.message);
        } catch (_) {
          setErrorMessage("The cosmic connection was interrupted. Your credit has been preserved.");
        }
        eventSource.close();
        setIsStreaming(false);
      });

      eventSource.addEventListener("end", () => {
        eventSource.close();
        setIsStreaming(false);

        // Commit completed message to chat thread
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant_${Date.now()}`,
            role: "assistant",
            text: accumulatedAnswer,
            userQuestion: qText,
            cited_facts: citedFacts,
            astro_references: astroReferences,
            provider: finalProvider,
            replacedReason: replacedReason,
          },
        ]);
        setCurrentStreamAnswer("");
        onQuestionCompleted();

        // Show Past Check trust reflection before paywall if user hasn't seen it
        if (!hasSeenPastCheck) {
          setTimeout(() => setShowPastCheck(true), 600);
        }
      });

      eventSource.onerror = () => {
        eventSource.close();
        setIsStreaming(false);
      };
    } catch (err) {
      setErrorMessage(err.message || "Unable to complete request. Please try again.");
      setIsStreaming(false);
    }
  };

  const handleEvidenceClick = (fact) => {
    fetch("/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: user?.id,
        event_name: "evidence_opened",
        payload: { fact_id: fact.id, subject: fact.subject },
      }),
    }).catch(() => {});

    onOpenEvidence(fact);
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-165px)] max-w-md mx-auto px-4 pb-2 relative">
      {/* Seamless Ethereal Nebula Atmosphere & Tasteful Translucent Astro Elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden select-none z-0">
        {/* Soft Radial Ambient Nebula Glows */}
        <div className="absolute top-[20%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-88 h-88 rounded-full bg-gradient-to-tr from-[#7B0D42]/25 via-[#B21E68]/15 to-transparent blur-3xl" />
        <div className="absolute top-[55%] -right-12 w-64 h-64 rounded-full bg-[#3B125C]/20 blur-3xl" />
        <div className="absolute bottom-16 -left-12 w-64 h-64 rounded-full bg-[#1F0A38]/25 blur-3xl" />

        {/* Subtle, Very Translucent Astro Cosmic Elements (Few, Delicate, Ethereal) */}
        <svg
          className="w-full h-full absolute inset-0 pointer-events-none select-none"
          viewBox="0 0 400 700"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Faint Astrolabe Orbit Rings behind top emblem */}
          <circle cx="200" cy="110" r="85" stroke="rgba(244, 184, 220, 0.12)" strokeWidth="0.75" strokeDasharray="3 5" />
          <circle cx="200" cy="110" r="125" stroke="rgba(229, 169, 60, 0.08)" strokeWidth="0.5" />
          <ellipse cx="200" cy="110" rx="145" ry="55" stroke="rgba(244, 184, 220, 0.07)" strokeWidth="0.5" strokeDasharray="4 6" />

          {/* Saptarishi Constellation Trace in lower space */}
          <g stroke="rgba(255, 255, 255, 0.09)" strokeWidth="0.6">
            <line x1="75" y1="410" x2="135" y2="435" />
            <line x1="135" y1="435" x2="185" y2="425" />
            <line x1="185" y1="425" x2="225" y2="455" />
            <line x1="225" y1="455" x2="310" y2="450" />
            <line x1="310" y1="450" x2="335" y2="505" />
            <line x1="335" y1="505" x2="265" y2="520" />
            <line x1="265" y1="520" x2="225" y2="455" />
          </g>

          {/* Translucent Star Nodes on the Constellation */}
          <circle cx="75" cy="410" r="2" fill="#E5A93C" fillOpacity="0.25" />
          <circle cx="135" cy="435" r="1.5" fill="#FFFFFF" fillOpacity="0.3" />
          <circle cx="185" cy="425" r="1.5" fill="#F4B8DC" fillOpacity="0.25" />
          <circle cx="225" cy="455" r="2.2" fill="#FFFFFF" fillOpacity="0.35" />
          <circle cx="310" cy="450" r="1.8" fill="#E5A93C" fillOpacity="0.28" />
          <circle cx="335" cy="505" r="1.8" fill="#FFFFFF" fillOpacity="0.3" />
          <circle cx="265" cy="520" r="2" fill="#F4B8DC" fillOpacity="0.3" />

          {/* Just 3 Delicate Ethereal Sparkles in Negative Spaces */}
          <g fill="#FDE68A" fillOpacity="0.22">
            <path d="M 330,65 Q 330,70 334,70 Q 330,70 330,75 Q 330,70 326,70 Q 330,70 330,65 Z" />
            <path d="M 55,360 Q 55,364 58,364 Q 55,364 55,368 Q 55,364 52,364 Q 55,364 55,360 Z" />
            <path d="M 345,385 Q 345,390 349,390 Q 345,390 345,395 Q 345,390 341,390 Q 345,390 345,385 Z" />
          </g>
        </svg>
      </div>

      {/* Authentic Melooha Chat Header (Screenshot 4) */}
      <div className="shrink-0 flex items-center justify-between py-2 px-1 border-b border-[#2C1D47]/80 relative z-20">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] text-white flex items-center justify-center font-bold text-xs ring-1 ring-[#F4B8DC]/40 shadow-sm">
              {(profile?.name || user?.name || "Akshat").slice(0, 2).toUpperCase()}
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-[#080511]" title="Online" />
          </div>

          <div>
            <div className="flex items-center gap-1">
              <span className="font-serif text-xs sm:text-sm font-bold text-white tracking-wide">
                Reading for {profile?.name || user?.name || "Member"}
              </span>
            </div>
            <span className="text-[11px] text-[#A299BC] flex items-center gap-1 font-medium">
              <span className="text-[#E5A93C]">✦</span>
              <span>Vaani • Melooha Astrologer</span>
            </span>
          </div>
        </div>

        {onOpenHistory && (
          <button
            onClick={onOpenHistory}
            className="p-1.5 rounded-xl bg-[#1C0E2D]/80 hover:bg-[#2B1445] text-[#DDD5EE] border border-[#B21E68]/30 hover:border-[#B21E68] transition-colors"
            title="Reading History"
          >
            <Clock className="w-4 h-4 text-[#FDE68A]" />
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pt-3 pb-3 relative z-10">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-4 px-4 relative">
            {/* Small & Refined Glowing Melooha Emblem */}
            <div className="relative w-14 h-14 mx-auto mb-2 flex items-center justify-center">
              {/* Outer Pulsing Nebula Glow Aura */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#931B58] via-[#D8227E] to-[#E5A93C] blur-lg opacity-70 animate-pulse" />
              
              {/* Rotating Astrological Orbit Ring */}
              <div className="absolute -inset-1.5 rounded-full border border-[#F4B8DC]/40 border-dashed animate-[spin_35s_linear_infinite]" />

              {/* Compact, Perfectly Fit Melooha Logo */}
              <div className="relative w-11 h-11 rounded-full overflow-hidden shadow-[0_0_20px_rgba(216,34,126,0.8)] ring-1.5 ring-[#F4B8DC] ring-offset-1 ring-offset-[#080312]">
                <img
                  src="/melooha-logo.png"
                  alt="Melooha AI"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>

            <h3 className="font-serif text-lg sm:text-xl font-bold text-white tracking-wide shimmer-text-gold">
              {t("askAstrologerTitle", lang)}
            </h3>
            <p className="text-xs text-[#DDD5EE] max-w-xs mx-auto mt-1 leading-relaxed">
              {t("askAstrologerSubtitle", lang)}
            </p>

            {/* Aesthetic Suggested Topic Pills - Seamless Camouflaged Glass */}
            <div className="pt-4 max-w-sm mx-auto space-y-2 text-left">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#A299BC] block text-center">
                {lang === "hi" ? "सुझाए गए प्रश्न" : "Suggested Topics"}
              </span>
              <div className="flex flex-col gap-2">
                {[
                  { text: lang === "hi" ? "मेरी वर्तमान महादशा मेरे करियर को कैसे प्रभावित कर रही है?" : "How is my active Mahadasha shaping my career?", icon: "🪐" },
                  { text: lang === "hi" ? "मेरे जीवन में स्थिरता और वित्तीय लाभ कब शुरू होंगे?" : "When will financial stability and growth settle in for me?", icon: "💰" },
                  { text: lang === "hi" ? "क्या इस वर्ष मेरे रिश्ते में अनुकूलता बढ़ेगी?" : "What does my chart reveal about relationships this year?", icon: "❤️" },
                ].map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuestionText(item.text);
                      handleAsk(item.text);
                    }}
                    className="w-full text-left p-3.5 rounded-2xl bg-gradient-to-r from-white/[0.06] via-[#1D0C30]/80 to-white/[0.03] hover:from-white/[0.1] hover:to-[#281140] border border-white/[0.1] hover:border-[#D8227E]/60 text-xs text-[#EAE3F7] hover:text-white transition-all flex items-center justify-between group active:scale-98 shadow-[0_4px_20px_rgba(0,0,0,0.4)] backdrop-blur-xl"
                  >
                    <span className="flex items-center gap-3 truncate pr-2">
                      <span className="text-base shrink-0">{item.icon}</span>
                      <span className="truncate font-medium">{item.text}</span>
                    </span>
                    <div className="w-6 h-6 rounded-full bg-white/10 group-hover:bg-[#B21E68] text-[#F4B8DC] group-hover:text-white flex items-center justify-center shrink-0 transition-colors shadow-sm">
                      <ArrowRight className="w-3 h-3" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Existing Messages */}
        {messages.map((m, msgIdx) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
          >
            {m.role === "user" ? (
              <div className="max-w-[85%] p-3.5 rounded-2xl rounded-tr-sm bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white text-xs sm:text-sm font-medium shadow-md">
                {m.text}
              </div>
            ) : (
              <div className="max-w-[96%] p-4 sm:p-5 rounded-2xl rounded-tl-sm bg-[#161028] border border-[#2D1F4D] text-[#E8E2F5] text-xs sm:text-sm shadow-md space-y-3 relative">
                {/* Voice Astrologer Header & Audio Reader */}
                <div className="flex items-center justify-between pb-2.5 border-b border-[#2C1C46] text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#E5A93C] flex items-center justify-center text-[10px] text-white shadow-sm shrink-0">
                      ✦
                    </div>
                    <span className="font-serif font-bold text-white text-xs truncate">
                      {lang === "hi" ? "मेलोहा वैदिक विश्लेषण" : "Melooha Vedic Reading"}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleToggleVoiceReading(m.id, m.text)}
                    className={`px-2.5 py-1 rounded-full text-[11px] font-semibold flex items-center gap-1.5 transition-all shadow-sm active:scale-95 shrink-0 ${
                      speakingMessageId === m.id
                        ? "bg-[#B21E68] text-white border border-[#F4B8DC]/50 shadow-[0_0_12px_rgba(216,34,126,0.6)]"
                        : "bg-[#251540] hover:bg-[#341854] text-[#F4B8DC] border border-[#522064]"
                    }`}
                    title={speakingMessageId === m.id ? "Stop voice reading" : "Listen to reading"}
                  >
                    {speakingMessageId === m.id ? (
                      <>
                        <VolumeX className="w-3.5 h-3.5 text-white" />
                        <span>{lang === "hi" ? "रोकें" : "Stop"}</span>
                        {/* Pulsing Audio Waveform Bars */}
                        <div className="flex items-center gap-0.5 ml-1">
                          <span className="w-0.5 h-3 bg-white rounded-full animate-[pulse_0.5s_ease-in-out_infinite]" />
                          <span className="w-0.5 h-4 bg-amber-300 rounded-full animate-[pulse_0.35s_ease-in-out_infinite]" />
                          <span className="w-0.5 h-2 bg-white rounded-full animate-[pulse_0.65s_ease-in-out_infinite]" />
                        </div>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3.5 h-3.5 text-[#E5A93C]" />
                        <span>{lang === "hi" ? "ऑडियो सुनें" : "Listen"}</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Formatted & Indented Answer Text */}
                <MarkdownContent text={m.text} />

                {m.replacedReason && (
                  <div className="p-2 rounded-lg bg-[#E5A93C]/10 border border-[#E5A93C]/30 text-[#E5A93C] text-[11px] flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                    <span>Safe Grounded Reading enforced</span>
                  </div>
                )}

                {/* Authentic Melooha Action Bar: Check Astrological References & Feedback (Screenshots 4 & 5) */}
                <div className="pt-2.5 border-t border-[#2A1D45]/80 flex flex-wrap items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => handleOpenAstroModal(m, messages[msgIdx - 1]?.text || m.userQuestion)}
                    className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#210F33] hover:bg-[#32154D] border border-[#B21E68]/50 text-[#F4B8DC] hover:text-white flex items-center gap-2 transition-all shadow-sm active:scale-95 group shrink-0"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#E5A93C] group-hover:rotate-12 transition-transform" />
                    <span>{lang === "hi" ? "ज्योतिषीय संदर्भ देखें" : "Check Astrological References"}</span>
                  </button>

                  {/* Thumbs up & Thumbs down feedback */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleFeedback(m.id, "like")}
                      className={`p-1.5 rounded-lg border text-xs transition-all ${
                        feedbackState[m.id] === "like"
                          ? "bg-[#B21E68]/40 border-[#B21E68] text-[#FDE68A] shadow-sm"
                          : "border-[#2D1F4D] text-[#A299BC] hover:text-white hover:border-[#B21E68]/40"
                      }`}
                      title="Helpful reading"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleFeedback(m.id, "dislike")}
                      className={`p-1.5 rounded-lg border text-xs transition-all ${
                        feedbackState[m.id] === "dislike"
                          ? "bg-[#B21E68]/40 border-[#B21E68] text-[#F4B8DC] shadow-sm"
                          : "border-[#2D1F4D] text-[#A299BC] hover:text-white hover:border-[#B21E68]/40"
                      }`}
                      title="Not helpful"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Live Streaming Bubble */}
        {isStreaming && (
          <div className="flex flex-col items-start max-w-[96%]">
            <div className="p-4 sm:p-5 rounded-2xl rounded-tl-sm bg-[#161028] border border-[#B21E68]/60 text-[#E8E2F5] text-xs sm:text-sm shadow-xl space-y-2">
              <div className="flex items-center gap-2 text-xs text-[#F4B8DC] font-medium">
                <div className="w-3.5 h-3.5 border-2 border-[#F4B8DC] border-t-transparent rounded-full animate-spin" />
                <span>{streamStatus}</span>
              </div>
              <div>
                <MarkdownContent text={currentStreamAnswer || "Aligning chart facts..."} />
              </div>
            </div>
          </div>
        )}

        {/* Error State with Retry Button */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs space-y-2.5">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span className="font-semibold">Generation Interrupted</span>
            </div>
            <p className="leading-relaxed">{errorMessage}</p>
            <button
              onClick={() => handleAsk(lastQuestion)}
              disabled={isStreaming}
              className="px-3.5 py-1.5 rounded-xl bg-rose-600/30 border border-rose-400 text-white font-medium flex items-center gap-1.5 hover:bg-rose-600/50 text-xs active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isStreaming ? "animate-spin" : ""}`} />
              <span>{isStreaming ? "Connecting..." : "Retry Question"}</span>
            </button>
          </div>
        )}

        {/* Zero-Balance Promo Discount Card (Screenshot 2) */}
        {balance <= 0 && !isStreaming && messages.length > 0 && (
          <div className="p-4 rounded-2xl crystal-card border border-[#B21E68]/50 space-y-3 relative overflow-hidden">
            <div className="flex items-center gap-2 text-[#F4B8DC] text-xs font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{t("insufficientBalanceAlert", lang)}</span>
            </div>

            <div className="p-3.5 rounded-xl bg-gradient-to-tr from-[#24133F] via-[#351A52] to-[#1C0E33] border border-[#B21E68]/40 space-y-2 relative">
              <div className="flex items-center justify-between">
                <h4 className="font-serif text-xs sm:text-sm font-bold text-white">
                  {t("promoTitle", lang)}
                </h4>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E5A93C]/20 text-[#FDE68A] font-bold">
                  QUESTMORE
                </span>
              </div>
              <p className="text-[11px] text-[#DDD5EE] leading-relaxed">
                {t("promoDesc", lang)}
              </p>
              <button
                onClick={onOpenPaywall}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg active:scale-95 transition-all"
              >
                <span>{t("buyQuestionsNow", lang)}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Area - Lifted cleanly above BottomNav */}
      <div className="shrink-0 border-t border-[#23173D] pt-2 pb-1 bg-[#080511]">
        {/* Follow-up Question Chips (Feature 5: Conversational Continuity) */}
        {messages.length > 0 && !isStreaming && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 pt-0.5 no-scrollbar scroll-smooth">
            <span className="text-[10px] text-[#A299BC] font-medium shrink-0 flex items-center gap-1 pl-1">
              <Sparkles className="w-3 h-3 text-[#E5A93C]" />
              {t("followUpLabel", lang)}
            </span>
            {[
              t("followUp1", lang),
              t("followUp2", lang),
              t("followUp3", lang),
              t("followUp4", lang),
            ].map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleAsk(prompt)}
                className="shrink-0 px-2.5 py-1 rounded-full text-[11px] bg-[#1E1438] border border-[#3E2963] text-[#DDD5EE] hover:border-[#B21E68] hover:text-white transition-all active:scale-95 shadow-sm"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Balance status pill */}
        <div className="flex items-center justify-between text-[11px] mb-1.5 px-1">
          <span className="text-[#8E82AA]">
            {balance} {balance === 1 ? t("questionLeft", lang) : t("questionsLeft", lang)}
          </span>
          {balance <= 0 && (
            <button
              onClick={onOpenPaywall}
              className="text-[#F4B8DC] font-semibold hover:underline"
            >
              + {t("addFree", lang)}
            </button>
          )}
        </div>

        {/* Input Bar with Glowing Cosmic Glass Container */}
        <div className="p-1.5 pl-4 rounded-2xl bg-[#160A2A]/90 border border-[#521C68] shadow-[0_4px_24px_rgba(0,0,0,0.8),inset_0_1px_1px_rgba(244,184,220,0.2)] focus-within:border-[#F4B8DC] focus-within:shadow-[0_0_20px_rgba(216,34,126,0.45)] flex items-center gap-2 transition-all">
          <input
            type="text"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder={
              balance <= 0
                ? t("buyQuestionsNow", lang)
                : (animatedAskPlaceholder || " ")
            }
            disabled={isStreaming}
            className="flex-1 bg-transparent text-sm sm:text-[14.5px] text-white font-medium placeholder-white/80 focus:outline-none"
          />

          <button
            onClick={() => handleAsk()}
            disabled={isStreaming || !questionText.trim()}
            className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#931B58] via-[#B21E68] to-[#D8227E] text-white flex items-center justify-center disabled:opacity-40 transition-all shadow-md active:scale-95 shrink-0"
          >
            {isStreaming ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Past Check Modal (Shown right after free answer, before zero-balance paywall) */}
      {showPastCheck && (
        <PastCheckModal
          userId={user?.id || "default_user"}
          balance={balance}
          lang={lang}
          onComplete={() => {
            setShowPastCheck(false);
            setHasSeenPastCheck(true);
          }}
          onOpenPaywall={onOpenPaywall}
          onPreFillQuestion={(q) => {
            setQuestionText(q);
            handleAsk(q);
          }}
        />
      )}

      {/* Authentic Melooha Astrological References Bottom-Sheet Modal (Screenshot 5) */}
      {activeAstroModal && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col justify-end p-0 sm:p-4 animate-in fade-in duration-200"
          onClick={() => setActiveAstroModal(null)}
        >
          <div
            className="bg-gradient-to-b from-[#1C0E2F] via-[#140A24] to-[#0D0518] border-t sm:border border-[#B21E68]/60 rounded-t-3xl sm:rounded-3xl p-5 max-w-md mx-auto w-full max-h-[85vh] flex flex-col space-y-4 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Top drag handle */}
            <div className="w-10 h-1 bg-white/25 rounded-full mx-auto -mt-1 mb-1 sm:hidden" />

            {/* Modal Title & Close Button */}
            <div className="flex items-center justify-between pb-2 border-b border-[#301B4D]">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-[#FDE68A] flex items-center justify-center shadow-md">
                  <Sparkles className="w-4 h-4 text-[#FDE68A]" />
                </div>
                <h3 className="font-serif text-base font-bold text-white tracking-wide">
                  {lang === "hi" ? "ज्योतिषीय संदर्भ" : "Astrological References"}
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

            {/* Subtitle / User Question Context */}
            {activeAstroModal.questionText && (
              <p className="text-xs sm:text-[13px] text-[#DDD5EE] leading-snug line-clamp-2 italic px-0.5">
                "{activeAstroModal.questionText}"
              </p>
            )}

            {/* Checked References List matching Melooha Screenshot 5 */}
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
                  {lang === "hi" ? "जन्म चक्र के आधार पर मानक ग्रह गणना सत्यापित है।" : "Standard astrological baseline verified."}
                </div>
              )}
            </div>

            {/* Close and Continue Action Button */}
            <div className="pt-2 border-t border-[#291745]">
              <button
                type="button"
                onClick={() => setActiveAstroModal(null)}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#931B58] via-[#B21E68] to-[#D8227E] text-white font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-[#931B58]/40 active:scale-95 transition-all"
              >
                <span>{lang === "hi" ? "बंद करें और जारी रखें →" : "Close and Continue →"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
