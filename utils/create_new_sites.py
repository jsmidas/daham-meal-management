#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

# 새로운 사업장 생성
sites_to_create = [
    {
        "name": "서울본사",
        "code": "HQ001",
        "site_type": "본사",
        "contact_person": "김관리",
        "contact_phone": "02-1234-5678",
        "address": "서울특별시 강남구",
        "description": "서울 본사 사업장"
    },
    {
        "name": "부산지점",
        "code": "BR001",
        "site_type": "지점",
        "contact_person": "이담당",
        "contact_phone": "051-5678-1234",
        "address": "부산광역시 해운대구",
        "description": "부산 지점 사업장"
    }
]

for site_data in sites_to_create:
    response = requests.post(
        "http://127.0.0.1:8001/api/admin/sites",
        json=site_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"[SUCCESS] 생성 성공: {site_data['name']} (ID: {result.get('id')})")
        else:
            print(f"[FAIL] 생성 실패: {site_data['name']} - {result.get('message')}")
    else:
        print(f"[ERROR] HTTP 오류: {response.status_code}")

# 생성된 사업장 목록 확인
print("\n현재 사업장 목록:")
response = requests.get("http://127.0.0.1:8001/api/admin/sites")
if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        for site in result.get("sites", []):
            print(f"  - {site['name']} ({site['site_type']}) - ID: {site['id']}")