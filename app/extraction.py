"""Utilities for extracting structured data from uploaded documents."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Optional

from fastapi import UploadFile
from unstructured.partition.auto import partition

# Supported file extensions for quick validation. The unstructured library is capable
# of handling many more formats, but we keep an allowlist for clarity and to make
# error messages actionable for callers.
SUPPORTED_EXTENSIONS: Iterable[str] = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xlsx",
    ".xls",
    ".csv",
    ".rtf",
    ".html",
    ".txt",
    ".md",
}


class ExtractionError(Exception):
    """Raised when a document cannot be processed."""


def _normalized_suffix(filename: Optional[str]) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def _validate_extension(filename: Optional[str]) -> None:
    suffix = _normalized_suffix(filename)
    if suffix and suffix not in SUPPORTED_EXTENSIONS:
        raise ExtractionError(
            f"Unsupported file type '{suffix}'. "
            "Update SUPPORTED_EXTENSIONS if this format should be accepted."
        )


async def _partition_file(temp_path: Path) -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()

    def _run_partition() -> List[Dict[str, Any]]:
        extracted = partition(filename=temp_path.as_posix())
        return [element.to_dict() for element in extracted]

    return await loop.run_in_executor(None, _run_partition)


async def extract_from_upload(upload: UploadFile) -> Dict[str, Any]:
    """Extract the structured content for an uploaded document."""
    _validate_extension(upload.filename)

    # Read the entire payload into memory. For very large files a different strategy
    # (streaming to disk in chunks) may be preferable, but this keeps the implementation
    # simple while covering common office documents.
    payload = await upload.read()
    await upload.close()

    if not payload:
        raise ExtractionError(f"The uploaded file '{upload.filename}' is empty.")

    suffix = _normalized_suffix(upload.filename) or ".bin"
    temp_path: Optional[Path] = None

    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(payload)
            temp_path = Path(temp_file.name)

        elements = await _partition_file(temp_path)
    except Exception as exc:  # pragma: no cover - surface library errors
        raise ExtractionError(
            f"Failed to extract '{upload.filename}': {exc}"
        ) from exc
    finally:
        if temp_path and temp_path.exists():
            try:
                os.remove(temp_path)
            except OSError:
                # If cleanup fails we log and move on; leaving the temp file around
                # is preferable to raising a secondary exception.
                pass

    return {"filename": upload.filename, "elements": elements}
