@echo off
cd /d "%~dp0"
python -c "import fastapi,uvicorn" >nul 2>nul
if errorlevel 1 (
 echo Please run: python -m pip install -r requirements.txt
 pause
 exit /b 1
)
echo Open http://127.0.0.1:8000 in your browser.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
