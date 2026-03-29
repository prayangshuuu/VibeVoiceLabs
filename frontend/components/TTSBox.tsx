"use client";

import { useState } from "react";
import { Loader2, Radio, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { generateTTS, resolveAudioUrl, type TTSMode } from "@/lib/api";
import { pcmChunksToWavBlob } from "@/lib/audio";
import { connectStream } from "@/lib/websocket";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface TTSBoxProps {
  voice: string;
  onAudioUrl: (url: string | null) => void;
  playerLoading: boolean;
  setPlayerLoading: (v: boolean) => void;
}

export function TTSBox({
  voice,
  onAudioUrl,
  playerLoading,
  setPlayerLoading,
}: TTSBoxProps) {
  const [text, setText] = useState(
    "Welcome to VibeVoiceLabs — real-time voice synthesis running entirely on your machine."
  );
  const [mode, setMode] = useState<TTSMode>("default");
  const [tab, setTab] = useState<"rest" | "stream">("rest");
  const [busy, setBusy] = useState(false);
  const [streamLabel, setStreamLabel] = useState("");

  const cfgForMode =
    mode === "podcast" ? 1.65 : mode === "narration" ? 1.45 : 1.5;

  const handleGenerate = async () => {
    const t = text.trim();
    if (!t) {
      toast.error("Enter some text first.");
      return;
    }
    if (voice === "custom") {
      toast.error("Pick a voice preset (Custom is coming soon).");
      return;
    }
    setBusy(true);
    setPlayerLoading(true);
    onAudioUrl(null);
    try {
      const res = await generateTTS({
        text: t,
        voice,
        mode,
        cfg_scale: cfgForMode,
      });
      const url = resolveAudioUrl(res.audio_url);
      onAudioUrl(url);
      toast.success("Audio ready");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setBusy(false);
      setPlayerLoading(false);
    }
  };

  const runStream = () => {
    const t = text.trim();
    if (!t) {
      toast.error("Enter some text first.");
      return;
    }
    if (voice === "custom") {
      toast.error("Pick a voice preset.");
      return;
    }
    setBusy(true);
    setPlayerLoading(true);
    onAudioUrl(null);
    setStreamLabel("start");

    const chunks: ArrayBuffer[] = [];

    connectStream(
      t,
      voice,
      {
        onStart: () => setStreamLabel("start"),
        onChunk: (pcm) => {
          chunks.push(pcm);
          setStreamLabel("chunk");
        },
        onEnd: () => {
          setStreamLabel("end");
          try {
            const blob = pcmChunksToWavBlob(chunks, 24000);
            const objectUrl = URL.createObjectURL(blob);
            onAudioUrl(objectUrl);
            toast.success("Stream complete");
          } catch {
            toast.error("Could not build audio from stream");
          }
          setBusy(false);
          setPlayerLoading(false);
        },
        onError: (msg) => {
          toast.error(msg);
          setStreamLabel("error");
          setBusy(false);
          setPlayerLoading(false);
        },
        onProgress: (p) => {
          if (p.stage === "chunk" && typeof p.chunk_index === "number") {
            setStreamLabel(`chunk ${(p.chunk_index as number) + 1}`);
          }
        },
      },
      cfgForMode
    );
  };

  return (
    <Card className="border-white/[0.08] bg-zinc-900/40">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Synthesis</CardTitle>
        <p className="text-sm font-normal text-zinc-500">
          REST batch or WebSocket streaming
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex gap-2 rounded-2xl bg-zinc-950/60 p-1 ring-1 ring-white/5">
          <button
            type="button"
            onClick={() => setTab("rest")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === "rest"
                ? "bg-white/10 text-white shadow-sm"
                : "text-zinc-500 hover:text-zinc-300"
            )}
          >
            <Wand2 className="size-4" />
            Generate
          </button>
          <button
            type="button"
            onClick={() => setTab("stream")}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === "stream"
                ? "bg-white/10 text-white shadow-sm"
                : "text-zinc-500 hover:text-zinc-300"
            )}
          >
            <Radio className="size-4" />
            Live stream
          </button>
        </div>

        <div className="grid gap-2">
          <label className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Mode
          </label>
          <Select
            value={mode}
            onValueChange={(v) => setMode(v as TTSMode)}
            disabled={busy}
          >
            <SelectTrigger>
              <SelectValue placeholder="Mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="default">Default</SelectItem>
              <SelectItem value="podcast">Podcast</SelectItem>
              <SelectItem value="narration">Narration</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <label className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Script
          </label>
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type what you want spoken…"
            disabled={busy}
            className="min-h-[160px]"
          />
        </div>

        <Separator className="bg-white/10" />

        {tab === "rest" ? (
          <Button
            className="w-full"
            size="lg"
            disabled={busy || playerLoading}
            onClick={handleGenerate}
          >
            {busy || playerLoading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Generating…
              </>
            ) : (
              <>
                <Wand2 className="size-4" />
                Generate audio
              </>
            )}
          </Button>
        ) : (
          <div className="space-y-2">
            <Button
              className="w-full"
              size="lg"
              variant="secondary"
              disabled={busy || playerLoading}
              onClick={runStream}
            >
              {busy || playerLoading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  {streamLabel.startsWith("chunk")
                    ? `Receiving (${streamLabel})…`
                    : streamLabel === "start"
                      ? "Generating…"
                      : "Working…"}
                </>
              ) : (
                <>
                  <Radio className="size-4" />
                  Stream to player
                </>
              )}
            </Button>
            <p className="text-center text-xs text-zinc-500">
              Server sends progress + PCM chunks; UI maps to start → chunk → end.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
