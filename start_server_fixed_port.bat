@echo off
echo 🚀 다함 식자재 관리 시스템 - 고정 포트 시작
echo ==========================================

echo 📋 기존 Python 프로세스 종료...
taskkill /f /im python.exe 2>nul

echo ⏳ 잠시 대기...
timeout /t 2 /nobreak > nul

echo 🔧 서버 시작...
echo ✅ 메인 API 서버: 포트 8001
start /B python main.py

echo ⏳ 메인 서버 시작 대기...
timeout /t 3 /nobreak > nul

echo ✅ 웹 서버: 포트 3000
start /B python -m http.server 3000

echo ⏳ 웹 서버 시작 대기...  
timeout /t 3 /nobreak > nul

echo 🌐 브라우저에서 열기...
start http://localhost:3000/admin_dashboard_working.html

echo.
echo 🎉 시스템이 준비되었습니다!
echo 📊 메인 API: http://localhost:8001
echo 🌐 웹 대시보드: http://localhost:3000/admin_dashboard_working.html
echo.
echo 💡 종료하려면 아무 키나 누르세요...
pause > nul