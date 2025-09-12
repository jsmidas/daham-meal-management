"""
Migrate ingredients table to new column structure
"""
import sqlite3
import os
from datetime import datetime

def migrate_ingredients_table():
    db_path = 'daham_meal.db'
    
    if not os.path.exists(db_path):
        print("Database not found, creating new one...")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingredients'")
        if cursor.fetchone():
            print("Found existing ingredients table, backing up...")
            
            # Create backup table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingredients_backup AS 
                SELECT * FROM ingredients
            """)
            
            # Drop the old table
            cursor.execute("DROP TABLE ingredients")
            print("Old table dropped")
        
        # Create new table with correct structure
        cursor.execute("""
            CREATE TABLE ingredients (
                id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                ingredient_code TEXT UNIQUE NOT NULL,
                ingredient_name TEXT NOT NULL,
                posting_status TEXT,
                origin TEXT,
                specification TEXT,
                unit TEXT NOT NULL,
                tax_type TEXT,
                delivery_days TEXT NOT NULL,
                purchase_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2) NOT NULL,
                supplier_name TEXT NOT NULL,
                notes TEXT,
                created_date DATETIME,
                extra_field1 TEXT,
                extra_field2 TEXT,
                extra_field3 TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_by TEXT,
                upload_batch_id INTEGER,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_ingredients_category ON ingredients(category)")
        cursor.execute("CREATE INDEX idx_ingredients_sub_category ON ingredients(sub_category)")
        cursor.execute("CREATE INDEX idx_ingredients_code ON ingredients(ingredient_code)")
        cursor.execute("CREATE INDEX idx_ingredients_name ON ingredients(ingredient_name)")
        cursor.execute("CREATE INDEX idx_ingredients_supplier ON ingredients(supplier_name)")
        
        print("New ingredients table created with proper structure")
        
        # Insert sample data
        sample_data = [
            ('채소류', '엽채류', 'VEG001', '시금치', 'Y', '국산', '1kg', 'kg', 'N', '1', 3000, 3500, '테스트업체', '테스트 데이터'),
            ('육류', '소고기', 'MEAT001', '등심', 'Y', '호주산', '1kg', 'kg', 'N', '2', 15000, 18000, '육류공급업체', '품질 좋은 등심'),
            ('곡물류', '쌀류', 'GRAIN001', '백미', 'Y', '국산', '20kg', 'kg', 'N', '1', 40000, 45000, '곡물업체', '프리미엄 쌀'),
        ]
        
        cursor.executemany("""
            INSERT INTO ingredients 
            (category, sub_category, ingredient_code, ingredient_name, posting_status, origin, 
             specification, unit, tax_type, delivery_days, purchase_price, selling_price, 
             supplier_name, notes, created_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
        """, sample_data)
        
        conn.commit()
        print(f"Inserted {len(sample_data)} sample ingredients")
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_ingredients_table()