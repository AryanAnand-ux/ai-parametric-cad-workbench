@echo off
REM Start the AI Parametric CAD Workbench frontend (Vite dev server on http://localhost:5173)
cd /d "%~dp0"
echo Starting frontend...
npm run dev
pause
