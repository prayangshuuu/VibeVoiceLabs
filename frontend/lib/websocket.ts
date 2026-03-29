const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/stream";

export type StreamPhase = "idle" | "start" | "chunk" | "end" | "error";

export interface StreamCallbacks {
  /** First progress / queued (maps product spec `start`) */
  onStart?: () => void;
  /** Each binary PCM frame (maps `chunk`) */
  onChunk?: (pcm: ArrayBuffer) => void;
  /** Generation finished (maps `end`) */
  onEnd?: () => void;
  onProgress?: (payload: Record<string, unknown>) => void;
  onError?: (message: string) => void;
}

/**
 * Sends synthesize command; server replies with JSON progress + binary PCM chunks.
 * Normalizes to start/chunk/end style callbacks for the UI.
 */
export function connectStream(
  text: string,
  voice: string | undefined,
  callbacks: StreamCallbacks,
  cfg_scale: number = 1.5
): { close: () => void } {
  const key = process.env.NEXT_PUBLIC_API_KEY;
  const url =
    key && !WS_URL.includes("api_key=")
      ? `${WS_URL}${WS_URL.includes("?") ? "&" : "?"}api_key=${encodeURIComponent(key)}`
      : WS_URL;
  const ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";

  let sawStart = false;

  ws.onopen = () => {
    ws.send(
      JSON.stringify({
        action: "synthesize",
        text,
        voice: voice || undefined,
        cfg_scale,
      })
    );
  };

  ws.onmessage = (ev) => {
    if (typeof ev.data !== "string") {
      callbacks.onChunk?.(ev.data as ArrayBuffer);
      if (!sawStart) {
        sawStart = true;
        callbacks.onStart?.();
      }
      return;
    }
    try {
      const msg = JSON.parse(ev.data) as Record<string, unknown>;
      if (msg.type === "error") {
        callbacks.onError?.(String(msg.detail ?? "Stream error"));
        return;
      }
      if (msg.type === "progress") {
        callbacks.onProgress?.(msg);
        const stage = msg.stage as string | undefined;
        if (stage === "start" && !sawStart) {
          sawStart = true;
          callbacks.onStart?.();
        }
        if (stage === "done") {
          callbacks.onEnd?.();
        }
      }
      if (msg.type === "audio_meta") {
        callbacks.onProgress?.(msg);
      }
    } catch {
      callbacks.onError?.("Invalid server message");
    }
  };

  ws.onerror = () => {
    callbacks.onError?.("WebSocket connection error");
  };

  return {
    close: () => {
      try {
        ws.close();
      } catch {
        /* ignore */
      }
    },
  };
}
