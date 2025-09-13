@echo off
cd /d "%~dp0"
cls

echo.
echo ================================================================
echo           다함 식자재 관리 시스템 - 확실한 시작
echo ================================================================
echo.
echo 이 스크립트는 완전히 독립적으로 실행됩니다.
echo 다른 프로그램이나 설정에 영향받지 않습니다.
echo.

REM 기존 프로세스 정리
echo [1/4] 기존 서버 프로세스 정리 중...
taskkill /F /IM python.exe 2>nul >nul
timeout /t 2 /nobreak >nul

echo [2/4] 새로운 서버 시작 중...
echo        포트: 9000 (고정)
echo        파일: simple_server.py
start /B python simple_server.py

echo [3/4] 서버 시작 대기 중...
timeout /t 5 /nobreak >nul

echo [4/4] 브라우저에서 관리 페이지 열기...
start http://localhost:9000/admin_dashboard.html

echo.
echo ================================================================
echo                    시작 완료!
echo ================================================================
echo.
echo 🌐 관리자 페이지: http://localhost:9000/admin_simple.html
echo 📡 API 베이스:    http://localhost:9000/api/
echo 📂 포트:          9000 (고정)
echo.
echo ✅ 모든 기능이 하나의 서버에서 독립적으로 실행됩니다
echo ✅ 다른 프로그램이나 설정에 영향받지 않습니다
echo ✅ 항상 동일한 방식으로 작동합니다
echo.
echo 서버를 종료하려면 python.exe 프로세스를 종료하세요
echo (작업 관리자에서 python.exe 종료)
echo.
pause