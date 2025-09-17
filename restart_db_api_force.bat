@echo off
echo 포트 8012를 사용하는 모든 프로세스 강제 종료 중...

rem 포트 8012를 사용하는 프로세스 찾아서 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8012 ^| findstr LISTENING') do (
    echo PID %%a 종료 중...
    taskkill /F /PID %%a 2>nul
)

echo 2초 대기...
timeout /t 2 /nobreak >nul

echo DB Recipe API 시작 중...
start "DB Recipe API" python db_recipe_api.py

echo.
echo DB Recipe API가 포트 8012에서 재시작되었습니다.
echo 브라우저를 새로고침하고 초록색 점이 있는 DB 레시피를 클릭해보세요.