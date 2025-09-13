#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 서버 관리자 (간단 버전)
"""

import os
import sys
import time
import subprocess
import requests

class SimpleServerManager:
    def __init__(self):
        self.api_port = 8015
        self.web_port = 9000

    def kill_all_python(self):
        """모든 Python 프로세스 종료"""
        print("기존 Python 프로세스 정리 중...")
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                         capture_output=True)
            time.sleep(3)
            print("Python 프로세스 정리 완료")
        except:
            print("프로세스 정리 중 오류 발생")

    def start_api_server(self):
        """API 서버 시작"""
        print(f"API 서버 시작 중 (포트: {self.api_port})...")

        env = os.environ.copy()
        env['API_PORT'] = str(self.api_port)

        subprocess.Popen([sys.executable, 'test_samsung_api.py'], env=env)

        # 서버 준비 대기
        for i in range(15):
            try:
                response = requests.get(f"http://127.0.0.1:{self.api_port}/api/admin/suppliers/stats", timeout=1)
                if response.status_code == 200:
                    print(f"API 서버 시작 완료: http://127.0.0.1:{self.api_port}")
                    return True
            except:
                pass
            print(f"대기 중... ({i+1}/15)")
            time.sleep(1)

        print("API 서버 시작 실패")
        return False

    def start_web_server(self):
        """웹 서버 시작"""
        print(f"웹 서버 시작 중 (포트: {self.web_port})...")

        subprocess.Popen([sys.executable, 'simple_server.py', str(self.web_port)])

        # 서버 준비 대기
        for i in range(10):
            try:
                response = requests.get(f"http://127.0.0.1:{self.web_port}", timeout=1)
                if response.status_code == 200:
                    print(f"웹 서버 시작 완료: http://127.0.0.1:{self.web_port}")
                    return True
            except:
                pass
            print(f"대기 중... ({i+1}/10)")
            time.sleep(1)

        print("웹 서버 시작 실패")
        return False

    def open_dashboard(self):
        """대시보드 열기"""
        url = f"http://127.0.0.1:{self.web_port}/admin_dashboard.html"
        print(f"대시보드 열기: {url}")
        try:
            subprocess.run(['start', url], shell=True)
        except:
            print(f"브라우저에서 열어주세요: {url}")

def main():
    manager = SimpleServerManager()

    print("다함 식자재 관리 시스템 - 서버 시작")
    print("=" * 40)

    # 모든 Python 프로세스 정리
    manager.kill_all_python()

    # 서버 시작
    if manager.start_api_server() and manager.start_web_server():
        print("\n모든 서버가 정상적으로 시작되었습니다!")
        print(f"API 서버: http://127.0.0.1:{manager.api_port}")
        print(f"웹 서버: http://127.0.0.1:{manager.web_port}")
        print(f"관리자 대시보드: http://127.0.0.1:{manager.web_port}/admin_dashboard.html")

        # 대시보드 열기
        time.sleep(2)
        manager.open_dashboard()

        print("\nCtrl+C를 눌러 종료할 수 있습니다.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n서버 종료 중...")
            manager.kill_all_python()
    else:
        print("서버 시작 실패")

if __name__ == "__main__":
    main()