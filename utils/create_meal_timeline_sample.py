#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15일 타임라인 식수 관리 샘플 데이터 생성
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, MealCountTemplate, MealCountTimeline
from datetime import datetime, date, timedelta

# 데이터베이스 연결
DATABASE_URL = "sqlite:///./meal_management.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_sample_templates():
    """식수 템플릿 샘플 데이터 생성"""
    db = SessionLocal()
    
    try:
        # 기존 템플릿 데이터 삭제
        db.query(MealCountTemplate).delete()
        
        # 템플릿 데이터 정의
        template_data = {
            '도시락': {
                '조식A': [('본사', 150), ('지사1', 80), ('지사2', 120)],
                '조식B': [('지점1', 60), ('지점2', 90)],
                '중식A': [('본사', 200), ('지사1', 100), ('지사2', 150), ('지사3', 80)],
                '중식B': [('지점1', 85), ('지점2', 110), ('지점3', 70)],
                '석식A': [('본사', 120), ('지사1', 60)],
                '야식A': [('본사', 50)]
            },
            '운반': {
                '조식A': [('운반1지역', 200), ('운반2지역', 180)],
                '중식A': [('운반1지역', 250), ('운반2지역', 220), ('운반3지역', 190)],
                '중식B': [('운반4지역', 160), ('운반5지역', 140)]
            },
            '학교': {
                '조식A': [('초등학교1', 300), ('초등학교2', 250)],
                '중식A': [('초등학교1', 320), ('초등학교2', 280), ('중학교1', 400), ('고등학교1', 450)],
                '석식A': [('중학교1', 200), ('고등학교1', 250)]
            },
            '요양원': {
                '조식A': [('요양원1', 80), ('요양원2', 75), ('요양원3', 90)],
                '중식A': [('요양원1', 85), ('요양원2', 78), ('요양원3', 92), ('요양원4', 70)],
                '중식B': [('요양원5', 65), ('요양원6', 88)],
                '석식A': [('요양원1', 75), ('요양원2', 70)],
                '야식A': [('요양원1', 30)]
            },
            '확장1': {
                '중식A': [('사업장1', 120), ('사업장2', 100)]
            },
            '확장2': {}
        }
        
        # 템플릿 데이터 생성
        display_order = 0
        for tab_type, categories in template_data.items():
            for meal_category, sites in categories.items():
                for site_name, default_count in sites:
                    template = MealCountTemplate(
                        tab_type=tab_type,
                        meal_category=meal_category,
                        site_name=site_name,
                        display_order=display_order,
                        is_active=True,
                        default_count=default_count
                    )
                    db.add(template)
                    display_order += 1
        
        db.commit()
        print(f"템플릿 데이터 {display_order}개 생성 완료")
        
    except Exception as e:
        db.rollback()
        print(f"템플릿 생성 오류: {e}")
    finally:
        db.close()

def create_sample_timeline_data():
    """타임라인 샘플 데이터 생성 (과거 3일 + 오늘 + 미래 11일)"""
    db = SessionLocal()
    
    try:
        # 기존 타임라인 데이터 삭제
        db.query(MealCountTimeline).delete()
        
        # 15일 날짜 범위 생성
        today = date.today()
        start_date = today - timedelta(days=3)  # 과거 3일부터
        
        # 템플릿 데이터 가져오기
        templates = db.query(MealCountTemplate).filter(MealCountTemplate.is_active == True).all()
        
        # 각 템플릿에 대해 15일치 데이터 생성
        for template in templates:
            for i in range(15):
                current_date = start_date + timedelta(days=i)
                
                # 과거/현재/미래에 따른 값 변동
                base_count = template.default_count
                
                if current_date < today:
                    # 과거 실적 (확정됨, 약간의 랜덤 변동)
                    import random
                    variation = random.uniform(0.85, 1.15)  # ±15% 변동
                    meal_count = int(base_count * variation)
                    is_confirmed = True
                elif current_date == today:
                    # 오늘 (편집 가능)
                    meal_count = base_count
                    is_confirmed = False
                else:
                    # 미래 예상 (기본값에서 약간 변동)
                    import random
                    variation = random.uniform(0.9, 1.1)  # ±10% 변동
                    meal_count = int(base_count * variation)
                    is_confirmed = False
                
                timeline_record = MealCountTimeline(
                    tab_type=template.tab_type,
                    meal_category=template.meal_category,
                    site_name=template.site_name,
                    meal_count=meal_count,
                    target_date=current_date,
                    is_confirmed=is_confirmed,
                    target_material_cost=2500.0  # 기본 목표 재료비
                )
                db.add(timeline_record)
        
        db.commit()
        
        # 생성된 데이터 개수 확인
        total_records = db.query(MealCountTimeline).count()
        print(f"타임라인 데이터 {total_records}개 생성 완료")
        print(f"기간: {start_date} ~ {start_date + timedelta(days=14)}")
        
    except Exception as e:
        db.rollback()
        print(f"타임라인 데이터 생성 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("15일 타임라인 식수 관리 샘플 데이터 생성 중...")
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 샘플 데이터 생성
    create_sample_templates()
    create_sample_timeline_data()
    
    print("샘플 데이터 생성 완료!")