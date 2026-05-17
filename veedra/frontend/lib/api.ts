import { createClient } from '@/lib/supabase/client';

const BASE = '/api/backend'; // proxied by next.config rewrites

async function authHeaders(): Promise<HeadersInit> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { headers: await authHeaders() });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export async function apiPost<T>(path: string, body: any): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...(await authHeaders()) },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

/**
 * Opens an SSE stream against the backend. Calls onEvent for every message,
 * resolves the returned promise when the server closes the stream.
 *
 * Note: native EventSource can't set Authorization headers; we use fetch +
 * a ReadableStream reader and parse SSE manually so we can attach the token.
 */
export async function apiSSE(
  path: string,
  onEvent: (evt: { event: string; data: any }) => void,
): Promise<void> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { accept: 'text/event-stream', ...(await authHeaders()) },
  });
  if (!r.ok || !r.body) throw new Error(`SSE failed: ${r.status}`);
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const lines = raw.split('\n');
      let event = 'message';
      let data = '';
      for (const ln of lines) {
        if (ln.startsWith('event:')) event = ln.slice(6).trim();
        else if (ln.startsWith('data:')) data += ln.slice(5).trim();
      }
      if (!data) continue;
      try { onEvent({ event, data: JSON.parse(data) }); }
      catch { onEvent({ event, data }); }
    }
  }
}
