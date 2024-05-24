from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from mainUI import Ui_MainWindow
import cv2
from time import sleep
import threading
import numpy as np
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import voice_command as vc

import config   # 본인의 key 모은 모듈


class Stream_receiver:
    mySignal = Signal(QPixmap)

    def __init__(self, topic='', host="127.0.0.1", port=1883):
        """
        Construct a new 'stream_receiver' object to retreive a video stream using Mosquitto_MQTT

        :param topic: MQTT topic to send Stream
        :param host:  IP address of Mosquitto MQTT Broker
        :param Port:  Port at which Mosquitto MQTT Broker is listening

        :return: returns nothing

        : use " object.frame  "  it contains latest frame received
        """

        self.topic = topic
        self.frame = None  # empty variable to store latest message received

        self.client = mqtt.Client()  # Create instance of client

        self.client.on_connect = self.on_connect  # Define callback function for successful connection
        self.client.message_callback_add(self.topic, self.on_message)

        self.client.connect(host, port)  # connecting to the broking server

        t = threading.Thread(target=self.subscribe)  # make a thread to loop for subscribing
        t.start()  # run this thread

    def subscribe(self):
        self.client.loop_forever()  # Start networking daemon

    def on_connect(self, client, userdata, flags, rc):  # The callback for when the client connects to the broker
        client.subscribe(self.topic)  # Subscribe to the topic, receive any messages published on it
        print("Subscring to topic :", self.topic)

    def on_message(self, client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.

        nparr = np.frombuffer(msg.payload, np.uint8)
        self.frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


class MyThread(QThread):
    mySignal = Signal(QPixmap)

    #Thread 시작 시 촬영
    def __init__(self):
        super().__init__()
        self.picam2 = Stream_receiver(topic="agv0/image", host="192.168.110.103")

    flag = False
    def run(self):
        self.flag = True
        while self.flag:
            self.img = self.picam2.frame
            if self.img is not None:  # Add this check
                self.printImage(self.img)
            sleep(0.1)

    def stop(self):
        self.flag = False

    def printImage(self, imgBGR):
        imgRGB = cv2.cvtColor(imgBGR, cv2.COLOR_BGR2RGB)
        h, w, byte = imgRGB.shape
        img = QImage(imgRGB, w, h, byte*w, QImage.Format_RGB888)
        q_img1 = QPixmap(img)

        self.mySignal.emit(q_img1)


class LogThread(QObject):
    distanceSignal = Signal(str)
    logSignal = Signal(str)
    zoneSignal = Signal(str)

    def __init__(self, topic='agv0/#', host='127.0.0.1', port=1883):
        super().__init__()
        self.topic = topic
        self.host = host
        self.port = port
        self.client = mqtt.Client()  # Create instance of client

        self.client.on_connect = self.on_connect  # Define callback function for successful connection
        self.client.on_message = self.on_message  # Define callback function for received messages

        self.client.connect(host, port)  # Connect to the broker

        t = threading.Thread(target=self.subscribe)  # Create a thread to loop for subscribing
        t.start()  # Run this thread

    def subscribe(self):
        self.client.loop_forever()  # Start networking daemon

    def on_connect(self, client, userdata, flags, rc):  # The callback for when the client connects to the broker
        client.subscribe(self.topic)  # Subscribe to the topic, receive any messages published on it
        print("Subscribing to topic:", self.topic)

    def on_message(self, client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
        try:
            if msg.topic.startswith('agv0/image'):
                # Handle binary image data separately
                log_entry = f"{datetime.now()} - {msg.topic}: [binary data]"
            else:
                message = msg.payload.decode('utf-8')
                log_entry = f"{datetime.now()} - {msg.topic}: {message}"
                if msg.topic == 'agv0/distance':
                    self.distanceSignal.emit(message)
                elif msg.topic == 'agv0/currentZone':
                    self.zoneSignal.emit(message)
        except UnicodeDecodeError:
            log_entry = f"{datetime.now()} - {msg.topic}: [invalid UTF-8 data]"

        self.logSignal.emit(log_entry)


class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.main()
        self.client = mqtt.Client()
        self.client.connect(config.BROKER_ADDRESS)
        self.recording_process = None  # recording_process 초기화
        self.language = 'en-US'

        # Create an instance of SensorLogThread and connect the signals
        self.sensor_thread = LogThread(topic='agv0/#', host=config.BROKER_ADDRESS)
        self.sensor_thread.distanceSignal.connect(self.updateDistanceLabel)
        self.sensor_thread.logSignal.connect(self.updateLogText)
        self.sensor_thread.zoneSignal.connect(self.updateZoneLabel)

    def main(self):
        self.th = MyThread()
        self.th.mySignal.connect(self.setImage)
        print('play')
        self.th.start()

    def setImage(self, img):
        self.cam.setPixmap(img)

    def updateDistanceLabel(self, distance):
        self.distanceLabel.setText(distance + 'cm')
        if int(distance) < 10:
            self.distanceLabel.setStyleSheet(u"color: rgb(255, 0, 0);")
        else:
            self.distanceLabel.setStyleSheet(u"color: rgb(0, 0, 0);")

    def updateLogText(self, log_entry):
        self.logText.appendPlainText(log_entry)

    def updateZoneLabel(self, msg):
        self.zoneLabel.setText(msg)

    def startRecording(self):
        print("Start Recording")
        self.recording_process = vc.record_audio()

    def stopRecording(self):
        print("Stop Recording")
        if self.recording_process:
            vc.stop_recording(self.recording_process)
            self.recording_process = None

            # 질문 작성하기
            query = vc.get_voice_message(self.language)
            gpt_answer = vc.query_openai_gpt(query)
            print("gpt answer:")
            print(gpt_answer)

            json_data = json.dumps(gpt_answer)
            topic = "agv" + str(self.comboBox.currentIndex()) + "/voiceCommand"
            self.client.publish(topic, json_data)

    def stop(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "stop")
        print("stop")

    def go(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "forward")
        print('go')

    def changeLanguage(self):
        index = self.comboBox_2.currentIndex()
        li = ['ko-KR', 'en-US', 'fr-FR', 'cn-CN']
        self.language = li[index]
        print('change language to ' + li[index])

    def back(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "backward")
        print('back')

    def left(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "left")
        print('left')

    def right(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "right")
        print('right')

    def follow(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "forward")
        print('follow')

    def emergencyBreak(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "emergencyBreak")
        print('stop move')

    def up(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "armUp")
        print('arm up')

    def down(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "armDown")
        print('arm down')

    def grab(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "grab")
        print('grab')

    def release(self):
        topic = "agv" + str(self.comboBox.currentIndex()) + "/command"
        self.client.publish(topic, "release")
        print('release')

    def closeEvent(self, event):
        self.th.stop()
        self.sensor_thread.client.disconnect()
        event.accept()


if __name__ == '__main__':
    app = QApplication()
    win = MyApp()
    win.show()
    app.exec_()
