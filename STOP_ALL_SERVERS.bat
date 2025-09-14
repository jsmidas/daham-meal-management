@echo off
chcp 65001 > nul
title 🛑 다함 식자재 관리 시스템 - 서버 종료

echo.
echo ========================================================
echo 🛑 다함 식자재 관리 시스템 - 모든 서버 종료
echo ========================================================
echo.

color 0C

echo [1/3] 실행 중인 Python 서버 확인 중...
echo.
netstat -ano | findstr ":8010 :8080 :3000" | findstr "LISTENING"
echo.

echo [2/3] 모든 Python 프로세스 종료 중...
taskkill /F /IM python.exe 2>nul

if %errorlevel%==0 (
    echo ✅ Python 프로세스가 종료되었습니다.
) else (
    echo ⚠️  종료할 Python 프로세스가 없습니다.
)

echo.
echo [3/3] 포트 상태 확인 중...
timeout /t 2 > nul
echo.

netstat -ano | findstr ":8010 :8080 :3000" | findstr "LISTENING" > nul
if %errorlevel%==1 (
    echo ✅ 모든 서버가 정상적으로 종료되었습니다.
) else (
    echo ⚠️  일부 포트가 아직 사용 중일 수 있습니다.
)

echo.
echo ========================================================
echo 서버 종료 완료!
echo ========================================================
echo.
pause