import paho.mqtt.client as mqtt
import time
from sense_hat import SenseHat
from gpiozero import DistanceSensor
from gpiozero import LED
from time import sleep
from gpiozero import TonalBuzzer
from gpiozero.tones import Tone
import random

# sense = SenseHat()
sensor = DistanceSensor(echo=5, trigger=6)
led = LED(16)
b = TonalBuzzer(26)

# MQTT 브로커 정보 설정
broker_address = "192.168.110.103"
port = 1883

# MQTT 클라이언트 생성
client = mqtt.Client()

# 플래그 변수 초기화
dance_flag = False

# MQTT 메시지 수신 콜백 함수
def on_message(client, userdata, message):
    global dance_flag
    if message.topic == "agv0/command" and message.payload.decode() == "dance":
        dance_flag = True

# 콜백 함수 설정
client.on_message = on_message

# MQTT 브로커에 연결
client.connect(broker_address, port)

# 특정 토픽 구독
client.subscribe("agv0/voiceCommand")

# 메시지를 주기적으로 발행하는 함수
def publish_message(topic, message):
    client.publish(topic, message)
    print("Message published:", message)

# dance 함수 정의
def dance():
    print("Dancing...")
    tones = ["C4", "E4", "G4", "C5", "E5", "G5"]
    start_time = time.time()
    while time.time() - start_time < 3:
        led.on()
        b.play(Tone(random.choice(tones)))
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
    b.stop()

# 비동기식으로 MQTT 메시지 수신 대기 시작
client.loop_start()

# 주기적으로 메시지 발행
while True:
    d = int(sensor.distance * 100)
    publish_message("agv0/distance", d)
    if d < 13:
        led.on()
        b.play(Tone("A4"))
        publish_message("agv0/command", "emergencyBreak")
    else:
        led.off()
        b.stop()

    # dance_flag가 설정되었는지 확인
    if dance_flag:
        dance()
        dance_flag = False  # dance 함수 실행 후 플래그 초기화

    time.sleep(0.1)

