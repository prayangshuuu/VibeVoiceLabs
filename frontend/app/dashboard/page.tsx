"use client";

import { useState } from "react";
import { Topbar } from "@/components/Topbar";
import { VoiceSelector } from "@/components/VoiceSelector";
import { TTSBox } from "@/components/TTSBox";
import { AudioPlayer } from "@/components/AudioPlayer";

export default function DashboardPage() {
  const [voice, setVoice] = useState("carter");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playerLoading, setPlayerLoading] = useState(false);

  return (
    <div className="min-h-screen">
      <Topbar
        title="Generate"
        subtitle="Batch TTS and live streaming against your local FastAPI backend."
      />
      <div className="mx-auto max-w-5xl space-y-8 p-8">
        <div className="grid gap-8 lg:grid-cols-5">
          <div className="space-y-8 lg:col-span-2">
            <VoiceSelector value={voice} onChange={setVoice} />
          </div>
          <div className="space-y-8 lg:col-span-3">
            <TTSBox
              voice={voice}
              onAudioUrl={setAudioUrl}
              playerLoading={playerLoading}
              setPlayerLoading={setPlayerLoading}
            />
          </div>
        </div>
        <AudioPlayer src={audioUrl} loading={playerLoading} />
      </div>
    </div>
  );
}
