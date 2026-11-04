// Pass 1 of the promo: run the real Ashariri (the API with the scripted model, and the Vite UI), drive it like a
// visitor would, and save DOM snapshots of each moment to promo/out/snaps. Pass 2 (kit/render.mjs) films them.
//
//   cd promo && pnpm install && node capture.mjs
import { rmSync } from "node:fs";
import { resolve } from "node:path";
import { freePort, launch, serve, sleep, snapper, until } from "./kit/snap.mjs";

const ROOT = resolve(import.meta.dirname, "..");
const SNAPS = resolve(import.meta.dirname, "out/snaps");
rmSync(SNAPS, { recursive: true, force: true });
const data = resolve(import.meta.dirname, "out/data");
rmSync(data, { recursive: true, force: true });

const api = await freePort();
const web = await freePort();
const stopApi = await serve("uv", ["run", "ashariri", "serve", "--port", String(api)], {
  cwd: resolve(ROOT, "backend"),
  env: { ASHARIRI_LLM: "scripted", ASHARIRI_SCRIPTED_DELAY: "0.05", ASHARIRI_SQLITE_PATH: resolve(data, "promo.db") },
  url: `http://127.0.0.1:${api}/api/health`,
});
const stopWeb = await serve("pnpm", ["exec", "vite", "--host", "127.0.0.1", "--port", String(web), "--strictPort"], {
  cwd: resolve(ROOT, "frontend"),
  env: { ASHARIRI_API: `http://127.0.0.1:${api}` },
  url: `http://127.0.0.1:${web}/`,
});

const { browser, page } = await launch();
await page.goto(`http://127.0.0.1:${web}/`);
await page.evaluate(() => (localStorage.clear(), localStorage.setItem("ashariri.theme", "dark")));
await page.reload();
await until(page, () => document.querySelector(".welcome") && document.querySelector(".status"));
await sleep(400);
const raw = snapper(page, SNAPS);
// The self-correction demo uses the scripted judge's test marker; keep it out of the picture.
const shot = async (name) => {
  await page.evaluate(() => document.querySelectorAll(".msg.user p, .episodes li").forEach((p) => (p.textContent = p.textContent.replace(" [[FORCE_REVISE]]", ""))));
  await raw(name);
};
const idle = () => !document.querySelector(".composer .send[aria-label=Stop]");

/** Ask a question and snapshot the reply as it streams, then once more when it settles. */
async function ask(prefix, question) {
  await page.click(".composer textarea");
  await page.keyboard.type(question, { delay: 6 });
  await page.keyboard.press("Enter");
  await sleep(120);
  let i = 0;
  for (; i < 60; i++) {
    await shot(`${prefix}-${String(i).padStart(2, "0")}`);
    if (await page.evaluate(idle)) break;
    await sleep(260);
  }
  await sleep(900);
  await shot(`${prefix}-done`);
  console.log(`${prefix}: ${i + 1} frames`);
}

await shot("welcome");
await ask("ask", "Tell me about the self-healing document intelligence product.");
// A citation opens its source in the inspector.
await page.click(".msg.twin .cite");
await sleep(700);
await shot("cite");
// Self-correction: the review fails the first draft and sends it back.
await ask("revise", "What makes something an agent rather than a chatbot? [[FORCE_REVISE]]");
await page.evaluate(() => document.querySelector(".right .timeline")?.scrollIntoView({ block: "start" }));
await sleep(300);
await shot("revise-trace");

// Guardrails: a private question gets a polite decline, no retrieval.
await page.click(".actions .ghost");
await sleep(500);
await ask("decline", "What's your salary and home address?");

// Memory: tell it who you are, then see what it kept.
await page.click(".actions .ghost");
await sleep(500);
await ask("memory", "Hi, I'm Priya, I hire for AI teams. What's in the Lab right now?");
await page.evaluate(() => document.querySelector(".memory")?.scrollIntoView({ block: "center" }));
await sleep(500);
await shot("memory-panel");

// Light theme.
await page.click(".actions .icon");
await sleep(600);
await shot("light");

await browser.close();
stopWeb();
stopApi();
console.log(`${raw.names.length} snapshots in promo/out/snaps`);
process.exit(0);
