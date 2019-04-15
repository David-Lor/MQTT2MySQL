
from signal import pause
from .mqtt import MQTTListener
from .sql import MySQL


def run():
    mysql = MySQL()
    mysql.connect()
    mqtt_listener = MQTTListener(mysql)
    mqtt_listener.run()
    try:
        pause()
    except (KeyboardInterrupt, InterruptedError):
        pass
    print("Bye!")
