#!/usr/bin/env python3
"""
backup.sql 전체 경로 데이터 추출기 (수동 DB 설정 지원)
"""

import re
import json
import psycopg2
import os
from dotenv import load_dotenv

# .env 파일 로드 시도 (fieldy/.env 경로)
env_paths = ['fieldy/.env', '.env']
env_loaded = False

for env_path in env_paths:
    if os.path.exists(env_path):
        try:
            load_dotenv(env_path)
            print(f"✅ .env 파일 로드 성공: {env_path}")
            env_loaded = True
            break
        except Exception as e:
            print(f"⚠️  {env_path} 로드 실패: {e}")
            continue

if not env_loaded:
    print("⚠️  .env 파일을 찾을 수 없음, 수동 설정으로 진행")

def get_database_config():
    """데이터베이스 설정을 가져오거나 수동으로 입력받기"""
    
    # 환경변수에서 먼저 시도
    config = {
        'host': os.getenv('DB_POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('DB_POSTGRES_PORT', 5432)),
        'database': os.getenv('DB_POSTGRES_NAME', 'appdb'),
        'user': os.getenv('DB_POSTGRES_USERNAME', 'postgres'),
        'password': os.getenv('DB_POSTGRES_PASSWORD', '')
    }
    
    print(f"\n🔍 현재 데이터베이스 설정:")
    print(f"  호스트: {config['host']}")
    print(f"  포트: {config['port']}")
    print(f"  데이터베이스: {config['database']}")
    print(f"  사용자: {config['user']}")
    print(f"  비밀번호: {'✅ 설정됨' if config['password'] else '❌ 설정 안됨'}")
    
    # 비밀번호가 없거나 연결 테스트가 실패하면 수동 입력
    if not config['password']:
        print(f"\n🔐 데이터베이스 비밀번호를 입력해주세요:")
        config['password'] = input(f"PostgreSQL 비밀번호 (사용자: {config['user']}): ")
    
    # 연결 테스트
    try:
        test_conn = psycopg2.connect(**config)
        test_conn.close()
        print("✅ 데이터베이스 연결 테스트 성공")
        return config
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        
        # 수동으로 모든 설정 입력받기
        print(f"\n🔧 데이터베이스 설정을 수동으로 입력해주세요:")
        config['host'] = input(f"호스트 [{config['host']}]: ") or config['host']
        config['port'] = int(input(f"포트 [{config['port']}]: ") or config['port'])
        config['database'] = input(f"데이터베이스명 [{config['database']}]: ") or config['database']
        config['user'] = input(f"사용자명 [{config['user']}]: ") or config['user']
        config['password'] = input(f"비밀번호: ")
        
        # 다시 연결 테스트
        try:
            test_conn = psycopg2.connect(**config)
            test_conn.close()
            print("✅ 데이터베이스 연결 테스트 성공")
            return config
        except Exception as e2:
            print(f"❌ 데이터베이스 연결 여전히 실패: {e2}")
            print("PostgreSQL이 실행 중인지, 설정이 올바른지 확인해주세요.")
            return None

def extract_all_paths_from_backup_sql(backup_file_path="backup.sql"):
    """backup.sql에서 모든 경로 데이터 추출"""
    
    if not os.path.exists(backup_file_path):
        print(f"❌ backup.sql 파일을 찾을 수 없습니다: {backup_file_path}")
        return {}
    
    print(f"📄 backup.sql 파일 읽는 중...")
    
    try:
        with open(backup_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(backup_file_path, 'r', encoding='latin-1') as f:
            content = f.read()
    
    print(f"✅ 파일 크기: {len(content) / 1024 / 1024:.2f} MB")
    
    # project 테이블의 COPY 데이터 찾기
    copy_pattern = r"COPY public\.project.*?FROM stdin;(.*?)\\\."
    copy_match = re.search(copy_pattern, content, re.DOTALL)
    
    if not copy_match:
        print("❌ project 테이블 데이터를 찾을 수 없습니다.")
        return {}
    
    copy_data = copy_match.group(1).strip()
    lines = copy_data.split('\n')
    
    print(f"📊 {len(lines)}개의 프로젝트 레코드 발견")
    
    extracted_paths = {}
    
    for line_num, line in enumerate(lines, 1):
        if not line.strip() or line.strip() == '\\N':
            continue
            
        try:
            fields = line.split('\t')
            
            if len(fields) < 8:
                continue
                
            project_id = int(fields[0])
            project_name = fields[1]
            paths_data = fields[7] if len(fields) > 7 else '\\N'
            
            if paths_data == '\\N' or not paths_data.strip():
                continue
            
            if paths_data.startswith('//') or paths_data.startswith('http'):
                continue
            
            try:
                paths_data_cleaned = paths_data.replace('\\\\', '\\')
                
                try:
                    paths_data_cleaned = paths_data_cleaned.encode().decode('unicode_escape')
                except:
                    pass
                
                paths_json = json.loads(paths_data_cleaned)
                
                if not isinstance(paths_json, dict):
                    continue
                
                if paths_json and len(paths_json) > 0:
                    extracted_paths[project_id] = {
                        'name': project_name,
                        'paths': paths_json
                    }
                    
                    path_count = len(paths_json)
                    coord_count = sum(len(coords) for coords in paths_json.values() if isinstance(coords, list))
                    
                    print(f"✅ 프로젝트 {project_id}: {project_name} ({path_count}개 경로, {coord_count}개 좌표)")
                        
            except json.JSONDecodeError:
                continue
                
        except (ValueError, IndexError):
            continue
    
    print(f"\n🎯 총 {len(extracted_paths)}개 프로젝트의 경로 데이터 추출 완료")
    return extracted_paths

def restore_extracted_paths(extracted_paths, db_config):
    """추출된 경로 데이터를 데이터베이스에 복원"""
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"\n🔗 데이터베이스 연결 성공")
        print(f"🔧 {len(extracted_paths)}개 프로젝트의 경로 데이터 복원 중...")
        
        success_count = 0
        error_count = 0
        
        for project_id, data in extracted_paths.items():
            try:
                project_name = data['name']
                paths_data = data['paths']
                
                # 현재 프로젝트가 존재하는지 확인
                cursor.execute("SELECT id FROM project WHERE id = %s", (project_id,))
                exists = cursor.fetchone()
                
                if not exists:
                    print(f"⚠️  프로젝트 {project_id}가 데이터베이스에 없습니다. 건너뜁니다.")
                    continue
                
                # paths 데이터를 JSON 문자열로 변환
                paths_json = json.dumps(paths_data, ensure_ascii=False)
                
                # 프로젝트의 paths 필드 업데이트
                cursor.execute("""
                    UPDATE project 
                    SET paths = %s, "updatedAt" = NOW() 
                    WHERE id = %s
                """, (paths_json, project_id))
                
                conn.commit()
                success_count += 1
                
                print(f"✅ 프로젝트 {project_id} ({project_name}) 복원 완료")
                
            except Exception as e:
                print(f"❌ 프로젝트 {project_id} 복원 실패: {e}")
                error_count += 1
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 복원 결과:")
        print(f"  ✅ 성공: {success_count}개")
        print(f"  ❌ 실패: {error_count}개")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 실패: {e}")
        return False

def verify_all_paths(db_config):
    """모든 프로젝트의 경로 상태 확인"""
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"\n🔍 전체 프로젝트 경로 상태 확인:")
        
        cursor.execute("""
            SELECT id, name,
                   CASE 
                       WHEN paths IS NULL THEN 'NULL'
                       WHEN paths = '{}' OR paths = '' THEN 'EMPTY'  
                       ELSE 'HAS_PATHS'
                   END as path_status,
                   CASE 
                       WHEN paths IS NOT NULL AND paths != '{}' AND paths != '' 
                       THEN json_array_length(json_object_keys(paths::json)::json)
                       ELSE 0
                   END as path_count
            FROM project 
            ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        null_count = 0
        empty_count = 0  
        has_paths_count = 0
        
        print(f"\n📋 프로젝트별 경로 상태:")
        print(f"{'ID':<4} {'이름':<30} {'상태':<10} {'경로수':<6}")
        print("-" * 60)
        
        for project_id, name, status, path_count in results:
            display_name = name[:27] + "..." if len(name) > 30 else name
            
            status_icon = {
                'NULL': '❌',
                'EMPTY': '⚠️ ',
                'HAS_PATHS': '✅'
            }.get(status, '?')
            
            print(f"{project_id:<4} {display_name:<30} {status_icon}{status:<8} {path_count or 0:<6}")
            
            if status == 'NULL':
                null_count += 1
            elif status == 'EMPTY':
                empty_count += 1
            else:
                has_paths_count += 1
        
        print("-" * 60)
        print(f"📊 요약:")
        print(f"  ✅ 경로 있음: {has_paths_count}개")
        print(f"  ⚠️  빈 경로: {empty_count}개") 
        print(f"  ❌ 경로 없음: {null_count}개")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 확인 중 오류: {e}")

def main():
    """메인 실행 함수"""
    
    print("🚀 CICLONE 전체 경로 데이터 복구 시작 (수동 DB 설정 지원)")
    print("=" * 60)
    
    # 1. 데이터베이스 설정 확인/입력
    print("1️⃣ 데이터베이스 설정 확인...")
    db_config = get_database_config()
    
    if not db_config:
        print("❌ 데이터베이스 연결 설정에 실패했습니다.")
        return
    
    # 2. backup.sql에서 모든 경로 데이터 추출
    print("\n2️⃣ backup.sql에서 모든 경로 데이터 추출 중...")
    extracted_paths = extract_all_paths_from_backup_sql()
    
    if not extracted_paths:
        print("❌ 추출된 경로 데이터가 없습니다.")
        return
    
    # 3. 데이터베이스에 복원
    print(f"\n3️⃣ 데이터베이스에 경로 데이터 복원 중...")
    success = restore_extracted_paths(extracted_paths, db_config)
    
    if not success:
        print("❌ 경로 데이터 복원에 실패했습니다.")
        return
    
    # 4. 전체 상태 확인
    print(f"\n4️⃣ 전체 프로젝트 경로 상태 확인...")
    verify_all_paths(db_config)
    
    print(f"\n" + "=" * 60)
    print(f"🎉 전체 경로 데이터 복구 완료!")
    print(f"💡 이제 웹 인터페이스에서 모든 경로를 선택할 수 있습니다.")

if __name__ == "__main__":
    main()