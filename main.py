from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="Daham Menu Manager API",
    description="다함식단관리 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 데이터베이스 연결
DATABASE_URL = "postgresql://postgres:123@localhost:5432/daham_menu"
# 엔진 생성 부분을 더 안전하게 수정
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "options": "-c client_encoding=utf8"
    },
    pool_pre_ping=True,
    echo=False  # 로그 출력 비활성화
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 세션 의존성 수정
def get_db():
    db = SessionLocal()
    try:
        # 인코딩 설정 제거 - 연결 시점에 문제 발생
        # db.execute(text("SET client_encoding TO 'UTF8'"))
        yield db
    finally:
        db.close()

# Pydantic 모델들
class DietPlanBase(BaseModel):
    category: str
    date: str
    description: Optional[str] = None

class MenuBase(BaseModel):
    menu_type: str
    target_num_persons: int
    target_food_cost: Optional[float] = None
    evaluation_score: Optional[int] = None
    color: Optional[str] = None

class MenuItemBase(BaseModel):
    name: str
    portion_num_persons: Optional[int] = None
    yield_rate: Optional[float] = 1.0
    photo_url: Optional[str] = None

# API 엔드포인트들
@app.get("/")
async def root():
    return {"message": "다함식단관리 API에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/diet-plans")
async def get_diet_plans(db: Session = Depends(get_db)):
    """식단표 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM DietPlans ORDER BY date DESC"))
        plans = [dict(row._mapping) for row in result]
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menus/{diet_plan_id}")
async def get_menus(diet_plan_id: int, db: Session = Depends(get_db)):
    """특정 식단표의 메뉴 목록 조회"""
    try:
        result = db.execute(
            text("SELECT * FROM Menus WHERE diet_plan_id = :plan_id"),
            {"plan_id": diet_plan_id}
        )
        menus = [dict(row._mapping) for row in result]
        return {"success": True, "data": menus}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu-items/{menu_id}")
async def get_menu_items(menu_id: int, db: Session = Depends(get_db)):
    """특정 메뉴의 메뉴 아이템 목록 조회"""
    try:
        result = db.execute(
            text("SELECT * FROM MenuItems WHERE menu_id = :menu_id"),
            {"menu_id": menu_id}
        )
        items = [dict(row._mapping) for row in result]
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recipes")
async def get_recipes(db: Session = Depends(get_db)):
    """레시피 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM Recipe ORDER BY name"))
        plans = [dict(row._mapping) for row in result]
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingredients")
async def get_ingredients(db: Session = Depends(get_db)):
    """식재료 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM Ingredients ORDER BY name"))
        ingredients = [dict(row._mapping) for row in result]
        return {"success": True, "data": ingredients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cost-analysis")
async def get_cost_analysis(db: Session = Depends(get_db)):
    """메뉴별 비용 분석 조회"""
    try:
        result = db.execute(text("SELECT * FROM menu_cost_analysis"))
        analysis = [dict(row._mapping) for row in result]
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # ... existing code ...

@app.get("/test-db")
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        db = SessionLocal()
        # 간단한 쿼리 실행
        result = db.execute(text("SELECT 1 as test"))
        db.close()
        return {"success": True, "message": "데이터베이스 연결 성공", "test": result.fetchone()[0]}
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)