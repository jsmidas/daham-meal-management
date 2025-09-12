#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티 인스턴스 배포 테스트
"""

from multi_instance_deployer import MultiInstanceDeployer

def test_create_customer():
    """테스트 고객사 생성"""
    
    deployer = MultiInstanceDeployer()
    
    # 테스트 고객사 생성
    customer_info = deployer.create_customer_instance(
        customer_id='testcompany',
        company_name='테스트 급식회사',
        system_name='테스트 급식회사 전용 급식관리 시스템'
    )
    
    print("\n[SUCCESS] 고객사 인스턴스 생성 완료!")
    print(f"URL: {customer_info['url']}")
    print(f"포트: {customer_info['port']}")
    
    return customer_info

def main():
    print("멀티 인스턴스 배포 테스트 시작")
    print("=" * 50)
    
    # 고객사 인스턴스 생성 테스트
    customer_info = test_create_customer()
    
    print("\n다음 단계:")
    print(f"1. {customer_info['url']} 브라우저에서 접속")
    print("2. 브랜딩이 '테스트 급식회사'로 변경되었는지 확인")
    print("3. 독립 데이터베이스로 운영되는지 확인")

if __name__ == "__main__":
    main()