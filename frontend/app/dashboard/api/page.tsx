import { Topbar } from "@/components/Topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function ApiDocsPage() {
  return (
    <div className="min-h-screen">
      <Topbar title="API" subtitle="Reference for the local FastAPI service." />
      <div className="space-y-6 p-8">
        <Card className="max-w-3xl border-white/[0.08] bg-zinc-900/40">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Base URL</CardTitle>
            <Badge variant="outline">{BASE}</Badge>
          </CardHeader>
          <CardContent className="space-y-6 text-sm text-zinc-400">
            <div>
              <p className="mb-2 font-medium text-zinc-200">POST /tts</p>
              <pre className="overflow-x-auto rounded-2xl bg-zinc-950 p-4 text-xs text-zinc-300 ring-1 ring-white/5">
                {`{
  "text": "Hello world",
  "voice": "carter",
  "mode": "default",
  "cfg_scale": 1.5
}`}
              </pre>
            </div>
            <div>
              <p className="mb-2 font-medium text-zinc-200">GET /voices</p>
              <p>List preset metadata and availability.</p>
            </div>
            <div>
              <p className="mb-2 font-medium text-zinc-200">WebSocket /stream</p>
              <pre className="overflow-x-auto rounded-2xl bg-zinc-950 p-4 text-xs text-zinc-300 ring-1 ring-white/5">
                {`{"action":"synthesize","text":"...","voice":"emma"}`}
              </pre>
            </div>
            <a
              href={`${BASE}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex text-violet-400 hover:text-violet-300"
            >
              Open Swagger UI →
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
