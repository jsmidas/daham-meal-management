@echo off
echo ================================
echo 다함 식자재 관리 시스템 서버 시작
echo ================================

echo.
REM Check if python is available
where python >nul 2>nul
if errorlevel 1 (
	echo [ERROR] Python is not installed or not in PATH.
	pause
	exit /b
)

REM Check if API script exists
if not exist "test_samsung_api.py" (
	echo [ERROR] test_samsung_api.py not found in current directory.
	pause
	exit /b
)

echo 1. API 서버 시작중... (포트 8006)
start /B python test_samsung_api.py

echo.
REM Check if proxy server script exists
if not exist "proxy_server.py" (
	echo [ERROR] proxy_server.py not found in current directory.
	pause
	exit /b
)

echo 2. 프록시 웹 서버 시작중... (포트 3000)  
start /B python proxy_server.py

echo.
echo 3초 후 브라우저에서 페이지를 엽니다...
timeout /t 3 /nobreak >nul

echo.
echo 4. 브라우저에서 관리자 페이지 열기... (캐시 없이)
start http://localhost:3000/admin_dashboard.html?v=%time%

echo.
echo ================================
echo 서버가 성공적으로 시작되었습니다!
echo ================================
echo.
echo API 서버: http://127.0.0.1:8006
echo 웹 페이지: http://localhost:3000/admin_dashboard.html
echo.
echo 서버를 종료하려면 이 창을 닫으세요.
echo.
pause