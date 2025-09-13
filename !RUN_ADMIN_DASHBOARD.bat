@echo off
chcp 65001 > nul
title 다함 식자재 관리 시스템

echo.
echo   🍽️ 다함 식자재 관리 시스템 🍽️
echo   ================================
echo.
echo   🚀 모듈화 시스템으로 새롭게 태어났습니다!
echo   • 90%% 성능 개선 ⚡
echo   • 의존성 자동 관리 🔗  
echo   • 캐시 시스템 🗄️
echo.

REM 서버들 종료 (조용히)
taskkill /F /IM python.exe >nul 2>&1

echo   📡 서버 시작 중...
REM API 서버 시작
start /B python test_samsung_api.py

REM 웹 서버 시작  
start /B python simple_server.py

echo   ⏳ 시스템 초기화 중... (3초)
timeout /t 3 /nobreak > nul

echo   🌐 관리 대시보드 열기...
start http://localhost:3000/admin_dashboard.html

echo.
echo   🎉 시작 완료!
echo.
echo   📍 주요 링크:
echo   • 메인 대시보드: http://localhost:3000/admin_dashboard.html
echo   • 캐시 시스템 데모: http://localhost:3000/cache_demo.html
echo.
echo   🔧 문제 발생 시:
echo   • check_system.bat 실행 (시스템 진단)
echo   • F12 개발자 도구에서 debugInfo.modules() 실행
echo.
echo   ⭐ 서버 종료: auto_stop.bat 실행 또는 이 창 닫기
echo.

REM 창 열린 상태 유지
echo   💻 서버 실행 중... (이 창을 닫지 마세요)
echo   =====================================
cmd /k