"""Shared audio I/O helpers for the REST API."""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import soundfile as sf
import torch
from fastapi import UploadFile


async def save_upload_to_temp(upload: UploadFile) -> str:
    """Write multipart audio to a temp file; caller must delete the path."""
    suffix = Path(upload.filename or "audio.wav").suffix.lower()
    if suffix not in {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".webm"}:
        suffix = ".wav"
    fd, path = tempfile.mkstemp(prefix="step_audio_", suffix=suffix)
    os.close(fd)
    try:
        data = await upload.read()
        if not data:
            os.unlink(path)
            raise ValueError("Uploaded audio is empty")
        with open(path, "wb") as f:
            f.write(data)
    except Exception:
        if os.path.exists(path):
            os.unlink(path)
        raise
    return path


def tensor_to_wav_bytes(audio: torch.Tensor, sample_rate: int) -> bytes:
    """
    Encode CosyVoice / StepAudioTTS output as WAV bytes.

    Must use soundfile — TorchCodec backend cannot write WAV into BytesIO
    (same pattern as utils.encode_wav / tokenizer.get_vq02_code).
    """
    wav = audio.detach().float().cpu()
    if wav.ndim > 1:
        wav_np = wav.squeeze(0).numpy()
    else:
        wav_np = wav.numpy()
    if wav_np.ndim != 1:
        raise ValueError(f"Unexpected audio tensor shape after squeeze: {wav_np.shape}")

    buf = io.BytesIO()
    sf.write(buf, wav_np, sample_rate, format="WAV")
    return buf.getvalue()


def cleanup_path(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass
