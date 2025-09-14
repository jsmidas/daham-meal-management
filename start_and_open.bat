@echo off
echo 다함 관리 시스템 시작...
echo.

REM API 서버가 실행 중인지 확인
netstat -ano | findstr :8010 >nul
if %errorlevel% neq 0 (
    echo API 서버 시작 중...
    start /min cmd /c "python test_samsung_api.py"
    timeout /t 3 /nobreak >nul
) else (
    echo API 서버가 이미 실행 중입니다.
)

echo.
echo 브라우저에서 관리자 대시보드 열기...
start http://127.0.0.1:8010/admin_dashboard.html

echo.
echo 완료! 브라우저를 확인하세요.
echo.
pause