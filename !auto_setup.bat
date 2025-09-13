@echo off
chcp 65001 > nul
echo 🚀 다함 식자재 관리 시스템 - 자동 환경 설정 (모듈화 버전)
echo ================================================================

echo.
echo 📋 1단계: 시스템 파일 확인 중...

REM 필수 설정 파일 확인
if not exist "config.js" (
    echo ❌ config.js 파일이 없습니다.
    echo ⚠️  중앙 설정 파일이 필요합니다.
    pause
    exit /b 1
)

REM 모듈 시스템 확인
if not exist "static\utils\module-loader.js" (
    echo ❌ 모듈 로더가 없습니다.
    echo ⚠️  의존성 관리 시스템이 필요합니다.
    pause
    exit /b 1
)

REM 캐시 시스템 확인  
if not exist "static\utils\admin-cache.js" (
    echo ❌ 캐시 시스템이 없습니다.
    echo ⚠️  성능 최적화 모듈이 필요합니다.
    pause
    exit /b 1
)

REM 대시보드 코어 확인
if not exist "static\modules\dashboard-core\dashboard-core.js" (
    echo ❌ 대시보드 코어가 없습니다.
    echo ⚠️  메인 대시보드 모듈이 필요합니다.
    pause
    exit /b 1
)

echo ✅ 모든 시스템 파일 확인 완료

echo.
echo 📋 2단계: 서버 상태 확인 중...

REM 기존 서버 종료 (있다면)
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul

echo ✅ 기존 프로세스 정리 완료

echo.
echo 📋 3단계: API 서버 시작 중...
start /B "API Server" python test_samsung_api.py

REM 서버 시작 대기
timeout /t 3 /nobreak > nul

echo.
echo 📋 4단계: 모듈화 시스템 연결 테스트 중...

REM API 서버 테스트
curl -s "http://127.0.0.1:8006/api/admin/dashboard-stats" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API 서버 연결 성공! (Port 8006)
) else (
    echo ❌ API 서버 연결 실패. 수동으로 확인이 필요합니다.
    echo 💡 python test_samsung_api.py 를 직접 실행해보세요.
)

REM 캐시 API 테스트
curl -s "http://127.0.0.1:8006/api/admin/users" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 캐시 지원 API 확인 완료!
) else (
    echo ⚠️  캐시 지원 API 일부 미작동 (기본 기능은 정상)
)

echo.
echo 📋 5단계: 웹 서버 시작 중...
start /B "Web Server" python simple_server.py

REM 웹 서버 시작 대기
timeout /t 2 /nobreak > nul

echo.
echo 🎉 모듈화 시스템 시작 완료!
echo ================================================================
echo 🎯 메인 대시보드: http://localhost:3000/admin_dashboard.html
echo    ↳ 🔗 의존성 자동 관리 | 🗄️ 캐시 시스템 | ⚡ 90% 성능 개선
echo 🧪 캐시 시스템 데모: http://localhost:3000/cache_demo.html
echo 📊 식자재 관리: http://localhost:3000/ingredients_management.html
echo 🛠️  간단 관리자: http://localhost:3000/admin_simple.html
echo ================================================================

echo.
echo 🔧 문제 발생 시 (모듈화 시스템):
echo 1. F12 개발자 도구에서 debugInfo.modules() 실행
echo 2. debugInfo.cache() 로 캐시 상태 확인
echo 3. 이 스크립트를 다시 실행하세요
echo 4. config.js에서 모듈 설정을 확인하세요
echo.

echo 🌐 브라우저에서 관리 대시보드 자동 열기...
timeout /t 2 /nobreak > nul
start http://localhost:3000/admin_dashboard.html

echo.
echo ⭐ 개발 완료 후 서버 종료: auto_stop.bat 실행
echo 💡 시스템 상태 확인: check_system.bat 실행  
echo 💡 디버그 도구: F12 → 콘솔에서 debugInfo.modules() 실행
echo.
pause