#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다함 식자재 관리 시스템 - 통합 시작 스크립트
모든 서버를 동시에 시작하는 스크립트
"""

import subprocess
import time
import os
import sys
from threading import Thread
import signal

def start_server(script_name, port, description):
    """개별 서버 시작"""
    try:
        print(f"🚀 {description} 시작 중... (포트 {port})")
        proc = subprocess.Popen([
            sys.executable, script_name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 서버 시작 대기
        time.sleep(2)

        if proc.poll() is None:
            print(f"✅ {description} 성공적으로 시작됨 (PID: {proc.pid})")
            return proc
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ {description} 시작 실패:")
            if stderr:
                print(stderr)
            return None
    except Exception as e:
        print(f"❌ {description} 시작 오류: {e}")
        return None

def main():
    """메인 함수"""
    print("=" * 60)
    print("🍱 다함 식자재 관리 시스템 통합 서버 시작")
    print("=" * 60)

    # 실행할 서버들
    servers = [
        {
            'script': 'menu_recipes_api.py',
            'port': 8011,
            'description': '메뉴/레시피 API 서버'
        },
        {
            'script': '★test_samsung_api.py',
            'port': 8010,
            'description': '메인 API 서버'
        }
    ]

    processes = []

    try:
        # 각 서버 시작
        for server in servers:
            proc = start_server(
                server['script'],
                server['port'],
                server['description']
            )
            if proc:
                processes.append((proc, server))

        if not processes:
            print("❌ 모든 서버 시작 실패")
            return

        print("\n" + "=" * 60)
        print("🎉 서버 시작 완료!")
        print("=" * 60)

        # 접속 URL 안내
        print("\n📍 접속 URL:")
        print("• 관리자 대시보드: http://127.0.0.1:8010/admin_dashboard.html")
        print("• 메뉴/레시피 관리: http://127.0.0.1:8011/menu_recipe_management.html")
        print("• 메인 API 문서: http://127.0.0.1:8010/docs")
        print("• 메뉴 API 문서: http://127.0.0.1:8011/docs")

        print("\n⚡ 서버 상태:")
        for proc, server in processes:
            status = "🟢 실행중" if proc.poll() is None else "🔴 중지됨"
            print(f"• {server['description']}: {status} (포트 {server['port']})")

        print("\n💡 Ctrl+C를 눌러 모든 서버를 종료할 수 있습니다.")

        # 서버들이 실행되는 동안 대기
        while True:
            time.sleep(1)

            # 프로세스 상태 확인
            running_count = 0
            for proc, server in processes:
                if proc.poll() is None:
                    running_count += 1
                else:
                    print(f"⚠️ {server['description']} 예상치 못하게 종료됨")

            if running_count == 0:
                print("❌ 모든 서버가 종료되었습니다.")
                break

    except KeyboardInterrupt:
        print("\n\n🛑 서버 종료 중...")

        # 모든 프로세스 종료
        for proc, server in processes:
            try:
                if proc.poll() is None:
                    print(f"🔄 {server['description']} 종료 중...")
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"✅ {server['description']} 종료됨")
            except subprocess.TimeoutExpired:
                print(f"⚠️ {server['description']} 강제 종료")
                proc.kill()
            except Exception as e:
                print(f"❌ {server['description']} 종료 오류: {e}")

        print("👋 모든 서버가 안전하게 종료되었습니다.")

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

    finally:
        # 남은 프로세스 정리
        for proc, server in processes:
            try:
                if proc.poll() is None:
                    proc.kill()
            except:
                pass

if __name__ == "__main__":
    # 작업 디렉토리 확인
    if not os.path.exists("★test_samsung_api.py"):
        print("❌ 올바른 디렉토리에서 실행해주세요.")
        print("현재 디렉토리:", os.getcwd())
        sys.exit(1)

    main()