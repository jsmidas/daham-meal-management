@echo off
echo DB Recipe API 재시작 중...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq db_recipe_api.py*" 2>nul
timeout /t 2 /nobreak >nul
start "DB Recipe API" python db_recipe_api.py
echo DB Recipe API가 포트 8012에서 시작되었습니다.