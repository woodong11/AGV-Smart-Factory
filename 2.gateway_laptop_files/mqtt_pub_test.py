import paho.mqtt.client as mqtt
import time

import config   # 본인의 key 모은 모듈

# MQTT 브로커 주소 및 주제 설정
broker_address = config.BROKER_ADDRESS
topic_current_zone = "agv0/currentZone"
topic_target_zone = "agv0/targetZone"
topic_command = "agv0/command"
topic_mode = "agv0/mode"
topic_orientation = "agv0/orientation"
topic_distance = "agv0/distance"
topic_analysis = "agv0/analysis"

# MQTT 클라이언트 설정
client = mqtt.Client()

# 브로커 연결
client.connect(broker_address)

# 1초마다 메시지 전송
try:
    while True:
        # "agv0/currentZone" 주제로 "red" 메시지 전송
        client.publish(topic_current_zone, "red")
        
        # "agv0/command" 주제로 "goToYellow" 메시지 전송
        client.publish(topic_command, "goToYellow")
        
        # "agv0/orientation" 주제로 "north" 메시지 전송
        client.publish(topic_orientation, "north")
        
        # "agv0/distance" 주제로 "4cm" 메시지 전송
        client.publish(topic_distance, "100")

        # "agv0/mode" 주제로 "voiceMode" 메시지 전송
        client.publish(topic_mode, "voiceMode")
        
        # "agv0/analysis" 주제로 "안녕하세요 전 AI고 로그 분석합니다" 메시지 전송
        client.publish(topic_analysis, "안녕하세요 전 AI고 로그 분석합니다")

        # 1초 대기
        time.sleep(1)
except KeyboardInterrupt:
    print("Script interrupted by user.")

# 클라이언트 연결 종료
client.disconnect()
