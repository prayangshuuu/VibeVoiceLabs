"""Single global load of VibeVoice-Realtime-0.5B (processor + model)."""

from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import torch

if TYPE_CHECKING:
    pass


def get_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@dataclass
class LoadedModel:
    device: str
    dtype: torch.dtype
    attn: str
    processor: Any
    model: Any


_state: Optional[LoadedModel] = None


def load_model(
    model_path: str | None = None,
    device: str | None = None,
) -> LoadedModel:
    global _state
    if _state is not None:
        return _state

    from vibevoice.modular.modeling_vibevoice_streaming_inference import (
        VibeVoiceStreamingForConditionalGenerationInference,
    )
    from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor

    model_path = model_path or os.environ.get("VIBEVOICE_MODEL_PATH", "microsoft/VibeVoice-Realtime-0.5B")
    device = device or os.environ.get("VIBEVOICE_DEVICE") or get_device()

    if device == "mps" and not torch.backends.mps.is_available():
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"

    if device == "mps":
        load_dtype = torch.float32
        attn_impl_primary = "sdpa"
    elif device == "cuda":
        load_dtype = torch.bfloat16
        attn_impl_primary = "flash_attention_2"
    else:
        load_dtype = torch.float32
        attn_impl_primary = "sdpa"

    processor = VibeVoiceStreamingProcessor.from_pretrained(model_path)

    try:
        if device == "mps":
            model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=load_dtype,
                attn_implementation=attn_impl_primary,
                device_map=None,
            )
            model.to("mps")
        elif device == "cuda":
            model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=load_dtype,
                device_map="cuda",
                attn_implementation=attn_impl_primary,
            )
        else:
            model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=load_dtype,
                device_map="cpu",
                attn_implementation=attn_impl_primary,
            )
    except Exception:
        if attn_impl_primary == "flash_attention_2":
            print(f"[model_loader] flash_attention_2 failed, falling back to sdpa:\n{traceback.format_exc()}")
            model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=load_dtype,
                device_map=(device if device in ("cuda", "cpu") else None),
                attn_implementation="sdpa",
            )
            if device == "mps":
                model.to("mps")
        else:
            raise

    model.eval()
    model.set_ddpm_inference_steps(num_steps=5)

    _state = LoadedModel(
        device=device,
        dtype=load_dtype,
        attn=attn_impl_primary,
        processor=processor,
        model=model,
    )
    return _state


def get_loaded() -> LoadedModel:
    if _state is None:
        raise RuntimeError("Model not loaded; call load_model() first.")
    return _state
