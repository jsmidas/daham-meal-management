@echo off
REM ===================================================================
REM 다함 급식관리 시스템 - 간단 시작 스크립트
REM 포트 충돌 자동 해결, 데이터베이스 검증, 통합 관리
REM ===================================================================

echo.
echo ==========================================
echo  🍱 다함 급식관리 시스템 시작
echo ==========================================
echo  시간: %date% %time%
echo  이 스크립트는 자동으로:
echo  - 포트 충돌 감지 및 해결
echo  - 데이터베이스 검증
echo  - 최적 포트로 서버 시작
echo  - 설정 파일 자동 업데이트
echo ==========================================
echo.

REM 기존 Python 프로세스 정리
echo 🧹 기존 프로세스 정리 중...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM 환경 변수 설정
set PYTHONIOENCODING=utf-8
set DAHAM_DB_PATH=daham_meal.db

REM 서버 관리자로 시작
echo 🚀 서버 관리자 시작 중...
echo    python server_manager.py start
echo.
python server_manager.py start

REM 종료 시 안내
echo.
echo ==========================================
echo  서버가 종료되었습니다.
echo  컨트롤 패널: ★server_control_panel.html
echo  수동 시작: python server_manager.py start
echo ==========================================
pause