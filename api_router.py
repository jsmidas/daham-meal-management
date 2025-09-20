#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 라우터 - 메인 API와 분리된 모듈들을 연결
"""

import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json

# 분리된 API 서버들의 URL
MENU_RECIPES_API_URL = "http://127.0.0.1:8011"

class APIRouter:
    """API 요청을 적절한 마이크로서비스로 라우팅"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def route_menu_recipe_request(self, path: str, method: str, request: Request):
        """메뉴/레시피 API 요청 라우팅"""
        try:
            # 요청 데이터 준비
            headers = dict(request.headers)
            # Host 헤더 제거 (충돌 방지)
            headers.pop('host', None)

            # 쿼리 파라미터
            query_params = str(request.query_params) if request.query_params else ""

            # 전체 URL 구성
            target_url = f"{MENU_RECIPES_API_URL}{path}"
            if query_params:
                target_url += f"?{query_params}"

            # 요청 바디 (POST/PUT인 경우)
            body = None
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                body = await request.body()

            # 분리된 API 서버로 요청 전달
            response = await self.client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body
            )

            # 응답 반환
            return JSONResponse(
                content=response.json() if response.headers.get('content-type', '').startswith('application/json') else {"data": response.text},
                status_code=response.status_code
            )

        except httpx.RequestError as e:
            return JSONResponse(
                content={"success": False, "error": f"API 연결 실패: {str(e)}"},
                status_code=503
            )
        except Exception as e:
            return JSONResponse(
                content={"success": False, "error": f"라우팅 오류: {str(e)}"},
                status_code=500
            )

    async def check_menu_recipes_api_health(self):
        """메뉴/레시피 API 서버 상태 확인"""
        try:
            response = await self.client.get(f"{MENU_RECIPES_API_URL}/api/recipes")
            return response.status_code == 200
        except:
            return False

    async def close(self):
        """클라이언트 연결 정리"""
        await self.client.aclose()

# 싱글톤 인스턴스
router = APIRouter()

async def route_to_menu_api(path: str, method: str, request: Request):
    """메뉴/레시피 API로 라우팅하는 헬퍼 함수"""
    return await router.route_menu_recipe_request(path, method, request)

async def get_api_health_status():
    """분리된 API 서버들의 상태 확인"""
    menu_api_healthy = await router.check_menu_recipes_api_health()

    return {
        "menu_recipes_api": {
            "url": MENU_RECIPES_API_URL,
            "healthy": menu_api_healthy,
            "status": "running" if menu_api_healthy else "down"
        }
    }