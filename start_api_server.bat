@echo off
REM 다함 급식관리 시스템 API 서버 시작 스크립트
REM 포트 설정을 여기서 중앙 관리

REM 현재 설정 포트
set API_PORT=8010

echo ==========================================
echo 다함 급식관리 시스템 API 서버 시작
echo 포트: %API_PORT%
echo 시간: %date% %time%
echo ==========================================
echo.

REM 기존 Python 프로세스 종료
echo 기존 Python 프로세스 종료...
taskkill /F /IM python.exe 2>nul

REM 잠시 대기
timeout /t 2 /nobreak >nul

REM API 서버 시작
echo API 서버 시작 중...
set PYTHONIOENCODING=utf-8
python ★test_samsung_api.py

pause