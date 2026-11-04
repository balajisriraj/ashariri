import { useCallback, useEffect, useRef, useState } from "react";

// Web Speech API: recognition is still prefixed in Chromium and Safari, and absent in Firefox.
type Recognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start(): void;
  stop(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
};

const Ctor = (globalThis as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition })
  .SpeechRecognition ?? (globalThis as unknown as { webkitSpeechRecognition?: new () => Recognition }).webkitSpeechRecognition;

export function useVoice(onFinal: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const rec = useRef<Recognition | null>(null);
  const canListen = Boolean(Ctor);
  const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

  const listen = useCallback(() => {
    if (!Ctor) return;
    if (listening) return rec.current?.stop();
    const r = new Ctor();
    r.lang = "en-GB";
    r.interimResults = true;
    r.continuous = false;
    r.onresult = (e) => {
      const result = e.results[e.results.length - 1];
      const text = Array.from(e.results, (x) => x[0].transcript).join(" ");
      if (result.isFinal) {
        setInterim("");
        onFinal(text);
      } else setInterim(text);
    };
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    rec.current = r;
    setListening(true);
    r.start();
  }, [listening, onFinal]);

  const speak = useCallback(
    (text: string) => {
      if (!canSpeak) return;
      speechSynthesis.cancel();
      const clean = text.replace(/\[\d+\]/g, "").replace(/\*\*/g, "");
      const u = new SpeechSynthesisUtterance(clean);
      u.lang = "en-GB";
      u.rate = 1.02;
      speechSynthesis.speak(u);
    },
    [canSpeak],
  );

  useEffect(() => () => speechSynthesis?.cancel(), []);

  return { canListen, canSpeak, listening, interim, listen, speak };
}
