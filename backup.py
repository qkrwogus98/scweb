#!/usr/bin/env python3
"""
CICLONE backup.sql PostgreSQL 마이그레이션 스크립트 (.env 지원)
.env 파일의 데이터베이스 설정을 자동으로 읽어서 마이그레이션을 수행합니다.
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql
import argparse
import logging
from datetime import datetime
from pathlib import Path

# python-dotenv 패키지가 있으면 사용, 없으면 수동 파싱
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnvConfigLoader:
    """환경변수 및 .env 파일 설정 로더"""
    
    def __init__(self, env_file='.env'):
        self.env_file = env_file
        self.config = {}
        
    def load_env_file_manual(self):
        """수동으로 .env 파일 파싱"""
        if not os.path.exists(self.env_file):
            logger.warning(f".env 파일을 찾을 수 없습니다: {self.env_file}")
            return
            
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 따옴표 제거
                    value = value.strip('\'"')
                    os.environ[key] = value
                    
        logger.info(f".env 파일 로드 완료: {self.env_file}")
    
    def load_config(self):
        """환경변수에서 데이터베이스 설정 로드"""
        if DOTENV_AVAILABLE:
            load_dotenv(self.env_file)
            logger.info("python-dotenv를 사용하여 .env 파일 로드")
        else:
            logger.info("python-dotenv가 없어서 수동으로 .env 파일 파싱")
            self.load_env_file_manual()
        
        # 데이터베이스 설정 추출
        self.config = {
            'host': os.getenv('DB_POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('DB_POSTGRES_PORT', 5432)),
            'database': os.getenv('DB_POSTGRES_NAME', 'appdb'),
            'user': os.getenv('DB_POSTGRES_USERNAME', 'postgres'),
            'password': os.getenv('DB_POSTGRES_PASSWORD', ''),
            'schema': os.getenv('DB_POSTGRES_SCHEMA', 'postgresql')
        }
        
        # 추가 설정들
        self.config.update({
            'sms_id': os.getenv('SMS_ID'),
            'sms_key': os.getenv('SMS_KEY'),
            'cesium_token': os.getenv('CESIUM_TOKEN')
        })
        
        logger.info(f"데이터베이스 설정 로드: {self.config['user']}@{self.config['host']}:{self.config['port']}/{self.config['database']}")
        return self.config

class CicloneMigrator:
    def __init__(self, source_file, config, target_db_name=None):
        self.source_file = source_file
        self.config = config
        self.target_db_name = target_db_name or config['database']
        self.connection = None
        
    def connect_to_target_db(self):
        """대상 데이터베이스에 연결"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.target_db_name,
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info(f"대상 데이터베이스에 연결 성공: {self.config['host']}:{self.config['port']}/{self.target_db_name}")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def check_backup_file(self):
        """백업 파일 존재 및 유효성 검사"""
        if not os.path.exists(self.source_file):
            logger.error(f"백업 파일을 찾을 수 없습니다: {self.source_file}")
            return False
            
        file_size = os.path.getsize(self.source_file)
        logger.info(f"백업 파일 크기: {file_size / 1024 / 1024:.2f} MB")
            
        # 파일 내용 간단 검사
        with open(self.source_file, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = f.read(1000)
            if 'PostgreSQL' in first_lines or 'CREATE TABLE' in first_lines:
                logger.info("PostgreSQL 백업 파일 형식 확인")
            else:
                logger.warning("PostgreSQL 백업 파일 형식이 명확하지 않습니다.")
            
        return True
    
    def create_target_database(self):
        """대상 데이터베이스가 존재하지 않으면 생성"""
        try:
            # postgres 데이터베이스에 연결하여 새 데이터베이스 생성
            temp_conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',  # 기본 데이터베이스에 연결
                user=self.config['user'],
                password=self.config['password']
            )
            temp_conn.autocommit = True
            cursor = temp_conn.cursor()
            
            # 데이터베이스 존재 확인
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                          (self.target_db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(
                    sql.Identifier(self.target_db_name)
                ))
                logger.info(f"새 데이터베이스 생성: {self.target_db_name}")
            else:
                logger.info(f"데이터베이스가 이미 존재합니다: {self.target_db_name}")
            
            cursor.close()
            temp_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 생성 실패: {e}")
            return False
    
    def backup_existing_data(self):
        """기존 데이터 백업"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{self.target_db_name}_{timestamp}.sql"
            
            cmd = [
                'pg_dump',
                '-h', self.config['host'],
                '-p', str(self.config['port']),
                '-U', self.config['user'],
                '-d', self.target_db_name,
                '-f', backup_filename,
                '--no-password',
                '--verbose'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config['password']
            
            logger.info(f"기존 데이터 백업 시작: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                backup_size = os.path.getsize(backup_filename) / 1024 / 1024
                logger.info(f"기존 데이터 백업 완료: {backup_filename} ({backup_size:.2f} MB)")
                return backup_filename
            else:
                logger.warning(f"기존 데이터 백업 실패: {result.stderr}")
                return None
                
        except Exception as e:
            logger.warning(f"기존 데이터 백업 중 오류: {e}")
            return None
    
    def get_ciclone_tables(self):
        """CICLONE 프로젝트의 테이블 목록 반환"""
        return [
            'device', 'logs', 'model', 'position', 
            'sensor', 'simulation', 'station', 'user'
        ]
    
    def clear_existing_tables(self):
        """기존 CICLONE 테이블들 정리"""
        try:
            cursor = self.connection.cursor()
            tables = self.get_ciclone_tables()
            
            # 외래키 제약 조건을 무시하고 테이블 삭제
            cursor.execute('SET session_replication_role = replica;')
            
            for table in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                logger.info(f"테이블 삭제: {table}")
            
            # 시퀀스들도 삭제
            sequences = ['user_user_id_seq']
            for seq in sequences:
                cursor.execute(f'DROP SEQUENCE IF EXISTS {seq} CASCADE;')
                logger.info(f"시퀀스 삭제: {seq}")
            
            cursor.execute('SET session_replication_role = DEFAULT;')
            self.connection.commit()
            cursor.close()
            logger.info("기존 CICLONE 테이블 정리 완료")
            return True
            
        except Exception as e:
            logger.error(f"테이블 정리 실패: {e}")
            self.connection.rollback()
            return False
    
    def restore_backup(self):
        """백업 파일을 대상 데이터베이스에 복원"""
        try:
            cmd = [
                'psql',
                '-h', self.config['host'],
                '-p', str(self.config['port']),
                '-U', self.config['user'],
                '-d', self.target_db_name,
                '-f', self.source_file,
                '--no-password',
                '--quiet'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config['password']
            
            logger.info("백업 파일 복원 시작...")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("백업 파일 복원 완료")
                return True
            else:
                logger.error(f"백업 복원 실패:")
                logger.error(result.stderr)
                # 일부 오류는 무시할 수 있는 경우가 있음
                if "already exists" in result.stderr or "duplicate key" in result.stderr:
                    logger.warning("일부 중복 오류가 있지만 계속 진행합니다.")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"백업 복원 중 오류: {e}")
            return False
    
    def verify_migration(self):
        """마이그레이션 검증"""
        try:
            cursor = self.connection.cursor()
            tables = self.get_ciclone_tables()
            total_records = 0
            
            logger.info("=== 마이그레이션 검증 결과 ===")
            
            for table in tables:
                # 테이블 존재 확인
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table,))
                
                if cursor.fetchone()[0] == 0:
                    logger.warning(f"❌ 테이블이 생성되지 않았습니다: {table}")
                else:
                    # 레코드 수 확인
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                    count = cursor.fetchone()[0]
                    total_records += count
                    logger.info(f"✅ 테이블 {table}: {count:,}개 레코드")
            
            logger.info(f"총 {total_records:,}개 레코드가 마이그레이션되었습니다.")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"마이그레이션 검증 실패: {e}")
            return False
    
    def migrate(self, create_db=True, backup_existing=True, clear_tables=False):
        """전체 마이그레이션 프로세스 실행"""
        logger.info("=" * 50)
        logger.info("CICLONE backup.sql 마이그레이션 시작")
        logger.info(f"소스 파일: {self.source_file}")
        logger.info(f"대상 DB: {self.config['host']}:{self.config['port']}/{self.target_db_name}")
        logger.info("=" * 50)
        
        # 1. 백업 파일 확인
        if not self.check_backup_file():
            return False
        
        # 2. 대상 데이터베이스 생성 (필요시)
        if create_db and not self.create_target_database():
            return False
        
        # 3. 대상 데이터베이스 연결
        if not self.connect_to_target_db():
            return False
        
        try:
            # 4. 기존 데이터 백업 (권장)
            backup_file = None
            if backup_existing:
                backup_file = self.backup_existing_data()
            
            # 5. 기존 테이블 정리 (옵션)
            if clear_tables:
                if not self.clear_existing_tables():
                    logger.warning("테이블 정리 실패, 계속 진행합니다.")
            
            # 6. 백업 파일 복원
            if not self.restore_backup():
                logger.error("마이그레이션 실패")
                return False
            
            # 7. 마이그레이션 검증
            self.verify_migration()
            
            logger.info("=" * 50)
            logger.info("✅ 마이그레이션 완료!")
            if backup_file:
                logger.info(f"📁 기존 데이터 백업: {backup_file}")
            logger.info("=" * 50)
            return True
            
        finally:
            if self.connection:
                self.connection.close()

def main():
    parser = argparse.ArgumentParser(description='CICLONE backup.sql 마이그레이션 도구 (.env 지원)')
    parser.add_argument('backup_file', nargs='?', default='backup.sql', 
                       help='백업 SQL 파일 경로 (기본값: backup.sql)')
    parser.add_argument('--env-file', default='.env', help='.env 파일 경로')
    parser.add_argument('--target-db', help='대상 데이터베이스 이름 (기본값: .env의 DB_POSTGRES_NAME)')
    parser.add_argument('--create-db', action='store_true', help='데이터베이스가 없으면 생성')
    parser.add_argument('--no-backup', action='store_true', help='기존 데이터 백업하지 않음')
    parser.add_argument('--clear-tables', action='store_true', help='기존 CICLONE 테이블 삭제')
    
    args = parser.parse_args()
    
    # 환경변수 설정 로드
    config_loader = EnvConfigLoader(args.env_file)
    config = config_loader.load_config()
    
    if not config['password']:
        logger.error("데이터베이스 비밀번호가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 마이그레이터 생성 및 실행
    migrator = CicloneMigrator(
        args.backup_file, 
        config, 
        args.target_db or config['database']
    )
    
    success = migrator.migrate(
        create_db=args.create_db,
        backup_existing=not args.no_backup,
        clear_tables=args.clear_tables
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()