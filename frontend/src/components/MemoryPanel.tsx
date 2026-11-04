import type { Memory } from "../api";

export function MemoryPanel({
  memories,
  remember,
  onToggle,
  onForget,
}: {
  memories: Memory[];
  remember: boolean;
  onToggle: (on: boolean) => void;
  onForget: () => void;
}) {
  const facts = memories.filter((m) => m.kind === "fact");
  const episodes = memories.filter((m) => m.kind === "episode");
  return (
    <section className="memory">
      <header>
        <h3>Memory</h3>
        <label className="switch">
          <input type="checkbox" checked={remember} onChange={(e) => onToggle(e.target.checked)} />
          <span aria-hidden="true" />
          <em>{remember ? "On" : "Off"}</em>
        </label>
      </header>
      <p className="hint">
        {remember
          ? "I keep what you tell me about yourself and a gist of what we discussed, only for this browser."
          : "Memory is off. Nothing from this conversation is stored."}
      </p>
      {facts.length > 0 && (
        <>
          <h4>About you</h4>
          <ul>
            {facts.map((m) => (
              <li key={m.id}>{m.text}</li>
            ))}
          </ul>
        </>
      )}
      {episodes.length > 0 && (
        <>
          <h4>We talked about</h4>
          <ul className="episodes">
            {episodes.slice(-5).map((m) => (
              <li key={m.id}>{m.text.split(" | ")[0].replace("They asked: ", "")}</li>
            ))}
          </ul>
        </>
      )}
      {memories.length > 0 && (
        <button className="ghost danger" onClick={onForget}>
          Forget everything
        </button>
      )}
    </section>
  );
}
