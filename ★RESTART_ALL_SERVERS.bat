@echo off
chcp 65001 >nul
cls
echo.
echo ================================================================================
echo                   ⭐ 모든 서버 재시작 - 다함 식자재 관리 시스템
echo ================================================================================
echo.

echo [단계 1/4] 기존 Python 프로세스 종료 중...
taskkill /F /IM python.exe 2>nul
echo ✅ 모든 Python 프로세스가 종료되었습니다.
echo.

echo [단계 2/4] 3초 대기 중...
timeout /t 3 /nobreak >nul
echo.

echo [단계 3/4] 서버 시작 중...
echo.

echo 📌 통합 컨트롤 타워 시작 (포트 8080)...
start "통합 컨트롤 타워" cmd /k "cd /d C:\Dev\daham-meal-management && python unified_control_tower.py"

timeout /t 3 /nobreak >nul

echo 📌 API 서버 시작 (포트 8010)...
start "API 서버" cmd /k "cd /d C:\Dev\daham-meal-management && set API_PORT=8010 && python test_samsung_api.py"

timeout /t 3 /nobreak >nul
echo.

echo [단계 4/4] 서버 컨트롤 패널 열기...
echo.
echo ================================================================================
echo.
echo   ✅ 모든 서버가 시작되었습니다!
echo.
echo   📌 실행 중인 서버:
echo      - 통합 컨트롤 타워: http://localhost:8080
echo      - API 서버: http://localhost:8010
echo.
echo   📌 관리 페이지:
echo      - 서버 컨트롤 패널: http://localhost:8080/★server_control_panel.html
echo      - 관리자 대시보드: http://localhost:8080/admin_dashboard.html
echo.
echo ================================================================================
echo.

start http://localhost:8080/★server_control_panel.html

echo 브라우저에서 서버 컨트롤 패널이 열렸습니다.
echo.
echo 이 창은 닫아도 서버는 계속 실행됩니다.
echo.
pause