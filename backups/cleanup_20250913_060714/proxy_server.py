#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 프록시 서버
정적 파일 서빙 + API 프록시 기능
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
from urllib.error import HTTPError

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """프록시 기능이 포함된 HTTP 요청 핸들러"""
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_to_api()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_api()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.proxy_to_api()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.proxy_to_api()
        else:
            self.send_error(405, "Method Not Allowed")
    
    def proxy_to_api(self):
        """API 요청을 API 서버로 프록시"""
        try:
            # API 서버 URL 구성
            api_url = f'http://127.0.0.1:8006{self.path}'
            
            # 요청 데이터 읽기 (POST/PUT의 경우)
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # API 서버에 요청 전달
            request = urllib.request.Request(api_url, data=post_data, method=self.command)
            
            # 헤더 복사 (Content-Type 등)
            if 'Content-Type' in self.headers:
                request.add_header('Content-Type', self.headers['Content-Type'])
            
            # API 서버에 요청하고 응답 받기
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                
                # 응답 헤더 설정
                self.send_response(response.getcode())
                self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                # 응답 데이터 전송
                self.wfile.write(response_data)
                
        except HTTPError as e:
            # API 서버 에러 응답
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({
                'success': False,
                'error': f'API Error: {e.reason}'
            }).encode('utf-8')
            self.wfile.write(error_response)
            
        except Exception as e:
            # 기타 에러
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = json.dumps({
                'success': False,
                'error': f'Proxy Error: {str(e)}'
            }).encode('utf-8')
            self.wfile.write(error_response)

if __name__ == "__main__":
    PORT = 3000
    
    with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"프록시 서버가 포트 {PORT}에서 시작되었습니다")
        print(f"정적 파일: http://localhost:{PORT}")
        print(f"API 프록시: http://localhost:{PORT}/api/* -> http://127.0.0.1:8006/api/*")
        print("서버를 중지하려면 Ctrl+C를 누르세요")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 중지합니다...")
            httpd.shutdown()