@echo off
chcp 65001 >nul
echo.
echo ================================================================================
echo                     ⭐ 다함 식자재 관리 시스템 - 서버 시작 ⭐
echo ================================================================================
echo.
echo 서버를 시작합니다...
echo.

echo [1/2] 통합 컨트롤 타워 시작 (포트 8080)...
start "통합 컨트롤 타워" cmd /c "python unified_control_tower.py"

echo.
echo 3초 대기 중...
timeout /t 3 /nobreak >nul

echo.
echo [2/2] 서버 컨트롤 패널 열기...
echo.
echo ================================================================================
echo.
echo   ✅ 서버가 시작되었습니다!
echo.
echo   📌 접속 URL:
echo      - 서버 컨트롤 패널: http://localhost:8080/★server_control_panel.html
echo      - 관리자 대시보드: http://localhost:8080/admin_dashboard.html
echo      - 컨트롤 패널: http://localhost:8080/control
echo      - 모니터링: http://localhost:8080/monitor
echo.
echo ================================================================================
echo.
echo 브라우저에서 서버 컨트롤 패널을 엽니다...
timeout /t 2 /nobreak >nul

start http://localhost:8080/★server_control_panel.html

echo.
echo 이 창은 닫아도 서버는 계속 실행됩니다.
echo.
pause