"use client";

import { Badge } from "@/components/ui/badge";

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/[0.06] bg-zinc-950/80 px-8 backdrop-blur-xl">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-white">
          {title}
        </h1>
        {subtitle ? (
          <p className="text-xs text-zinc-500">{subtitle}</p>
        ) : null}
      </div>
      <Badge variant="default" className="gap-1.5 pr-3">
        <span className="relative flex size-2">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-40" />
          <span className="relative inline-flex size-2 rounded-full bg-emerald-400" />
        </span>
        Model: Loaded
      </Badge>
    </header>
  );
}
