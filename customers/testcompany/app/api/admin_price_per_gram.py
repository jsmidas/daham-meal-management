#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from models import Ingredient
import re

router = APIRouter()

def extract_weight_in_grams(specification, unit=None):
    """
    규격 문자열에서 중량을 추출하여 그램 단위로 변환합니다.
    개선된 로직: 판매 단위 우선 파싱 + 단위 필드 조합
    """
    if not specification or specification == '규격정보없음':
        return None
    
    # 1순위: KG 단위 (판매 단위로 가장 많이 사용)
    kg_patterns = [
        r'(\d+(?:\.\d+)?)\s*KG\b',      # "1KG", "2.5KG"
        r'(\d+(?:\.\d+)?)\s*kg\b',      # "1kg", "2.5kg"  
        r'(\d+(?:\.\d+)?)\s*Kg\b',      # "1Kg", "2.5Kg"
        r'^KG$',                        # 단순히 "KG"만 있는 경우 → 1kg로 간주
        r'^KG[,\s]',                    # "KG,"로 시작하는 경우 → 1kg로 간주
    ]
    
    for pattern in kg_patterns:
        if pattern in [r'^KG$', r'^KG[,\s]']:
            if re.search(pattern, specification):
                return 1000.0  # "KG"만 있거나 "KG,"로 시작하면 1kg = 1000g
        else:
            matches = re.findall(pattern, specification)
            if matches:
                weight = float(matches[0])
                return weight * 1000  # kg → g
    
    # 2순위: 명시적인 판매단위 그램 (상품명에 있는 경우)
    g_sale_patterns = [
        r'(\d+(?:\.\d+)?)\s*G/EA',      # "500G/EA" 
        r'(\d+(?:\.\d+)?)\s*g/EA',      # "500g/EA"
        r'(\d+(?:\.\d+)?)\s*G\*',       # "100G*10EA"
        r'(\d+(?:\.\d+)?)\s*g\*',       # "100g*10EA"
    ]
    
    for pattern in g_sale_patterns:
        matches = re.findall(pattern, specification)
        if matches:
            weight = float(matches[0])
            return weight  # 이미 g 단위
    
    # 3순위: 단순 G 단위 (크기 설명이 아닌 판매 단위로 추정)
    simple_g_patterns = [
        r'^(\d+(?:\.\d+)?)\s*G$',       # "500G" (전체가 이것뿐)
        r'^(\d+(?:\.\d+)?)\s*g$',       # "500g" (전체가 이것뿐)
        r'\b(\d+(?:\.\d+)?)\s*G\b',     # "500G" (단어 경계)
        r'\b(\d+(?:\.\d+)?)\s*g\b',     # "500g" (단어 경계)
    ]
    
    for pattern in simple_g_patterns:
        matches = re.findall(pattern, specification)
        if matches:
            weight = float(matches[0])
            return weight  # 이미 g 단위
    
    # 4순위: 부피→중량 변환 (물 기준: 1L = 1kg, 1ml = 1g)
    volume_patterns = [
        r'(\d+(?:\.\d+)?)\s*L\b',       # "1.8L", "1L"
        r'(\d+(?:\.\d+)?)\s*l\b',       # "1.8l", "1l" 
        r'(\d+(?:\.\d+)?)\s*ML\b',      # "500ML"
        r'(\d+(?:\.\d+)?)\s*ml\b',      # "500ml"
    ]
    
    for pattern in volume_patterns:
        matches = re.findall(pattern, specification)
        if matches:
            volume = float(matches[0])
            if 'L' in pattern or 'l' in pattern:
                return volume * 1000  # L → g (1L ≈ 1kg = 1000g)
            else:  # ML or ml
                return volume  # ml → g (1ml ≈ 1g)
    
    # 5순위: 단순 단위들 + 텍스트 포함된 KG 케이스
    if specification.strip() in ['Kg', 'kg']:
        return 1000.0  # 1kg = 1000g
    
    # 텍스트가 포함되어도 KG가 있으면 1kg로 간주 (특급, 냉동 등 등급 무관)
    if re.search(r'\bKG\b', specification) or re.search(r'\bkg\b', specification):
        return 1000.0  # 1kg = 1000g
    
    # 6순위: 범위 중간값 계산
    range_patterns = [
        r'(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)\s*KG',  # "0.8~1.2KG"
        r'(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)\s*kg',  # "0.8~1.2kg"
        r'(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)\s*G',   # "400~600G"
        r'(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)\s*g',   # "400~600g"
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*KG',  # "0.8-1.2KG"
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*G',   # "400-600G"
    ]
    
    for pattern in range_patterns:
        matches = re.findall(pattern, specification)
        if matches:
            min_val, max_val = matches[0]
            avg_val = (float(min_val) + float(max_val)) / 2
            if 'KG' in pattern or 'kg' in pattern:
                return avg_val * 1000  # kg → g
            else:
                return avg_val  # 이미 g 단위
    
    # 7순위: 단위 필드 활용 (규격에서 중량을 찾지 못했지만 단위가 중량 단위인 경우)
    if unit:
        unit_clean = unit.strip().upper()
        if unit_clean in ['KG', 'Kg', 'kg']:
            return 1000.0  # 단위가 kg면 1kg = 1000g로 간주
        elif unit_clean in ['G', 'g', 'GM', 'gm']:
            return 1.0  # 단위가 g면 1g로 간주 (이건 거의 없을 듯하지만)
        elif unit_clean in ['L', 'l', 'LITER', 'liter']:
            return 1000.0  # 단위가 L면 1L ≈ 1kg = 1000g로 간주
        elif unit_clean in ['ML', 'ml', 'CC', 'cc']:
            return 1.0  # 단위가 ml면 1ml ≈ 1g로 간주
    
    return None

@router.post("/calculate-price-per-gram")
async def calculate_price_per_gram(db: Session = Depends(get_db)):
    """모든 식자재의 g당 단가를 계산하여 업데이트합니다."""
    try:
        # 입고가와 규격 정보가 있는 항목 조회 (필터링 적용)
        ingredients = db.query(Ingredient).filter(
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0,
            Ingredient.specification.isnot(None),
            Ingredient.specification != '규격정보없음',
            Ingredient.specification != '',
            # 게시유무 필터 (미게시 항목 제외)
            Ingredient.posting_status == '유'
        ).all()
        
        calculated_count = 0
        failed_count = 0
        
        for ingredient in ingredients:
            try:
                # 규격에서 중량(g) 추출 (단위 정보도 함께 활용)
                weight_in_grams = extract_weight_in_grams(ingredient.specification, ingredient.unit)
                
                if weight_in_grams and weight_in_grams > 0:
                    # g당 단가 계산 (입고가 ÷ 중량(g))
                    price_per_gram = float(ingredient.purchase_price) / weight_in_grams
                    ingredient.price_per_gram = price_per_gram
                    calculated_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"계산 실패 - {ingredient.ingredient_code}: {e}")
                failed_count += 1
        
        # 변경사항 저장
        db.commit()
        
        # 결과 확인
        total_count = db.query(Ingredient).count()
        calculated_total = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None)
        ).count()
        
        return {
            "success": True,
            "message": "g당 단가 계산이 완료되었습니다.",
            "total_ingredients": total_count,
            "calculated_count": calculated_total,
            "new_calculated": calculated_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"g당 단가 계산 중 오류가 발생했습니다: {str(e)}")

@router.get("/price-per-gram-stats")
async def get_price_per_gram_stats(db: Session = Depends(get_db)):
    """g당 단가 계산 통계를 반환합니다."""
    try:
        # 필터링된 전체 개수 (게시상태 '유'이면서 입고가가 있는 것)
        total_count = db.query(Ingredient).filter(
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).count()
        
        # g당단가가 계산된 개수 (동일한 필터링 적용)
        calculated_count = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None),
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).count()
        
        # 최고/최저 g당 단가 (필터링 적용)
        highest_price = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None),
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).order_by(Ingredient.price_per_gram.desc()).first()
        
        lowest_price = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None),
            Ingredient.price_per_gram > 0,
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).order_by(Ingredient.price_per_gram.asc()).first()
        
        # 실제 계산 가능한 대상 (필터링 적용) 기준 성공률도 계산
        filtered_total = db.query(Ingredient).filter(
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).count()
        
        filtered_calculated = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None),
            Ingredient.posting_status == '유',
            Ingredient.purchase_price.isnot(None),
            Ingredient.purchase_price > 0
        ).count()
        
        # 전체 기준 (기존)
        all_ingredients_total = db.query(Ingredient).count()
        all_calculated = db.query(Ingredient).filter(
            Ingredient.price_per_gram.isnot(None)
        ).count()
        
        return {
            "total_ingredients": total_count,
            "calculated_count": calculated_count,
            "coverage_percentage": round((calculated_count / total_count * 100), 2) if total_count > 0 else 0,
            "filtered_total": filtered_total,
            "filtered_calculated": filtered_calculated, 
            "filtered_coverage_percentage": round((filtered_calculated / filtered_total * 100), 2) if filtered_total > 0 else 0,
            "all_ingredients_total": all_ingredients_total,
            "all_calculated": all_calculated,
            "all_coverage_percentage": round((all_calculated / all_ingredients_total * 100), 2) if all_ingredients_total > 0 else 0,
            "highest_price": {
                "ingredient_name": highest_price.ingredient_name if highest_price else None,
                "price_per_gram": float(highest_price.price_per_gram) if highest_price else None,
                "specification": highest_price.specification if highest_price else None
            } if highest_price else None,
            "lowest_price": {
                "ingredient_name": lowest_price.ingredient_name if lowest_price else None,
                "price_per_gram": float(lowest_price.price_per_gram) if lowest_price else None,
                "specification": lowest_price.specification if lowest_price else None
            } if lowest_price else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")