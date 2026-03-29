import Link from "next/link";
import { Sidebar } from "@/components/Sidebar";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#030303]">
      <Sidebar />
      <nav
        className={cn(
          "sticky top-0 z-30 flex gap-2 border-b border-white/[0.06] bg-zinc-950/95 px-4 py-3 backdrop-blur-xl md:hidden"
        )}
      >
        {[
          ["/dashboard", "Generate"],
          ["/dashboard/voices", "Voices"],
          ["/dashboard/api", "API"],
        ].map(([href, label]) => (
          <Link
            key={href}
            href={href as string}
            className="rounded-xl bg-white/5 px-3 py-2 text-xs font-medium text-zinc-300 ring-1 ring-white/10 hover:bg-white/10"
          >
            {label}
          </Link>
        ))}
      </nav>
      <div className="md:pl-64">{children}</div>
    </div>
  );
}
