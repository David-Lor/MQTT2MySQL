
# # Native # #
import asyncio

__all__ = ("MySQLClient",)


class MySQLClient:
    def __init__(self, loop, messages_queue: asyncio.Queue):
        self.loop = loop
        self.messages_queue = messages_queue

    async def connect(self):
        pass

    async def listen_for_messages(self):
        while True:
            try:
                message = await self.messages_queue.get()
                print("RX ON DATABASE LISTENER:", message)
            except Exception as ex:
                print(ex)  # TODO Improve
