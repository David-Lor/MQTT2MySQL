
# # Native # #
import asyncio
import time
from collections import namedtuple

# # Installed # #
import aiomqtt

# # Project # #
from .settings_handler import load_settings
from .settings_handler.const import *

__all__ = ("MQTTClient",)

settings = load_settings()

Message = namedtuple("Message", ("topic", "payload", "timestamp", "retained", "qos"))


class MQTTClient:
    def __init__(self, loop):
        self.loop = loop
        self.client = aiomqtt.Client(self.loop)
        self.messages_queue = asyncio.Queue(loop=self.loop)

        self._connected = asyncio.Event(loop=self.loop)
        self._subscribed = asyncio.Event(loop=self.loop)
        self._ready_to_store = False
        self._subscriptions = 0

        self.client.loop_start()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe

    # noinspection PyUnusedLocal
    def on_connect(self, *args, **kwargs):
        self._connected.set()

    # noinspection PyUnusedLocal
    def on_subscribe(self, client, userdata, mid, granted_qos):
        self._subscriptions += 1
        if self._subscriptions == len(settings[MQTT_TOPICS]):
            self._subscribed.set()

    # noinspection PyUnusedLocal
    def on_message(self, client, userdata, message):
        # TODO Avoid saving first messages
        topic = message.topic
        payload = message.payload.decode()
        retained = bool(message.retain)
        msg = Message(
            topic=message.topic,
            payload=message.payload.decode(),  # TODO What if payload is not text, or empty (null)?
            retained=bool(message.retain),
            qos=message.qos,
            timestamp=int(time.time())
        )
        print(f"RX @ {topic} : {payload}{' (Retained)' if retained else ''}")
        self.loop.create_task(self.messages_queue.put(msg))

    async def connect(self):
        await self.client.connect(
            host=settings[MQTT_BROKER],
            port=settings[MQTT_PORT],
            keepalive=settings[MQTT_KEEPALIVE]
        )
        await self._connected.wait()
        print("MQTT Connected!")

        for topic in settings[MQTT_TOPICS]:
            self.client.subscribe(topic)
        await self._subscribed.wait()
        print("MQTT Subscribed to all topics!")
