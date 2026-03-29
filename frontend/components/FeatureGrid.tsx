"use client";

import { motion } from "framer-motion";
import { Cpu, Radio, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    icon: Radio,
    title: "Real-time streaming",
    body: "Token-by-token synthesis with chunked playback and low perceived latency.",
  },
  {
    icon: Users,
    title: "Multi-speaker voices",
    body: "Curated presets and script parsing for dialogue-style generation.",
  },
  {
    icon: Cpu,
    title: "Local inference",
    body: "Apple Silicon, CUDA, or CPU — your hardware, your data, your cost curve.",
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export function FeatureGrid() {
  return (
    <section id="features" className="border-t border-white/[0.06] px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="mb-14 text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Everything you need to ship voice
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-zinc-400">
            A focused toolkit for builders who care about quality, privacy, and
            control.
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid gap-6 md:grid-cols-3"
        >
          {features.map((f) => (
            <motion.div key={f.title} variants={item}>
              <Card className="group h-full border-white/[0.08] bg-gradient-to-b from-zinc-900/80 to-zinc-950/80 transition-all duration-300 hover:border-violet-500/25 hover:shadow-violet-500/10">
                <CardContent className="flex flex-col gap-4 pt-8">
                  <span className="flex size-12 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-400 ring-1 ring-violet-500/20 transition-transform group-hover:scale-105">
                    <f.icon className="size-6" />
                  </span>
                  <h3 className="text-lg font-semibold text-white">{f.title}</h3>
                  <p className="text-sm leading-relaxed text-zinc-400">
                    {f.body}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
