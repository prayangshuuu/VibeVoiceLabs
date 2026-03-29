# VibeVoiceLabs — FastAPI TTS backend

Local-first, **ElevenLabs-style** API around Microsoft **[VibeVoice-Realtime-0.5B](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B)** using the official open-source **[VibeVoice](https://github.com/microsoft/VibeVoice)** Python package (no private Microsoft code).

## Features

- **POST `/tts`** — synthesize text to `storage/outputs/*.wav`, return JSON with `audio_url`
- **WebSocket `/stream`** — chunked synthesis with **progress messages** (demo mode) and **raw PCM s16le** chunks (24 kHz)
- **GET `/voices`** — preset voice ids and whether `.pt` voice files are installed
- **Optional `API_KEY`** — require `X-API-Key` on protected routes (see below)
- **Multi-speaker text** — optional parsing `A: ...` / `B: ...` with per-label voice mapping

## Requirements

- **Python 3.10**
- PyTorch (pulled in via `vibevoice`)
- **Apple Silicon (MPS)**, **CUDA**, or **CPU** (CPU is slow but works for demos)
- Voice preset files (`.pt`) under `backend/voices/streaming_model/` — use the downloader script

## Setup

```bash
cd /path/to/VibeVoiceLabs
python3.10 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Voice presets (required)

Download the English streaming voices from the upstream repo:

```bash
cd backend
python scripts/download_voices.py
```

Optional: set `VIBEVOICE_VOICES_DIR` to a folder that contains `*.pt` voice files.

### Run the API

From the **`backend`** directory (so `main` and `services` import correctly):

```bash
cd backend
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive OpenAPI.

## Environment variables

| Variable | Description |
|----------|-------------|
| `API_KEY` | If set, requests must send header `X-API-Key: <value>` (WebSocket: header or `?api_key=`). Public: `/`, `/health`, `/docs`, `/audio/*`. |
| `VIBEVOICE_MODEL_PATH` | Default `microsoft/VibeVoice-Realtime-0.5B` |
| `VIBEVOICE_DEVICE` | Force `cuda`, `mps`, or `cpu` (optional) |
| `VIBEVOICE_VOICES_DIR` | Directory containing `*.pt` voices (default: `backend/voices/streaming_model`) |

## API examples

### List voices

```bash
curl -s http://127.0.0.1:8000/voices
```

### Synthesize (REST)

```bash
curl -s -X POST http://127.0.0.1:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from VibeVoice realtime.","voice":"emma","cfg_scale":1.5}'
```

### Multi-speaker script (REST)

```bash
curl -s -X POST http://127.0.0.1:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A: Hello there.\nB: Hi! Nice to meet you.",
    "multi_speaker": true,
    "speaker_voices": {"A": "carter", "B": "emma"}
  }'
```

### WebSocket streaming

Send JSON messages over `WS /stream`:

1. **One-shot** (buffer + optional `append_text` not required):

```json
{"action": "synthesize", "text": "Your paragraph here.", "voice": "carter", "cfg_scale": 1.5}
```

2. **Buffered text** (optional):

```json
{"action": "append_text", "text": "First chunk "}
{"action": "append_text", "text": "second chunk."}
{"action": "synthesize", "voice": "emma"}
```

The server sends JSON lines for **progress** / **audio_meta**, then **binary** frames for **PCM int16** audio (little-endian, mono, 24 kHz).

## Project layout

```
backend/
  main.py
  routes/
    tts.py
    stream.py
  services/
    model_loader.py
    inference.py
    voices.py
  middleware/
    api_key.py
  storage/
    outputs/
  voices/
    streaming_model/    # place .pt files here
  scripts/
    download_voices.py
```

## Notes

- First run downloads **~0.5B** model weights from Hugging Face (cache under `~/.cache/huggingface`).
- **MPS** uses **float32**; **CUDA** uses **bfloat16** where supported (matches upstream demo behavior).
- **FP32 on MPS** is required for stability; do not force FP16 on Apple Silicon.
- Intended for **demos and R&D**; see the [VibeVoice license and model card](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B) for terms.
