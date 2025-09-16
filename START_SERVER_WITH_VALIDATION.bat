@echo off
echo =====================================
echo    다함 식자재 관리 시스템 시작
echo =====================================
echo.

echo [1/3] 데이터베이스 검증 중...
python validate_database.py
if %errorlevel% neq 0 (
    echo.
    echo 데이터베이스에 문제가 발견되어 자동 복구되었습니다.
    echo 계속 진행합니다...
    echo.
)

echo [2/3] 기존 서버 종료 중...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [3/3] API 서버 시작 중...
echo.
echo ======================================
echo   서버가 시작되었습니다!
echo   주소: http://127.0.0.1:8010
echo
echo   관리자 대시보드 접속:
echo   http://127.0.0.1:8010/admin_dashboard.html
echo ======================================
echo.
python test_samsung_api.py