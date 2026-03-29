"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Mic2, Sparkles, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Generate", icon: Mic2 },
  { href: "/dashboard/voices", label: "Voices", icon: LayoutDashboard },
  { href: "/dashboard/api", label: "API", icon: Terminal },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col border-r border-white/[0.06] bg-zinc-950/90 backdrop-blur-xl md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-white/[0.06] px-5">
        <span className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 shadow-lg shadow-violet-500/20">
          <Sparkles className="size-4 text-white" />
        </span>
        <span className="font-semibold tracking-tight text-white">
          VibeVoiceLabs
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {links.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-white/10 text-white shadow-inner ring-1 ring-white/10"
                  : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
              )}
            >
              <Icon className="size-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/[0.06] p-4">
        <p className="text-xs text-zinc-500">
          Research & demo use. See model license on Hugging Face.
        </p>
      </div>
    </aside>
  );
}
