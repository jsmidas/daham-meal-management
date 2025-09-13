@echo off
chcp 65001 > nul
echo 🛑 다함 식자재 관리 시스템 - 서버 종료
echo ========================================

echo.
echo 📋 실행 중인 서버 프로세스를 종료합니다...

REM Python 서버들 종료
taskkill /F /IM python.exe /T 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python 서버 종료 완료
) else (
    echo ℹ️  실행 중인 Python 서버가 없습니다
)

REM Node.js 서버들 종료 (있다면)
taskkill /F /IM node.exe /T 2>nul
if %errorlevel% equ 0 (
    echo ✅ Node.js 서버 종료 완료
) else (
    echo ℹ️  실행 중인 Node.js 서버가 없습니다
)

echo.
echo ✅ 모든 서버가 안전하게 종료되었습니다.
echo.
timeout /t 2 /nobreak > nul