
# # Native # #
import asyncio

# # Package # #
from .mqtt import MQTTClient
from .database import MySQLClient


def main():
    loop = asyncio.get_event_loop()

    mqtt = MQTTClient(loop)
    mysql = MySQLClient(loop, mqtt.messages_queue)

    loop.create_task(mqtt.connect())
    loop.create_task(mysql.connect())
    loop.create_task(mysql.listen_for_messages())

    loop.run_forever()


if __name__ == '__main__':
    main()
