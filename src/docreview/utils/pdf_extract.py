from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def extract_text_layer(data: bytes) -> str | None:
    """Extract text from PDF text layer using pdftotext."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir) / "document"
        pdf_path = base.with_suffix(".pdf")
        txt_path = base.with_suffix(".txt")
        pdf_path.write_bytes(data)
        try:
            subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return None
        if not txt_path.exists():
            return None
        text = txt_path.read_text(encoding="utf-8", errors="replace").strip()
        return text or None


def pdf_to_images(data: bytes) -> list[bytes]:
    """Convert PDF pages to PNG images using pdftoppm."""
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "document.pdf"
        output_prefix = Path(temp_dir) / "page"
        pdf_path.write_bytes(data)
        try:
            subprocess.run(
                ["pdftoppm", "-png", str(pdf_path), str(output_prefix)],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return []
        pages: list[bytes] = []
        for image_path in sorted(Path(temp_dir).glob("page-*.png"), key=lambda p: p.name):
            pages.append(image_path.read_bytes())
        return pages
