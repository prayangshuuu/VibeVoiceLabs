"use client";

import { useEffect, useState } from "react";
import { Topbar } from "@/components/Topbar";
import { getVoices, type VoiceRow } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export default function VoicesPage() {
  const [rows, setRows] = useState<VoiceRow[] | null>(null);

  useEffect(() => {
    getVoices()
      .then(setRows)
      .catch(() => {
        toast.error("Failed to load voices");
        setRows([]);
      });
  }, []);

  return (
    <div className="min-h-screen">
      <Topbar
        title="Voices"
        subtitle="Presets from your backend /voices endpoint."
      />
      <div className="p-8">
        <Card className="max-w-3xl border-white/[0.08] bg-zinc-900/40">
          <CardHeader>
            <CardTitle>Installed presets</CardTitle>
            <p className="text-sm font-normal text-zinc-500">
              Run{" "}
              <code className="rounded-md bg-zinc-950 px-1.5 py-0.5 text-xs text-violet-300">
                python scripts/download_voices.py
              </code>{" "}
              in the backend if files show unavailable.
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {rows === null ? (
              <>
                <Skeleton className="h-14 w-full" />
                <Skeleton className="h-14 w-full" />
              </>
            ) : rows.length === 0 ? (
              <p className="text-sm text-zinc-500">No voice metadata returned.</p>
            ) : (
              rows.map((r) => (
                <div
                  key={r.id + r.filename}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-zinc-950/50 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-white">{r.label}</p>
                    <p className="text-xs text-zinc-500">{r.filename}</p>
                  </div>
                  <Badge
                    variant={
                      r.available === "True" ? "default" : "secondary"
                    }
                  >
                    {r.available === "True" ? "Available" : "Missing file"}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
