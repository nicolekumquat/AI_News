
@echo off
cd /d C:\Users\nical\Dev\Specify\AI_News\src

rem US-style example: assumes %DATE% like "Thu 02/26/2026"
for /f "tokens=2-4 delims=/ " %%i in ("%date%") do set datestring=%%k%%i%%j

python -c "from cli.__main__ import main; main()" --html > "AI-News-%datestring%.html"

start "" "AI-News-%datestring%.html"

