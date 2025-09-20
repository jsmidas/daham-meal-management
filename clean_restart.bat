@echo off
chcp 65001 >nul
echo 다함 식자재 관리 시스템 - 서버 재시작
echo =====================================

echo 1. 모든 Python 프로세스 종료 중...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 >nul

echo 2. API 서버 시작 중 (포트 8010)...
set API_PORT=8010
start /B python ★test_samsung_api.py

echo 3. 서버 시작 대기 중...
timeout /t 10 >nul

echo 4. 웹 서버 시작 중 (포트 9000)...
start /B python simple_server.py 9000

echo 5. 웹 서버 시작 대기 중...
timeout /t 5 >nul

echo 6. 관리자 대시보드 열기...
start http://127.0.0.1:8010/admin_dashboard.html

echo.
echo 완료! 브라우저에서 대시보드가 열립니다.
echo 문제가 있으면 이 창을 닫고 다시 실행해주세요.
echo.
pause