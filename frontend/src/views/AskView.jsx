import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, RefreshCw, AlertCircle, ShieldCheck, Compass } from "lucide-react";

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
  onOpenPaywall,
  onOpenEvidence,
  initialQuestion,
  onQuestionCompleted,
}) {
  const [questionText, setQuestionText] = useState(initialQuestion || "");
  const [lastQuestion, setLastQuestion] = useState(initialQuestion || "");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const [messages, setMessages] = useState([]);
  const [currentStreamAnswer, setCurrentStreamAnswer] = useState("");
  const [errorMessage, setErrorMessage] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamAnswer]);

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
        finalProvider = d.provider;
      });

      eventSource.addEventListener("replace", (e) => {
        const d = JSON.parse(e.data);
        accumulatedAnswer = d.answer;
        setCurrentStreamAnswer(d.answer);
        citedFacts = d.cited_facts || [];
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
            cited_facts: citedFacts,
            provider: finalProvider,
            replacedReason: replacedReason,
          },
        ]);
        setCurrentStreamAnswer("");
        onQuestionCompleted();
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
    <div className="flex flex-col h-[calc(100dvh-64px)] max-w-md mx-auto px-4 pb-[84px]">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pt-3 pb-3">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-10 px-4">
            <div className="w-14 h-14 rounded-full bg-[#1A1230] border border-[#B21E68]/40 flex items-center justify-center text-[#E5A93C] mx-auto mb-3">
              <Sparkles className="w-7 h-7" />
            </div>
            <h3 className="font-serif text-lg font-bold text-white">
              Ask Vaani Astrologer
            </h3>
            <p className="text-xs text-[#A299BC] max-w-xs mx-auto mt-1 leading-relaxed">
              Ask about career shifts, relationship compatibility, or life timing. Answers are 100% grounded in your birth chart.
            </p>
          </div>
        )}

        {/* Existing Messages */}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
          >
            {m.role === "user" ? (
              <div className="max-w-[85%] p-3.5 rounded-2xl rounded-tr-sm bg-gradient-to-r from-[#931B58] to-[#B21E68] text-white text-xs sm:text-sm font-medium shadow-md">
                {m.text}
              </div>
            ) : (
              <div className="max-w-[96%] p-4 sm:p-5 rounded-2xl rounded-tl-sm bg-[#161028] border border-[#2D1F4D] text-[#E8E2F5] text-xs sm:text-sm shadow-md space-y-3">
                {/* Formatted & Indented Answer Text */}
                <MarkdownContent text={m.text} />

                {m.replacedReason && (
                  <div className="p-2 rounded-lg bg-[#E5A93C]/10 border border-[#E5A93C]/30 text-[#E5A93C] text-[11px] flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                    <span>Safe Grounded Reading enforced</span>
                  </div>
                )}

                {/* Evidence Chips */}
                {m.cited_facts && m.cited_facts.length > 0 && (
                  <div className="pt-2.5 border-t border-[#2A1D45]">
                    <span className="text-[10px] uppercase tracking-wider text-[#9E92BA] font-semibold block mb-1.5">
                      Chart Evidence Used (Tap to verify)
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {m.cited_facts.map((f) => (
                        <button
                          key={f.id}
                          onClick={() => handleEvidenceClick(f)}
                          className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#B21E68]/15 border border-[#B21E68]/45 text-[#F4B8DC] hover:bg-[#B21E68]/30 transition-all flex items-center gap-1.5 active:scale-95"
                        >
                          <Compass className="w-3 h-3 text-[#E5A93C]" />
                          <span>{f.id}: {f.subject}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
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

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Area - Lifted cleanly above BottomNav */}
      <div className="shrink-0 border-t border-[#23173D] pt-2 pb-1 bg-[#080511]">
        {/* Balance status pill */}
        <div className="flex items-center justify-between text-[11px] mb-1.5 px-1">
          <span className="text-[#8E82AA]">
            {balance} question credit remaining
          </span>
          {balance <= 0 && (
            <button
              onClick={onOpenPaywall}
              className="text-[#F4B8DC] font-semibold hover:underline"
            >
              + Add Free Questions
            </button>
          )}
        </div>

        {/* Input Bar */}
        <div className="glass-panel p-1.5 pl-3 flex items-center gap-2">
          <input
            type="text"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder={balance <= 0 ? "Top up to ask your next question..." : "Ask your astrology question..."}
            disabled={isStreaming}
            className="flex-1 bg-transparent text-sm text-white placeholder-[#786B94] focus:outline-none"
          />

          <button
            onClick={() => handleAsk()}
            disabled={isStreaming || !questionText.trim()}
            className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#931B58] to-[#B21E68] text-white flex items-center justify-center disabled:opacity-40 transition-all shadow-md active:scale-95 shrink-0"
          >
            {isStreaming ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
