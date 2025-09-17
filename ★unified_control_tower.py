#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 통합 컨트롤 타워
웹 서버 + 서버 관리 + 모니터링을 모두 포함하는 올인원 시스템
"""

import os
import sys
import time
import json
import psutil
import threading
import subprocess
import requests
from flask import Flask, render_template_string, jsonify, request, send_from_directory, send_file
from datetime import datetime

class UnifiedControlTower:
    def __init__(self):
        self.servers = {
            'api_server': {
                'name': 'API 서버',
                'script': 'test_samsung_api.py',
                'port': 8015,
                'status': 'stopped',
                'process': None,
                'last_check': None,
                'env': {'API_PORT': '8015'}
            }
        }
        self.control_port = 8080
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.flask_app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Flask 라우트 설정"""

        # 컨트롤 타워 대시보드
        @self.flask_app.route('/control')
        def control_dashboard():
            return render_template_string(CONTROL_DASHBOARD_HTML)

        # 정적 파일 서빙 (웹 서버 기능)
        @self.flask_app.route('/')
        def index():
            return self.serve_static_file('admin_dashboard.html')

        @self.flask_app.route('/<path:filename>')
        def serve_static_file(filename):
            """정적 파일 서빙"""
            try:
                # admin_dashboard.html은 루트에 있음
                if filename == 'admin_dashboard.html':
                    return send_file(os.path.join(self.base_dir, filename))

                # static 폴더의 파일들
                static_path = os.path.join(self.base_dir, 'static')
                if os.path.exists(os.path.join(static_path, filename)):
                    return send_from_directory(static_path, filename)

                # 루트 폴더의 파일들
                if os.path.exists(os.path.join(self.base_dir, filename)):
                    return send_file(os.path.join(self.base_dir, filename))

                # 파일을 찾을 수 없는 경우
                return f"파일을 찾을 수 없습니다: {filename}", 404
            except Exception as e:
                return f"파일 서빙 오류: {str(e)}", 500

        # API 엔드포인트들
        @self.flask_app.route('/api/control/status')
        def get_control_status():
            """컨트롤 타워 전용 상태 반환"""
            self.check_all_servers()
            return jsonify({
                'servers': self.servers,
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'timestamp': datetime.now().isoformat()
                },
                'tower_info': {
                    'web_server_integrated': True,
                    'port': self.control_port,
                    'functions': ['웹 서버', 'API 관리', '모니터링', '프로세스 제어']
                }
            })

        @self.flask_app.route('/api/control/start/<server_name>')
        def start_server(server_name):
            """서버 시작"""
            if server_name in self.servers:
                success = self.start_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 시작 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/control/stop/<server_name>')
        def stop_server(server_name):
            """서버 중지"""
            if server_name in self.servers:
                success = self.stop_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 중지 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/control/restart/<server_name>')
        def restart_server(server_name):
            """서버 재시작"""
            if server_name in self.servers:
                self.stop_single_server(server_name)
                time.sleep(2)
                success = self.start_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 재시작 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/control/cleanup')
        def cleanup_all():
            """모든 Python 프로세스 정리"""
            try:
                killed_count = 0
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if proc.info['name'] == 'python.exe':
                        cmdline = proc.info['cmdline'] or []
                        if any('test_samsung_api.py' in cmd for cmd in cmdline):
                            if proc.pid != os.getpid():  # 현재 프로세스 제외
                                try:
                                    proc.terminate()
                                    killed_count += 1
                                except:
                                    pass
                time.sleep(2)
                self.check_all_servers()
                return jsonify({'success': True, 'message': f'{killed_count}개의 프로세스를 정리했습니다'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'정리 실패: {str(e)}'})

        @self.flask_app.route('/api/control/start_all')
        def start_all():
            """모든 서버 시작"""
            results = {}
            for server_name in self.servers:
                results[server_name] = self.start_single_server(server_name)
            return jsonify({'success': all(results.values()), 'results': results})

        # 관리자 대시보드 바로가기
        @self.flask_app.route('/admin')
        def admin_redirect():
            return self.serve_static_file('admin_dashboard.html')

        # 시각적 서버 모니터링 대시보드
        @self.flask_app.route('/monitor')
        def server_monitor():
            return render_template_string(SERVER_MONITOR_HTML)

        # 실시간 서버 상태 API (모든 실행중인 프로세스 포함)
        @self.flask_app.route('/api/monitor/full-status')
        def get_full_server_status():
            """모든 실행 중인 서버와 프로세스의 상태를 반환"""
            self.check_all_servers()

            # 실행 중인 모든 Python 프로세스 찾기
            running_processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
                    if proc.info['name'] == 'python.exe':
                        cmdline = proc.info['cmdline'] or []
                        if len(cmdline) > 1:
                            script_name = cmdline[1].split('\\')[-1] if '\\' in cmdline[1] else cmdline[1]

                            # 포트 추출 시도
                            port = None
                            for arg in cmdline:
                                if 'API_PORT=' in str(arg):
                                    port = str(arg).split('=')[1]
                                elif str(arg).isdigit() and len(str(arg)) == 4:
                                    port = str(arg)

                            # 서버 타입 판단
                            server_type = 'Unknown'
                            if 'test_samsung_api.py' in script_name:
                                server_type = 'API Server'
                                if not port:
                                    port = '8015'  # 기본 포트
                            elif 'simple_server.py' in script_name:
                                server_type = 'Web Server'
                            elif 'unified_control_tower.py' in script_name:
                                server_type = 'Control Tower'
                                port = '8080'
                            elif 'server_control_tower.py' in script_name:
                                server_type = 'Old Control Tower'
                                port = '8080'

                            running_processes.append({
                                'pid': proc.info['pid'],
                                'script': script_name,
                                'type': server_type,
                                'port': port,
                                'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 1),
                                'cpu_percent': round(proc.info['cpu_percent'], 1),
                                'uptime_seconds': int(time.time() - proc.info['create_time']),
                                'cmdline': ' '.join(cmdline[:3])  # 명령어 요약
                            })
            except Exception as e:
                print(f"프로세스 스캔 오류: {e}")

            # 포트 사용 상황 확인
            port_usage = []
            common_ports = [8005, 8006, 8007, 8010, 8013, 8014, 8015, 8080, 8090, 9000]
            for port in common_ports:
                is_used = not self.check_port_available(port)
                port_usage.append({
                    'port': port,
                    'status': 'used' if is_used else 'free',
                    'process': next((p for p in running_processes if p['port'] == str(port)), None)
                })

            return jsonify({
                'servers': self.servers,
                'running_processes': running_processes,
                'port_usage': port_usage,
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'total_processes': len(running_processes),
                    'timestamp': datetime.now().isoformat()
                }
            })

        # 프로세스 종료 API
        @self.flask_app.route('/api/monitor/kill-process/<int:pid>')
        def kill_process(pid):
            """특정 PID의 프로세스 종료"""
            try:
                if pid == os.getpid():
                    return jsonify({'success': False, 'message': '자기 자신은 종료할 수 없습니다'})

                proc = psutil.Process(pid)
                proc.terminate()
                return jsonify({'success': True, 'message': f'프로세스 {pid} 종료됨'})
            except psutil.NoSuchProcess:
                return jsonify({'success': False, 'message': '프로세스를 찾을 수 없습니다'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'종료 실패: {str(e)}'})

    def check_server_health(self, server_name):
        """서버 상태 확인"""
        server = self.servers[server_name]

        if server_name == 'api_server':
            try:
                response = requests.get(f"http://127.0.0.1:{server['port']}/api/admin/suppliers/stats", timeout=2)
                return response.status_code == 200
            except:
                return False
        return False

    def check_all_servers(self):
        """모든 서버 상태 확인"""
        for server_name, server in self.servers.items():
            # 프로세스 상태 확인
            if server['process']:
                try:
                    if server['process'].poll() is None:  # 프로세스가 살아있음
                        # 헬스체크
                        if self.check_server_health(server_name):
                            server['status'] = 'running'
                        else:
                            server['status'] = 'unhealthy'
                    else:
                        server['status'] = 'stopped'
                        server['process'] = None
                except:
                    server['status'] = 'error'
                    server['process'] = None
            else:
                server['status'] = 'stopped'

            server['last_check'] = datetime.now().isoformat()

    def start_single_server(self, server_name):
        """단일 서버 시작"""
        server = self.servers[server_name]

        if server['status'] == 'running':
            return True

        try:
            env = os.environ.copy()
            if 'env' in server:
                env.update(server['env'])

            cmd = [sys.executable, server['script']]
            if 'args' in server:
                cmd.extend(server['args'])

            server['process'] = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 서버 시작 대기
            max_wait = 15
            for i in range(max_wait):
                time.sleep(1)
                if self.check_server_health(server_name):
                    server['status'] = 'running'
                    return True

            server['status'] = 'failed'
            return False

        except Exception as e:
            server['status'] = 'error'
            print(f"서버 시작 오류 ({server_name}): {e}")
            return False

    def stop_single_server(self, server_name):
        """단일 서버 중지"""
        server = self.servers[server_name]

        if server['process']:
            try:
                server['process'].terminate()
                server['process'].wait(timeout=5)
            except subprocess.TimeoutExpired:
                server['process'].kill()
            except:
                pass

            server['process'] = None

        server['status'] = 'stopped'
        return True

    def run_unified_tower(self):
        """통합 컨트롤 타워 실행"""
        print(f"통합 컨트롤 타워 시작:")
        print(f"  관리자 대시보드: http://127.0.0.1:{self.control_port}")
        print(f"  컨트롤 패널: http://127.0.0.1:{self.control_port}/control")
        print(f"  웹 서버 + 서버 관리 통합 완료!")

        # 상태 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        monitor_thread.start()

        try:
            self.flask_app.run(host='127.0.0.1', port=self.control_port, debug=False)
        except KeyboardInterrupt:
            print("\n통합 컨트롤 타워 종료 중...")
            for server_name in self.servers:
                self.stop_single_server(server_name)

    def monitor_servers(self):
        """서버 상태 모니터링"""
        while True:
            self.check_all_servers()
            time.sleep(10)  # 10초마다 상태 확인

# 서버 모니터링 HTML 템플릿
SERVER_MONITOR_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>서버 모니터링 대시보드 - 다함 식자재 관리 시스템</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e27; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header p { font-size: 18px; opacity: 0.9; }

        .stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 12px; text-align: center; }
        .stat-value { font-size: 36px; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 14px; opacity: 0.8; }

        .section { background: #16213e; border-radius: 15px; padding: 25px; margin-bottom: 25px; border: 1px solid #0f3460; }
        .section h2 { color: #64b5f6; margin-bottom: 20px; font-size: 24px; }

        .processes-grid { display: grid; gap: 15px; }
        .process-card { background: #1a2332; border-radius: 10px; padding: 20px; border-left: 4px solid #4caf50; position: relative; }
        .process-card.api-server { border-left-color: #2196f3; }
        .process-card.web-server { border-left-color: #ff9800; }
        .process-card.control-tower { border-left-color: #9c27b0; }
        .process-card.unknown { border-left-color: #607d8b; }

        .process-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
        .process-title { font-size: 18px; font-weight: bold; }
        .process-type { background: rgba(100, 181, 246, 0.2); color: #64b5f6; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .process-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 15px; }
        .info-item { display: flex; flex-direction: column; }
        .info-label { font-size: 12px; opacity: 0.7; margin-bottom: 2px; }
        .info-value { font-size: 14px; font-weight: bold; }
        .kill-btn { background: #f44336; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; }
        .kill-btn:hover { background: #d32f2f; }

        .ports-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; }
        .port-card { background: #1a2332; padding: 15px; border-radius: 10px; text-align: center; }
        .port-card.used { border: 2px solid #f44336; }
        .port-card.free { border: 2px solid #4caf50; }
        .port-number { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
        .port-status { font-size: 12px; padding: 4px 8px; border-radius: 12px; }
        .port-status.used { background: #f44336; }
        .port-status.free { background: #4caf50; }
        .port-process { font-size: 11px; margin-top: 5px; opacity: 0.8; }

        .nav-buttons { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; }
        .nav-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; text-decoration: none; }
        .nav-btn:hover { opacity: 0.9; }

        .loading { text-align: center; padding: 40px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .uptime-badge { background: rgba(76, 175, 80, 0.2); color: #4caf50; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
        .memory-usage { color: #ff9800; }
        .cpu-usage { color: #2196f3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ 서버 모니터링 대시보드</h1>
            <p>실시간 프로세스 및 포트 상태 모니터링</p>
        </div>

        <div class="nav-buttons">
            <a href="/control" class="nav-btn">🎛️ 컨트롤 패널</a>
            <a href="/" class="nav-btn">📊 관리자 대시보드</a>
            <button class="nav-btn" onclick="refreshData()">🔄 새로고침</button>
        </div>

        <div class="stats-row" id="statsRow">
            <div class="stat-card">
                <div class="stat-value" id="totalProcesses">-</div>
                <div class="stat-label">실행중인 프로세스</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="usedPorts">-</div>
                <div class="stat-label">사용중인 포트</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="cpuUsage">-</div>
                <div class="stat-label">CPU 사용률</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="memoryUsage">-</div>
                <div class="stat-label">메모리 사용률</div>
            </div>
        </div>

        <div class="section">
            <h2>🚀 실행 중인 서버 프로세스</h2>
            <div id="processesContainer" class="loading">
                <div class="spinner"></div>
                <p>프로세스 정보를 불러오는 중...</p>
            </div>
        </div>

        <div class="section">
            <h2>🔌 포트 사용 현황</h2>
            <div id="portsContainer" class="loading">
                <div class="spinner"></div>
                <p>포트 정보를 불러오는 중...</p>
            </div>
        </div>
    </div>

    <script>
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;

            if (hours > 0) {
                return `${hours}시간 ${minutes}분`;
            } else if (minutes > 0) {
                return `${minutes}분 ${secs}초`;
            } else {
                return `${secs}초`;
            }
        }

        function getProcessTypeClass(type) {
            const typeMap = {
                'API Server': 'api-server',
                'Web Server': 'web-server',
                'Control Tower': 'control-tower',
                'Old Control Tower': 'control-tower',
                'Unknown': 'unknown'
            };
            return typeMap[type] || 'unknown';
        }

        function getProcessIcon(type) {
            const iconMap = {
                'API Server': '🔗',
                'Web Server': '🌐',
                'Control Tower': '🎛️',
                'Old Control Tower': '🎛️',
                'Unknown': '❓'
            };
            return iconMap[type] || '❓';
        }

        async function killProcess(pid) {
            if (!confirm(`프로세스 ${pid}를 종료하시겠습니까?`)) return;

            try {
                const response = await fetch(`/api/monitor/kill-process/${pid}`);
                const data = await response.json();

                if (data.success) {
                    alert(data.message);
                    refreshData();
                } else {
                    alert('오류: ' + data.message);
                }
            } catch (error) {
                alert('프로세스 종료 실패: ' + error.message);
            }
        }

        async function refreshData() {
            try {
                const response = await fetch('/api/monitor/full-status');
                const data = await response.json();

                // 통계 업데이트
                document.getElementById('totalProcesses').textContent = data.running_processes.length;
                document.getElementById('usedPorts').textContent = data.port_usage.filter(p => p.status === 'used').length;
                document.getElementById('cpuUsage').textContent = data.system.cpu_percent.toFixed(1) + '%';
                document.getElementById('memoryUsage').textContent = data.system.memory_percent.toFixed(1) + '%';

                // 프로세스 목록 업데이트
                const processesContainer = document.getElementById('processesContainer');
                if (data.running_processes.length === 0) {
                    processesContainer.innerHTML = '<p style="text-align: center; opacity: 0.7;">실행 중인 Python 프로세스가 없습니다.</p>';
                } else {
                    processesContainer.innerHTML = '<div class="processes-grid">' +
                        data.running_processes.map(proc => `
                            <div class="process-card ${getProcessTypeClass(proc.type)}">
                                <div class="process-header">
                                    <div class="process-title">${getProcessIcon(proc.type)} ${proc.script}</div>
                                    <div class="process-type">${proc.type}</div>
                                </div>
                                <div class="process-info">
                                    <div class="info-item">
                                        <div class="info-label">PID</div>
                                        <div class="info-value">${proc.pid}</div>
                                    </div>
                                    <div class="info-item">
                                        <div class="info-label">포트</div>
                                        <div class="info-value">${proc.port || '미지정'}</div>
                                    </div>
                                    <div class="info-item">
                                        <div class="info-label">메모리</div>
                                        <div class="info-value memory-usage">${proc.memory_mb} MB</div>
                                    </div>
                                    <div class="info-item">
                                        <div class="info-label">CPU</div>
                                        <div class="info-value cpu-usage">${proc.cpu_percent}%</div>
                                    </div>
                                    <div class="info-item">
                                        <div class="info-label">실행시간</div>
                                        <div class="info-value"><span class="uptime-badge">${formatUptime(proc.uptime_seconds)}</span></div>
                                    </div>
                                    <div class="info-item">
                                        <div class="info-label">액션</div>
                                        <div class="info-value">
                                            <button class="kill-btn" onclick="killProcess(${proc.pid})">종료</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('') + '</div>';
                }

                // 포트 사용 현황 업데이트
                const portsContainer = document.getElementById('portsContainer');
                portsContainer.innerHTML = '<div class="ports-section">' +
                    data.port_usage.map(port => `
                        <div class="port-card ${port.status}">
                            <div class="port-number">${port.port}</div>
                            <div class="port-status ${port.status}">${port.status === 'used' ? '사용중' : '사용가능'}</div>
                            ${port.process ? `<div class="port-process">${getProcessIcon(port.process.type)} ${port.process.script}</div>` : ''}
                        </div>
                    `).join('') + '</div>';

            } catch (error) {
                console.error('데이터 로드 오류:', error);
                document.getElementById('processesContainer').innerHTML = '<p style="text-align: center; color: #f44336;">데이터 로드 실패: ' + error.message + '</p>';
            }
        }

        // 페이지 로드 시 데이터 로드
        document.addEventListener('DOMContentLoaded', refreshData);

        // 5초마다 자동 새로고침
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
'''

# 컨트롤 대시보드 HTML 템플릿
CONTROL_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>다함 식자재 관리 시스템 - 통합 컨트롤 타워</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a2e; color: #eee; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { font-size: 16px; opacity: 0.9; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .feature-card { background: #16213e; border-radius: 15px; padding: 25px; text-align: center; border: 1px solid #0f3460; }
        .feature-icon { font-size: 48px; margin-bottom: 15px; }
        .feature-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #64b5f6; }
        .quick-actions { background: #16213e; border-radius: 15px; padding: 25px; margin-bottom: 30px; border: 1px solid #0f3460; }
        .quick-actions h3 { margin-bottom: 20px; color: #64b5f6; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; color: white; font-weight: bold; margin: 5px; transition: all 0.3s; }
        .btn-start { background: linear-gradient(135deg, #4caf50, #45a049); }
        .btn-stop { background: linear-gradient(135deg, #f44336, #d32f2f); }
        .btn-restart { background: linear-gradient(135deg, #2196f3, #1976d2); }
        .btn-cleanup { background: linear-gradient(135deg, #9c27b0, #7b1fa2); }
        .btn-dashboard { background: linear-gradient(135deg, #ff9800, #f57c00); }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .server-card { background: #16213e; border-radius: 15px; padding: 25px; border: 1px solid #0f3460; }
        .server-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .server-name { font-size: 20px; font-weight: bold; color: #64b5f6; }
        .status-badge { padding: 8px 16px; border-radius: 25px; color: white; font-size: 14px; font-weight: bold; }
        .status-running { background: linear-gradient(135deg, #4caf50, #45a049); }
        .status-stopped { background: linear-gradient(135deg, #f44336, #d32f2f); }
        .status-unhealthy { background: linear-gradient(135deg, #ff9800, #f57c00); }
        .status-error { background: linear-gradient(135deg, #9c27b0, #7b1fa2); }
        .server-info { margin: 15px 0; }
        .server-info div { margin: 5px 0; color: #b0bec5; }
        .server-actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
        .system-info { background: #16213e; border-radius: 15px; padding: 25px; border: 1px solid #0f3460; }
        .system-info h3 { color: #64b5f6; margin-bottom: 15px; }
        .logs { background: #16213e; border-radius: 15px; padding: 25px; margin-top: 20px; border: 1px solid #0f3460; max-height: 300px; overflow-y: auto; }
        .logs h3 { color: #64b5f6; margin-bottom: 15px; }
        .log-entry { padding: 8px 0; border-bottom: 1px solid #0f3460; font-size: 14px; color: #b0bec5; }
        .integration-notice { background: linear-gradient(135deg, #1e3c72, #2a5298); border-radius: 15px; padding: 20px; margin-bottom: 30px; text-align: center; }
        .integration-notice h3 { color: #64b5f6; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎛️ 다함 식자재 관리 시스템 - 통합 컨트롤 타워</h1>
            <p>웹 서버 + 서버 관리 + 모니터링을 모두 포함하는 올인원 시스템</p>
        </div>

        <div class="integration-notice">
            <h3>🎉 통합 완료!</h3>
            <p>이제 웹 서버 기능이 컨트롤 타워에 완전히 통합되었습니다. 별도의 웹 서버가 필요하지 않습니다!</p>
        </div>

        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">🌐</div>
                <div class="feature-title">통합 웹 서버</div>
                <p>관리자 대시보드와 정적 파일을 직접 서빙</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔧</div>
                <div class="feature-title">서버 관리</div>
                <p>API 서버의 시작/중지/재시작을 원클릭으로 제어</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">실시간 모니터링</div>
                <p>서버 상태와 시스템 리소스를 실시간 추적</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧹</div>
                <div class="feature-title">프로세스 관리</div>
                <p>중복 프로세스를 자동으로 정리하고 최적화</p>
            </div>
        </div>

        <div class="quick-actions">
            <h3>빠른 작업</h3>
            <button class="btn btn-start" onclick="startAllServers()">🚀 API 서버 시작</button>
            <button class="btn btn-cleanup" onclick="cleanupProcesses()">🧹 프로세스 정리</button>
            <a href="/" class="btn btn-dashboard">📊 관리자 대시보드 열기</a>
            <a href="/admin" class="btn btn-dashboard">🎛️ 관리자 페이지</a>
        </div>

        <div class="status-grid" id="serverGrid">
            <!-- 서버 카드들이 여기에 동적으로 생성됩니다 -->
        </div>

        <div class="system-info">
            <h3>시스템 정보</h3>
            <div id="systemInfo">로딩 중...</div>
        </div>

        <div class="logs">
            <h3>실시간 로그</h3>
            <div id="logContainer"></div>
        </div>
    </div>

    <script>
        let logs = [];

        function addLog(message) {
            const timestamp = new Date().toLocaleTimeString();
            logs.unshift(`[${timestamp}] ${message}`);
            if (logs.length > 50) logs.pop();
            updateLogs();
        }

        function updateLogs() {
            const container = document.getElementById('logContainer');
            container.innerHTML = logs.map(log => `<div class="log-entry">${log}</div>`).join('');
        }

        async function updateStatus() {
            try {
                const response = await fetch('/api/control/status');
                const data = await response.json();

                // 서버 카드 업데이트
                const grid = document.getElementById('serverGrid');
                grid.innerHTML = Object.entries(data.servers).map(([name, server]) => `
                    <div class="server-card">
                        <div class="server-header">
                            <div class="server-name">${server.name}</div>
                            <div class="status-badge status-${server.status}">${getStatusText(server.status)}</div>
                        </div>
                        <div class="server-info">
                            <div>📍 포트: ${server.port}</div>
                            <div>📝 스크립트: ${server.script}</div>
                            <div>🕐 마지막 확인: ${new Date(server.last_check).toLocaleTimeString()}</div>
                        </div>
                        <div class="server-actions">
                            <button class="btn btn-start" onclick="startServer('${name}')">시작</button>
                            <button class="btn btn-stop" onclick="stopServer('${name}')">중지</button>
                            <button class="btn btn-restart" onclick="restartServer('${name}')">재시작</button>
                        </div>
                    </div>
                `).join('');

                // 시스템 정보 업데이트
                document.getElementById('systemInfo').innerHTML = `
                    <div>🖥️ CPU 사용률: ${data.system.cpu_percent.toFixed(1)}%</div>
                    <div>💾 메모리 사용률: ${data.system.memory_percent.toFixed(1)}%</div>
                    <div>🎛️ 통합 포트: ${data.tower_info.port}</div>
                    <div>🌐 통합 기능: ${data.tower_info.functions.join(', ')}</div>
                    <div>🕐 마지막 업데이트: ${new Date(data.system.timestamp).toLocaleTimeString()}</div>
                `;
            } catch (error) {
                addLog(`상태 업데이트 오류: ${error.message}`);
            }
        }

        function getStatusText(status) {
            const texts = {
                'running': '🟢 실행중',
                'stopped': '🔴 중지됨',
                'unhealthy': '🟡 불안정',
                'error': '🟣 오류',
                'failed': '❌ 실패'
            };
            return texts[status] || status;
        }

        async function startServer(name) {
            try {
                const response = await fetch(`/api/control/start/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 시작 오류: ${error.message}`);
            }
        }

        async function stopServer(name) {
            try {
                const response = await fetch(`/api/control/stop/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 중지 오류: ${error.message}`);
            }
        }

        async function restartServer(name) {
            try {
                const response = await fetch(`/api/control/restart/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 재시작 오류: ${error.message}`);
            }
        }

        async function startAllServers() {
            try {
                const response = await fetch('/api/control/start_all');
                const data = await response.json();
                addLog('API 서버 시작 요청 완료');
                updateStatus();
            } catch (error) {
                addLog(`서버 시작 오류: ${error.message}`);
            }
        }

        async function cleanupProcesses() {
            try {
                const response = await fetch('/api/control/cleanup');
                const data = await response.json();
                addLog(data.message);
                setTimeout(updateStatus, 2000);
            } catch (error) {
                addLog(`프로세스 정리 오류: ${error.message}`);
            }
        }

        // 초기 로드 및 주기적 업데이트
        updateStatus();
        setInterval(updateStatus, 5000); // 5초마다 업데이트
        addLog('통합 컨트롤 타워가 시작되었습니다 - 웹 서버 기능 포함');
    </script>
</body>
</html>
'''

def main():
    tower = UnifiedControlTower()
    tower.run_unified_tower()

if __name__ == "__main__":
    main()