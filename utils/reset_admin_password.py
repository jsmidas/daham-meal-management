#!/usr/bin/env python3
"""admin 비밀번호를 'admin'으로 재설정"""

import sqlite3
import hashlib

def reset_admin_password():
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 새 비밀번호 설정 (admin)
        new_password = 'admin'
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # admin 사용자의 비밀번호 업데이트
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?
            WHERE username = 'admin'
        """, (password_hash,))
        
        conn.commit()
        conn.close()
        
        print(f"admin 계정의 비밀번호가 '{new_password}'로 재설정되었습니다.")
        print("브라우저에서 http://127.0.0.1:8001/login 으로 이동하여")
        print("사용자명: admin, 비밀번호: admin 으로 로그인하세요.")
        
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    reset_admin_password()