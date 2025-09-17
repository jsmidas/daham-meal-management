@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║            ⭐ 다함 식자재 관리 시스템 - 빠른 시작 가이드 ⭐              ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.
echo 어떤 서버를 시작하시겠습니까?
echo.
echo   [1] 🎛️  통합 컨트롤 타워 (권장) - 모든 기능 포함
echo   [2] 🔗  API 서버만 시작
echo   [3] 🌐  간단한 웹 서버만 시작
echo   [4] 🚀  모든 서버 시작
echo   [5] ⭐  서버 컨트롤 패널 열기 (브라우저)
echo   [6] 🧹  모든 Python 프로세스 종료
echo   [0] ❌  종료
echo.
echo ────────────────────────────────────────────────────────────────────────────

set /p choice="선택 (0-6): "

if "%choice%"=="1" goto START_CONTROL_TOWER
if "%choice%"=="2" goto START_API_SERVER
if "%choice%"=="3" goto START_WEB_SERVER
if "%choice%"=="4" goto START_ALL
if "%choice%"=="5" goto OPEN_CONTROL_PANEL
if "%choice%"=="6" goto CLEANUP
if "%choice%"=="0" goto END

echo.
echo ❌ 잘못된 선택입니다. 다시 선택해주세요.
echo.
pause
goto :eof

:START_CONTROL_TOWER
echo.
echo 🎛️ 통합 컨트롤 타워를 시작합니다... (포트 8080)
start "통합 컨트롤 타워" cmd /c "python ★unified_control_tower.py"
echo.
echo ✅ 통합 컨트롤 타워가 시작되었습니다!
echo.
echo 📌 접속 URL:
echo    - 서버 컨트롤 패널: http://localhost:8080/★server_control_panel.html
echo    - 관리자 대시보드: http://localhost:8080/admin_dashboard.html
echo    - 컨트롤 패널: http://localhost:8080/control
echo.
timeout /t 3 /nobreak >nul
start http://localhost:8080/★server_control_panel.html
goto END

:START_API_SERVER
echo.
echo 🔗 API 서버를 시작합니다... (포트 8010)
start "API 서버" cmd /c "set API_PORT=8010 && python ★test_samsung_api.py"
echo.
echo ✅ API 서버가 시작되었습니다!
echo    URL: http://localhost:8010/api/admin/
echo.
pause
goto END

:START_WEB_SERVER
echo.
echo 🌐 웹 서버를 시작합니다... (포트 9000)
start "웹 서버" cmd /c "python ★simple_server.py"
echo.
echo ✅ 웹 서버가 시작되었습니다!
echo    URL: http://localhost:9000/
echo.
pause
goto END

:START_ALL
echo.
echo 🚀 모든 서버를 시작합니다...
echo.
echo [1/3] 통합 컨트롤 타워 시작...
start "통합 컨트롤 타워" cmd /c "python ★unified_control_tower.py"
timeout /t 2 /nobreak >nul

echo [2/3] API 서버 시작...
start "API 서버" cmd /c "set API_PORT=8010 && python ★test_samsung_api.py"
timeout /t 2 /nobreak >nul

echo [3/3] 웹 서버 시작...
start "웹 서버" cmd /c "python ★simple_server.py"
echo.
echo ✅ 모든 서버가 시작되었습니다!
echo.
timeout /t 3 /nobreak >nul
start http://localhost:8080/★server_control_panel.html
goto END

:OPEN_CONTROL_PANEL
echo.
echo ⭐ 서버 컨트롤 패널을 브라우저에서 엽니다...
echo.
echo 주의: 통합 컨트롤 타워가 실행 중이어야 합니다!
echo.
start http://localhost:8080/★server_control_panel.html
goto END

:CLEANUP
echo.
echo 🧹 모든 Python 프로세스를 종료합니다...
echo.
echo 정말로 종료하시겠습니까? (Y/N)
set /p confirm="선택: "
if /i "%confirm%"=="Y" (
    taskkill /F /IM python.exe 2>nul
    echo ✅ 모든 Python 프로세스가 종료되었습니다.
) else (
    echo ❌ 취소되었습니다.
)
echo.
pause
goto END

:END
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 프로그램을 종료합니다.
echo.
timeout /t 2 /nobreak >nul
exit