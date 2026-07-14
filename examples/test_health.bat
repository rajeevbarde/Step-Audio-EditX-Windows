@echo off
REM Smoke: GET /v1/health and /v1/capabilities
REM Double-click from examples\ is OK. API must be up (run_api.bat at repo root).
cd /d "%~dp0"
set "BASE=http://127.0.0.1:8080"

echo === GET %BASE%/v1/health ===
curl.exe -s -S "%BASE%/v1/health"
echo.
echo.
echo === GET %BASE%/v1/capabilities ===
curl.exe -s -S "%BASE%/v1/capabilities"
echo.
echo.
pause
