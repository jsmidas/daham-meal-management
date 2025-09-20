# API 검증 가이드

## 메뉴/레시피 API 검증 체크리스트

### 1. 저장 API 검증
- [ ] `/api/recipe/save` 엔드포인트가 직접 구현되어 있는가?
- [ ] 프록시 전달이 아닌 직접 DB 저장인가?
- [ ] 저장 완료 후 실제 DB에 데이터가 있는가?

### 2. 테이블 구조 검증
```sql
-- 재료 테이블 구조 확인
PRAGMA table_info(menu_recipe_ingredients);

-- INSERT 쿼리 검증
INSERT INTO menu_recipe_ingredients (
    recipe_id, ingredient_code, ingredient_name, specification, unit,
    delivery_days, selling_price, quantity, amount, supplier_name, sort_order
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

### 3. 데이터 저장 검증
```python
# 저장 후 즉시 확인
cursor.execute("SELECT COUNT(*) FROM menu_recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
ingredient_count = cursor.fetchone()[0]
print(f"[DEBUG] 저장된 재료 개수: {ingredient_count}")
```

### 4. 포트 통합 검증
- [ ] 모든 API가 동일한 포트(8010)에서 동작하는가?
- [ ] 외부 프록시 호출이 없는가?
- [ ] config.js가 올바른 포트를 가리키는가?

## 문제 발생 시 체크포인트
1. 서버 로그에서 DEBUG 메시지 확인
2. 브라우저 네트워크 탭에서 실제 API 호출 확인
3. 데이터베이스에서 직접 데이터 존재 여부 확인
4. 테이블 구조와 INSERT 쿼리 일치성 확인