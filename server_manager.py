#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 서버 관리자
서버 및 API 프로세스를 중앙에서 관리하는 스크립트
"""

import os
import sys
import time
import signal
import subprocess
import requests
import threading
from typing import Optional

class ServerManager:
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.web_process: Optional[subprocess.Popen] = None
        self.api_port = 8015
        self.web_port = 9000
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def kill_all_python_processes(self):
        """모든 Python 프로세스 종료 (현재 프로세스 제외)"""
        print("기존 Python 프로세스 정리 중...")
        current_pid = os.getpid()

        try:
            # Windows에서 Python 프로세스 찾기
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                                  capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
                killed_count = 0

                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid_str = parts[1].strip('"')
                            try:
                                pid = int(pid_str)
                                if pid != current_pid:
                                    subprocess.run(['taskkill', '/PID', str(pid), '/F'],
                                                 capture_output=True)
                                    killed_count += 1
                            except (ValueError, subprocess.SubprocessError):
                                continue

                print(f"✅ {killed_count}개의 Python 프로세스를 정리했습니다.")
                time.sleep(2)  # 프로세스 종료 대기

        except Exception as e:
            print(f"⚠️ 프로세스 정리 중 오류: {e}")

    def check_port_available(self, port: int) -> bool:
        """포트 사용 가능 여부 확인"""
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            return f":{port}" not in result.stdout
        except:
            return True

    def wait_for_server(self, url: str, timeout: int = 30) -> bool:
        """서버가 준비될 때까지 대기"""
        print(f"⏳ 서버 준비 대기 중: {url}")

        for i in range(timeout):
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ 서버 준비 완료: {url}")
                    return True
            except requests.RequestException:
                pass

            print(f"   대기 중... ({i+1}/{timeout})")
            time.sleep(1)

        print(f"❌ 서버 시작 실패: {url}")
        return False

    def start_api_server(self):
        """API 서버 시작"""
        print(f"🚀 API 서버 시작 중 (포트: {self.api_port})...")

        if not self.check_port_available(self.api_port):
            print(f"⚠️ 포트 {self.api_port}가 이미 사용 중입니다.")
            return False

        try:
            # 환경변수 설정
            env = os.environ.copy()
            env['API_PORT'] = str(self.api_port)

            # API 서버 시작
            self.api_process = subprocess.Popen(
                [sys.executable, 'test_samsung_api.py'],
                cwd=self.base_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 서버 준비 대기
            api_url = f"http://127.0.0.1:{self.api_port}/api/admin/suppliers/stats"
            if self.wait_for_server(api_url, 15):
                print(f"✅ API 서버 시작 완료: http://127.0.0.1:{self.api_port}")
                return True
            else:
                self.stop_api_server()
                return False

        except Exception as e:
            print(f"❌ API 서버 시작 실패: {e}")
            return False

    def start_web_server(self):
        """웹 서버 시작"""
        print(f"🌐 웹 서버 시작 중 (포트: {self.web_port})...")

        if not self.check_port_available(self.web_port):
            print(f"⚠️ 포트 {self.web_port}가 이미 사용 중입니다.")
            return False

        try:
            # 웹 서버 시작
            self.web_process = subprocess.Popen(
                [sys.executable, 'simple_server.py', str(self.web_port)],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 서버 준비 대기
            web_url = f"http://127.0.0.1:{self.web_port}"
            if self.wait_for_server(web_url, 10):
                print(f"✅ 웹 서버 시작 완료: http://127.0.0.1:{self.web_port}")
                return True
            else:
                self.stop_web_server()
                return False

        except Exception as e:
            print(f"❌ 웹 서버 시작 실패: {e}")
            return False

    def stop_api_server(self):
        """API 서버 중지"""
        if self.api_process:
            print("🛑 API 서버 중지 중...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            self.api_process = None
            print("✅ API 서버 중지 완료")

    def stop_web_server(self):
        """웹 서버 중지"""
        if self.web_process:
            print("🛑 웹 서버 중지 중...")
            self.web_process.terminate()
            try:
                self.web_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.web_process.kill()
            self.web_process = None
            print("✅ 웹 서버 중지 완료")

    def stop_all_servers(self):
        """모든 서버 중지"""
        self.stop_api_server()
        self.stop_web_server()

    def restart_all_servers(self):
        """모든 서버 재시작"""
        print("🔄 서버 재시작 중...")
        self.stop_all_servers()
        time.sleep(2)

        if self.start_api_server() and self.start_web_server():
            print("✅ 서버 재시작 완료")
            return True
        else:
            print("❌ 서버 재시작 실패")
            return False

    def get_status(self):
        """서버 상태 확인"""
        print("\n📊 서버 상태:")

        # API 서버 상태
        try:
            response = requests.get(f"http://127.0.0.1:{self.api_port}/api/admin/suppliers/stats", timeout=2)
            if response.status_code == 200:
                print(f"✅ API 서버: 정상 (포트 {self.api_port})")
            else:
                print(f"⚠️ API 서버: 응답 오류 (포트 {self.api_port})")
        except requests.RequestException:
            print(f"❌ API 서버: 연결 실패 (포트 {self.api_port})")

        # 웹 서버 상태
        try:
            response = requests.get(f"http://127.0.0.1:{self.web_port}", timeout=2)
            if response.status_code == 200:
                print(f"✅ 웹 서버: 정상 (포트 {self.web_port})")
            else:
                print(f"⚠️ 웹 서버: 응답 오류 (포트 {self.web_port})")
        except requests.RequestException:
            print(f"❌ 웹 서버: 연결 실패 (포트 {self.web_port})")

    def open_dashboard(self):
        """관리자 대시보드 열기"""
        dashboard_url = f"http://127.0.0.1:{self.web_port}/admin_dashboard.html"
        print(f"🌐 관리자 대시보드 열기: {dashboard_url}")

        try:
            subprocess.run(['start', dashboard_url], shell=True)
        except:
            print(f"📋 브라우저에서 다음 주소를 열어주세요: {dashboard_url}")

def main():
    manager = ServerManager()

    print("🔧 다함 식자재 관리 시스템 - 서버 관리자")
    print("=" * 50)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'start':
            manager.kill_all_python_processes()
            if manager.start_api_server() and manager.start_web_server():
                print("\n🎉 모든 서버가 정상적으로 시작되었습니다!")
                print(f"📊 API 서버: http://127.0.0.1:{manager.api_port}")
                print(f"🌐 웹 서버: http://127.0.0.1:{manager.web_port}")
                print(f"🎛️ 관리자 대시보드: http://127.0.0.1:{manager.web_port}/admin_dashboard.html")

                # 자동으로 대시보드 열기
                time.sleep(2)
                manager.open_dashboard()

                # 서버 유지
                try:
                    print("\n⌨️ Ctrl+C를 눌러 서버를 종료할 수 있습니다.")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 서버 종료 중...")
                    manager.stop_all_servers()

        elif command == 'stop':
            manager.kill_all_python_processes()

        elif command == 'restart':
            manager.kill_all_python_processes()
            manager.restart_all_servers()

        elif command == 'status':
            manager.get_status()

        elif command == 'clean':
            manager.kill_all_python_processes()

        else:
            print("사용법: python server_manager.py [start|stop|restart|status|clean]")
    else:
        # 인터랙티브 모드
        print("사용 가능한 명령어:")
        print("  start   - 모든 서버 시작")
        print("  stop    - 모든 서버 중지")
        print("  restart - 모든 서버 재시작")
        print("  status  - 서버 상태 확인")
        print("  clean   - 모든 Python 프로세스 정리")

        command = input("\n명령어를 입력하세요: ").strip().lower()

        if command == 'start':
            manager.kill_all_python_processes()
            if manager.start_api_server() and manager.start_web_server():
                print("\n🎉 모든 서버가 정상적으로 시작되었습니다!")
                manager.open_dashboard()
        elif command in ['stop', 'restart', 'status', 'clean']:
            exec(f"manager.{command}_all_servers()" if command in ['stop', 'restart'] else
                 f"manager.{command}()" if command in ['status'] else
                 "manager.kill_all_python_processes()")

if __name__ == "__main__":
    main()