import { Fragment, type ReactNode } from "react";

// Replies are short markdown-ish text: paragraphs, **bold**, "- " bullets and [n] citations.
// Rendered as React nodes, never as HTML, so model output can't inject markup.
function inline(text: string, onCite: (n: number) => void): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, i) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite)
      return (
        <button key={i} className="cite" onClick={() => onCite(Number(cite[1]))} aria-label={`Source ${cite[1]}`}>
          {cite[1]}
        </button>
      );
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function Answer({ text, onCite }: { text: string; onCite: (n: number) => void }) {
  return (
    <>
      {text
        .trim()
        .split(/\n\s*\n/)
        .map((block, i) => {
          const lines = block.split("\n");
          if (lines.every((l) => /^\s*[-*] /.test(l)))
            return (
              <ul key={i}>
                {lines.map((l, j) => (
                  <li key={j}>{inline(l.replace(/^\s*[-*] /, ""), onCite)}</li>
                ))}
              </ul>
            );
          return <p key={i}>{inline(block, onCite)}</p>;
        })}
    </>
  );
}
