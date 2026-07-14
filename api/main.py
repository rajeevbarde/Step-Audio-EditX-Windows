"""
FastAPI service for Step-Audio-EditX.

Endpoints (see SupaEazyUI docs/tts/stepaudioEditX/API.md):
  GET  /v1/health
  GET  /v1/capabilities
  POST /v1/clone
  POST /v1/edit
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

# Must be set before vLLM / model imports
os.environ.setdefault("VLLM_ATTENTION_BACKEND", "TRITON_ATTN")

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from api.audio_io import cleanup_path, save_upload_to_temp, tensor_to_wav_bytes
from api.capabilities import build_capabilities
from api.engine import engine
from api.metrics import (
    InferTimer,
    audio_duration_sec,
    format_metrics,
    new_request_id,
    truncate,
)
from config.edit_config import get_supported_edit_types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

# Serialize GPU inference (vLLM with max_num_seqs=1)
_infer_lock = asyncio.Lock()

EDIT_TYPES = {"emotion", "style", "speed", "paralinguistic", "denoise", "vad"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API — loading models (this can take several minutes)...")
    try:
        # Block until loaded so /v1/health model_loaded is accurate after ready.
        await asyncio.to_thread(engine.load)
    except Exception:
        logger.exception("Failed to load models at startup")
        raise
    yield
    logger.info("API shutting down")


def _http_from_engine_error(exc: Exception, fallback_prefix: str) -> HTTPException:
    """Map upstream tts.HTTPException (status_code + detail) to FastAPI errors."""
    status = getattr(exc, "status_code", None)
    detail = getattr(exc, "detail", None)
    if status is not None and detail is not None:
        try:
            code = int(status)
        except Exception:
            code = 400
        return HTTPException(status_code=code, detail=str(detail))
    return HTTPException(status_code=500, detail=f"{fallback_prefix}: {exc}")


app = FastAPI(
    title="Step-Audio-EditX API",
    version="1.0.0",
    description="Zero-shot clone + audio edit REST API (no typed emotion/style routes).",
    lifespan=lifespan,
)


@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": engine.loaded,
        "paths": (
            {
                "model_path": engine.paths.model_path,
                "tokenizer_path": engine.paths.tokenizer_path,
                "model_source": engine.paths.model_source,
            }
            if engine.paths
            else None
        ),
    }


@app.get("/v1/capabilities")
async def capabilities():
    return build_capabilities()


def _validate_clone(prompt_text: str, target_text: str) -> None:
    if not prompt_text or not prompt_text.strip():
        raise HTTPException(status_code=400, detail="prompt_text is required")
    if not target_text or not target_text.strip():
        raise HTTPException(status_code=400, detail="target_text is required")


def _validate_edit(
    edit_type: str,
    edit_info: Optional[str],
    prompt_text: Optional[str],
    target_text: Optional[str],
) -> tuple[str, Optional[str], str, Optional[str]]:
    et = (edit_type or "").strip().lower()
    if et == "clone":
        raise HTTPException(
            status_code=400,
            detail="Use POST /v1/clone for clone; /v1/edit does not accept edit_type=clone",
        )
    if et not in EDIT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported edit_type: {edit_type}. Allowed: {sorted(EDIT_TYPES)}",
        )

    info = (edit_info or "").strip() or None
    allowed = get_supported_edit_types().get(et, [])
    if et in {"emotion", "style", "speed"}:
        if not info:
            raise HTTPException(
                status_code=400,
                detail=f"edit_info is required for edit_type={et}",
            )
        if info not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid edit_info '{info}' for {et}. Allowed: {allowed}",
            )

    pt = prompt_text if prompt_text is not None else ""
    if et not in {"denoise", "vad"} and (not pt or not pt.strip()):
        raise HTTPException(
            status_code=400,
            detail="prompt_text is required for this edit_type",
        )

    tt = target_text if target_text is not None else None
    if et == "paralinguistic":
        if not tt or not tt.strip():
            raise HTTPException(
                status_code=400,
                detail="target_text is required for edit_type=paralinguistic",
            )

    return et, info, pt, tt


@app.post("/v1/clone")
async def clone(
    audio: UploadFile = File(..., description="Reference prompt audio"),
    prompt_text: str = Form(...),
    target_text: str = Form(...),
):
    _validate_clone(prompt_text, target_text)
    if not engine.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    req_id = new_request_id()
    timer = InferTimer()
    prompt = prompt_text.strip()
    target = target_text.strip()
    logger.info(
        "clone start | id=%s | file=%s | prompt_chars=%d | target_chars=%d | prompt=%r | target=%r",
        req_id,
        audio.filename,
        len(prompt),
        len(target),
        truncate(prompt),
        truncate(target),
    )

    path: str | None = None
    try:
        path = await save_upload_to_temp(audio)
        tts = engine.require()

        async with _infer_lock:
            timer.mark_infer_start()
            wav_tensor, sr = await asyncio.to_thread(
                tts.clone,
                path,
                prompt,
                target,
            )

        times = timer.stop()
        out_s = audio_duration_sec(wav_tensor, sr)
        body = tensor_to_wav_bytes(wav_tensor, sr)
        logger.info(
            format_metrics(
                op="clone",
                req_id=req_id,
                times=times,
                out_audio_s=out_s,
                status="ok",
                bytes=len(body),
                sr=sr,
            )
        )
        return Response(content=body, media_type="audio/wav")
    except HTTPException:
        raise
    except ValueError as e:
        times = timer.stop()
        logger.warning(
            format_metrics(
                op="clone",
                req_id=req_id,
                times=times,
                out_audio_s=0.0,
                status="bad_request",
                error=str(e),
            )
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        times = timer.stop()
        logger.exception(
            format_metrics(
                op="clone",
                req_id=req_id,
                times=times,
                out_audio_s=0.0,
                status="error",
                error=str(e),
            )
        )
        raise _http_from_engine_error(e, "Clone failed") from e
    finally:
        cleanup_path(path)


@app.post("/v1/edit")
async def edit(
    audio: UploadFile = File(..., description="Source audio to edit"),
    prompt_text: str = Form(""),
    edit_type: str = Form(...),
    edit_info: Optional[str] = Form(None),
    target_text: Optional[str] = Form(None),
):
    et, info, pt, tt = _validate_edit(edit_type, edit_info, prompt_text, target_text)
    if not engine.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    req_id = new_request_id()
    timer = InferTimer()
    prompt = pt.strip() if pt else ""
    target = tt.strip() if tt else None
    logger.info(
        "edit start | id=%s | file=%s | edit_type=%s | edit_info=%s | prompt_chars=%d | target_chars=%s | prompt=%r",
        req_id,
        audio.filename,
        et,
        info,
        len(prompt),
        len(target) if target else 0,
        truncate(prompt),
    )

    path: str | None = None
    try:
        path = await save_upload_to_temp(audio)
        tts = engine.require()

        async with _infer_lock:
            timer.mark_infer_start()
            wav_tensor, sr = await asyncio.to_thread(
                tts.edit,
                path,
                prompt,
                et,
                info,
                target,
            )

        times = timer.stop()
        out_s = audio_duration_sec(wav_tensor, sr)
        body = tensor_to_wav_bytes(wav_tensor, sr)
        logger.info(
            format_metrics(
                op="edit",
                req_id=req_id,
                times=times,
                out_audio_s=out_s,
                status="ok",
                edit_type=et,
                edit_info=info,
                bytes=len(body),
                sr=sr,
            )
        )
        return Response(content=body, media_type="audio/wav")
    except HTTPException:
        raise
    except ValueError as e:
        times = timer.stop()
        logger.warning(
            format_metrics(
                op="edit",
                req_id=req_id,
                times=times,
                out_audio_s=0.0,
                status="bad_request",
                edit_type=et,
                error=str(e),
            )
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        times = timer.stop()
        logger.exception(
            format_metrics(
                op="edit",
                req_id=req_id,
                times=times,
                out_audio_s=0.0,
                status="error",
                edit_type=et,
                error=str(e),
            )
        )
        raise _http_from_engine_error(e, "Edit failed") from e
    finally:
        cleanup_path(path)
