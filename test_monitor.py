#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트용 모니터링 서버
"""

from flask import Flask, jsonify, render_template_string
import psutil
import os
import time

app = Flask(__name__)

@app.route('/')
def index():
    return "서버 모니터링 테스트 서버가 실행 중입니다"

@app.route('/api/monitor/full-status')
def get_full_server_status():
    """모든 실행 중인 Python 프로세스의 상태를 반환"""

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
                    server_type = "Unknown"
                    if 'test_samsung_api.py' in script_name:
                        server_type = "API Server"
                    elif 'simple_server.py' in script_name:
                        server_type = "Web Server"
                    elif 'unified_control_tower.py' in script_name:
                        server_type = "Control Tower"
                    elif 'server_control_tower.py' in script_name:
                        server_type = "Control Tower"
                    elif 'test_monitor.py' in script_name:
                        server_type = "Monitor Test"

                    # 프로세스 정보 수집
                    memory_info = proc.info.get('memory_info')
                    memory_mb = memory_info.rss / 1024 / 1024 if memory_info else 0

                    uptime = time.time() - proc.info.get('create_time', time.time())

                    running_processes.append({
                        'pid': proc.info['pid'],
                        'script': script_name,
                        'port': port,
                        'type': server_type,
                        'memory_mb': round(memory_mb, 1),
                        'cpu_percent': proc.info.get('cpu_percent', 0),
                        'uptime_seconds': int(uptime),
                        'cmdline': ' '.join(cmdline[:3])  # 처음 3개 인자만
                    })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'processes': []
        })

    # 포트 상태 체크
    port_status = {}
    for port in [8005, 8006, 8007, 8010, 8013, 8014, 8015, 8080, 8090, 9000]:
        port_status[str(port)] = {
            'used': False,
            'process': None
        }

        for proc in running_processes:
            if proc['port'] == str(port):
                port_status[str(port)]['used'] = True
                port_status[str(port)]['process'] = {
                    'pid': proc['pid'],
                    'type': proc['type'],
                    'script': proc['script']
                }
                break

    return jsonify({
        'success': True,
        'timestamp': time.time(),
        'processes': running_processes,
        'port_status': port_status,
        'total_processes': len(running_processes)
    })

@app.route('/monitor')
def monitor_page():
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>서버 프로세스 모니터링</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 10px; font-size: 12px; }
        h1 { font-size: 18px; margin: 5px 0; }
        h2 { font-size: 14px; margin: 10px 0 5px 0; }
        h3 { font-size: 12px; margin: 5px 0; }
        h4 { font-size: 11px; margin: 3px 0; }
        .process-card { border: 1px solid #ddd; padding: 8px; margin: 3px 0; border-radius: 3px; font-size: 10px; }
        .api-server { border-left: 3px solid #007bff; }
        .web-server { border-left: 3px solid #28a745; }
        .control-tower { border-left: 3px solid #dc3545; }
        .monitor-test { border-left: 3px solid #ffc107; }
        .port-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 3px; margin: 10px 0; }
        .port-card { padding: 5px; border-radius: 3px; text-align: center; font-size: 9px; }
        .port-used { background-color: #ffebee; border: 1px solid #f44336; }
        .port-free { background-color: #e8f5e8; border: 1px solid #4caf50; }
        .refresh-btn { padding: 5px 15px; background: #007bff; color: white; border: none; border-radius: 3px; margin: 5px 0; font-size: 11px; }
        .main-container { display: grid; grid-template-columns: 2fr 1fr; gap: 15px; }
        .processes-section { max-height: 70vh; overflow-y: auto; }
        .ports-section { }
        p { margin: 2px 0; line-height: 1.2; }
    </style>
</head>
<body>
    <h1>서버 프로세스 모니터링</h1>
    <button class="refresh-btn" onclick="loadStatus()">새로고침</button>

    <div class="main-container">
        <div class="processes-section">
            <h2>실행중인 프로세스</h2>
            <div id="processes"></div>
        </div>
        <div class="ports-section">
            <h2>포트 상태</h2>
            <div id="ports" class="port-grid"></div>
        </div>
    </div>

    <script>
        async function loadStatus() {
            try {
                const response = await fetch('/api/monitor/full-status');
                const data = await response.json();

                if (data.success) {
                    displayProcesses(data.processes);
                    displayPorts(data.port_status);
                } else {
                    document.getElementById('processes').innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                }
            } catch (error) {
                document.getElementById('processes').innerHTML = '<p style="color: red;">Failed to load: ' + error + '</p>';
            }
        }

        function displayProcesses(processes) {
            const container = document.getElementById('processes');
            container.innerHTML = '';

            processes.forEach(proc => {
                const div = document.createElement('div');
                div.className = 'process-card ' + getProcessClass(proc.type);
                div.innerHTML = `
                    <h3>${proc.type} - ${proc.script}</h3>
                    <p>PID: ${proc.pid} | Port: ${proc.port || 'N/A'} | Mem: ${proc.memory_mb}MB</p>
                    <p>Uptime: ${Math.floor(proc.uptime_seconds / 60)}m ${proc.uptime_seconds % 60}s</p>
                `;
                container.appendChild(div);
            });
        }

        function displayPorts(portStatus) {
            const container = document.getElementById('ports');
            container.innerHTML = '';

            Object.keys(portStatus).forEach(port => {
                const status = portStatus[port];
                const div = document.createElement('div');
                div.className = 'port-card ' + (status.used ? 'port-used' : 'port-free');
                div.innerHTML = `
                    <div><strong>${port}</strong></div>
                    <div>${status.used ? 'USED' : 'FREE'}</div>
                    ${status.used ? '<div style="font-size:8px;">' + status.process.type + '<br>PID:' + status.process.pid + '</div>' : ''}
                `;
                container.appendChild(div);
            });
        }

        function getProcessClass(type) {
            switch(type.toLowerCase()) {
                case 'api server': return 'api-server';
                case 'web server': return 'web-server';
                case 'control tower': return 'control-tower';
                case 'monitor test': return 'monitor-test';
                default: return '';
            }
        }

        // 페이지 로드시 자동 실행
        loadStatus();

        // 5초마다 자동 새로고침
        setInterval(loadStatus, 5000);
    </script>
</body>
</html>
    '''
    return html_content

if __name__ == '__main__':
    print("테스트 모니터링 서버 시작: http://127.0.0.1:8888")
    print("모니터링 페이지: http://127.0.0.1:8888/monitor")
    app.run(host='127.0.0.1', port=8888, debug=True)