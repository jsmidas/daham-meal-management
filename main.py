"""
모듈화된 메인 애플리케이션 파일
- FastAPI 앱 생성 및 설정
- 7개 도메인별 라우터 등록
- 미들웨어 설정
- 예외 핸들러
- 총 라인 수: ~200라인 (기존 4907라인에서 96% 감소)

라우터 구조:
├── auth: 인증/로그인 관리
├── suppliers: 협력업체 관리
├── customers: 사업장 관리
├── admin: 관리자 기능
├── meal_plans: 식단/메뉴/레시피 관리
├── operations: 발주/입고/전처리 관리
└── dashboard: 대시보드/통계/유틸리티
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 데이터베이스 초기화
from app.database import init_db, test_db_connection

# 모델 임포트 (테이블 생성을 위해 필요)
import models

# API 라우터 imports
from app.api.auth import router as auth_router
from app.api.suppliers import router as suppliers_router
from app.api.customers import router as customers_router
from app.api.admin import router as admin_router
from app.api.meal_plans import router as meal_plans_router
from app.api.operations import router as operations_router
from app.api.dashboard import router as dashboard_router

# 예외 처리
from app.core.exceptions import BaseCustomException, create_error_response

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 애플리케이션 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 코드"""
    # 시작시 실행
    logger.info("애플리케이션 시작")
    
    # 데이터베이스 연결 테스트
    if test_db_connection():
        logger.info("데이터베이스 연결 성공")
    else:
        logger.error("데이터베이스 연결 실패")
        
    # 데이터베이스 테이블 생성 (개발 환경에서만)
    try:
        init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
    
    yield
    
    # 종료시 실행
    logger.info("애플리케이션 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="다함 급식관리시스템",
    description="견고하고 확장 가능한 급식관리시스템",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # API 문서 URL
    redoc_url="/redoc"  # ReDoc 문서 URL
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영환경에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# API 라우터 등록
# ==============================================================================

# 인증 라우터
app.include_router(auth_router, tags=["인증"])

# 협력업체 라우터  
app.include_router(suppliers_router, tags=["협력업체"])

# 사업장 라우터
app.include_router(customers_router, tags=["사업장"])

# 관리자 라우터
app.include_router(admin_router, tags=["관리자"])

# 식단 관리 라우터
app.include_router(meal_plans_router, tags=["식단관리"])

# 운영 관리 라우터
app.include_router(operations_router, tags=["운영관리"])

# 대시보드 라우터
app.include_router(dashboard_router, tags=["대시보드"])

# ==============================================================================
# 전역 예외 핸들러
# ==============================================================================

@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    """사용자 정의 예외 처리"""
    logger.error(f"Custom exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "내부 서버 오류가 발생했습니다.",
                "status_code": 500
            }
        }
    )

# ==============================================================================
# 기본 라우트
# ==============================================================================

# Favicon handling
@app.get("/favicon.ico")
async def favicon():
    """Favicon handler to prevent 404 errors"""
    from fastapi.responses import FileResponse
    import os
    if os.path.exists("favicon.ico"):
        return FileResponse("favicon.ico")
    else:
        # Return empty response to prevent 404
        return Response(status_code=204)

# Chrome dev tools handler
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    """Chrome DevTools discovery handler to prevent 404 errors"""
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/")
async def root():
    """루트 페이지 - 대시보드"""
    try:
        from fastapi.responses import FileResponse
        import os
        if os.path.exists("dashboard.html"):
            return FileResponse("dashboard.html")
        else:
            return {"error": "Dashboard HTML file not found", "cwd": os.getcwd()}
    except Exception as e:
        return {"error": str(e), "type": "FileResponse Error"}

@app.get("/menu_recipe_management.html")
async def menu_recipe_page():
    """메뉴 레시피 관리 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("menu_recipe_management.html")

@app.get("/menu")
async def menu_page():
    """메뉴 관리 페이지 (단축 URL)"""
    from fastapi.responses import FileResponse
    return FileResponse("menu_recipe_management.html")

@app.get("/meal-plan")
async def meal_plan_page():
    """식단관리 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("meal_plan_management.html")

@app.get("/meal_plan_management.html")
async def meal_plan_management_page():
    """식단관리 페이지 (직접 접근)"""
    from fastapi.responses import FileResponse
    return FileResponse("meal_plan_management.html")

# 기타 주요 페이지 라우트들
@app.get("/meal-count")
async def meal_count_page():
    """급식수 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("meal_count_management.html")

@app.get("/dashboard")
async def dashboard_redirect():
    """대시보드 리다이렉트"""
    from fastapi.responses import FileResponse
    return FileResponse("dashboard.html")

@app.get("/ordering")
async def ordering_page():
    """발주관리"""
    from fastapi.responses import FileResponse
    return FileResponse("ordering_management.html")

@app.get("/receiving")
async def receiving_page():
    """입고관리"""
    from fastapi.responses import FileResponse
    return FileResponse("receiving_management.html")

@app.get("/preprocessing")
async def preprocessing_page():
    """전처리관리"""
    from fastapi.responses import FileResponse
    return FileResponse("preprocessing_management.html")

@app.get("/login")
async def login_page():
    """로그인 페이지"""
    from fastapi.responses import FileResponse
    return FileResponse("login.html")

@app.get("/admin")
async def admin_page():
    """관리자 페이지 - 모듈화된 버전"""
    from fastapi.responses import FileResponse
    return FileResponse("admin_dashboard.html")

@app.get("/admin-legacy")
async def admin_legacy_page():
    """관리자 페이지 - 레거시 버전 (백업용)"""
    from fastapi.responses import FileResponse
    return FileResponse("admin_dashboard_legacy_backup.html")

@app.get("/suppliers")
async def suppliers_page():
    """협력업체 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("supplier_management.html")

@app.get("/supplier")
async def supplier_page():
    """협력업체 관리 (단수형)"""
    from fastapi.responses import FileResponse
    return FileResponse("supplier_management.html")

@app.get("/ingredients")
async def ingredients_page():
    """식재료 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("ingredients_management.html")

@app.get("/cooking")
async def cooking_page():
    """조리지시서"""
    from fastapi.responses import FileResponse
    return FileResponse("cooking_instruction_management.html")

@app.get("/portion")
async def portion_page():
    """소분지시서"""
    from fastapi.responses import FileResponse
    return FileResponse("portion_instruction_management.html")


@app.get("/cooking-instructions")
async def cooking_instructions_page():
    """조리지시서 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("cooking_instruction_management.html")

@app.get("/portion-instructions")
async def portion_instructions_page():
    """소분지시서 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("portion_instruction_management.html")

@app.get("/meal-timeline")
async def meal_timeline_page():
    """급식수 타임라인"""
    from fastapi.responses import FileResponse
    return FileResponse("meal_count_timeline.html")

@app.get("/ingredient-upload")
async def ingredient_upload_page():
    """식재료 업로드"""
    from fastapi.responses import FileResponse
    return FileResponse("ingredient_file_upload.html")

@app.get("/user-management")
async def user_management_page():
    """사용자 관리"""
    from fastapi.responses import FileResponse
    return FileResponse("user_management.html")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    db_status = test_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": "2.0.0"
    }

# ==============================================================================
# 정적 파일 서빙 (개발환경용)
# ==============================================================================

# HTML 파일과 정적 파일 서빙
import os
try:
    # CSS와 JS 파일이 루트 디렉토리에 있으므로 루트를 정적 파일로 서빙
    app.mount("/static", StaticFiles(directory="."), name="static")
    logger.info("Static files mounted successfully from current directory")
except Exception as e:
    logger.warning(f"Static files mounting failed: {e}")

# ==============================================================================
# 애플리케이션 실행
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )