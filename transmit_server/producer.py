import time
import os
import json
import pandas as pd
from kafka import KafkaProducer

# --- 사용자 설정 ---
# Kafka 서버 주소
BOOTSTRAP_SERVERS = 'localhost:9092'
# Kafka 토픽 이름
TOPIC_NAME = 'data_topic'
# 전송할 엑셀 파일 이름
EXCEL_FILE_NAME = 'truck_gps_0915-16.xlsx'  # 전송할 엑셀 파일 이름으로 변경하세요.
# 데이터 전송 간격 (초)
SEND_INTERVAL_SECONDS = 1
# --------------------

def create_kafka_producer(servers):
    """Kafka Producer 인스턴스를 생성하고 반환합니다."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka Producer가 성공적으로 생성되었습니다.")
        return producer
    except Exception as e:
        print(f"Kafka Producer 생성 중 오류 발생: {e}")
        return None

def send_data_from_excel(producer, topic, file_path):
    """엑셀 파일에서 데이터를 읽어 Kafka 토픽으로 전송합니다."""
    try:
        # 엑셀 파일 읽기
        data = pd.read_excel(file_path)
        print(f"'{file_path}' 파일에서 총 {len(data)}개의 행을 읽었습니다.")

        # 데이터프레임의 각 행을 순회하며 데이터 전송
        for index, row in data.iterrows():
            # NaN/NA 값을 None으로 변환
            row_dict = row.where(pd.notnull(row), None).to_dict()

            # Timestamp 객체를 ISO 형식의 문자열로 변환
            for key, value in row_dict.items():
                if isinstance(value, pd.Timestamp):
                    row_dict[key] = value.isoformat()

            # 데이터 전송
            producer.send(topic, row_dict)
            print(f"전송 ({index + 1}/{len(data)}): {row_dict}")

            # 다음 데이터 전송까지 대기
            # 만약 엑셀에 시간 간격 컬럼이 있다면 아래와 같이 활용할 수 있습니다.
            # sleep_time = row_dict.get('time_diff_seconds', SEND_INTERVAL_SECONDS)
            # time.sleep(sleep_time)
            time.sleep(SEND_INTERVAL_SECONDS)

        print("모든 데이터 전송을 완료했습니다.")

    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해주세요.")
    except Exception as e:
        print(f"데이터 전송 중 오류 발생: {e}")

if __name__ == '__main__':
    # 스크립트가 위치한 디렉토리 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(script_dir, EXCEL_FILE_NAME)

    # Kafka Producer 생성
    kafka_producer = create_kafka_producer(BOOTSTRAP_SERVERS)

    if kafka_producer:
        # 데이터 전송 함수 호출
        send_data_from_excel(kafka_producer, TOPIC_NAME, excel_file_path)
        # 프로듀서 리소스 정리
        kafka_producer.flush()
        kafka_producer.close()
        print("Kafka Producer 연결이 종료되었습니다.")