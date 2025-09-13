#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 관리자 대시보드 접근을 위한 간단 서버
"""

import http.server
import socketserver
import os
import webbrowser
import time
from threading import Timer

class QuickAdminHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    """브라우저에서 관리자 대시보드 열기"""
    webbrowser.open('http://127.0.0.1:8020/admin_dashboard.html')

def main():
    PORT = 8020

    with socketserver.TCPServer(("", PORT), QuickAdminHandler) as httpd:
        print(f"다함 식자재 관리 시스템 - 빠른 접근 서버")
        print(f"URL: http://127.0.0.1:{PORT}/admin_dashboard.html")
        print(f"API 서버: http://127.0.0.1:8015")
        print(f"브라우저에서 자동으로 열립니다...")

        # 1초 후 브라우저 열기
        Timer(1.0, open_browser).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버 종료")
            httpd.shutdown()

if __name__ == "__main__":
    main()