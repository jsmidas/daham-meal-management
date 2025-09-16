@echo off
echo API 서버 재시작 중...

REM 모든 Python 프로세스 종료
taskkill /F /IM python.exe 2>nul

REM 잠시 대기
timeout /t 2 /nobreak >nul

REM 새로운 서버 시작
echo API 서버 시작 중...
python test_samsung_api.py

pause