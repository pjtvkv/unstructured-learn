"""FastAPI application exposing document extraction powered by unstructured.io."""

from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .extraction import ExtractionError, SUPPORTED_EXTENSIONS, extract_from_upload

router = APIRouter()


@router.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.post("/v1/extract")
async def extract(files: List[UploadFile] = File(...)) -> JSONResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for extraction.")

    try:
        results = await asyncio.gather(*(extract_from_upload(upload) for upload in files))
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected extraction failure: {exc}",
        ) from exc

    return JSONResponse({"documents": results})


def create_app() -> FastAPI:
    application = FastAPI(
        title="Unstructured Extraction Service",
        description=(
            "Upload documents such as PDF, DOCX, PPTX, and more to extract their "
            "structured content using unstructured.io."
        ),
        version="0.1.0",
    )
    application.include_router(router)
    application.extra["supported_extensions"] = sorted(SUPPORTED_EXTENSIONS)
    return application


app = create_app()

