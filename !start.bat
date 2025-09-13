@echo off
chcp 65001 > nul
echo 🚀 다함 식자재 관리 시스템 - 빠른 시작
echo ========================================

REM 기존 서버 종료
taskkill /F /IM python.exe 2>nul >nul

echo ⚡ API 서버 시작 중... (Port 8006)
start /B python test_samsung_api.py

echo ⚡ 웹 서버 시작 중... (Port 3000)  
start /B python simple_server.py

echo 📱 브라우저에서 대시보드 열기...
timeout /t 3 /nobreak > nul
start http://localhost:3000/admin_dashboard.html

echo.
echo 🎉 시스템 시작 완료!
echo 📋 종료하려면: auto_stop.bat 실행
echo.