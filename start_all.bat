@echo off
echo =============================================================
echo   RESQ-NET  -  Starting ALL Services
echo =============================================================

:: ─── 1. Print local IP and URLs ───────────────────────────────
"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe" -c ^
  "import socket; ip = socket.gethostbyname(socket.gethostname()); ^
   print(); ^
   print('  [BACKEND API]   http://' + ip + ':8000'); ^
   print('  [API DOCS]      http://' + ip + ':8000/docs'); ^
   print('  [ADMIN / DASH]  http://' + ip + ':3000/dashboard/'); ^
   print('  [VICTIM APP]    http://' + ip + ':3000/victim_app/'); ^
   print('  [ESP8266 URL]   http://' + ip + ':8000/api/iot/state'); ^
   print()"

echo.
echo  Launching services in separate windows...
echo =============================================================
echo.

:: ─── 2. FastAPI backend (port 8000) ───────────────────────────
:: NOTE: --reload is intentionally OMITTED. Using --reload would restart the
:: Python process on every file save, killing the RouteExecutor background
:: thread and resetting the iot_controller singleton (all motors stop).
start "RESQ-NET  |  Backend API :8000" cmd /k ^
  "title RESQ-NET Backend API :8000 && ^
   \"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe\" -m uvicorn main:app ^
   --app-dir \"D:\FOR CAREER\PROJECTS\Omniboy\backend\" ^
   --host 0.0.0.0 --port 8000"

:: ─── 3. Static file server for Admin + Victim web (port 3000) ─
start "RESQ-NET  |  Web Apps :3000" cmd /k ^
  "title RESQ-NET Web Apps :3000 && ^
   \"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe\" -m http.server 3000 ^
   --directory \"D:\FOR CAREER\PROJECTS\Omniboy\""

echo  All services started!
echo  Close each window individually to stop a specific service.
echo =============================================================
pause
