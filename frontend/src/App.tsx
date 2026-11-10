import { useCallback, useEffect, useRef, useState } from "react";
import { forgetMemories, getHealth, getMemories, getPersona, type Health, type Memory, type Persona } from "./api";
import { Answer } from "./components/Answer";
import { Icon } from "./components/Icon";
import { Inspector } from "./components/Inspector";
import { MemoryPanel } from "./components/MemoryPanel";
import { sessionId, useTwin } from "./useTwin";
import { useVoice } from "./useVoice";

// Shown until the API answers, and if a persona file has no suggestions of its own.
const FALLBACK: Persona = {
  name: "",
  short_name: "",
  role: "",
  avatar: "/avatar.svg",
  tagline: "Digital twin",
  greeting: "Ask about my work, what I'm building and how I think.",
  suggestions: ["What do you do?", "What are you building right now?", "What are you reading?"],
};

type Tab = "chat" | "agent" | "memory";

export function App() {
  const [theme, setTheme] = useState<"dark" | "light">(() =>
    (localStorage.getItem("ashariri.theme") as "dark" | "light") ??
    (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"),
  );
  const [remember, setRemember] = useState(() => localStorage.getItem("ashariri.remember") !== "off");
  const [speakReplies, setSpeakReplies] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [persona, setPersona] = useState<Persona>(FALLBACK);
  const [offline, setOffline] = useState(false);
  const [draft, setDraft] = useState("");
  const [highlight, setHighlight] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("chat");
  const thread = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  const refreshMemory = useCallback(() => {
    getMemories(sessionId()).then(setMemories).catch(() => {});
  }, []);
  const { messages, send, stop, clear, busy, selected, setSelected } = useTwin(remember, refreshMemory);
  const voice = useVoice((text) => send(text));

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("ashariri.theme", theme);
  }, [theme]);
  useEffect(() => localStorage.setItem("ashariri.remember", remember ? "on" : "off"), [remember]);
  useEffect(() => {
    getHealth()
      .then((h) => (setHealth(h), setOffline(false)))
      .catch(() => setOffline(true));
    getPersona()
      .then((p) => {
        setPersona({ ...p, suggestions: p.suggestions.length ? p.suggestions : FALLBACK.suggestions });
        document.title = `Ashariri · ${p.tagline}`;
      })
      .catch(() => {});
    refreshMemory();
  }, [refreshMemory]);

  // Deep link: /?q=... asks a question on load (the portfolio links straight into the twin).
  const asked = useRef(false);
  useEffect(() => {
    const q = new URLSearchParams(location.search).get("q");
    if (q && !asked.current) {
      asked.current = true;
      history.replaceState(null, "", location.pathname);
      send(q);
    }
  }, [send]);

  // Keep the newest tokens in view while streaming.
  const last = messages[messages.length - 1];
  useEffect(() => {
    thread.current?.scrollTo({ top: thread.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, last?.text]);

  // Read finished replies aloud when voice replies are on.
  const spoken = useRef<string | null>(null);
  useEffect(() => {
    if (speakReplies && last?.role === "assistant" && !last.streaming && last.text && spoken.current !== last.id) {
      spoken.current = last.id;
      voice.speak(last.text);
    }
  }, [last, speakReplies, voice]);

  const submit = () => {
    if (!draft.trim()) return;
    send(draft);
    setDraft("");
  };

  const cite = (messageId: string, n: number) => {
    setSelected(messageId);
    setHighlight(n);
    setTab("agent");
    requestAnimationFrame(() => document.getElementById(`src-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
  };

  const inspected = messages.find((m) => m.id === selected);
  const who = persona.short_name || "the persona";

  return (
    <div className={`app tab-${tab}`}>
      <header className="top">
        <div className="brand">
          <img src={persona.avatar} alt="" width="34" height="34" />
          <div>
            <b>Ashariri</b>
            <span>{persona.tagline}</span>
          </div>
        </div>
        <nav className="tabs" aria-label="Panels">
          {(["chat", "agent", "memory"] as Tab[]).map((t) => (
            <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
              {t === "chat" ? "Chat" : t === "agent" ? "Agent" : "Memory"}
            </button>
          ))}
        </nav>
        <div className="actions">
          {health && (
            <span className="status" title={`${health.embedder} embeddings · ${health.passages} passages`}>
              <i className="live" /> {health.model} · {health.store}
            </span>
          )}
          {offline && (
            <span className="status off">
              <i /> API offline
            </span>
          )}
          <button className="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme">
            <Icon name={theme === "dark" ? "sun" : "moon"} />
          </button>
          <button className="ghost" onClick={clear} disabled={!messages.length}>
            New chat
          </button>
        </div>
      </header>

      <aside className="left">
        <section className="about">
          <h3>What this is</h3>
          <p>
            An agent that answers as {who}, grounded in their own writing and work. Every reply is routed,
            retrieved, drafted, then reviewed against the persona's boundaries before you see it.
          </p>
          <ul className="facts">
            <li>
              <b>LangGraph</b> state machine with a self-correction loop
            </li>
            <li>
              <b>Hybrid retrieval</b>: vectors + BM25, fused by rank
            </li>
            <li>
              <b>Guardrails</b>: deterministic rules + an LLM judge
            </li>
            <li>
              <b>Memory</b> you can see, switch off and erase
            </li>
          </ul>
        </section>
        <MemoryPanel
          memories={memories}
          remember={remember}
          onToggle={setRemember}
          onForget={() => forgetMemories(sessionId()).then(refreshMemory)}
        />
      </aside>

      <main className="chat">
        <div className="thread" ref={thread} aria-live="polite">
          {messages.length === 0 ? (
            <div className="welcome">
              <img src={persona.avatar} alt={`${who}'s avatar`} width="112" height="112" />
              <h1>
                Hi, I'm <span className="grad">{persona.short_name ? `${persona.short_name}'s twin.` : "a digital twin."}</span>
              </h1>
              <p>{persona.greeting}</p>
              <div className="suggest">
                {persona.suggestions.map((s) => (
                  <button key={s} onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) =>
              m.role === "user" ? (
                <div key={m.id} className="msg user">
                  <p>{m.text}</p>
                </div>
              ) : (
                <div
                  key={m.id}
                  className={`msg twin ${selected === m.id ? "sel" : ""} ${m.error ? "err" : ""}`}
                  onClick={() => setSelected(m.id)}
                >
                  <img src={persona.avatar} alt="" width="28" height="28" />
                  <div className="bubble">
                    {m.text ? (
                      <Answer text={m.text} onCite={(n) => cite(m.id, n)} />
                    ) : (
                      <p className="thinking">
                        <span />
                        <span />
                        <span />
                        {m.steps?.length ? ` ${m.steps[m.steps.length - 1].node}…` : ""}
                      </p>
                    )}
                    {m.streaming && m.text && <span className="caret" />}
                    {!m.streaming && m.outcome === "revised" && <span className="tag">self-corrected</span>}
                  </div>
                </div>
              ),
            )
          )}
        </div>

        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <textarea
            ref={input}
            value={voice.listening ? voice.interim || "Listening…" : draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask me anything…"
            rows={1}
            maxLength={2000}
            aria-label="Message"
          />
          {voice.canSpeak && (
            <button
              type="button"
              className={`icon ${speakReplies ? "on" : ""}`}
              onClick={() => (setSpeakReplies(!speakReplies), speechSynthesis.cancel())}
              aria-pressed={speakReplies}
              title="Read replies aloud"
            >
              <Icon name="speaker" />
            </button>
          )}
          {voice.canListen && (
            <button
              type="button"
              className={`icon ${voice.listening ? "rec" : ""}`}
              onClick={voice.listen}
              title="Speak your question"
              aria-pressed={voice.listening}
            >
              <Icon name="mic" />
            </button>
          )}
          {busy ? (
            <button type="button" className="send" onClick={stop} aria-label="Stop">
              <Icon name="stop" />
            </button>
          ) : (
            <button type="submit" className="send" disabled={!draft.trim()} aria-label="Send">
              <Icon name="send" />
            </button>
          )}
        </form>
        <p className="disclaimer">Grounded in {who}'s own writing and work. It can still be wrong.</p>
      </main>

      <aside className="right">
        <h2>
          Inside the agent <span>{inspected ? "selected reply" : "waiting"}</span>
        </h2>
        <Inspector message={inspected} highlight={highlight} />
      </aside>
    </div>
  );
}
