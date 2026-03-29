const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

function headers(json = false): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["Content-Type"] = "application/json";
  const key = process.env.NEXT_PUBLIC_API_KEY;
  if (key) h["X-API-Key"] = key;
  return h;
}

export type TTSMode = "default" | "podcast" | "narration";

export interface TTSRequestBody {
  text: string;
  voice?: string;
  mode?: TTSMode;
  cfg_scale?: number;
}

export interface TTSResponse {
  filename: string;
  output_path: string;
  audio_url: string;
  message?: string;
}

export interface VoiceRow {
  id: string;
  label: string;
  available: string;
  filename: string;
}

export async function getVoices(): Promise<VoiceRow[]> {
  const res = await fetch(`${API_BASE}/voices`, {
    cache: "no-store",
    headers: headers(),
  });
  if (!res.ok) throw new Error(`Voices failed: ${res.status}`);
  const data = (await res.json()) as { voices: VoiceRow[] };
  return data.voices ?? [];
}

export async function generateTTS(body: TTSRequestBody): Promise<TTSResponse> {
  const res = await fetch(`${API_BASE}/tts`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({
      text: body.text,
      voice: body.voice,
      mode: body.mode,
      cfg_scale: body.cfg_scale ?? 1.5,
    }),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = (j as { detail?: string }).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<TTSResponse>;
}

export function resolveAudioUrl(audioUrlFromServer: string): string {
  if (audioUrlFromServer.startsWith("http")) return audioUrlFromServer;
  return `${API_BASE}${audioUrlFromServer.startsWith("/") ? "" : "/"}${audioUrlFromServer}`;
}
