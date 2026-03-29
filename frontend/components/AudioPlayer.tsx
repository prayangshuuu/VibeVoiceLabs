"use client";

import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import { Loader2, Pause, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface AudioPlayerProps {
  src: string | null;
  loading?: boolean;
  title?: string;
}

export function AudioPlayer({
  src,
  loading = false,
  title = "Output",
}: AudioPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "rgba(113, 113, 122, 0.85)",
      progressColor: "rgba(167, 139, 250, 0.95)",
      cursorColor: "rgba(244, 244, 245, 0.5)",
      cursorWidth: 2,
      height: 88,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      normalize: true,
    });
    wsRef.current = ws;
    ws.on("ready", () => setReady(true));
    ws.on("play", () => setPlaying(true));
    ws.on("pause", () => setPlaying(false));
    ws.on("finish", () => setPlaying(false));
    ws.on("timeupdate", (t) => {
      const d = ws.getDuration();
      setProgress(d > 0 ? t / d : 0);
    });
    return () => {
      ws.destroy();
      wsRef.current = null;
      setReady(false);
    };
  }, []);

  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || !src) return;
    setReady(false);
    ws.load(src).catch(() => setReady(false));
  }, [src]);

  const toggle = () => {
    const ws = wsRef.current;
    if (!ws) return;
    ws.playPause();
  };

  return (
    <Card className="border-white/[0.08] bg-zinc-900/40">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="text-sm font-normal text-zinc-500">
          WaveSurfer waveform · play / pause
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-hidden rounded-2xl bg-zinc-950/80 ring-1 ring-white/5">
          {loading ? (
            <div className="flex h-[88px] items-center justify-center">
              <Loader2 className="size-6 animate-spin text-violet-400" />
            </div>
          ) : !src ? (
            <div className="flex h-[88px] items-center justify-center px-4">
              <Skeleton className="h-12 w-full max-w-md" />
            </div>
          ) : (
            <div ref={containerRef} className="w-full" />
          )}
        </div>

        <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-[width] duration-150"
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>

        <div className="flex items-center justify-between gap-4">
          <Button
            variant="secondary"
            size="icon"
            type="button"
            disabled={!src || !ready}
            onClick={toggle}
            aria-label={playing ? "Pause" : "Play"}
          >
            {playing ? (
              <Pause className="size-4" />
            ) : (
              <Play className="size-4 ml-0.5" />
            )}
          </Button>
          <p className="text-xs text-zinc-500">
            {!src
              ? "Generate or stream audio to load the waveform."
              : !ready
                ? "Loading waveform…"
                : "Ready"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
