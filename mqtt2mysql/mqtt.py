
# # Native # #
import asyncio
import time
from collections import namedtuple

# # Installed # #
import aiomqtt

# # Project # #
from .settings_handler import load_settings
from .settings_handler.const import *

__all__ = ("MQTTClient", "Message")

settings = load_settings()

Message = namedtuple("Message", ("topic", "payload", "timestamp", "qos", "ssl"))


class MQTTClient:
    def __init__(self, loop):
        self.loop: asyncio.AbstractEventLoop = loop
        """Asyncio event loop"""
        self.client = aiomqtt.Client(self.loop)
        """aiomqtt MQTT Client"""
        self.messages_queue = asyncio.Queue(loop=self.loop)
        """Async Queue where to put MQTT messages, to be processed by the MySQL service"""

        self._event_connected = asyncio.Event(loop=self.loop)
        """Async Event to set when connected to MQTT"""
        self._event_subscribed = asyncio.Event(loop=self.loop)
        """Async Event to set when subscribed to the MQTT topics"""
        self._event_disconnected = asyncio.Event(loop=self.loop)
        """Async Event to set when disconnected from MQTT"""
        self._event_stop = asyncio.Event(loop=self.loop)
        """Async Event to set when the MQTT service must stop"""
        self._subscriptions = 0
        """Counter to count the number of subscriptions performed. Used on the _on_subscribe callback"""

        self._event_disconnected.set()  # By default, MQTT is disconnected
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_disconnect = self._on_disconnect

    # noinspection PyUnusedLocal
    def _on_connect(self, *args, **kwargs):
        self._event_connected.set()
        self._event_disconnected.clear()
        self._event_subscribed.clear()

    # noinspection PyUnusedLocal
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        self._subscriptions += 1
        if self._subscriptions == len(settings[MQTT_TOPICS]):
            self._event_subscribed.set()

    # noinspection PyUnusedLocal
    def _on_message(self, client, userdata, message):
        skip_conditions = (
            message.retain and settings[MQTT_SKIP_RETAINED],
            not message.payload and settings[MQTT_SKIP_EMPTY]
        )
        if not any(skip_conditions):
            topic = message.topic
            payload = message.payload.decode()
            msg = Message(
                topic=message.topic,
                payload=message.payload.decode(),  # TODO What if payload is not text, or empty (null)?
                qos=message.qos,
                ssl=0,  # Unsupported feature for now
                timestamp=int(time.time())
            )
            print(f"RX @ {topic} : {payload}")
            self.loop.create_task(self.messages_queue.put(msg))

    # noinspection PyUnusedLocal
    def _on_disconnect(self, *args, **kwargs):
        self._event_disconnected.set()
        self._event_connected.clear()
        self._event_subscribed.clear()
        print("MQTT disconnected!")
        if not self._event_stop.is_set():
            # If disconnected due to an external factor, must re-connect
            self.loop.create_task(self.connect())

    async def stop(self):
        """Async method to be called when the MQTT service must be stopped"""
        print("Stopping MQTT service...")
        self._event_stop.set()
        self.client.disconnect()
        await self._event_disconnected.wait()
        print("MQTT service stopped!")

    async def connect(self):
        """Async method to be called when the MQTT service must be started"""
        print("Connecting MQTT...")
        # TODO try/except to handle connection refused and other problems
        connected = False
        while not connected and not self._event_stop.is_set():
            try:
                await self.client.connect(
                    host=settings[MQTT_BROKER],
                    port=settings[MQTT_PORT],
                    keepalive=settings[MQTT_KEEPALIVE]
                )
                self.loop.create_task(self.client.loop_forever(retry_first_connection=True))
            except ConnectionError as ex:
                print(ex, "when connecting to MQTT, trying again in 10 seconds...")
                await asyncio.sleep(10)
            else:
                connected = True

        if self._event_stop.is_set():
            return

        await self._event_connected.wait()
        print("MQTT Connected!")

        for topic in settings[MQTT_TOPICS]:
            self.client.subscribe(topic)
        await self._event_subscribed.wait()
        print("MQTT Subscribed to all topics!")
