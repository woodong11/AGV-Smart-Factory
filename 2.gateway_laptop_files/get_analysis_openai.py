import openai
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
import paho.mqtt.client as mqtt

import config   # 본인의 key 모은 모듈

# MQTT 브로커 설정
broker_address = config.BROKER_ADDRESS         
topic_analysis = "agv0/analysis"

# MQTT 클라이언트 설정
client = mqtt.Client()
client.connect(broker_address)

# OpenAI API 키 설정
openai.api_key = config.OPENAI_API_KEY         # 본인의 openai api 키로 변경 필요!! 
MODEL = "gpt-3.5-turbo"

# Firebase 초기화
cred = credentials.Certificate(config.FIREBASE_JSON)               # 본인의 firebase json키의 위치로 변경 필요!! 
firebase_admin.initialize_app(cred, {
    'databaseURL': config.DATABASE_URL                             # 본인의 데이터베이스로 usl 변경 필요
})

# Firebase에서 데이터 읽기 - commandTable과 sensingTable에서 5개씩 읽어온다.
def get_last_5_entries():
    command_ref = db.reference('/agv0/commandTable')
    sensing_ref = db.reference('/agv0/sensingTable')
    
    all_commands = command_ref.order_by_key().limit_to_last(5).get()
    all_sensing = sensing_ref.order_by_key().limit_to_last(5).get()
    
    last_5_commands = [command for command in all_commands.values()]
    last_5_sensing = [sensing for sensing in all_sensing.values()]
    
    return last_5_commands, last_5_sensing

# 명령어 분석
def analyze_entries(commands, sensings):
    global MODEL
    messages = [
        {"role": "system", "content": "You are an assistant that analyzes commands and sensing data."},
        {"role": "user", "content": "Analyze the following commands and sensing data and provide insights in one sentence, For reference, ahead_obstacle_distance is the distance from unnecessary obstacles in front of the robot. korean please:"}
    ]
    for command in commands:
        command_details = f"Cmd String: {command['command']}, Current_position: {command['current_position']}"
        messages.append({"role": "user", "content": command_details})
    
    for sensing in sensings:
        sensing_details = f"Distance: {sensing['ahead_obstacle_distance']}, Orientation: {sensing['orientation']}"
        messages.append({"role": "user", "content": sensing_details})
    
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

# 분석하기
try:
    while True:
        last_5_commands, last_5_sensings = get_last_5_entries()
        analysis = analyze_entries(last_5_commands, last_5_sensings)
        print("Analysis:\n", analysis)
        
        # MQTT로 분석 결과 전송
        client.publish(topic_analysis, analysis.encode('utf-8'))
        time.sleep(1)

except KeyboardInterrupt:
    print("Script interrupted by user.")

# 클라이언트 연결 종료
client.disconnect()
