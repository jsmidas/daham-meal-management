@echo off
echo 🚀 다함 식자재 관리 시스템 - 빠른 시작
echo ==========================================

echo ✅ 1/3 - API 서버 시작 중...
start /B python test_samsung_api.py
timeout /t 3 /nobreak > nul

echo ✅ 2/3 - API 연결 테스트 중...
curl -s "http://127.0.0.1:8000/all-ingredients-for-suppliers?limit=1" > nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ API 연결 성공!
) else (
    echo ❌ API 연결 실패 - 수동으로 확인 필요
)

echo ✅ 3/3 - 식자재 관리 페이지 열기...
start ingredients_management.html

echo.
echo 🎉 시스템이 준비되었습니다!
echo 📊 업체별 현황: 삼성웰스토리, 현대그린푸드, CJ, 푸디스트, 동원홈푸드
echo 📈 총 식자재: 84,215개
echo.
echo 💡 종료하려면 아무 키나 누르세요...
pause > nul