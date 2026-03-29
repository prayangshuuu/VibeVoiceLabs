"""TTS generation: chunking, optional multi-speaker lines, tensor -> PCM / WAV."""

from __future__ import annotations

import copy
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import numpy as np
import torch

from services.model_loader import LoadedModel, get_loaded
from services.voices import resolve_voice_path

SAMPLE_RATE = 24000


def normalize_text(text: str) -> str:
    return (
        text.replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .strip()
    )


def split_text_chunks(text: str, max_chars: int = 220) -> List[str]:
    """Split into small segments for incremental synthesis (sentence-ish, capped)."""
    text = normalize_text(text)
    if not text:
        return []

    # Prefer sentence boundaries
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

    # Merge very short tail chunks (model is less stable on ultra-short-only runs)
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


@dataclass
class SpeakerTurn:
    speaker: str
    text: str


MULTI_SPEAKER_LINE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)$")


def parse_multi_speaker(text: str) -> List[SpeakerTurn]:
    """
    Parse lines like:
      A: Hello there
      B: Hi!
    Unlabeled lines attach to the previous speaker or 'default'.
    """
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
    # Rotate through a small stable set by letter
    key = speaker.upper()
    pool = ["carter", "emma", "davis", "grace", "frank", "mike"]
    if len(key) == 1 and "A" <= key <= "Z":
        return pool[(ord(key) - ord("A")) % len(pool)]
    h = sum(ord(c) for c in speaker) % len(pool)
    return pool[h]


def _load_voice_tensor(voice_path: str, device: str) -> Any:
    target_device = device if device != "cpu" else "cpu"
    return torch.load(voice_path, map_location=target_device, weights_only=False)


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


def synthesize_to_file(
    text: str,
    voice: Optional[str] = None,
    cfg_scale: float = 1.5,
    output_dir: Optional[Path] = None,
    multi_speaker: bool = False,
    speaker_voice_map: Optional[Dict[str, str]] = None,
) -> str:
    """Full pipeline: chunk text, generate, save outputs/<uuid>.wav."""
    loaded = get_loaded()
    output_dir = output_dir or Path(__file__).resolve().parent.parent / "storage" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{uuid.uuid4().hex}.wav"
    out_path = output_dir / out_name

    if multi_speaker:
        turns = parse_multi_speaker(text)
        wave_parts: List[torch.Tensor] = []
        for turn in turns:
            vid = speaker_to_voice_id(turn.speaker, speaker_voice_map)
            vp = resolve_voice_path(vid)
            prefilled = _load_voice_tensor(vp, loaded.device)
            for chunk in split_text_chunks(turn.text):
                w = _generate_one(loaded, chunk, prefilled, cfg_scale)
                wave_parts.append(w)
        full = concatenate_waveforms(wave_parts)
    else:
        vp = resolve_voice_path(voice)
        prefilled = _load_voice_tensor(vp, loaded.device)
        wave_parts = []
        for chunk in split_text_chunks(text):
            w = _generate_one(loaded, chunk, prefilled, cfg_scale)
            wave_parts.append(w)
        full = concatenate_waveforms(wave_parts)

    loaded.processor.save_audio(full, output_path=str(out_path), sampling_rate=SAMPLE_RATE, normalize=False)
    return str(out_path)


def synthesize_stream_pcm(
    text: str,
    voice: Optional[str] = None,
    cfg_scale: float = 1.5,
) -> Generator[Dict[str, Any], None, None]:
    """Yields event dicts: {type: progress|audio_meta|audio_bytes|done, ...}."""
    loaded = get_loaded()
    vp = resolve_voice_path(voice)
    prefilled = _load_voice_tensor(vp, loaded.device)
    chunks = split_text_chunks(text)
    yield {"type": "progress", "stage": "start", "message": "Queued synthesis", "demo": True}
    for i, chunk in enumerate(chunks):
        yield {
            "type": "progress",
            "stage": "chunk",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "message": f"Generating segment {i + 1} of {len(chunks)}",
            "demo": True,
        }
        w = _generate_one(loaded, chunk, prefilled, cfg_scale)
        pcm = tensor_to_pcm_s16le(w)
        yield {"type": "audio_meta", "sample_rate": SAMPLE_RATE, "format": "pcm_s16le", "bytes_length": len(pcm)}
        yield {"type": "pcm", "data": pcm}
    yield {"type": "progress", "stage": "done", "message": "Complete", "demo": True}
