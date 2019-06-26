
# # Native # #
import asyncio

# # Package # #
from .mqtt import MQTTClient
from .database import MySQLClient


async def stop_all(mqtt, mysql):
    await asyncio.gather(mqtt.stop(), mysql.stop())


def main():
    loop = asyncio.get_event_loop()

    mqtt = MQTTClient(loop)
    mysql = MySQLClient(loop, mqtt.messages_queue)

    loop.create_task(mqtt.connect())
    loop.create_task(mysql.connect())
    # loop.create_task(mysql.listen_for_messages())

    try:
        loop.run_forever()
    except (KeyboardInterrupt, InterruptedError):
        pass
    finally:
        print("Exiting app, Starting disconnect sequence...")
        loop.run_until_complete(stop_all(mqtt, mysql))


if __name__ == '__main__':
    main()
