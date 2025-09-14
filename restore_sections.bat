@echo off
echo 섹션 복원 스크립트
echo.
echo 이 스크립트는 템플릿 로딩 문제가 있을 때 사용합니다.
echo 백업에서 직접 HTML 섹션을 복원합니다.
echo.
echo 복원할 섹션을 선택하세요:
echo 1. 사용자 관리
echo 2. 사업장 관리
echo 3. 식단가 관리
echo 4. 모두 복원
echo.
set /p choice="선택 (1-4): "

if "%choice%"=="1" (
    echo 사용자 관리 섹션 복원 중...
    copy /Y "backups\admin_dashboard_original_962lines.html" "admin_dashboard_with_users.html"
    echo 완료! admin_dashboard_with_users.html 파일을 확인하세요.
)

if "%choice%"=="2" (
    echo 사업장 관리 섹션 복원 중...
    copy /Y "backups\admin_dashboard_original_962lines.html" "admin_dashboard_with_sites.html"
    echo 완료! admin_dashboard_with_sites.html 파일을 확인하세요.
)

if "%choice%"=="3" (
    echo 식단가 관리 섹션 복원 중...
    copy /Y "backups\admin_dashboard_original_962lines.html" "admin_dashboard_with_pricing.html"
    echo 완료! admin_dashboard_with_pricing.html 파일을 확인하세요.
)

if "%choice%"=="4" (
    echo 모든 섹션 복원 중...
    copy /Y "backups\admin_dashboard_original_962lines.html" "admin_dashboard_full.html"
    echo 완료! admin_dashboard_full.html 파일을 확인하세요.
)

pause