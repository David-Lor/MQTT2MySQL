
# Native libraries
import os
import atexit
from traceback import format_exc
from time import time
from typing import List
from collections import namedtuple
from threading import Thread, Lock, Event

# Installed libraries
import pymysql
import paho.mqtt.client as mqtt
from dotenv import load_dotenv


load_dotenv()
HOST = os.getenv("SQL_HOST", "127.0.0.1")
PORT = int(os.getenv("SQL_PORT", 3306))
DATABASE = os.getenv("SQL_DATABASE")
USER = os.getenv("SQL_USER")
PASSWORD = os.getenv("SQL_PASSWORD")
CHARSET = os.getenv("SQL_CHARSET", "utf8mb4")
QUEUE_FREQ = int(os.getenv("SQL_QUEUE_FREQ", 30))

SQL_CREATE_QUERIES = (
    """CREATE TABLE IF NOT EXISTS `mqtt_topics` (
        `id` MEDIUMINT UNSIGNED PRIMARY KEY AUTO_INCREMENT
            COMMENT 'Auto-increment primary key (unsigned mediumint)',
        `topic` TEXT NOT NULL
            COMMENT 'MQTT topic (string)'
    )
    ROW_FORMAT=COMPRESSED
    KEY_BLOCK_SIZE=8
    ENGINE=InnoDB;""",
    """CREATE TABLE IF NOT EXISTS `mqtt` (
        `id` INTEGER UNSIGNED PRIMARY KEY AUTO_INCREMENT
            COMMENT 'Auto-increment primary key (unsigned int)',
        `topic` MEDIUMINT UNSIGNED NOT NULL
            COMMENT 'MQTT message topic (foreign key: unsigned mediumint from table mqtt_topics',
        `payload` LONGTEXT NOT NULL
            COMMENT 'MQTT message payload',
        `qos` TINYINT NOT NULL DEFAULT 0
            COMMENT 'MQTT QoS level (0/1/2)',
        `timestamp` INTEGER UNSIGNED NOT NULL
            COMMENT 'Epoch timestamp when this MQTT message was received by MQTT2MySQL',
        `ssl` BOOLEAN NOT NULL DEFAULT 0
            COMMENT 'True if the message was sent to the SSL broker endpoint',
        FOREIGN KEY `fk_topic`(`topic`)
            REFERENCES `mqtt_topics`(`id`)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    )
    ROW_FORMAT=COMPRESSED
    KEY_BLOCK_SIZE=8
    ENGINE=InnoDB;""",
    """CREATE OR REPLACE VIEW `messages` AS
        SELECT mqtt.id, mqtt_topics.topic, mqtt.payload, mqtt.qos, mqtt.ssl, FROM_UNIXTIME(mqtt.timestamp) AS datetime
        FROM `mqtt` JOIN `mqtt_topics` ON mqtt.topic = mqtt_topics.id GROUP BY mqtt.id
        ORDER BY mqtt.timestamp DESC;
    """
)

SQL_INSERT_MESSAGE = """
    INSERT INTO `mqtt` (`topic`, `payload`, `qos`, `timestamp`, `ssl`)
    VALUES ((SELECT mqtt_topics.id FROM mqtt_topics WHERE mqtt_topics.topic = %s), %s, %s, %s, %s);
"""

SQL_INSERT_TOPIC = """
    INSERT INTO mqtt_topics (topic)
    SELECT %s
    FROM mqtt_topics
    WHERE topic = %s
    HAVING COUNT(id) = 0;
"""

Message = namedtuple("Message", ["topic", "payload", "timestamp", "qos", "ssl"])


class MySQL:
    def __init__(self):
        self.connection: pymysql.Connection = None
        self.queue: List[Message] = list()
        self.insert_lock = Lock()
        self.queue_thread = Thread(target=self.__queue_processing, daemon=True)
        self.queue_thread_stop_event = Event()
        self.start = self.connect
        atexit.register(self.stop)

    def connect(self):
        self.connection = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            db=DATABASE,
            charset=CHARSET,
            cursorclass=pymysql.cursors.DictCursor
        )
        with self.connection.cursor() as cursor:
            for query in SQL_CREATE_QUERIES:
                cursor.execute(query)
        self.connection.commit()
        self.queue_thread.start()

    def stop(self):
        self.queue_thread_stop_event.set()
        self.queue_thread.join()
        self.disconnect()

    def disconnect(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def _insert(
            self, topic: str, payload: str, qos: int, timestamp: int,
            ssl: bool = False, commit: bool = True
    ) -> bool:
        inserted = 0
        try:
            self.insert_lock.acquire()
            with self.connection.cursor() as cursor:
                # Insert topic
                cursor.execute(SQL_INSERT_TOPIC, (topic, topic))
                # Insert message
                inserted = cursor.execute(SQL_INSERT_MESSAGE, (topic, payload, qos, timestamp, int(ssl)))
            if commit:
                self.connection.commit()
        except pymysql.Error:
            print(f"Can't insert MQTT message on DB:\n{format_exc()}")
        else:
            print(f"Inserted MQTT @ {topic} : {payload[:50]}{' ...' if len(payload) > 50 else ''}")
        finally:
            self.insert_lock.release()
            return bool(inserted)

    def __queue_processing(self):
        running = True
        not_inserted_messages = list()  # Messages that could not be inserted
        print("MySQL queue processing thread started")

        while running:
            # Get current state of the Stop Event
            # This allows saving the remaining messages in queue before closing
            running = not self.queue_thread_stop_event.is_set()
            inserted_messages = list()

            # Insert each queued message
            while self.queue:
                message = self.queue.pop(0)
                message_inserted = self._insert(
                    topic=message.topic,
                    payload=message.payload,
                    qos=message.qos,
                    timestamp=message.timestamp,
                    ssl=message.ssl,
                    commit=False
                )
                if not message_inserted:
                    not_inserted_messages.append(message)
                else:
                    inserted_messages.append(message)

            # Commit
            if inserted_messages:
                try:
                    self.connection.commit()
                except pymysql.Error as ex:
                    print(f"Can't commit messages queue ({ex})")
                    not_inserted_messages.extend(inserted_messages)

            # Put not-inserted messages on queue again
            if not_inserted_messages:
                self.queue.extend(not_inserted_messages)
                not_inserted_messages.clear()

            # Sleep thread using the stop event
            self.queue_thread_stop_event.wait(QUEUE_FREQ)

    def save_message(
            self, message: mqtt.MQTTMessage, ssl: bool = False
    ):
        msg = Message(
            topic=message.topic,
            payload=message.payload.decode(),
            qos=message.qos,
            timestamp=getattr(message, "timestamp", int(time())),
            ssl=ssl
        )
        self.queue.append(msg)
