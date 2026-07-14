@echo off
REM Smoke: English zero-shot TTS -> ..\output\clone_en.wav
REM Double-click from examples\ is OK. API must be up (run_api.bat at repo root).
cd /d "%~dp0"
set "BASE=http://127.0.0.1:8080"
set "WAV=%~dp0zero_shot_en_prompt.wav"
set "PROMPT_TXT=%~dp0prompts\zero_shot_en_prompt_text.txt"
set "TARGET_TXT=%~dp0prompts\zero_shot_en_target_text.txt"
set "OUT=%~dp0..\output"
if not exist "%OUT%" mkdir "%OUT%"

if not exist "%WAV%" (
  echo Missing prompt WAV: %WAV%
  pause
  exit /b 1
)
if not exist "%PROMPT_TXT%" (
  echo Missing text file: %PROMPT_TXT%
  pause
  exit /b 1
)

echo === POST %BASE%/v1/clone  (English) ===
echo WAV: %WAV%
echo OUT: %OUT%\clone_en.wav
echo.

curl.exe -s -S -f -X POST "%BASE%/v1/clone" -F "audio=@%WAV%;type=audio/wav" -F "prompt_text=<%PROMPT_TXT%" -F "target_text=<%TARGET_TXT%" -o "%OUT%\clone_en.wav"
if errorlevel 1 (
  echo Clone EN FAILED
  pause
  exit /b 1
)

echo.
echo OK - wrote %OUT%\clone_en.wav
pause
