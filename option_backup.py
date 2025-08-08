#!/usr/bin/env python3
"""
backup.sql 완전 복원기 (paths + model 데이터)
backup.sql 파일에서 paths와 model 데이터를 모두 추출하여 복원합니다.
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
        return None

def extract_complete_project_data(backup_file_path="backup.sql"):
    """backup.sql에서 paths와 model 데이터를 모두 추출"""
    
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
    
    extracted_projects = {}
    
    for line_num, line in enumerate(lines, 1):
        if not line.strip() or line.strip() == '\\N':
            continue
            
        try:
            fields = line.split('\t')
            
            if len(fields) < 11:  # paths(7) + model(10) 필드까지 필요
                continue
                
            project_id = int(fields[0])
            project_name = fields[1]
            paths_data = fields[7] if len(fields) > 7 else '\\N'
            model_data = fields[10] if len(fields) > 10 else '\\N'
            
            print(f"\n🔍 프로젝트 {project_id} ({project_name}) 확인 중...")
            
            # paths와 model 데이터 처리
            project_info = {
                'name': project_name,
                'paths': None,
                'model': None
            }
            
            # paths 데이터 처리
            if paths_data != '\\N' and paths_data.strip() and not paths_data.startswith('//') and not paths_data.startswith('http'):
                try:
                    paths_cleaned = paths_data.replace('\\\\', '\\')
                    try:
                        paths_cleaned = paths_cleaned.encode().decode('unicode_escape')
                    except:
                        pass
                    
                    paths_json = json.loads(paths_cleaned)
                    
                    if isinstance(paths_json, dict) and len(paths_json) > 0:
                        project_info['paths'] = paths_json
                        path_count = len(paths_json)
                        coord_count = sum(len(coords) for coords in paths_json.values() if isinstance(coords, list))
                        print(f"   ✅ Paths: {path_count}개 경로, {coord_count}개 좌표")
                    else:
                        print(f"   ⚠️  Paths: 빈 딕셔너리")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Paths: JSON 파싱 실패")
            else:
                print(f"   ⚠️  Paths: 데이터 없음")
            
            # model 데이터 처리
            if model_data != '\\N' and model_data.strip():
                try:
                    model_cleaned = model_data.replace('\\\\', '\\')
                    try:
                        model_cleaned = model_cleaned.encode().decode('unicode_escape')
                    except:
                        pass
                    
                    model_json = json.loads(model_cleaned)
                    
                    if isinstance(model_json, dict):
                        project_info['model'] = model_json
                        
                        # model 데이터 분석
                        if 'model' in model_json:
                            equipment_count = len(model_json['model'])
                            
                            # 경로가 설정된 장비 찾기
                            path_configs = []
                            for eq_id, eq_data in model_json['model'].items():
                                if 'path' in eq_data:
                                    path_configs.append(f"{eq_data.get('desc', eq_id)}:{eq_data['path']}")
                            
                            print(f"   ✅ Model: {equipment_count}개 장비")
                            if path_configs:
                                print(f"     경로 설정: {', '.join(path_configs[:3])}{'...' if len(path_configs) > 3 else ''}")
                        else:
                            print(f"   ✅ Model: 설정됨")
                    else:
                        print(f"   ⚠️  Model: 딕셔너리가 아님")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Model: JSON 파싱 실패")
            else:
                print(f"   ⚠️  Model: 데이터 없음")
            
            # paths나 model 중 하나라도 있으면 저장
            if project_info['paths'] is not None or project_info['model'] is not None:
                extracted_projects[project_id] = project_info
                        
        except (ValueError, IndexError) as e:
            print(f"⚠️  라인 {line_num} 파싱 오류: {e}")
            continue
    
    print(f"\n🎯 총 {len(extracted_projects)}개 프로젝트의 데이터 추출 완료")
    return extracted_projects

def restore_complete_project_data(extracted_projects, db_config):
    """추출된 프로젝트 데이터를 데이터베이스에 복원"""
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"\n🔗 데이터베이스 연결 성공")
        print(f"🔧 {len(extracted_projects)}개 프로젝트의 데이터 복원 중...")
        
        success_count = 0
        error_count = 0
        paths_restored = 0
        models_restored = 0
        
        for project_id, data in extracted_projects.items():
            try:
                project_name = data['name']
                paths_data = data['paths']
                model_data = data['model']
                
                # 현재 프로젝트가 존재하는지 확인
                cursor.execute("SELECT id FROM project WHERE id = %s", (project_id,))
                exists = cursor.fetchone()
                
                if not exists:
                    print(f"⚠️  프로젝트 {project_id}가 데이터베이스에 없습니다. 건너뜁니다.")
                    continue
                
                # 업데이트할 필드들 준비
                update_fields = []
                update_values = []
                
                if paths_data is not None:
                    paths_json = json.dumps(paths_data, ensure_ascii=False)
                    update_fields.append('paths = %s')
                    update_values.append(paths_json)
                    paths_restored += 1
                
                if model_data is not None:
                    model_json = json.dumps(model_data, ensure_ascii=False)
                    update_fields.append('model = %s')
                    update_values.append(model_json)
                    models_restored += 1
                
                if update_fields:
                    update_fields.append('"updatedAt" = NOW()')
                    update_values.append(project_id)
                    
                    query = f"""
                        UPDATE project 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """
                    
                    cursor.execute(query, update_values)
                    conn.commit()
                    success_count += 1
                    
                    restored_items = []
                    if paths_data is not None:
                        restored_items.append("경로")
                    if model_data is not None:
                        restored_items.append("모델")
                    
                    print(f"✅ 프로젝트 {project_id} ({project_name}) {', '.join(restored_items)} 복원 완료")
                
            except Exception as e:
                print(f"❌ 프로젝트 {project_id} 복원 실패: {e}")
                error_count += 1
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 복원 결과:")
        print(f"  ✅ 성공: {success_count}개 프로젝트")
        print(f"  📍 경로 복원: {paths_restored}개")
        print(f"  🔧 모델 복원: {models_restored}개")
        print(f"  ❌ 실패: {error_count}개")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    
    print("🚀 CICLONE 완전 데이터 복구 시작 (paths + model)")
    print("=" * 60)
    
    # 1. 데이터베이스 설정 확인/입력
    print("1️⃣ 데이터베이스 설정 확인...")
    db_config = get_database_config()
    
    if not db_config:
        print("❌ 데이터베이스 연결 설정에 실패했습니다.")
        return
    
    # 2. backup.sql에서 완전한 프로젝트 데이터 추출
    print("\n2️⃣ backup.sql에서 완전한 프로젝트 데이터 추출 중...")
    extracted_projects = extract_complete_project_data()
    
    if not extracted_projects:
        print("❌ 추출된 프로젝트 데이터가 없습니다.")
        return
    
    # 3. 데이터베이스에 완전 복원
    print(f"\n3️⃣ 데이터베이스에 완전한 프로젝트 데이터 복원 중...")
    success = restore_complete_project_data(extracted_projects, db_config)
    
    if not success:
        print("❌ 프로젝트 데이터 복원에 실패했습니다.")
        return
    
    print(f"\n" + "=" * 60)
    print(f"🎉 완전한 프로젝트 데이터 복구 완료!")
    print(f"💡 이제 웹 인터페이스에서:")
    print(f"   📍 모든 경로를 선택할 수 있습니다")
    print(f"   🔧 장비별 경로 설정이 복원되었습니다")
    print(f"   🚀 기존 시뮬레이션 설정이 완전히 복원되었습니다")

if __name__ == "__main__":
    main()