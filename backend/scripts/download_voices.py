#!/usr/bin/env python3
"""Download English streaming voice presets from the official VibeVoice repo (GitHub raw)."""

from __future__ import annotations

import os
import urllib.request

FILES = [
    "en-Carter_man.pt",
    "en-Davis_man.pt",
    "en-Emma_woman.pt",
    "en-Frank_man.pt",
    "en-Grace_woman.pt",
    "en-Mike_man.pt",
]

BASE = "https://raw.githubusercontent.com/microsoft/VibeVoice/main/demo/voices/streaming_model/"


def main() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "voices", "streaming_model"))
    os.makedirs(root, exist_ok=True)
    for name in FILES:
        url = BASE + name
        dest = os.path.join(root, name)
        if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
            print(f"skip (exists): {name}")
            continue
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest}")
    print("Done. Set VIBEVOICE_VOICES_DIR if you use a custom folder.")


if __name__ == "__main__":
    main()
