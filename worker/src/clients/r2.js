// R2 binding helper。worker 内部からの read / list のみ (書き込みは GH Actions の publish.py)。
// bucket は cross-project 共有 iwachan-general、keiba/ prefix 配下。

export async function getObject(env, key) {
  return await env.KEIBA_R2.get(key);
}

export async function getJson(env, key) {
  const obj = await env.KEIBA_R2.get(key);
  if (!obj) return null;
  return await obj.json();
}

// prefix 配下の key を列挙 (race ごとの briefing 一覧表示に使う)。
export async function listKeys(env, prefix) {
  const out = [];
  let cursor;
  do {
    const res = await env.KEIBA_R2.list({ prefix, cursor });
    for (const o of res.objects) out.push(o.key);
    cursor = res.truncated ? res.cursor : undefined;
  } while (cursor);
  return out;
}
