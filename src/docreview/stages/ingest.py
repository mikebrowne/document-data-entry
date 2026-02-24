from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

from docreview.core.schemas import IngestSection


def ingest(input_path: Path) -> tuple[IngestSection, bytes]:
    data = input_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    mime_type, _ = mimetypes.guess_type(str(input_path))
    return (
        IngestSection(
            ok=True,
            source_path=str(input_path),
            file_hash=digest,
            file_size_bytes=len(data),
            mime_type=mime_type or "application/octet-stream",
        ),
        data,
    )
