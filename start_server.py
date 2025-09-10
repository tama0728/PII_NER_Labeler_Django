#!/usr/bin/env python3
"""
Django 서버 시작 스크립트
기본 포트 8080으로 시작하며, 사용 중이면 자동으로 다음 포트를 찾습니다.
"""

import os
import sys
import socket
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def is_port_available(port):
    """포트가 사용 가능한지 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', int(port)))
        sock.close()
        return result != 0  # 연결 실패하면 포트가 사용 가능
    except:
        return False

def find_available_port(start_port):
    """사용 가능한 포트 찾기"""
    port = int(start_port)
    original_port = port
    
    while not is_port_available(port):
        print(f"⚠️  포트 {port}는 이미 사용 중입니다. 다음 포트를 확인합니다...")
        port += 1
        if port > original_port + 20:
            print(f"❌ 사용 가능한 포트를 찾을 수 없습니다 ({original_port}-{original_port + 20} 범위)")
            sys.exit(1)
    
    if port != original_port:
        print(f"✅ 포트 {port}를 사용합니다 (원래 요청: {original_port})")
    
    return str(port)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kdpii_labeler_django.settings")
    django.setup()
    
    # 포트 인수 확인
    if len(sys.argv) > 1:
        requested_port = sys.argv[1]
    else:
        # 환경 변수에서 기본 포트 가져오기
        from decouple import config
        requested_port = config("DEFAULT_PORT", default="8080")
    
    # 사용 가능한 포트 찾기
    port = find_available_port(requested_port)
    
    # runserver 명령 실행
    print(f"🚀 Django KDPII NER Labeler 서버 시작")
    print(f"📍 포트: {port}")
    print(f"📋 관리자 페이지: http://localhost:{port}/admin/")
    print(f"🏠 메인 대시보드: http://localhost:{port}/")
    print("⏹️  서버를 중지하려면 Ctrl+C를 누르세요")
    print("=" * 60)
    
    execute_from_command_line([
        "manage.py", 
        "runserver", 
        f"0.0.0.0:{port}"
    ])