// keiba.iwachan.dev entrypoint: routing と workflow dispatch のみ。
// 認証は手前の CF Access (One-Time PIN) が担う (terraform/access.tf)。
// R2 read / HTML 整形は workflows/ 配下に閉じる。全 env / binding は config.js 参照。
import { assertRequiredEnv } from "./config.js";
import { renderHome, renderRace } from "./workflows/render_index.js";
import { serveAsset } from "./workflows/serve_asset.js";

const RACE_ID = /^\d{12}$/;

export default {
  async fetch(req, env) {
    try {
      assertRequiredEnv(env);
    } catch (e) {
      return new Response(e.message, { status: 500 });
    }
    if (req.method !== "GET") return new Response("method not allowed", { status: 405 });

    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean); // [] | [raceId] | [raceId, ...file]

    if (parts.length === 0) return renderHome(env);

    const [raceId, ...rest] = parts;
    if (!RACE_ID.test(raceId)) return new Response("not found", { status: 404 });

    if (rest.length === 0) return renderRace(env, raceId); // /<race-id>/
    return serveAsset(req, env, raceId, rest.join("/")); // /<race-id>/<file> (charts/<f> も)
  },
};
