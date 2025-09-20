import sqlite3

def create_learning_tables():
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 계산 패턴 학습 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_calculation_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        specification_pattern TEXT NOT NULL,
        unit_pattern TEXT NOT NULL,
        extraction_method TEXT NOT NULL,
        extraction_value REAL NOT NULL,
        success_count INTEGER DEFAULT 1,
        failure_count INTEGER DEFAULT 0,
        last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    ''')

    # 계산 오류 피드백 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS calculation_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingredient_id INTEGER,
        original_specification TEXT,
        original_unit TEXT,
        original_price REAL,
        calculated_unit_price REAL,
        corrected_unit_price REAL,
        feedback_type TEXT, -- 'manual_correction', 'pattern_error', 'unit_mismatch'
        pattern_suggestion TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT DEFAULT 'system'
    )
    ''')

    conn.commit()
    print("계산 패턴 학습 테이블 생성 완료")

    # 기존 패턴들을 초기 데이터로 삽입
    initial_patterns = [
        ('*kg', 'kg', 'direct_kg', 1000, 'kg단위 직접 변환'),
        ('*g', 'g', 'direct_g', 1, 'g단위 직접 변환'),
        ('*ml', 'ml', 'direct_ml', 1, 'ml단위 직접 변환'),
        ('*l', 'l', 'direct_l', 1000, 'l단위를 ml로 변환'),
        ('*개입', 'kg', 'extract_count_per_kg', 0, '개입수로 나누기'),
        ('*팩', 'kg', 'extract_pack_weight', 0, '팩 중량 추출'),
        ('*포', 'kg', 'extract_pack_weight', 0, '포 중량 추출'),
    ]

    for spec_pattern, unit_pattern, method, value, notes in initial_patterns:
        cursor.execute('''
            INSERT OR IGNORE INTO price_calculation_patterns
            (specification_pattern, unit_pattern, extraction_method, extraction_value, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (spec_pattern, unit_pattern, method, value, notes))

    conn.commit()
    conn.close()
    print("초기 패턴 데이터 삽입 완료")

if __name__ == "__main__":
    create_learning_tables()