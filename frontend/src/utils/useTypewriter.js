import { useState, useEffect, useRef } from "react";

/**
 * Custom hook for a smooth typewriter effect that forms sentences character-by-character,
 * pauses at full sentence, backspaces character-by-character, and transitions seamlessly
 * into the next phrase without jarring flashes or fallback text jumpiness.
 *
 * @param {string[]} phrases - Array of sentences to cycle through
 * @param {object} options - Animation timings
 * @returns {string} current rendered string
 */
export function useTypewriter(
  phrases = [],
  {
    typingSpeed = 50,
    deletingSpeed = 25,
    pauseMs = 2200,
    emptyPauseMs = 240,
    enabled = true,
  } = {}
) {
  // Pre-seed with the first phrase so the UI never starts blank or stutters on load
  const [displayText, setDisplayText] = useState(() => (phrases && phrases[0] ? phrases[0] : ""));
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const lastPhrasesRef = useRef(phrases);

  // If phrases array changes (e.g. language toggle), smoothly sync to the new language
  useEffect(() => {
    if (
      phrases.length > 0 &&
      (lastPhrasesRef.current.length === 0 || lastPhrasesRef.current[0] !== phrases[0])
    ) {
      lastPhrasesRef.current = phrases;
      setDisplayText(phrases[0] || "");
      setIsDeleting(false);
      setPhraseIndex(0);
    }
  }, [phrases]);

  useEffect(() => {
    if (!enabled || !phrases || phrases.length === 0) return;

    const currentPhrase = phrases[phraseIndex % phrases.length] || "";

    let timer;

    if (!isDeleting) {
      // Typing forward
      if (displayText.length < currentPhrase.length) {
        timer = setTimeout(() => {
          setDisplayText(currentPhrase.slice(0, displayText.length + 1));
        }, typingSpeed);
      } else {
        // Sentence is fully formed -> hold for comfortable reading before backspacing
        timer = setTimeout(() => {
          setIsDeleting(true);
        }, pauseMs);
      }
    } else {
      // Backspacing backward
      if (displayText.length > 0) {
        timer = setTimeout(() => {
          setDisplayText(currentPhrase.slice(0, displayText.length - 1));
        }, deletingSpeed);
      } else {
        // Fully erased -> pause seamlessly, then advance to next sentence
        timer = setTimeout(() => {
          setIsDeleting(false);
          setPhraseIndex((prev) => (prev + 1) % phrases.length);
        }, emptyPauseMs);
      }
    }

    return () => clearTimeout(timer);
  }, [
    displayText,
    isDeleting,
    phraseIndex,
    phrases,
    typingSpeed,
    deletingSpeed,
    pauseMs,
    emptyPauseMs,
    enabled,
  ]);

  return displayText;
}

export default useTypewriter;
