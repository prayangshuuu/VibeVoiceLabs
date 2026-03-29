"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Mic2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pb-24 pt-36 md:pb-32 md:pt-44">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(139,92,246,0.25),transparent)]" />
      <div className="pointer-events-none absolute -left-40 top-1/3 h-80 w-80 rounded-full bg-fuchsia-600/20 blur-[100px]" />
      <div className="pointer-events-none absolute -right-40 top-1/2 h-80 w-80 rounded-full bg-violet-600/15 blur-[100px]" />

      <div className="relative mx-auto max-w-4xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-zinc-300 backdrop-blur-md"
        >
          <Mic2 className="size-3.5 text-violet-400" />
          Local inference · Zero API cost
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-balance text-4xl font-bold tracking-tight text-white md:text-6xl md:leading-[1.08]"
        >
          Real-Time Voice AI Platform
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.18 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-zinc-400 md:text-xl"
        >
          Generate ultra-realistic voices locally with zero API cost. Built on
          VibeVoice-Realtime — streaming text in, studio-grade audio out.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.26 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Button size="lg" asChild>
            <Link href="/dashboard" className="gap-2">
              Open dashboard
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button size="lg" variant="secondary" asChild>
            <a href="#features">Explore features</a>
          </Button>
        </motion.div>
      </div>
    </section>
  );
}
