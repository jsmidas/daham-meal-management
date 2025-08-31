@echo off
echo ========================================
echo 다함식단관리 API 서버 시작
echo ========================================
echo.

cd /d C:\Dev\daham-meal-management

echo [개발 모드로 실행 중...]
echo 종료하려면 Ctrl+C를 누르세요
echo.
echo API 문서: http://127.0.0.1:8001/docs
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload

pause