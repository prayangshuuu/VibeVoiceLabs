"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { toast } from "sonner";
import { getVoices, type VoiceRow } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const FALLBACK: { id: string; label: string }[] = [
  { id: "carter", label: "Carter" },
  { id: "emma", label: "Emma" },
  { id: "davis", label: "Davis" },
  { id: "grace", label: "Grace" },
  { id: "custom", label: "Custom (soon)" },
];

interface VoiceSelectorProps {
  value: string;
  onChange: (id: string) => void;
}

export function VoiceSelector({ value, onChange }: VoiceSelectorProps) {
  const [rows, setRows] = useState<VoiceRow[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const v = await getVoices();
        if (!cancelled) setRows(v);
      } catch {
        if (!cancelled) {
          setRows([]);
          toast.error("Could not load voices — using defaults.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const presets =
    rows && rows.length > 0
      ? [
          ...rows
            .filter((r) => r.available === "True" || r.available === "true")
            .map((r) => ({ id: r.id, label: r.label })),
          { id: "custom", label: "Custom (soon)" },
        ]
      : FALLBACK;

  return (
    <Card className="border-white/[0.08] bg-zinc-900/40">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Voice</CardTitle>
        <p className="text-sm font-normal text-zinc-500">
          Card-style selector — tap a preset
        </p>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {presets.map((p) => {
              const disabled = p.id === "custom";
              const selected = value === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  disabled={disabled}
                  onClick={() => !disabled && onChange(p.id)}
                  className={cn(
                    "relative flex flex-col items-start rounded-2xl border px-4 py-3 text-left text-sm transition-all duration-200",
                    selected
                      ? "border-violet-500/50 bg-violet-500/10 text-white shadow-lg shadow-violet-500/10 ring-1 ring-violet-500/30"
                      : "border-white/10 bg-zinc-950/50 text-zinc-300 hover:border-white/20 hover:bg-zinc-900/80",
                    disabled && "cursor-not-allowed opacity-40 hover:border-white/10"
                  )}
                >
                  {selected ? (
                    <span className="absolute right-3 top-3 flex size-5 items-center justify-center rounded-full bg-violet-500 text-white">
                      <Check className="size-3" />
                    </span>
                  ) : null}
                  <span className="font-medium">{p.label}</span>
                  <span className="mt-0.5 text-xs text-zinc-500">{p.id}</span>
                </button>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
