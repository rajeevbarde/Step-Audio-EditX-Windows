@echo off
REM Run section 7 smoke tests in order.
REM Double-click from examples\ is OK. API must be up (run_api.bat at repo root).
cd /d "%~dp0"
set "BASE=http://127.0.0.1:8080"
set "OUT=%~dp0..\output"
set "PROMPTS=%~dp0prompts"
if not exist "%OUT%" mkdir "%OUT%"

echo ========================================
echo Step-Audio-EditX API smoke tests
echo BASE=%BASE%
echo OUT=%OUT%
echo ========================================
echo.

echo [1/5] health
curl.exe -s -S -f "%BASE%/v1/health" || goto :fail
echo.
echo.

echo [2/5] capabilities
curl.exe -s -S -f "%BASE%/v1/capabilities" || goto :fail
echo.
echo.

echo [3/5] clone
curl.exe -s -S -f -X POST "%BASE%/v1/clone" -F "audio=@%~dp0fear_zh_female_prompt.wav;type=audio/wav" -F "prompt_text=<%PROMPTS%\fear_zh_prompt_text.txt" -F "target_text=<%PROMPTS%\fear_zh_target_text.txt" -o "%OUT%\clone.wav" || goto :fail
echo wrote %OUT%\clone.wav
echo.

echo [4/5] edit emotion=fear
curl.exe -s -S -f -X POST "%BASE%/v1/edit" -F "audio=@%~dp0fear_zh_female_prompt.wav;type=audio/wav" -F "prompt_text=<%PROMPTS%\fear_zh_prompt_text.txt" -F "edit_type=emotion" -F "edit_info=fear" -o "%OUT%\edit_emotion_fear.wav" || goto :fail
echo wrote %OUT%\edit_emotion_fear.wav
echo.

echo [5/5] edit style=whisper
curl.exe -s -S -f -X POST "%BASE%/v1/edit" -F "audio=@%~dp0whisper_prompt.wav;type=audio/wav" -F "prompt_text=<%PROMPTS%\whisper_prompt_text.txt" -F "edit_type=style" -F "edit_info=whisper" -o "%OUT%\edit_style_whisper.wav" || goto :fail
echo wrote %OUT%\edit_style_whisper.wav
echo.

echo ========================================
echo ALL PASSED (optional: also run test_edit_speed.bat / test_clone_en.bat)
echo ========================================
pause
exit /b 0

:fail
echo.
echo FAILED - is the API up? Start run_api.bat at the repo root first.
pause
exit /b 1
