@echo off
REM Smoke: POST /v1/edit speed=faster -> ..\output\edit_speed_faster.wav
REM Double-click from examples\ is OK. API must be up (run_api.bat at repo root).
cd /d "%~dp0"
set "BASE=http://127.0.0.1:8080"
set "WAV=%~dp0speed_prompt.wav"
set "PROMPT_TXT=%~dp0prompts\speed_prompt_text.txt"
set "OUT=%~dp0..\output"
if not exist "%OUT%" mkdir "%OUT%"

if not exist "%WAV%" (
  echo Missing prompt WAV: %WAV%
  pause
  exit /b 1
)

echo === POST %BASE%/v1/edit  speed=faster ===
echo WAV: %WAV%
echo OUT: %OUT%\edit_speed_faster.wav
echo.

curl.exe -s -S -f -X POST "%BASE%/v1/edit" -F "audio=@%WAV%;type=audio/wav" -F "prompt_text=<%PROMPT_TXT%" -F "edit_type=speed" -F "edit_info=faster" -o "%OUT%\edit_speed_faster.wav"
if errorlevel 1 (
  echo Edit speed FAILED
  pause
  exit /b 1
)

echo.
echo OK - wrote %OUT%\edit_speed_faster.wav
pause
