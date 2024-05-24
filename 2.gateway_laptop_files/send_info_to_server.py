import time
import paho.mqtt.client as mqtt
from firebase import firebase
from datetime import datetime
import pytz

import config   # 본인의 key 모은 모듈

# Firebase Realtime Database에 연결하는 Firebase 객체 생성
firebase_url = config.DATABASE_URL
firebase = firebase.FirebaseApplication(firebase_url, None)

# 한국 시간대 (Asia/Seoul)로 설정
korea_timezone = pytz.timezone("Asia/Seoul")

# MQTT 브로커 설정
broker_address = config.BROKER_ADDRESS
topic_current_zone = "agv0/currentZone"
topic_command = "agv0/command"
topic_orientation = "agv0/orientation"
topic_distance = "agv0/distance"
topic_analysis = "agv0/analysis"

# 전역 변수 초기화
current_zone = "None"
command = "None"
orientation = "None"
distance = "None"
analysis = "None"

# MQTT 메시지를 받을 때 호출되는 콜백 함수
def on_message(client, userdata, message):
    global current_zone, command, orientation, distance, analysis
    if message.topic == topic_current_zone:
        current_zone = message.payload.decode('utf-8')
    elif message.topic == topic_command:
        command = message.payload.decode('utf-8')
    elif message.topic == topic_orientation:
        orientation = message.payload.decode('utf-8')
    elif message.topic == topic_distance:
        distance = message.payload.decode('utf-8')
    elif message.topic == topic_analysis:
        analysis = message.payload.decode('utf-8')


# 샘플 데이터 쓰기 예제
def write_data():
    global current_zone, command, orientation, distance
    current_time = datetime.now(korea_timezone)
    time_key = current_time.strftime("%Y-%m-%d %H:%M:%S")
    commandData = {
        "command": command,
        "current_position": current_zone
    }
    sensingData = {
        "orientation": orientation,
        "ahead_obstacle_distance": distance
    }
    # "/commandTable" 경로에 데이터 쓰기
    result = firebase.put("/agv0/commandTable", time_key, commandData)
    print("Command data successfully written. Key:", result)
    # "/sensingTable" 경로에 데이터 쓰기
    result = firebase.put("/agv0/sensingTable", time_key, sensingData)
    print("Sensing data successfully written. Key:", result)

# MQTT 클라이언트 설정
client = mqtt.Client()
client.on_message = on_message
client.connect(broker_address)

# 토픽 구독
client.subscribe(topic_current_zone)
client.subscribe(topic_command)
client.subscribe(topic_orientation)
client.subscribe(topic_distance)
client.subscribe(topic_analysis)

# 메시지 루프 시작
client.loop_start()

# 계속 전송
if __name__ == '__main__':
    try:
        while(True):
            write_data()
            time.sleep(1)

    except KeyboardInterrupt:
        print("Script interrupted by user.")
    finally:
        client.loop_stop()
        client.disconnect()
