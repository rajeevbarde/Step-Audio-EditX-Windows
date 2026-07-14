"""Lazy singleton loader for StepAudioTokenizer + StepAudioTTS."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from model_loader import ModelSource
from tokenizer import StepAudioTokenizer
from tts import StepAudioTTS

logger = logging.getLogger(__name__)


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


@dataclass
class EnginePaths:
    model_path: str
    tokenizer_path: str
    model_source: str


def resolve_paths() -> EnginePaths:
    """
    Default paths match Docker mount layout:
      /model/Step-Audio-EditX
      /model/Step-Audio-Tokenizer
    """
    model_path = _env("STEP_AUDIO_MODEL_PATH", "/model/Step-Audio-EditX")
    tokenizer_path = _env("STEP_AUDIO_TOKENIZER_PATH", "/model/Step-Audio-Tokenizer")
    model_source = _env("STEP_AUDIO_MODEL_SOURCE", "local")
    return EnginePaths(
        model_path=model_path,
        tokenizer_path=tokenizer_path,
        model_source=model_source,
    )


class Engine:
    def __init__(self) -> None:
        self.tts: StepAudioTTS | None = None
        self.paths: EnginePaths | None = None

    @property
    def loaded(self) -> bool:
        return self.tts is not None

    def load(self) -> None:
        if self.tts is not None:
            return

        paths = resolve_paths()
        if not os.path.isdir(paths.model_path):
            raise FileNotFoundError(
                f"Model path does not exist: {paths.model_path}. "
                "Mount models at /model (Step-Audio-EditX + Step-Audio-Tokenizer)."
            )
        if not os.path.isdir(paths.tokenizer_path):
            raise FileNotFoundError(
                f"Tokenizer path does not exist: {paths.tokenizer_path}."
            )

        source = paths.model_source
        if source not in {
            ModelSource.AUTO,
            ModelSource.LOCAL,
            ModelSource.MODELSCOPE,
            ModelSource.HUGGINGFACE,
            "auto",
            "local",
            "modelscope",
            "huggingface",
        }:
            raise ValueError(f"Unsupported STEP_AUDIO_MODEL_SOURCE: {source}")

        logger.info("Loading StepAudioTokenizer from %s", paths.tokenizer_path)
        tokenizer = StepAudioTokenizer(paths.tokenizer_path, model_source=source)

        gpu_mem = float(_env("STEP_AUDIO_GPU_MEMORY_UTILIZATION", "0.5"))
        max_model_len = int(_env("STEP_AUDIO_MAX_MODEL_LEN", "3072"))
        dtype = _env("STEP_AUDIO_DTYPE", "bfloat16")
        cosy_dtype = _env("STEP_AUDIO_COSYVOICE_DTYPE", "bfloat16")
        enforce_eager = _env("STEP_AUDIO_ENFORCE_EAGER", "0") in {"1", "true", "True"}

        logger.info("Loading StepAudioTTS from %s", paths.model_path)
        self.tts = StepAudioTTS(
            paths.model_path,
            tokenizer,
            model_source=source,
            gpu_memory_utilization=gpu_mem,
            max_model_len=max_model_len,
            dtype=dtype,
            max_num_seqs=1,
            enforce_eager=enforce_eager,
            cosyvoice_dtype=cosy_dtype,
            cosyvoice_cuda_graph=True,
        )
        self.paths = paths
        logger.info("Engine ready")

    def require(self) -> StepAudioTTS:
        if self.tts is None:
            raise RuntimeError("Model not loaded")
        return self.tts


engine = Engine()
