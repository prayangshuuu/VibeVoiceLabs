import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] px-6 py-12">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 md:flex-row">
        <p className="text-sm text-zinc-500">
          © {new Date().getFullYear()} VibeVoiceLabs · Local voice AI
        </p>
        <div className="flex gap-6 text-sm text-zinc-400">
          <Link href="/dashboard" className="hover:text-white transition-colors">
            Dashboard
          </Link>
          <a
            href="http://127.0.0.1:8000/docs"
            className="hover:text-white transition-colors"
            target="_blank"
            rel="noreferrer"
          >
            API docs
          </a>
        </div>
      </div>
    </footer>
  );
}
