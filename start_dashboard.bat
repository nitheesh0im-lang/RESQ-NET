@echo off
echo =============================================================
echo  RESQ-NET Dashboard File Server Starting...
echo  Dashboard: http://127.0.0.1:3000/dashboard/
echo  Victim App: http://127.0.0.1:3000/victim_app/
echo =============================================================
"D:\FOR CAREER\PROJECTS\Omniboy\backend\venv\Scripts\python.exe" -m http.server 3000 --directory "D:\FOR CAREER\PROJECTS\Omniboy"
pause
