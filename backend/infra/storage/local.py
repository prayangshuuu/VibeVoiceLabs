"""Local filesystem storage — S3-shaped interface for future swap."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


class Storage:
    """Persist blobs under a root directory and expose HTTP-relative URLs."""

    def __init__(self, root: Path, public_mount_prefix: str = "/audio/"):
        self.root = root
        self.public_mount_prefix = public_mount_prefix.rstrip("/") + "/"
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: bytes) -> Path:
        path = self.root / filename
        path.write_bytes(data)
        return path

    def get_path(self, filename: str) -> Path:
        return self.root / filename

    def get_public_url(self, filename: str, base_url: str) -> str:
        base = str(base_url).rstrip("/") + "/"
        rel = f"{self.public_mount_prefix.strip('/')}/{filename}"
        return urljoin(base, rel)

    def exists(self, filename: str) -> bool:
        return self.get_path(filename).is_file()


def default_outputs_dir(backend_root: Optional[Path] = None) -> Path:
    root = backend_root or Path(__file__).resolve().parents[1]
    return root / "storage" / "outputs"
