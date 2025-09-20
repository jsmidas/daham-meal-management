#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 급식관리 시스템 - 포트 총괄 관리 시스템
모든 포트 관련 작업을 중앙에서 처리
"""

import os
import socket
import subprocess
import sys
import json
import time
from datetime import datetime

# 기본 포트 설정
DEFAULT_PORTS = {
    'API_SERVER': 8010,  # 메인 API 서버 (통합 완료)
    'WEB_SERVER': 3000,  # 웹 서버 (정적 파일)
    'BACKUP_PORTS': [8011, 8012, 8013, 8014, 8015, 8016, 8017],
    'RESERVED_PORTS': [8080, 9000],  # 시스템 예약 포트
}

# 포트 설정
class PortManager:
    def __init__(self):
        self.config = {
            'API_SERVER': 8010,  # 메인 API 서버 (통합 완료)
            'WEB_SERVER': 3000,  # 웹 서버 (정적 파일)
            'BACKUP_PORTS': [8010, 8011, 8012, 8014, 8015, 8016, 8017],
            'RESERVED_PORTS': [8080, 9000],  # 시스템 예약 포트
            'DATABASE_PATH': 'daham_meal.db',  # 메인 데이터베이스 경로
            'BACKUP_DATABASE_PATH': 'backups/daham_meal.db'  # 백업 데이터베이스 경로
        }
        self.active_processes = {}  # 활성 프로세스 추적

    def get_config(self):
        """전체 설정 반환"""
        return self.config.copy()

    def get_api_port(self):
        """API 서버 포트 반환"""
        return int(os.environ.get('API_PORT', self.config['API_SERVER']))

    def get_web_port(self):
        """웹 서버 포트 반환"""
        return int(os.environ.get('WEB_PORT', self.config['WEB_SERVER']))

    def get_database_path(self):
        """메인 데이터베이스 경로 반환"""
        return os.environ.get('DATABASE_PATH', self.config['DATABASE_PATH'])

def get_api_port():
    """API 서버 포트를 환경변수 또는 기본값에서 가져오기"""
    return int(os.environ.get('API_PORT', DEFAULT_PORTS['API_SERVER']))

def get_web_port():
    """웹 서버 포트를 환경변수 또는 기본값에서 가져오기"""
    return int(os.environ.get('WEB_PORT', DEFAULT_PORTS['WEB_SERVER']))

def get_next_available_port():
    """사용 가능한 다음 포트 찾기"""
    import socket

    ports_to_try = [DEFAULT_PORTS['API_SERVER']] + DEFAULT_PORTS['BACKUP_PORTS']

    for port in ports_to_try:
        if is_port_available(port):
            return port

    # 모든 포트가 사용 중이면 랜덤 포트 사용
    return find_free_port()

def is_port_available(port):
    """포트가 사용 가능한지 확인"""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def find_free_port():
    """자동으로 빈 포트 찾기"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

def kill_processes_on_port(port):
    """특정 포트의 프로세스 종료"""
    import subprocess
    import sys

    try:
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                            print(f"포트 {port}의 프로세스 PID {pid} 종료됨")
                        except subprocess.CalledProcessError:
                            pass
        else:
            # Linux/Mac
            subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
    except Exception as e:
        print(f"포트 {port} 정리 중 오류: {e}")

def cleanup_all_ports():
    """모든 관련 포트 정리"""
    all_ports = [DEFAULT_PORTS['API_SERVER']] + DEFAULT_PORTS['BACKUP_PORTS']

    for port in all_ports:
        kill_processes_on_port(port)

if __name__ == "__main__":
    print("=== 다함 급식관리 시스템 포트 설정 ===")
    print(f"API 서버 포트: {get_api_port()}")
    print(f"웹 서버 포트: {get_web_port()}")
    print(f"사용 가능한 포트: {get_next_available_port()}")
    print(f"백업 포트들: {DEFAULT_PORTS['BACKUP_PORTS']}")

    print("\n=== 포트 상태 확인 ===")
    all_ports = [DEFAULT_PORTS['API_SERVER']] + DEFAULT_PORTS['BACKUP_PORTS']
    for port in all_ports:
        status = "사용 가능" if is_port_available(port) else "사용 중"
        print(f"포트 {port}: {status}")