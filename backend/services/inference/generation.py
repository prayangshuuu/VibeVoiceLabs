"""Low-level VibeVoice generation: chunking, tensors, WAV/PCM."""

from __future__ import annotations

import copy
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import numpy as np
import torch

from domain.models import InferenceRequest
from infra.model_loader import LoadedModel, get_loaded
from observability.profiler import profile_chunk
from services.voice.manager import VoiceManager

SAMPLE_RATE = 24000


def normalize_text(text: str) -> str:
    return (
        text.replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .strip()
    )


def split_text_chunks(text: str, max_chars: int = 220) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks: List[str] = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) + 1 <= max_chars:
            buf = f"{buf} {p}".strip() if buf else p
        else:
            if buf:
                chunks.append(buf)
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    chunks.append(p[i : i + max_chars])
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)

    merged: List[str] = []
    i = 0
    while i < len(chunks):
        if i + 1 < len(chunks) and len(chunks[i]) < 24:
            merged.append(f"{chunks[i]} {chunks[i + 1]}".strip())
            i += 2
        else:
            merged.append(chunks[i])
            i += 1
    return [c for c in merged if c.strip()]


class SpeakerTurn:
    __slots__ = ("speaker", "text")

    def __init__(self, speaker: str, text: str) -> None:
        self.speaker = speaker
        self.text = text


MULTI_SPEAKER_LINE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)$")


def parse_multi_speaker(text: str) -> List[SpeakerTurn]:
    lines = text.strip().splitlines()
    if not lines:
        return [SpeakerTurn("default", text)]

    turns: List[SpeakerTurn] = []
    current_speaker = "A"
    for line in lines:
        m = MULTI_SPEAKER_LINE.match(line)
        if m:
            current_speaker = m.group(1)
            rest = m.group(2).strip()
            if rest:
                turns.append(SpeakerTurn(current_speaker, rest))
        else:
            if turns:
                prev = turns[-1]
                turns[-1] = SpeakerTurn(prev.speaker, f"{prev.text} {line.strip()}".strip())
            else:
                turns.append(SpeakerTurn(current_speaker, line.strip()))
    if not turns and text.strip():
        return [SpeakerTurn("default", text.strip())]
    return turns


def speaker_to_voice_id(speaker: str, mapping: Optional[Dict[str, str]]) -> str:
    if mapping and speaker in mapping:
        return mapping[speaker]
    key = speaker.upper()
    pool = ["carter", "emma", "davis", "grace", "frank", "mike"]
    if len(key) == 1 and "A" <= key <= "Z":
        return pool[(ord(key) - ord("A")) % len(pool)]
    h = sum(ord(c) for c in speaker) % len(pool)
    return pool[h]


def _generate_one(
    loaded: LoadedModel,
    text: str,
    prefilled: Any,
    cfg_scale: float,
) -> torch.Tensor:
    processor = loaded.processor
    model = loaded.model
    target_device = loaded.device if loaded.device != "cpu" else "cpu"

    inputs = processor.process_input_with_cached_prompt(
        text=text,
        cached_prompt=prefilled,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    for k, v in list(inputs.items()):
        if torch.is_tensor(v):
            inputs[k] = v.to(target_device)

    with profile_chunk("model.generate"):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=None,
                cfg_scale=cfg_scale,
                tokenizer=processor.tokenizer,
                generation_config={"do_sample": False},
                verbose=False,
                all_prefilled_outputs=copy.deepcopy(prefilled) if prefilled is not None else None,
            )
    if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
        raise RuntimeError("Model returned no speech audio.")
    return outputs.speech_outputs[0]


def tensor_to_pcm_s16le(waveform: torch.Tensor) -> bytes:
    x = waveform.detach().float().cpu().numpy().reshape(-1)
    x = np.clip(x, -1.0, 1.0)
    return (x * 32767.0).astype(np.int16).tobytes()


def concatenate_waveforms(parts: List[torch.Tensor]) -> torch.Tensor:
    if not parts:
        raise ValueError("No audio segments.")
    flat = [p.reshape(-1) if p.dim() > 1 else p.flatten() for p in parts]
    return torch.cat(flat, dim=0)


def synthesize_to_file_sync(
    req: InferenceRequest,
    *,
    voice_manager: VoiceManager,
    chunk_max_chars: int,
) -> str:
    loaded = get_loaded()
    output_dir = req.output_dir or Path(__file__).resolve().parents[2] / "storage" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex}.wav"
    out_path = output_dir / out_name

    if req.multi_speaker:
        turns = parse_multi_speaker(req.text)
        wave_parts: List[torch.Tensor] = []
        for turn in turns:
            vid = speaker_to_voice_id(turn.speaker, req.speaker_voice_map)
            prefilled = voice_manager.get_prefilled(vid, loaded.device)
            for chunk in split_text_chunks(turn.text, chunk_max_chars):
                w = _generate_one(loaded, chunk, prefilled, req.cfg_scale)
                wave_parts.append(w)
        full = concatenate_waveforms(wave_parts)
    else:
        prefilled = voice_manager.get_prefilled(req.voice, loaded.device)
        wave_parts = []
        for chunk in split_text_chunks(req.text, chunk_max_chars):
            w = _generate_one(loaded, chunk, prefilled, req.cfg_scale)
            wave_parts.append(w)
        full = concatenate_waveforms(wave_parts)

    loaded.processor.save_audio(
        full, output_path=str(out_path), sampling_rate=SAMPLE_RATE, normalize=False
    )
    return str(out_path)


def synthesize_stream_pcm(
    text: str,
    voice_manager: VoiceManager,
    voice: Optional[str],
    cfg_scale: float,
    chunk_max_chars: int,
    *,
    multi_speaker: bool = False,
    speaker_voice_map: Optional[Dict[str, str]] = None,
) -> Generator[Dict[str, Any], None, None]:
    loaded = get_loaded()
    chunks_meta: List[tuple[str, Optional[str]]] = []

    if multi_speaker:
        turns = parse_multi_speaker(text)
        for turn in turns:
            vid = speaker_to_voice_id(turn.speaker, speaker_voice_map)
            for ch in split_text_chunks(turn.text, chunk_max_chars):
                chunks_meta.append((ch, vid))
    else:
        for ch in split_text_chunks(text, chunk_max_chars):
            chunks_meta.append((ch, voice))

    yield {
        "type": "progress",
        "stage": "start",
        "message": "Queued synthesis",
        "total_chunks": len(chunks_meta),
        "demo": True,
    }
    current_vid: Optional[str] = None
    prefilled: Any = None

    for i, (chunk, vid) in enumerate(chunks_meta):
        if vid != current_vid:
            current_vid = vid
            prefilled = voice_manager.get_prefilled(vid, loaded.device)
        yield {
            "type": "progress",
            "stage": "chunk",
            "chunk_index": i,
            "total_chunks": len(chunks_meta),
            "message": f"Generating segment {i + 1} of {len(chunks_meta)}",
            "demo": True,
        }
        w = _generate_one(loaded, chunk, prefilled, cfg_scale)
        pcm = tensor_to_pcm_s16le(w)
        yield {"type": "audio_meta", "sample_rate": SAMPLE_RATE, "format": "pcm_s16le", "bytes_length": len(pcm)}
        yield {"type": "pcm", "data": pcm}
    yield {"type": "progress", "stage": "done", "message": "Complete", "demo": True}
