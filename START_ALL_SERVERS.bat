@echo off
chcp 65001 > nul
title 🚀 다함 식자재 관리 시스템 - 통합 서버 시작

echo.
echo ========================================================
echo 🚀 다함 식자재 관리 시스템 - 통합 서버 시작
echo ========================================================
echo.

:: 색상 설정
color 0A

:: 기존 서버 종료
echo [1/4] 기존 서버 프로세스 정리 중...
taskkill /F /IM python.exe 2>nul
timeout /t 2 > nul

echo.
echo [2/4] 메인 API 서버 시작 (포트: 8010)...
start /min cmd /k "title 📡 메인 API 서버 (8010) && python test_samsung_api.py"
timeout /t 3 > nul

echo.
echo [3/4] 정적 파일 서버 시작 (포트: 3000)...
start /min cmd /k "title 📁 정적 파일 서버 (3000) && python simple_server.py"
timeout /t 2 > nul

echo.
echo [4/4] 서버 상태 확인 중...
timeout /t 3 > nul

echo.
echo ========================================================
echo ✅ 모든 서버가 시작되었습니다!
echo ========================================================
echo.
echo 📌 접속 정보:
echo    - 관리자 대시보드: http://127.0.0.1:3000/admin_dashboard.html
echo    - API 문서: http://127.0.0.1:8010/docs
echo.
echo 📌 서버 포트:
echo    - 메인 API 서버: 8010
echo    - 정적 파일 서버: 3000
echo.
echo ========================================================
echo.

:: 서버 모니터링 실행 옵션
echo 서버 모니터링을 시작하시겠습니까? (Y/N)
choice /C YN /N /M "선택: "
if %errorlevel%==1 (
    echo.
    echo 서버 모니터링을 시작합니다...
    python server_monitor.py
) else (
    echo.
    echo 서버가 백그라운드에서 실행 중입니다.
    echo 이 창을 닫아도 서버는 계속 실행됩니다.
    pause
)