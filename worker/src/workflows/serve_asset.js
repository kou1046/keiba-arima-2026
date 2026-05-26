// GET /<race-id>/<file>  … R2 の keiba/briefings/<race-id>/<file> をそのまま配信。
// .md は既定 raw (text/markdown、Claude が読む)、?html クエリで HTML wrap (人間ブラウザ)。

import { briefingsPrefix, contentTypeFor } from "../config.js";
import { getObject } from "../clients/r2.js";
import { htmlPage, mdToHtml } from "../lib/markdown.js";

export async function serveAsset(req, env, raceId, file) {
  const key = `${briefingsPrefix(env)}/${raceId}/${file}`;
  const obj = await getObject(env, key);
  if (!obj) return new Response("not found", { status: 404 });

  const wantHtml = new URL(req.url).searchParams.has("html");
  if (file.endsWith(".md") && wantHtml) {
    const md = await obj.text();
    return html(htmlPage(`${raceId} briefing`, mdToHtml(md)));
  }
  return new Response(obj.body, {
    headers: { "Content-Type": contentTypeFor(file), "Cache-Control": cacheControl(raceId) },
  });
}

// 過去年のレースの briefing は事実上 immutable なので長めに cache。当年は更新があり得るので短く。
function cacheControl(raceId) {
  const year = parseInt(raceId.slice(0, 4), 10);
  const immutable = Number.isFinite(year) && year < new Date().getUTCFullYear();
  return immutable ? "public, max-age=86400" : "public, max-age=300";
}

function html(body) {
  return new Response(body, { headers: { "Content-Type": "text/html; charset=utf-8" } });
}
