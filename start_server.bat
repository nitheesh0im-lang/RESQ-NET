@echo off
echo =============================================================
echo  RESQ-NET Backend API Server Starting...
echo =============================================================
"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe" -c "import socket; ip = socket.gethostbyname(socket.gethostname()); print('  [SERVER] Listening on http://0.0.0.0:8000'); print('  [ESP8266] Set SERVER_URL in resq_robot.ino to: http://' + ip + ':8000/api/iot/state'); print('  [DASHBOARD] http://' + ip + ':8000/dashboard/\n')"
"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe" -m uvicorn main:app --app-dir "D:\FOR CAREER\PROJECTS\Omniboy\backend" --host 0.0.0.0 --port 8000
pause
