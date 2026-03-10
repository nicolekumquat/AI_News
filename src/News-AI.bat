
@echo off
cd /d C:\Users\nical\Dev\Specify\AI_News\src

rem US-style example: assumes %DATE% like "Thu 02/26/2026"
for /f "tokens=2-4 delims=/ " %%i in ("%date%") do set datestring=%%k%%i%%j

set "LOGFILE=News-AI-%datestring%.log"

echo [%date% %time%] Starting digest generation for %datestring% >> "%LOGFILE%"

python -c "from cli.__main__ import main; main()" --html --output "AI-News-%datestring%.html" 2>> "%LOGFILE%"

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ERROR: Digest generation failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    rem Remove empty/broken HTML file on failure
    del "AI-News-%datestring%.html" 2>nul
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Digest generated successfully >> "%LOGFILE%"

rem Rebuild the digests.json manifest so the index page picks up the new file
python generate_manifest.py >> "%LOGFILE%" 2>&1

echo [%date% %time%] Done >> "%LOGFILE%"

start "" "AI-News-%datestring%.html"

