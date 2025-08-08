#!/usr/bin/env python3
"""
Tileset 복구 스크립트
CDN tileset 경로를 로컬 서버 경로로 변경합니다.
"""

import re
import json
import psycopg2
import os
from dotenv import load_dotenv

# .env 파일 로드
env_paths = ['fieldy/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ .env 파일 로드 성공: {env_path}")
        break

def get_database_config():
    """데이터베이스 설정"""
    config = {
        'host': os.getenv('DB_POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('DB_POSTGRES_PORT', 5432)),
        'database': os.getenv('DB_POSTGRES_NAME', 'appdb'),
        'user': os.getenv('DB_POSTGRES_USERNAME', 'postgres'),
        'password': os.getenv('DB_POSTGRES_PASSWORD', '')
    }
    
    if not config['password']:
        config['password'] = input(f"PostgreSQL 비밀번호: ")
    
    return config

def create_tileset_directories():
    """tileset 디렉토리 생성"""
    tileset_dirs = [
        'fieldy/static/tilesets/sc/1',
        'fieldy/static/tilesets/sc/8-3'
    ]
    
    for dir_path in tileset_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 디렉토리 생성: {dir_path}")

def extract_cdn_tilesets(backup_file_path="backup.sql"):
    """backup.sql에서 CDN tileset 경로 추출"""
    
    if not os.path.exists(backup_file_path):
        print(f"❌ backup.sql 파일을 찾을 수 없습니다.")
        return {}
    
    try:
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(backup_file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # project 테이블에서 tileset 경로 찾기
    copy_pattern = r"COPY public\.project.*?FROM stdin;(.*?)\\\."
    copy_match = re.search(copy_pattern, content, re.DOTALL)
    
    if not copy_match:
        print("❌ project 테이블 데이터를 찾을 수 없습니다.")
        return {}
    
    copy_data = copy_match.group(1).strip()
    lines = copy_data.split('\n')
    
    cdn_tilesets = {}
    
    for line in lines:
        if not line.strip():
            continue
            
        try:
            fields = line.split('\t')
            if len(fields) < 7:
                continue
                
            project_id = int(fields[0])
            project_name = fields[1]
            tileset_field = fields[6]  # tileset 필드
            
            # CDN tileset 경로인 경우
            if tileset_field.startswith('//fieldy.cdn.ntruss.com'):
                cdn_tilesets[project_id] = {
                    'name': project_name,
                    'cdn_url': tileset_field,
                    'local_path': convert_cdn_to_local(tileset_field)
                }
                print(f"🔍 프로젝트 {project_id}: {project_name}")
                print(f"   CDN: {tileset_field}")
                print(f"   로컬: {cdn_tilesets[project_id]['local_path']}")
                
        except (ValueError, IndexError):
            continue
    
    print(f"\n🎯 총 {len(cdn_tilesets)}개 프로젝트의 CDN tileset 발견")
    return cdn_tilesets

def convert_cdn_to_local(cdn_url):
    """CDN URL을 로컬 경로로 변환"""
    # //fieldy.cdn.ntruss.com/sc/8-3/tileset.json -> /static/tilesets/sc/8-3/tileset.json
    if cdn_url.startswith('//fieldy.cdn.ntruss.com'):
        path_part = cdn_url.replace('//fieldy.cdn.ntruss.com', '')
        return f"/static/tilesets{path_part}"
    return cdn_url

def create_placeholder_tilesets():
    """플레이스홀더 tileset 파일들 생성"""
    
    # 기본 tileset.json 템플릿
    tileset_template = {
        "asset": {
            "version": "1.0"
        },
        "geometricError": 500,
        "root": {
            "boundingVolume": {
                "region": [
                    -1.3197004795898053,
                    0.6393117910552205,
                    -1.3196595204101946,
                    0.6393527502347795,
                    0,
                    500
                ]
            },
            "geometricError": 500,
            "refine": "REPLACE",
            "children": []
        }
    }
    
    tileset_paths = [
        'fieldy/static/tilesets/sc/1/tileset.json',
        'fieldy/static/tilesets/sc/8-3/tileset.json'
    ]
    
    for tileset_path in tileset_paths:
        os.makedirs(os.path.dirname(tileset_path), exist_ok=True)
        
        with open(tileset_path, 'w', encoding='utf-8') as f:
            json.dump(tileset_template, f, indent=2, ensure_ascii=False)
        
        print(f"📄 플레이스홀더 tileset 생성: {tileset_path}")

def update_tileset_paths(cdn_tilesets, db_config):
    """데이터베이스의 tileset 경로를 로컬 경로로 업데이트"""
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"\n🔧 {len(cdn_tilesets)}개 프로젝트의 tileset 경로 업데이트 중...")
        
        success_count = 0
        
        for project_id, data in cdn_tilesets.items():
            try:
                local_path = data['local_path']
                
                # tileset 경로 업데이트
                cursor.execute("""
                    UPDATE project 
                    SET tileset = %s, "updatedAt" = NOW() 
                    WHERE id = %s
                """, (local_path, project_id))
                
                conn.commit()
                success_count += 1
                
                print(f"✅ 프로젝트 {project_id} ({data['name']}) tileset 경로 업데이트 완료")
                
            except Exception as e:
                print(f"❌ 프로젝트 {project_id} 업데이트 실패: {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 업데이트 결과: {success_count}개 성공")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 실패: {e}")
        return False

def setup_nginx_config():
    """nginx 설정 예시 생성"""
    
    nginx_config = """
# nginx.conf 에 추가할 설정

server {
    listen 80;
    server_name localhost;
    
    # 기존 Flask 앱
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # tileset 정적 파일 서빙
    location /static/tilesets/ {
        alias /path/to/your/project/fieldy/static/tilesets/;
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
    }
}
"""
    
    with open('nginx_tileset_config.txt', 'w', encoding='utf-8') as f:
        f.write(nginx_config)
    
    print(f"📝 nginx 설정 파일 생성: nginx_tileset_config.txt")

def main():
    """메인 실행 함수"""
    
    print("🚀 CICLONE Tileset 복구 시작")
    print("=" * 60)
    
    # 1. 데이터베이스 설정
    print("1️⃣ 데이터베이스 설정...")
    db_config = get_database_config()
    
    # 2. tileset 디렉토리 생성
    print("\n2️⃣ tileset 디렉토리 생성...")
    create_tileset_directories()
    
    # 3. backup.sql에서 CDN tileset 추출
    print("\n3️⃣ backup.sql에서 CDN tileset 추출...")
    cdn_tilesets = extract_cdn_tilesets()
    
    if not cdn_tilesets:
        print("❌ CDN tileset을 찾을 수 없습니다.")
        return
    
    # 4. 플레이스홀더 tileset 파일 생성
    print("\n4️⃣ 플레이스홀더 tileset 파일 생성...")
    create_placeholder_tilesets()
    
    # 5. 데이터베이스 경로 업데이트
    print("\n5️⃣ 데이터베이스 tileset 경로 업데이트...")
    success = update_tileset_paths(cdn_tilesets, db_config)
    
    if not success:
        print("❌ tileset 경로 업데이트에 실패했습니다.")
        return
    
    # 6. nginx 설정 생성
    print("\n6️⃣ nginx 설정 파일 생성...")
    setup_nginx_config()
    
    print(f"\n" + "=" * 60)
    print(f"🎉 Tileset 복구 완료!")
    print(f"")
    print(f"📋 다음 단계:")
    print(f"1. 실제 3D tileset 파일을 다음 경로에 배치하세요:")
    for project_id, data in cdn_tilesets.items():
        local_dir = os.path.dirname(f"fieldy/static/tilesets{data['cdn_url'].replace('//fieldy.cdn.ntruss.com', '')}")
        print(f"   - {local_dir}/")
    print(f"")
    print(f"2. nginx 설정을 적용하세요:")
    print(f"   - nginx_tileset_config.txt 파일을 참고하여 nginx.conf 수정")
    print(f"   - nginx 재시작: sudo systemctl restart nginx")
    print(f"")
    print(f"3. 또는 Flask 개발 서버에서 정적 파일 서빙 확인")

if __name__ == "__main__":
    main()