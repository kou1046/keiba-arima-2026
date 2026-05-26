// Worker の全 env var / binding / 定数を 1 箇所に集約 (worker-lambda-structure)。
// keiba.iwachan.dev フロント。CF Access (One-Time PIN) が edge で認証済の前提で、
// この Worker は R2 の keiba/ prefix を読み出して配信するだけ。

export const ENV_VARS = {
  KEIBA_R2: {
    required: true,
    source: "binding", // wrangler.toml [[r2_buckets]] (iwachan-general)
    purpose: "公開ストレージ。keiba/ prefix 配下の briefing md / chart svg / index.json",
  },
  R2_PREFIX: {
    required: true,
    source: "vars",
    purpose: "R2 上の居住 prefix (既定 'keiba')",
  },
};

export function assertRequiredEnv(env) {
  const missing = Object.entries(ENV_VARS)
    .filter(([, spec]) => spec.required)
    .filter(([name]) => !env[name])
    .map(([name]) => name);
  if (missing.length) throw new Error(`missing env: ${missing.join(", ")}`);
}

// R2 key の組み立て: 公開 URL の <race-id>/... を keiba/briefings/<race-id>/... に写す。
export function briefingsPrefix(env) {
  return `${env.R2_PREFIX}/briefings`;
}

export function indexKey(env) {
  return `${env.R2_PREFIX}/index.json`;
}

// content-type 推定 (拡張子ベース)。
export function contentTypeFor(path) {
  if (path.endsWith(".md")) return "text/markdown; charset=utf-8";
  if (path.endsWith(".svg")) return "image/svg+xml";
  if (path.endsWith(".json")) return "application/json";
  return "application/octet-stream";
}
