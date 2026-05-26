// GET /           … index.json から直近 briefing 一覧
// GET /<race-id>/  … そのレースの briefing/review 時系列リスト
// いずれも index.json (publish.py が更新) を真実の出所にする。

import { indexKey } from "../config.js";
import { getJson } from "../clients/r2.js";
import { htmlPage } from "../lib/markdown.js";

const RECENT_LIMIT = 30;

export async function renderHome(env) {
  const index = (await getJson(env, indexKey(env))) ?? { briefings: [] };
  const items = index.briefings.slice(0, RECENT_LIMIT).map(itemLine).join("\n");
  return page("keiba briefings", `<h1>keiba briefings</h1>\n<ul>\n${items}\n</ul>`);
}

export async function renderRace(env, raceId) {
  const index = (await getJson(env, indexKey(env))) ?? { briefings: [] };
  const entries = index.briefings.filter((b) => b.race_id === raceId);
  if (entries.length === 0) return new Response("not found", { status: 404 });
  const items = entries.map(itemLine).join("\n");
  return page(`${raceId} briefings`, `<h1>${raceId}</h1>\n<ul>\n${items}\n</ul>`);
}

function itemLine(b) {
  const tag = b.type === "review" ? "[review]" : "[briefing]";
  const at = b.generated_at ?? "";
  return `<li>${tag} <a href="${b.url}">${b.race_id}</a> <small>${at}</small> ` +
    `(<a href="${b.url}?html">html</a>)</li>`;
}

function page(title, body) {
  return new Response(htmlPage(title, body), {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}
