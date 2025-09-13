"""
Import recipes from bok2.boksili.kr into local database
"""
import json
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Recipe, RecipeIngredient, Ingredient

def import_recipes_to_db():
    """Import recipes into database"""
    print("=" * 50)
    print("레시피 데이터베이스 임포트")
    print("=" * 50)
    
    # Database setup
    engine = create_engine('sqlite:///daham_meal.db', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Load recipe data
        with open('recipes_for_import.json', 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
        
        print(f"\n[정보] 임포트할 레시피: {len(recipes_data)}개")
        
        # Track statistics
        stats = {
            'total': len(recipes_data),
            'imported': 0,
            'skipped': 0,
            'ingredients_created': 0
        }
        
        # Clear existing recipes (optional)
        existing_count = db.query(Recipe).count()
        if existing_count > 0:
            print(f"[경고] 기존 레시피 {existing_count}개 존재")
            print("[정보] 기존 레시피를 유지하고 새 레시피 추가")
            # Skip deletion to preserve existing data
        
        # Import recipes
        print("\n[진행] 레시피 임포트 시작...")
        
        # Keep track of ingredients
        ingredient_cache = {}
        
        # Get existing ingredients
        existing_ingredients = db.query(Ingredient).all()
        for ing in existing_ingredients:
            ingredient_cache[ing.name.lower()] = ing
        
        batch_size = 100
        for i, recipe_data in enumerate(recipes_data):
            if i % batch_size == 0 and i > 0:
                db.commit()
                print(f"  - {i}/{len(recipes_data)} 레시피 처리 중...")
            
            # Create recipe  
            # Store category and raw text in notes field
            notes = f"카테고리: {recipe_data['category']}\n업장수: {recipe_data['business_count']}\n\n{recipe_data.get('raw_text', '')}"
            
            recipe = Recipe(
                name=recipe_data['name'],
                version="1.0",  # Default version
                notes=notes
            )
            
            db.add(recipe)
            db.flush()  # Get recipe ID
            
            # Add ingredients (track to avoid duplicates)
            added_ingredients = set()
            for ing_data in recipe_data.get('ingredients', []):
                ing_name = ing_data['name'].strip().lower()
                
                # Get or create ingredient
                if ing_name not in ingredient_cache:
                    # Check if ingredient exists
                    ingredient = db.query(Ingredient).filter(
                        Ingredient.name.ilike(f"%{ing_name}%")
                    ).first()
                    
                    if not ingredient:
                        # Create new ingredient
                        ingredient = Ingredient(
                            name=ing_data['name'],
                            base_unit=ing_data.get('unit', 'EA')
                        )
                        db.add(ingredient)
                        db.flush()
                        stats['ingredients_created'] += 1
                    
                    ingredient_cache[ing_name] = ingredient
                else:
                    ingredient = ingredient_cache[ing_name]
                
                # Skip if already added this ingredient to this recipe
                if ingredient.id in added_ingredients:
                    continue
                added_ingredients.add(ingredient.id)
                
                # Create recipe-ingredient relationship
                recipe_ing = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=Decimal(str(ing_data['quantity'])),
                    unit=ing_data.get('unit', 'EA')  # Use unit from data or default to EA
                )
                db.add(recipe_ing)
            
            stats['imported'] += 1
        
        # Final commit
        db.commit()
        
        # Print statistics
        print("\n" + "=" * 50)
        print("[완료] 레시피 임포트 완료!")
        print(f"  - 전체 레시피: {stats['total']}개")
        print(f"  - 임포트 성공: {stats['imported']}개")
        print(f"  - 새로운 식재료: {stats['ingredients_created']}개")
        
        # Verify import
        final_recipe_count = db.query(Recipe).count()
        final_ingredient_count = db.query(Ingredient).count()
        final_recipe_ing_count = db.query(RecipeIngredient).count()
        
        print("\n[데이터베이스 현황]")
        print(f"  - 총 레시피: {final_recipe_count}개")
        print(f"  - 총 식재료: {final_ingredient_count}개")
        print(f"  - 레시피-식재료 관계: {final_recipe_ing_count}개")
        
        # Show sample recipes
        print("\n[샘플 레시피]")
        sample_recipes = db.query(Recipe).limit(5).all()
        for recipe in sample_recipes:
            ing_count = db.query(RecipeIngredient).filter(
                RecipeIngredient.recipe_id == recipe.id
            ).count()
            print(f"  - {recipe.name}: {ing_count}개 식재료")
        
        print("\n[OK] 모든 작업 완료!")
        
    except Exception as e:
        print(f"\n[ERROR] 임포트 중 오류 발생: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

def main():
    """Main function"""
    import_recipes_to_db()

if __name__ == "__main__":
    main()