@echo off
cd /d "%~dp0"

echo Starting Step-Audio-EditX API (supaeazy-step-audio-api) on :8080
echo Mount: %~dp0models -^> /model
echo.

docker run --rm --gpus all ^
  -v "%~dp0models:/model" ^
  -p 8080:8080 ^
  -e STEP_AUDIO_MODEL_PATH=/model/Step-Audio-EditX ^
  -e STEP_AUDIO_TOKENIZER_PATH=/model/Step-Audio-Tokenizer ^
  -e STEP_AUDIO_MODEL_SOURCE=local ^
  supaeazy-step-audio-api

pause
