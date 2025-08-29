import time
import os
import json
import pandas as pd
from kafka import KafkaProducer
from pyproj import Transformer

# --- 사용자 설정 ---
BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC_NAME = 'data_topic'
EXCEL_FILE_NAME = 'dozer.xlsx'  # 전송할 엑셀 파일
SEND_INTERVAL_SECONDS = 1

# 좌표 변환 관련 설정
X_COL = 'x'            # 엑셀의 x 컬럼명 (EPSG:3857)
Y_COL = 'y'            # 엑셀의 y 컬럼명 (EPSG:3857)
LON_COL = 'lon'        # 생성할 경도 컬럼명 (EPSG:4326)
LAT_COL = 'lat'        # 생성할 위도 컬럼명 (EPSG:4326)
DROP_ORIGINAL_XY = True  # 전송 전 x,y 컬럼 제거할지 여부

# EPSG:3857(Web Mercator) -> EPSG:4326(WGS84 lon/lat)
TRANSFORMER = Transformer.from_crs(3857, 4326, always_xy=True)
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

def convert_xy_to_lonlat(df, x_col=X_COL, y_col=Y_COL, lon_col=LON_COL, lat_col=LAT_COL):
    """DataFrame의 x,y(3857)를 lon,lat(4326)으로 변환해 컬럼을 추가합니다."""
    # 숫자로 강제 변환(문자/빈값 -> NaN)
    xs = pd.to_numeric(df[x_col], errors='coerce')
    ys = pd.to_numeric(df[y_col], errors='coerce')

    # pyproj 벡터 변환
    lons, lats = TRANSFORMER.transform(xs.values, ys.values)

    df[lon_col] = lons
    df[lat_col] = lats

    # 변환 실패(결측) 행 제거
    before = len(df)
    df = df.dropna(subset=[lon_col, lat_col]).copy()
    removed = before - len(df)
    if removed > 0:
        print(f"[좌표 변환] 결측 좌표 {removed}행 제거")

    # 필요 시 원래 x,y 제거
    if DROP_ORIGINAL_XY:
        df = df.drop(columns=[x_col, y_col], errors='ignore')

    return df

def send_data_from_excel(producer, topic, file_path):
    """엑셀 파일에서 데이터를 읽어 Kafka 토픽으로 전송합니다."""
    try:
        # 엑셀 읽기
        data = pd.read_excel(file_path)
        print(f"'{file_path}' 파일에서 총 {len(data)}개의 행을 읽었습니다.")

        # x,y -> lon,lat 변환
        if (X_COL not in data.columns) or (Y_COL not in data.columns):
            raise KeyError(f"엑셀에 '{X_COL}', '{Y_COL}' 컬럼이 없습니다. 현재 컬럼: {list(data.columns)}")

        data = convert_xy_to_lonlat(data, X_COL, Y_COL, LON_COL, LAT_COL)
        print(f"[좌표 변환] {len(data)}개 행에 경도/위도 추가 완료 (예시 1행): "
              f"{LON_COL}={data.iloc[0][LON_COL]:.6f}, {LAT_COL}={data.iloc[0][LAT_COL]:.6f}")

        # 각 행 전송
        for index, row in data.iterrows():
            row_dict = row.where(pd.notnull(row), None).to_dict()

            # Timestamp -> ISO8601 문자열
            for key, value in row_dict.items():
                if isinstance(value, pd.Timestamp):
                    row_dict[key] = value.isoformat()

            producer.send(topic, row_dict)
            print(f"전송 ({index + 1}/{len(data)}): {row_dict}")
            time.sleep(SEND_INTERVAL_SECONDS)

        print("모든 데이터 전송을 완료했습니다.")

    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 이름과 경로를 확인해주세요.")
    except KeyError as e:
        print(f"컬럼 오류: {e}")
    except Exception as e:
        print(f"데이터 전송 중 오류 발생: {e}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(script_dir, EXCEL_FILE_NAME)

    kafka_producer = create_kafka_producer(BOOTSTRAP_SERVERS)

    if kafka_producer:
        send_data_from_excel(kafka_producer, TOPIC_NAME, excel_file_path)
        kafka_producer.flush()
        kafka_producer.close()
        print("Kafka Producer 연결이 종료되었습니다.")
