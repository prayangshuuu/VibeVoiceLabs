"use client";

import { motion } from "framer-motion";
import { Pause, Play } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/** Landing preview — visual-only waveform (no backend call). */
export function DemoSection() {
  const [playing, setPlaying] = useState(false);

  return (
    <section className="border-t border-white/[0.06] px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <Card className="overflow-hidden border-white/[0.08] bg-zinc-900/50">
            <CardHeader className="border-b border-white/[0.06] pb-4">
              <CardTitle className="text-base font-medium text-zinc-200">
                Live preview
              </CardTitle>
              <p className="text-sm text-zinc-500">
                Experience the dashboard player with real waveforms after you
                generate.
              </p>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="flex h-24 items-end justify-center gap-0.5 rounded-2xl bg-zinc-950/80 px-4 py-3 ring-1 ring-white/5">
                {Array.from({ length: 48 }).map((_, i) => {
                  const h = 20 + ((i * 17) % 73);
                  return (
                    <motion.div
                      key={i}
                      className="w-1 rounded-full bg-gradient-to-t from-violet-600/40 to-fuchsia-400/80"
                      initial={{ height: 8 }}
                      animate={{
                        height: playing ? h : 12 + (i % 5) * 4,
                      }}
                      transition={{
                        duration: playing ? 0.35 : 0.8,
                        repeat: playing ? Infinity : 0,
                        delay: playing ? i * 0.02 : 0,
                        ease: "easeInOut",
                      }}
                      style={{ height: playing ? h : undefined }}
                    />
                  );
                })}
              </div>
              <div className="flex items-center justify-between gap-4">
                <div className="text-xs text-zinc-500">
                  <span className="text-zinc-300">0:00</span>
                  <span className="mx-2 text-zinc-600">/</span>
                  <span>0:14</span>
                </div>
                <Button
                  variant="secondary"
                  size="icon"
                  type="button"
                  aria-label={playing ? "Pause preview" : "Play preview"}
                  onClick={() => setPlaying(!playing)}
                >
                  {playing ? (
                    <Pause className="size-4" />
                  ) : (
                    <Play className="size-4 ml-0.5" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
