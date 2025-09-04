"""
견고한 데이터베이스 연결 관리
- 연결 풀링
- 트랜잭션 관리
- 에러 처리
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 설정
DATABASE_URL = "sqlite:///./daham_meal.db"

# SQLite 최적화 설정
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # SQLite 멀티스레드 지원
        "timeout": 20,               # 타임아웃 설정
    },
    pool_pre_ping=True,             # 연결 상태 확인
    pool_recycle=3600,              # 연결 재활용 시간
    echo=False                      # SQL 로깅 (운영시 False)
)

# SQLite Foreign Key 제약조건 활성화
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 최적화 설정"""
    cursor = dbapi_connection.cursor()
    # Foreign Key 제약조건 활성화
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL 모드 활성화 (성능 향상)
    cursor.execute("PRAGMA journal_mode=WAL")
    # 동기화 모드 최적화
    cursor.execute("PRAGMA synchronous=NORMAL")
    # 캐시 크기 최적화
    cursor.execute("PRAGMA cache_size=10000")
    cursor.close()

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스
Base = declarative_base()

# 의존성 주입용 세션 제공자
def get_db() -> Generator:
    """
    데이터베이스 세션 제공
    - 자동 커밋/롤백
    - 연결 해제 보장
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# 데이터베이스 초기화
def init_db():
    """
    데이터베이스 테이블 생성
    - 개발 환경에서만 사용
    - 운영 환경은 마이그레이션 도구 사용
    - 임시로 비활성화 (기존 데이터베이스 스키마 사용)
    """
    try:
        Base.metadata.create_all(bind=engine)  # 테이블 생성 활성화
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# 데이터베이스 연결 테스트
def test_db_connection():
    """데이터베이스 연결 상태 확인"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False