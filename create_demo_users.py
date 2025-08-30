#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데모 사용자 생성 스크립트
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, RoleEnum
from datetime import datetime

DATABASE_PATH = "meal_management.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def create_demo_users():
    """데모 사용자들 생성"""
    if not os.path.exists(DATABASE_PATH):
        print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {DATABASE_PATH}")
        return False
    
    try:
        # 데이터베이스 연결
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print(f"[INFO] 데이터베이스 연결 성공: {DATABASE_URL}")
        
        # 기존 사용자 확인
        existing_count = session.query(User).count()
        print(f"[INFO] 기존 사용자 수: {existing_count}")
        
        # 데모 사용자 데이터
        demo_users = [
            {
                'username': 'admin',
                'password_hash': 'demo_hash_admin123',  # 실제로는 해시화된 비밀번호
                'role': RoleEnum.admin,
                'contact_info': 'admin@daham.co.kr',
                'department': 'IT부',
                'position': '시스템 관리자',
                'managed_site': '전체',
                'operator': True,
                'semi_operator': False
            },
            {
                'username': 'nutritionist',
                'password_hash': 'demo_hash_nutri123',  # 실제로는 해시화된 비밀번호
                'role': RoleEnum.nutritionist,
                'contact_info': 'nutritionist@daham.co.kr',
                'department': '영양관리팀',
                'position': '수석 영양사',
                'managed_site': '웰스토리 본사',
                'operator': False,
                'semi_operator': True
            }
        ]
        
        # 데모 사용자 생성 또는 업데이트
        for user_data in demo_users:
            existing_user = session.query(User).filter(User.username == user_data['username']).first()
            
            if existing_user:
                # 기존 사용자 업데이트
                for key, value in user_data.items():
                    if key != 'username':  # username은 변경하지 않음
                        setattr(existing_user, key, value)
                existing_user.updated_at = datetime.now()
                print(f"[UPDATE] 기존 사용자 업데이트: {user_data['username']}")
            else:
                # 새 사용자 생성
                new_user = User(**user_data)
                session.add(new_user)
                print(f"[CREATE] 새 사용자 생성: {user_data['username']}")
        
        # 변경사항 저장
        session.commit()
        
        # 결과 확인
        total_users = session.query(User).count()
        print(f"[SUCCESS] 데모 사용자 생성 완료. 총 사용자 수: {total_users}")
        
        # 생성된 사용자 목록 출력
        users = session.query(User).all()
        print("\n[INFO] 등록된 사용자 목록:")
        for user in users:
            print(f"  - {user.username} ({user.role.value}): {user.department} {user.position}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 데모 사용자 생성 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("데모 사용자 생성 시작")
    print("=" * 60)
    
    success = create_demo_users()
    
    print("=" * 60)
    if success:
        print("데모 사용자 생성 성공!")
        print("\n로그인 정보:")
        print("- 관리자: admin / admin123")
        print("- 영양사: nutritionist / nutri123")
    else:
        print("데모 사용자 생성 실패!")
    print("=" * 60)