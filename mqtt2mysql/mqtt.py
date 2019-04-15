
# Native libraries
import atexit
import os
from time import time

# Installed libraries
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Package modules
from .sql import MySQL


load_dotenv()
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))
MQTT_QOS = int(os.getenv("MQTT_QOS", 0))
MQTT_TOPICS = os.getenv("MQTT_TOPICS", "")  # comma separated
MQTT_TOPICS_BLACKLIST = os.getenv("MQTT_TOPICS_BLACKLIST", "")  # comma separared

if not MQTT_TOPICS.strip():
    MQTT_TOPICS = ("#",)
else:
    MQTT_TOPICS = [e.strip().replace("$$$$", "#") for e in MQTT_TOPICS.split(",")]

if not MQTT_TOPICS_BLACKLIST.strip():
    MQTT_TOPICS_BLACKLIST = ()
else:
    MQTT_TOPICS_BLACKLIST = [e.strip().replace("$$$$", "#") for e in MQTT_TOPICS_BLACKLIST.split(",")]


class MQTTListener:
    def __init__(self, database: MySQL = None):
        if not database:
            self.database = MySQL()
        else:
            self.database = database
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        atexit.register(self.stop)

    # noinspection PyUnusedLocal
    @staticmethod
    def on_connect(client: mqtt.Client, userdata, flags, rc):
        print(f"Connected MQTT at {MQTT_BROKER}:{MQTT_PORT}")
        for topic in MQTT_TOPICS:
            client.subscribe(topic, MQTT_QOS)
            print("Sub to", topic)

    # noinspection PyUnusedLocal
    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        print(f"Rx MQTT @ {msg.topic} : {msg.payload.decode()[:50]}")
        try:
            setattr(msg, "timestamp", int(time()))
            if msg.topic not in MQTT_TOPICS_BLACKLIST:
                self.database.save_message(msg)
        except Exception as ex:
            print(ex)

    def run(self):
        print(f"Running MQTT listening to broker {MQTT_BROKER}:{MQTT_PORT}")
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        self.mqtt_client.loop_start()

    def stop(self):
        print("Stopping MQTT")
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
