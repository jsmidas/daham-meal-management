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
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 데이터베이스 초기화
from app.database import init_db, test_db_connection

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

@app.get("/")
async def root():
    """루트 페이지"""
    return {"message": "다함 급식관리시스템 v2.0", "status": "running"}

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

# 운영환경에서는 nginx 등 웹서버에서 처리
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Static files mounting failed: {e}")

# ==============================================================================
# 애플리케이션 실행
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_new:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )