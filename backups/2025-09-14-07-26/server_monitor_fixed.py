#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🖥️ 다함 식자재 관리 시스템 - 서버 모니터링 도구
실시간으로 서버 상태를 모니터링하고 관리합니다.
"""

import os
import sys
import time
import psutil
import socket
import subprocess
from datetime import datetime
from colorama import init, Fore, Back, Style
import requests

# Windows 콘솔 색상 초기화
init(autoreset=True)

class ServerMonitor:
    def __init__(self):
        self.servers = {
            '8010': {
                'name': '메인 API 서버',
                'type': 'FastAPI',
                'file': 'test_samsung_api.py',
                'url': 'http://127.0.0.1:8010/api/admin/dashboard-stats',
                'status': '정지',
                'pid': None,
                'memory': 0,
                'cpu': 0
            },
            '8080': {
                'name': '통합 컨트롤 타워',
                'type': 'Flask',
                'file': 'unified_control_tower.py',
                'url': 'http://127.0.0.1:8080/control',
                'status': '정지',
                'pid': None,
                'memory': 0,
                'cpu': 0
            },
            '3000': {
                'name': '정적 파일 서버',
                'type': 'Python HTTP',
                'file': 'simple_server.py',
                'url': 'http://127.0.0.1:3000/',
                'status': '정지',
                'pid': None,
                'memory': 0,
                'cpu': 0
            }
        }

    def clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def check_port(self, port):
        """포트 사용 여부 확인"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        sock.close()
        return result == 0

    def get_process_by_port(self, port):
        """포트를 사용하는 프로세스 정보 가져오기"""
        try:
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = int(parts[-1])
                        try:
                            process = psutil.Process(pid)
                            return {
                                'pid': pid,
                                'name': process.name(),
                                'memory': process.memory_info().rss / 1024 / 1024,  # MB
                                'cpu': process.cpu_percent(interval=0.1)
                            }
                        except:
                            return {'pid': pid, 'name': 'Unknown', 'memory': 0, 'cpu': 0}
        except Exception as e:
            pass
        return None

    def check_server_health(self, url):
        """서버 상태 확인"""
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False

    def update_server_status(self):
        """모든 서버 상태 업데이트"""
        for port, server in self.servers.items():
            if self.check_port(port):
                process_info = self.get_process_by_port(port)
                if process_info:
                    server['status'] = '실행중'
                    server['pid'] = process_info['pid']
                    server['memory'] = process_info['memory']
                    server['cpu'] = process_info['cpu']

                    # 헬스 체크
                    if self.check_server_health(server['url']):
                        server['health'] = '정상'
                    else:
                        server['health'] = '응답없음'
                else:
                    server['status'] = '포트사용중'
                    server['pid'] = None
                    server['health'] = '확인불가'
            else:
                server['status'] = '정지'
                server['pid'] = None
                server['memory'] = 0
                server['cpu'] = 0
                server['health'] = '-'

    def display_status(self):
        """서버 상태 표시"""
        self.clear_screen()

        # 헤더
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}[SERVER MONITOR] 다함 식자재 관리 시스템")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.WHITE}현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*80}\n")

        # 서버 상태 테이블
        print(f"{Fore.YELLOW}{'포트':<8} {'서버명':<20} {'타입':<12} {'상태':<10} {'PID':<8} {'메모리':<10} {'CPU':<8} {'헬스':<10}")
        print(f"{Fore.YELLOW}{'-'*90}")

        for port, server in self.servers.items():
            # 상태에 따른 색상
            if server['status'] == '실행중':
                if server['health'] == '정상':
                    status_color = Fore.GREEN
                else:
                    status_color = Fore.YELLOW
            else:
                status_color = Fore.RED

            pid_str = str(server['pid']) if server['pid'] else '-'
            memory_str = f"{server['memory']:.1f} MB" if server['memory'] > 0 else '-'
            cpu_str = f"{server['cpu']:.1f}%" if server['cpu'] > 0 else '-'
            health_str = server.get('health', '-')

            print(f"{Fore.WHITE}{port:<8} "
                  f"{server['name']:<20} "
                  f"{server['type']:<12} "
                  f"{status_color}{server['status']:<10} "
                  f"{Fore.WHITE}{pid_str:<8} "
                  f"{memory_str:<10} "
                  f"{cpu_str:<8} "
                  f"{health_str:<10}")

        print(f"\n{Fore.CYAN}{'='*90}\n")

        # 시스템 리소스
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        print(f"{Fore.YELLOW}📊 시스템 리소스:")
        print(f"  CPU 사용률: {cpu_percent}%")
        print(f"  메모리 사용: {memory.percent}% ({memory.used/1024/1024/1024:.1f}GB / {memory.total/1024/1024/1024:.1f}GB)")

        # 명령어 안내
        print(f"\n{Fore.CYAN}{'='*90}")
        print(f"{Fore.GREEN}명령어:")
        print(f"  [R] 새로고침")
        print(f"  [S] 모든 서버 시작")
        print(f"  [K] 모든 서버 종료")
        print(f"  [1] 메인 API 서버 시작/종료")
        print(f"  [2] 통합 컨트롤 타워 시작/종료")
        print(f"  [3] 정적 파일 서버 시작/종료")
        print(f"  [Q] 종료")
        print(f"{Fore.CYAN}{'='*90}")

    def start_server(self, port):
        """서버 시작"""
        server = self.servers.get(port)
        if not server:
            return

        if server['status'] == '실행중':
            print(f"{Fore.YELLOW}{server['name']}이(가) 이미 실행 중입니다.")
            return

        print(f"{Fore.GREEN}{server['name']} 시작 중...")

        try:
            if port == '8010':
                subprocess.Popen(['python', 'test_samsung_api.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif port == '8080':
                subprocess.Popen(['python', 'unified_control_tower.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif port == '3000':
                subprocess.Popen(['python', 'simple_server.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)

            time.sleep(2)
            print(f"{Fore.GREEN}{server['name']} 시작 완료!")
        except Exception as e:
            print(f"{Fore.RED}서버 시작 실패: {e}")

    def stop_server(self, port):
        """서버 종료"""
        server = self.servers.get(port)
        if not server:
            return

        if server['status'] != '실행중':
            print(f"{Fore.YELLOW}{server['name']}이(가) 실행 중이 아닙니다.")
            return

        if server['pid']:
            try:
                subprocess.run(['taskkill', '/F', '/PID', str(server['pid'])],
                             capture_output=True)
                print(f"{Fore.GREEN}{server['name']} 종료 완료!")
                time.sleep(1)
            except Exception as e:
                print(f"{Fore.RED}서버 종료 실패: {e}")

    def start_all_servers(self):
        """모든 서버 시작"""
        for port in ['8010', '3000', '8080']:
            if self.servers[port]['status'] != '실행중':
                self.start_server(port)
                time.sleep(2)

    def stop_all_servers(self):
        """모든 서버 종료"""
        for port in self.servers.keys():
            if self.servers[port]['status'] == '실행중':
                self.stop_server(port)

    def run(self):
        """메인 실행 루프"""
        while True:
            self.update_server_status()
            self.display_status()

            try:
                command = input(f"\n{Fore.CYAN}명령 입력: ").upper()

                if command == 'Q':
                    print(f"{Fore.YELLOW}모니터링을 종료합니다.")
                    break
                elif command == 'R':
                    continue
                elif command == 'S':
                    self.start_all_servers()
                elif command == 'K':
                    self.stop_all_servers()
                elif command == '1':
                    if self.servers['8010']['status'] == '실행중':
                        self.stop_server('8010')
                    else:
                        self.start_server('8010')
                elif command == '2':
                    if self.servers['8080']['status'] == '실행중':
                        self.stop_server('8080')
                    else:
                        self.start_server('8080')
                elif command == '3':
                    if self.servers['3000']['status'] == '실행중':
                        self.stop_server('3000')
                    else:
                        self.start_server('3000')
                else:
                    print(f"{Fore.RED}잘못된 명령입니다.")

                time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}모니터링을 종료합니다.")
                break

if __name__ == "__main__":
    monitor = ServerMonitor()
    monitor.run()