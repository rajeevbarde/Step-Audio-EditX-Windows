# Step-Audio-EditX (Windows + REST API)

Windows-oriented fork of [stepfun-ai/Step-Audio-EditX](https://github.com/stepfun-ai/Step-Audio-EditX) with a **persistent FastAPI** service.

Native Windows install is not supported (vLLM has no Windows wheels). This fork runs via **Docker Desktop + NVIDIA GPU**.

**Upstream / original README (model, Gradio, training, tags):**  
https://github.com/stepfun-ai/Step-Audio-EditX/blob/main/README.md

**This fork:** Docker image + HTTP API on port **8080** (`/v1/clone`, `/v1/edit`, …).

---

## Requirements

- Windows 10/11 with NVIDIA GPU  
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with GPU support enabled  
- Enough disk for the image (~40GB) and model weights (~9GB)

---

## Install (minimal)

```bat
git clone https://github.com/rajeevbarde/Step-Audio-EditX-Windows.git
cd Step-Audio-EditX-Windows

docker build . -t supaeazy-step-audio-api

mkdir models
cd models
git lfs install
git clone https://huggingface.co/stepfun-ai/Step-Audio-Tokenizer
git clone https://huggingface.co/stepfun-ai/Step-Audio-EditX
cd ..
```

Expected layout:

```text
models/Step-Audio-EditX/
models/Step-Audio-Tokenizer/
```

---

## Run the API

### `run_api.bat` (recommended)

From the repo root, double-click or run:

```bat
run_api.bat
```

This starts:

```bat
docker run --rm --gpus all ^
  -v "%~dp0models:/model" ^
  -p 8080:8080 ^
  -e STEP_AUDIO_MODEL_PATH=/model/Step-Audio-EditX ^
  -e STEP_AUDIO_TOKENIZER_PATH=/model/Step-Audio-Tokenizer ^
  -e STEP_AUDIO_MODEL_SOURCE=local ^
  supaeazy-step-audio-api
```

- Base URL: `http://127.0.0.1:8080`  
- First start loads models (several minutes).  
- Stop: focus the window → **Ctrl+C** (or close it). Container uses `--rm`.

Optional env overrides: `STEP_AUDIO_GPU_MEMORY_UTILIZATION`, `STEP_AUDIO_MAX_MODEL_LEN`, `STEP_AUDIO_DTYPE`, `STEP_AUDIO_COSYVOICE_DTYPE`.

---

## REST API

Base: `http://127.0.0.1:8080`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/health` | Process up + `model_loaded` |
| `GET` | `/v1/capabilities` | Allowed `edit_type` / `edit_info` lists |
| `POST` | `/v1/clone` | Zero-shot voice clone / TTS → `audio/wav` |
| `POST` | `/v1/edit` | Emotion / style / speed / paralinguistic / denoise / vad → `audio/wav` |

There are **no** typed routes like `/v1/emotion`. Use `/v1/edit` with `edit_type` + `edit_info`.  
Use `/v1/clone` for cloning (do not send `edit_type=clone` to `/v1/edit`).

Multipart forms. Success responses are raw **WAV** bytes. Errors are JSON `{ "detail": "..." }`.

### `GET /v1/health`

```bat
curl -s http://127.0.0.1:8080/v1/health
```

```json
{ "status": "ok", "model_loaded": true }
```

### `GET /v1/capabilities`

```bat
curl -s http://127.0.0.1:8080/v1/capabilities
```

Returns allowed edit types, `edit_info` values, language tags, and paralinguistic tags. See also upstream README tag tables and `config/edit_config.py`.

### `POST /v1/clone` — zero-shot TTS

| Field | Required | Description |
|-------|----------|-------------|
| `audio` | yes | Reference prompt WAV |
| `prompt_text` | yes | Transcript of the reference audio |
| `target_text` | yes | Text to synthesize in that voice |

English example:

```bat
curl -s -S -f -X POST http://127.0.0.1:8080/v1/clone ^
  -F "audio=@examples/zero_shot_en_prompt.wav;type=audio/wav" ^
  -F "prompt_text=His political stance was conservative, and he was particularly close to margaret thatcher." ^
  -F "target_text=Underneath the courtyard is a large underground exhibition room which connects the two buildings." ^
  -o output/clone_en.wav
```

### `POST /v1/edit`

| Field | Required | Description |
|-------|----------|-------------|
| `audio` | yes | Source WAV to edit |
| `prompt_text` | yes* | Transcript (*may be empty for `denoise` / `vad`) |
| `edit_type` | yes | `emotion` \| `style` \| `speed` \| `paralinguistic` \| `denoise` \| `vad` |
| `edit_info` | conditional | Required for emotion / style / speed |
| `target_text` | conditional | Required for `paralinguistic` (text including tags) |

Emotion:

```bat
curl -s -S -f -X POST http://127.0.0.1:8080/v1/edit ^
  -F "audio=@examples/fear_zh_female_prompt.wav;type=audio/wav" ^
  -F "prompt_text=我总觉得，有人在跟着我，我能听到奇怪的脚步声。" ^
  -F "edit_type=emotion" ^
  -F "edit_info=fear" ^
  -o output/edit_emotion_fear.wav
```

Style:

```bat
curl -s -S -f -X POST http://127.0.0.1:8080/v1/edit ^
  -F "audio=@examples/whisper_prompt.wav;type=audio/wav" ^
  -F "prompt_text=比如在工作间隙，做一些简单的伸展运动，放松一下身体，这样，会让你更有精力。" ^
  -F "edit_type=style" ^
  -F "edit_info=whisper" ^
  -o output/edit_style_whisper.wav
```

Speed:

```bat
curl -s -S -f -X POST http://127.0.0.1:8080/v1/edit ^
  -F "audio=@examples/speed_prompt.wav;type=audio/wav" ^
  -F "prompt_text=上次你说鞋子有点磨脚，我给你买了一双软软的鞋垫。" ^
  -F "edit_type=speed" ^
  -F "edit_info=faster" ^
  -o output/edit_speed_faster.wav
```

**Iterative edits:** POST the previous output WAV back into `/v1/edit` (update `prompt_text` if needed).

---

## Example smoke bats

With the API running, open the `examples\` folder and double-click:

| Bat | What |
|-----|------|
| `test_health.bat` | Health + capabilities |
| `test_clone.bat` | ZH clone → `..\output\clone.wav` |
| `test_clone_en.bat` | EN clone → `..\output\clone_en.wav` |
| `test_edit_emotion.bat` | emotion=fear |
| `test_edit_style.bat` | style=whisper |
| `test_edit_speed.bat` | speed=faster |
| `test_all.bat` | health → clone → emotion → style |

Prompt text for Chinese (and English) forms is kept in `examples\prompts\*.txt` so the `.bat` files stay ASCII-safe under Windows `cmd`.

---

## License / credit

Model and upstream code: see [stepfun-ai/Step-Audio-EditX](https://github.com/stepfun-ai/Step-Audio-EditX).  
This fork adds Windows Docker packaging and the `/v1/*` REST API.
