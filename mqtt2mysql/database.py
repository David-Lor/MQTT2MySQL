
# # Native # #
import asyncio

# # Installed # #
import aiomysql

# # Project # #
from .settings_handler import load_settings
from .settings_handler.const import *

# # Package # #
from .mqtt import Message
from .sql_queries import *

__all__ = ("MySQLClient",)

settings = load_settings()


class MySQLClient:
    # noinspection PyTypeChecker
    def __init__(self, loop, messages_queue: asyncio.Queue):
        self.loop = loop
        """Asyncio event loop"""
        self.messages_queue = messages_queue
        """Async Queue where to put MQTT messages, to be processed by the listen_for_messages service"""
        self.connection: aiomysql.connection.Connection = None
        """Async aiomysql Connection to the MySQL database"""
        self.writing_lock = asyncio.Lock()
        """Async Lock to avoid parallel writing operations"""
        self._disconnected_event = asyncio.Event(loop=self.loop)
        """Async Event to set when the MySQL service must be stopped"""
        self._listener_stopped_event = asyncio.Event(loop=self.loop)
        """Async Event to set when the listen_for_messages service is stopped"""
        self._stop_queue = -1
        """Value inserted on the messages_queue when the listen_for_messages service must be stopped"""

    async def _insert(self, message: Message):
        await self.writing_lock.acquire()

        try:
            if not self.connection:
                await self.connect()
            else:
                await self.connection.ping(reconnect=True)

            async with self.connection.cursor() as cursor:
                # Insert topic
                await cursor.execute(SQL_INSERT_TOPIC, (message.topic, message.topic))

                # Insert message
                await cursor.execute(SQL_INSERT_MESSAGE, (
                    message.topic, message.payload, message.qos, message.timestamp, int(message.ssl)
                ))

                await self.connection.commit()
                print("Inserted!", message)
        except Exception as ex:
            # On Error: retry after some time putting the message on the queue again
            print("Error inserting", message, ex)
            self.writing_lock.release()
            # Wait some time before putting the message on the queue again
            await asyncio.sleep(settings[SQL_INSERT_RETRY_DELAY])
            await self.messages_queue.put(message)

        else:
            self.writing_lock.release()

    async def stop(self):
        """Async method to be called when the MySQL service must be stopped"""
        print("Stopping MySQL service...")
        self._disconnected_event.set()
        await self.messages_queue.put(self._stop_queue)
        await self._listener_stopped_event.wait()
        print("MySQL service stopped!")

    async def connect(self):
        """Async method to be called when the MySQL service must be started"""
        self.connection = await aiomysql.connect(
            host=settings[SQL_HOST],
            port=settings[SQL_PORT],
            user=settings[SQL_USER],
            password=settings[SQL_PASSWORD],
            db=settings[SQL_DATABASE],
            charset=settings[SQL_CHARSET],
            connect_timeout=settings[SQL_CONNECT_TIMEOUT],
            program_name="MQTT2MySQL",
            cursorclass=aiomysql.cursors.DictCursor,
            autocommit=False,
            loop=self.loop
        )

        async with self.connection.cursor() as cursor:
            for create_query in SQL_CREATE_QUERIES:
                await cursor.execute(create_query)

        self.loop.create_task(self.listen_for_messages())

    async def listen_for_messages(self):
        """Async method to be called when the MySQL service must be started"""
        while not self._disconnected_event.is_set():
            message: Message = await self.messages_queue.get()
            if message != self._stop_queue:
                print("Rx @ Database listener:", message)
                # Create one Insert task for each received message
                self.loop.create_task(self._insert(message))

        self._listener_stopped_event.set()
