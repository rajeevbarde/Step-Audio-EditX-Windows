@echo off
REM Smoke: POST /v1/edit style=whisper -> ..\output\edit_style_whisper.wav
REM Double-click from examples\ is OK. API must be up (run_api.bat at repo root).
cd /d "%~dp0"
set "BASE=http://127.0.0.1:8080"
set "WAV=%~dp0whisper_prompt.wav"
set "PROMPT_TXT=%~dp0prompts\whisper_prompt_text.txt"
set "OUT=%~dp0..\output"
if not exist "%OUT%" mkdir "%OUT%"

if not exist "%WAV%" (
  echo Missing prompt WAV: %WAV%
  pause
  exit /b 1
)

echo === POST %BASE%/v1/edit  style=whisper ===
echo WAV: %WAV%
echo OUT: %OUT%\edit_style_whisper.wav
echo.

curl.exe -s -S -f -X POST "%BASE%/v1/edit" -F "audio=@%WAV%;type=audio/wav" -F "prompt_text=<%PROMPT_TXT%" -F "edit_type=style" -F "edit_info=whisper" -o "%OUT%\edit_style_whisper.wav"
if errorlevel 1 (
  echo Edit style FAILED
  pause
  exit /b 1
)

echo.
echo OK - wrote %OUT%\edit_style_whisper.wav
pause
