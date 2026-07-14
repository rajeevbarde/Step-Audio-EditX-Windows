"""Inference timing / activity helpers for API request logs."""
from __future__ import annotations

import time
import uuid
from typing import Any

import torch


def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


def audio_duration_sec(audio: torch.Tensor, sample_rate: int) -> float:
    """Duration of CosyVoice-style (channels, samples) or (samples,) tensor."""
    if sample_rate <= 0:
        return 0.0
    wav = audio.detach()
    if wav.ndim > 1:
        wav = wav.squeeze(0)
    samples = int(wav.reshape(-1).numel())
    return float(samples) / float(sample_rate)


def truncate(text: str | None, limit: int = 80) -> str:
    if text is None:
        return ""
    t = text.replace("\n", " ").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 3] + "..."


class InferTimer:
    """Wall-clock timing from start(); reports wait vs infer if mark_infer_start() used."""

    def __init__(self) -> None:
        self.t0 = time.perf_counter()
        self.t_infer0: float | None = None
        self.t1: float | None = None

    def mark_infer_start(self) -> None:
        self.t_infer0 = time.perf_counter()

    def stop(self) -> dict[str, float]:
        self.t1 = time.perf_counter()
        total = self.t1 - self.t0
        if self.t_infer0 is None:
            return {"total_s": total, "wait_s": 0.0, "infer_s": total}
        wait = self.t_infer0 - self.t0
        infer = self.t1 - self.t_infer0
        return {"total_s": total, "wait_s": wait, "infer_s": infer}


def format_metrics(
    *,
    op: str,
    req_id: str,
    times: dict[str, float],
    out_audio_s: float,
    status: str = "ok",
    **extra: Any,
) -> str:
    infer_s = times["infer_s"]
    wait_s = times["wait_s"]
    total_s = times["total_s"]
    if out_audio_s > 0 and infer_s > 0:
        rtf = infer_s / out_audio_s
        x_rt = out_audio_s / infer_s
        speed = f"rtf={rtf:.3f} ({x_rt:.2f}x realtime)"
    else:
        speed = "rtf=n/a"

    parts = [
        f"{op} {status}",
        f"id={req_id}",
        f"wait={wait_s:.2f}s",
        f"infer={infer_s:.2f}s",
        f"total={total_s:.2f}s",
        f"out_audio={out_audio_s:.2f}s",
        speed,
    ]
    for k, v in extra.items():
        if v is None or v == "":
            continue
        parts.append(f"{k}={v}")
    return " | ".join(parts)
