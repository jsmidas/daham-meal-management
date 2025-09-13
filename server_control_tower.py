#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 서버 컨트롤 타워
모든 서버를 중앙에서 관리하고 제어하는 통합 시스템
"""

import os
import sys
import time
import json
import psutil
import threading
import subprocess
import requests
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime

class ServerControlTower:
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
            },
            'web_server': {
                'name': '웹 서버',
                'script': 'simple_server.py',
                'port': 9000,
                'status': 'stopped',
                'process': None,
                'last_check': None,
                'args': ['9000']
            }
        }
        self.control_port = 8080
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.flask_app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Flask 라우트 설정"""

        @self.flask_app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_HTML)

        @self.flask_app.route('/api/status')
        def get_status():
            """서버 상태 반환"""
            self.check_all_servers()
            return jsonify({
                'servers': self.servers,
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'timestamp': datetime.now().isoformat()
                }
            })

        @self.flask_app.route('/api/start/<server_name>')
        def start_server(server_name):
            """서버 시작"""
            if server_name in self.servers:
                success = self.start_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 시작 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/stop/<server_name>')
        def stop_server(server_name):
            """서버 중지"""
            if server_name in self.servers:
                success = self.stop_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 중지 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/restart/<server_name>')
        def restart_server(server_name):
            """서버 재시작"""
            if server_name in self.servers:
                self.stop_single_server(server_name)
                time.sleep(2)
                success = self.start_single_server(server_name)
                return jsonify({'success': success, 'message': f'{self.servers[server_name]["name"]} 재시작 {"성공" if success else "실패"}'})
            return jsonify({'success': False, 'message': '서버를 찾을 수 없습니다'})

        @self.flask_app.route('/api/cleanup')
        def cleanup_all():
            """모든 Python 프로세스 정리"""
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if proc.info['name'] == 'python.exe':
                        cmdline = proc.info['cmdline'] or []
                        if any('test_samsung_api.py' in cmd or 'simple_server.py' in cmd for cmd in cmdline):
                            if proc.pid != os.getpid():  # 현재 프로세스 제외
                                try:
                                    proc.terminate()
                                except:
                                    pass
                time.sleep(2)
                self.check_all_servers()
                return jsonify({'success': True, 'message': '프로세스 정리 완료'})
            except Exception as e:
                return jsonify({'success': False, 'message': f'정리 실패: {str(e)}'})

        @self.flask_app.route('/api/start_all')
        def start_all():
            """모든 서버 시작"""
            results = {}
            for server_name in self.servers:
                results[server_name] = self.start_single_server(server_name)
            return jsonify({'success': all(results.values()), 'results': results})

    def check_server_health(self, server_name):
        """서버 상태 확인"""
        server = self.servers[server_name]

        if server_name == 'api_server':
            try:
                response = requests.get(f"http://127.0.0.1:{server['port']}/api/admin/suppliers/stats", timeout=2)
                return response.status_code == 200
            except:
                return False
        elif server_name == 'web_server':
            try:
                response = requests.get(f"http://127.0.0.1:{server['port']}", timeout=2)
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
            max_wait = 15 if server_name == 'api_server' else 10
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

    def run_control_tower(self):
        """컨트롤 타워 실행"""
        print(f"서버 컨트롤 타워 시작: http://127.0.0.1:{self.control_port}")

        # 상태 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        monitor_thread.start()

        try:
            self.flask_app.run(host='127.0.0.1', port=self.control_port, debug=False)
        except KeyboardInterrupt:
            print("\n컨트롤 타워 종료 중...")
            for server_name in self.servers:
                self.stop_single_server(server_name)

    def monitor_servers(self):
        """서버 상태 모니터링"""
        while True:
            self.check_all_servers()
            time.sleep(10)  # 10초마다 상태 확인

# HTML 대시보드 템플릿
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>다함 식자재 관리 시스템 - 서버 컨트롤 타워</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .server-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .server-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
        .server-name { font-size: 18px; font-weight: bold; }
        .status-badge { padding: 5px 12px; border-radius: 20px; color: white; font-size: 12px; }
        .status-running { background: #27ae60; }
        .status-stopped { background: #e74c3c; }
        .status-unhealthy { background: #f39c12; }
        .status-error { background: #8e44ad; }
        .server-info { margin: 10px 0; }
        .server-actions { display: flex; gap: 10px; margin-top: 15px; }
        .btn { padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; color: white; }
        .btn-start { background: #27ae60; }
        .btn-stop { background: #e74c3c; }
        .btn-restart { background: #3498db; }
        .btn-cleanup { background: #8e44ad; }
        .btn:hover { opacity: 0.8; }
        .system-info { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .quick-actions { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .dashboard-link { display: inline-block; margin-top: 10px; padding: 10px 20px; background: #2980b9; color: white; text-decoration: none; border-radius: 5px; }
        .logs { background: white; border-radius: 10px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .log-entry { padding: 5px 0; border-bottom: 1px solid #eee; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎛️ 다함 식자재 관리 시스템 - 서버 컨트롤 타워</h1>
            <p>모든 서버를 중앙에서 관리하고 모니터링합니다</p>
        </div>

        <div class="quick-actions">
            <h3>빠른 작업</h3>
            <button class="btn btn-start" onclick="startAllServers()">🚀 모든 서버 시작</button>
            <button class="btn btn-cleanup" onclick="cleanupProcesses()">🧹 프로세스 정리</button>
            <a href="http://127.0.0.1:9000/admin_dashboard.html" target="_blank" class="dashboard-link">📊 관리자 대시보드 열기</a>
        </div>

        <div class="status-grid" id="serverGrid">
            <!-- 서버 카드들이 여기에 동적으로 생성됩니다 -->
        </div>

        <div class="system-info">
            <h3>시스템 정보</h3>
            <div id="systemInfo">로딩 중...</div>
        </div>

        <div class="logs">
            <h3>최근 로그</h3>
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
                const response = await fetch('/api/status');
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
                const response = await fetch(`/api/start/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 시작 오류: ${error.message}`);
            }
        }

        async function stopServer(name) {
            try {
                const response = await fetch(`/api/stop/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 중지 오류: ${error.message}`);
            }
        }

        async function restartServer(name) {
            try {
                const response = await fetch(`/api/restart/${name}`);
                const data = await response.json();
                addLog(data.message);
                updateStatus();
            } catch (error) {
                addLog(`서버 재시작 오류: ${error.message}`);
            }
        }

        async function startAllServers() {
            try {
                const response = await fetch('/api/start_all');
                const data = await response.json();
                addLog('모든 서버 시작 요청 완료');
                updateStatus();
            } catch (error) {
                addLog(`전체 시작 오류: ${error.message}`);
            }
        }

        async function cleanupProcesses() {
            try {
                const response = await fetch('/api/cleanup');
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
        addLog('서버 컨트롤 타워가 시작되었습니다');
    </script>
</body>
</html>
'''

def main():
    control_tower = ServerControlTower()
    control_tower.run_control_tower()

if __name__ == "__main__":
    main()