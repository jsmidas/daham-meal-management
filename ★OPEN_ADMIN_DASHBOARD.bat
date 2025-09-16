@echo off
chcp 65001 >nul
echo.
echo ================================================================================
echo                   ⭐ 관리자 대시보드 열기
echo ================================================================================
echo.
echo 📌 올바른 접속 방법:
echo.
echo    ✅ 정상 접속 (HTTP 프로토콜):
echo       http://localhost:8080/admin_dashboard.html
echo.
echo    ❌ 잘못된 접속 (FILE 프로토콜):
echo       file:///C:/Dev/daham-meal-management/admin_dashboard.html
echo.
echo ================================================================================
echo.
echo 브라우저에서 관리자 대시보드를 올바른 주소로 엽니다...
echo.

start http://localhost:8080/admin_dashboard.html

echo.
echo ✅ 관리자 대시보드가 열렸습니다!
echo.
echo 📌 주의사항:
echo    - 반드시 http://localhost:8080 으로 접속해야 합니다
echo    - file:// 프로토콜로는 API 호출이 제한됩니다
echo    - 사용자 관리 등 모든 기능이 정상 작동합니다
echo.
pause