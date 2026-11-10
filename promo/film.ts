// Ashariri's promo: the problem, the product, then each feature given room on the real UI (DOM snapshots from
// capture.mjs), and what's under the hood. 100 bpm; shots are counted in beats.
import { big, chips, eyebrow, grad, makeFilm, stream, sub } from "./kit/film";

const logo = `<div style="width:150px;height:150px;margin:0 auto;border-radius:44px;background:linear-gradient(135deg,#9b99ff,#6f9bff 50%,#5ac8fa);box-shadow:0 30px 80px -24px #6f9bff;display:grid;place-items:center"><div style="width:62px;height:62px;border-radius:50%;border:9px solid #fff"></div></div>`;
const { word, ui, run, BEAT } = makeFilm({
  name: "ashariri",
  style: "midnight",
  bpm: 100,
  bgs: { dark: ["#000", "#f5f5f7"], light: ["#f5f5f7", "#1d1d1f"], grad: ["linear-gradient(120deg,#5e5ce6,#3478f6 55%,#0a9fd6)", "#fff"] },
  grad: "linear-gradient(92deg, #9b99ff 0%, #6f9bff 45%, #5ac8fa 100%)",
  font: `"SF Pro Display", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif`,
  stage: "radial-gradient(1200px 700px at 50% 40%, #1a1a3a, #000)",
  caption: { bg: "rgba(20, 20, 28, .72)", ink: "#f5f5f7", shadow: "0 24px 60px -24px rgba(0,0,0,.8), 0 0 0 .5px rgba(255,255,255,.14)" },
  logo,
  css: `#type[data-bg=grad] .grad { -webkit-text-fill-color: #fff; }`,
});
const C = { x: 960, y: 540 };

// The hook: you can't be everywhere, and everyone has a question.
word(4, big("You can't be everywhere.", "s"), "dark");
word(7, `${big("But people still want you.", "s")}${sub("Friends with plans. Family with news. Strangers with questions. Recruiters with follow-ups.")}`, "light");
word(4, big(`What if your voice could ${grad("answer for you?")}`, "s"), "dark");
// The product, and its name.
word(6, `${logo}${big("Ashariri")}${sub("A digital twin that answers in my voice, grounded only in what I've actually said.")}`, "dark", { mark: "reveal", hit: true });
word(7, `${eyebrow("The name")}${big("A voice without a body.", "s")}${sub("From the Sanskrit aśarīrin, 'bodiless'. In Tamil, asariri is the voice from the sky, with no one there.")}`, "dark");
ui(6, { snap: "welcome", cam: [0.7, C, 0.78, C] });

// 1. Ask.
word(4, `${eyebrow("01 · Ask")}${big("Ask it anything.", "m")}${sub("Plans, ideas, life, work. In plain words.")}`, "dark");
const Q1 = "Are you free for a movie on Friday?";
ui(12, {
  snap: [[0, "welcome"], ...stream("ask", 3.2, 0.3)],
  type: { sel: ".composer textarea", text: Q1, from: 0.5, to: 2.6, until: 3.2 },
  cursor: { path: [[0, { x: 1300, y: 900 }], [2.7, ".composer .send"], [3.4, ".composer .send"], [4.4, { x: 1500, y: 700 }]], click: [2.9] },
  cam: [1.4, ".composer", 1.3, ".msg.user"],
  caption: ["Ask", "A friend's question, a streamed answer"],
});
ui(8, { snap: "ask-done", cam: [1.4, ".msg.twin .bubble", 1.55, ".msg.twin .bubble"], ring: [{ sel: ".msg.twin .cite", from: 1.6 }], caption: ["Honest", "It won't say yes for me, and it cites why"] });

// 2. Sources.
ui(8, {
  snap: [[0, "ask-done"], [1.4, "cite"]],
  cursor: { path: [[0, { x: 1000, y: 400 }], [1.0, ".msg.twin .cite"], [2.2, ".msg.twin .cite"]], click: [1.2] },
  cam: [1.6, ".msg.twin .cite", 1.55, ".source.hl"],
  ring: [{ sel: ".source.hl", from: 2.2 }],
  caption: ["Sources", "Tap a citation, read the passage"],
});

// 3. The hero: inside the agent.
word(4, big("Most AI is a black box.", "s"), "dark", { mark: "heroIn" });
word(4, big(grad("This one shows its work.")), "dark", { mark: "hero", hit: true });
ui(8, { snap: "ask-done", cam: [2.1, ".right .graph", 2.0, ".right .graph"], caption: ["Inside the agent", "A LangGraph state machine, live"] });
ui(8, { snap: "ask-done", cam: [1.85, ".right .outcome", 1.7, ".right .timeline"], caption: ["The trace", "Route · recall · retrieve · respond · review · remember"] });

// 4. Self-correction.
word(5, `${eyebrow("02 · Review")}${big("It checks its own work.", "s")}${sub("A reviewer fails weak drafts and sends them back to be rewritten.")}`, "dark");
ui(10, { snap: stream("revise", 0, 0.3), cam: [1.25, ".msg.user ~ .msg.user", 1.5, ".right .timeline"], caption: ["Self-correction", "Draft, review, revise"] });
ui(8, { snap: "revise-trace", cam: [1.8, ".right .t-fail", 1.65, ".right .t-fail"], ring: [{ sel: ".right .t-fail", from: 1.0 }], caption: ["Review failed", "So it revised, then passed"] }, { mark: "heroEnd" });

// 5. Guardrails.
word(5, `${eyebrow("03 · Boundaries")}${big("And it knows what not to say.", "s")}`, "dark");
ui(9, { snap: stream("decline", 0, 0.4), cam: [1.3, ".msg.twin .bubble", 1.45, ".msg.twin .bubble"], caption: ["Guardrails", "Private questions get a polite no"] });

// 6. Memory.
word(5, `${eyebrow("04 · Memory")}${big("It remembers you.", "m")}${sub("Only with your consent. See it, switch it off, erase it.")}`, "dark");
ui(9, { snap: stream("memory", 0, 0.3), cam: [1.3, ".msg.user", 1.4, ".msg.twin .bubble"], caption: ["Memory", "Tell it who you are"] });
ui(8, { snap: "memory-panel", cam: [1.9, ".memory", 2.1, ".memory"], ring: [{ sel: ".memory", from: 1.2 }], caption: ["Your data, your call", "What it kept, in plain sight"] });

// Light and dark.
word(2, big("Dark.", "m"), "dark");
ui(3, { snap: "ask-done", cam: [0.82, C, 0.86, C] });
word(2, big("Light.", "m"), "light");
ui(3, { snap: "light", cam: [0.82, C, 0.86, C] });

// The angles: how it's built, and who it's for.
word(8, `${eyebrow("Under the hood")}${big("A real agent, not a long prompt.", "s")}${chips("LangGraph", "Hybrid search", "LLM judge", "SSE streaming", "Evals in CI", "pgvector")}`, "light");
word(7, `${big("For friends and family, a quick answer.", "s")}${sub("For strangers and recruiters, a real conversation. For engineers, an agent you can trust.")}`, "dark");
word(8, `${eyebrow("Coming next")}${big(`Learns from what I've said. ${grad("Then acts for me.")}`, "s")}${sub("Posts, messages and talks, with sensitive things removed first. Then calendars and plans, with my approval.")}`, "light");
word(8, `${logo}${big(grad("Ashariri"))}${sub("Ask me anything · by Balaji Sri Raj")}`, "dark", { mark: "outro" });

run((m) => ({ teaser: [m.reveal, m.reveal + 36 * BEAT], poster: [m.hero + 6 * BEAT, 0] }));
