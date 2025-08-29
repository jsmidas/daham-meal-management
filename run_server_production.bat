@echo off
echo ========================================
echo 다함식단관리 API 서버 시작 (운영 모드)
echo ========================================
echo.

cd /d C:\Dev\daham-meal-management

echo [운영 모드로 실행 중...]
echo 종료하려면 Ctrl+C를 누르세요
echo.
echo API 문서: http://127.0.0.1:8000/docs
echo.

:: 운영 모드: reload 없음, 다중 워커
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

pause