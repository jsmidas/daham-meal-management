@echo off
chcp 65001 > nul
echo 🔍 다함 식자재 관리 시스템 - 상태 진단
echo ==========================================

echo.
echo 📋 1. 필수 파일 확인...
if exist "config.js" (echo ✅ config.js) else (echo ❌ config.js 없음)
if exist "static\utils\module-loader.js" (echo ✅ 모듈 로더) else (echo ❌ 모듈 로더 없음)
if exist "static\utils\admin-cache.js" (echo ✅ 캐시 시스템) else (echo ❌ 캐시 시스템 없음)
if exist "static\modules\dashboard-core\dashboard-core.js" (echo ✅ 대시보드 코어) else (echo ❌ 대시보드 코어 없음)
if exist "admin_dashboard.html" (echo ✅ 메인 대시보드) else (echo ❌ 메인 대시보드 없음)

echo.
echo 📋 2. 서버 상태 확인...
netstat -ano | findstr ":8006" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API 서버 실행 중 (Port 8006)
) else (
    echo ❌ API 서버 미실행 (Port 8006)
)

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 웹 서버 실행 중 (Port 3000)
) else (
    echo ❌ 웹 서버 미실행 (Port 3000)
)

echo.
echo 📋 3. API 연결 테스트...
curl -s -m 5 "http://127.0.0.1:8006/" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 기본 API 응답 정상
) else (
    echo ❌ 기본 API 응답 없음
)

curl -s -m 5 "http://127.0.0.1:8006/api/admin/dashboard-stats" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 대시보드 API 응답 정상
) else (
    echo ❌ 대시보드 API 응답 없음
)

echo.
echo 📋 4. 웹 서버 테스트...
curl -s -m 5 "http://127.0.0.1:3000/" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 웹 서버 응답 정상
) else (
    echo ❌ 웹 서버 응답 없음
)

echo.
echo 🔧 권장 사항:
if not exist "static\utils\module-loader.js" echo - 모듈 로더 누락: 의존성 관리 불가
if not exist "static\utils\admin-cache.js" echo - 캐시 시스템 누락: 성능 저하 예상
netstat -ano | findstr ":8006" | findstr "LISTENING" >nul 2>&1
if not %errorlevel% equ 0 echo - API 서버 시작: python test_samsung_api.py
netstat -ano | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if not %errorlevel% equ 0 echo - 웹 서버 시작: python simple_server.py

echo.
echo 💡 빠른 시작: start.bat 실행
echo 💡 완전 설정: auto_setup.bat 실행
echo.
pause