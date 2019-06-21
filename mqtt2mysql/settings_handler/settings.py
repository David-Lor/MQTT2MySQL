
# # Native # #
from typing import Dict, List, Optional
from os import getenv

# # Installed # #
from dotenv import load_dotenv

# # Package # #
from .const import *

__all__ = ("load_settings",)


def _parse_topics(topics_line: Optional[str]) -> Optional[List[str]]:
    if topics_line:
        return [
            topic.strip().replace(MQTT_TOPIC_SEPARATOR, "#")
            for topic in topics_line.split(",")
        ]


def load_settings(*args, **kwargs) -> Dict:
    load_dotenv(*args, **kwargs)
    return {
        MQTT_BROKER: getenv(MQTT_BROKER, DEFAULT_MQTT_BROKER),
        MQTT_PORT: int(getenv(MQTT_PORT, DEFAULT_MQTT_PORT)),
        MQTT_KEEPALIVE: int(getenv(MQTT_KEEPALIVE, DEFAULT_MQTT_KEEPALIVE)),
        MQTT_QOS: int(getenv(MQTT_QOS, DEFAULT_MQTT_QOS)),
        MQTT_TOPICS: _parse_topics(getenv(MQTT_TOPICS)) or DEFAULT_MQTT_TOPICS,
        MQTT_TOPICS_BLACKLIST: _parse_topics(getenv(MQTT_TOPICS_BLACKLIST)),

        SQL_HOST: getenv(SQL_HOST, DEFAULT_SQL_HOST),
        SQL_PORT: int(getenv(SQL_PORT, DEFAULT_SQL_PORT)),
        SQL_DATABASE: getenv(SQL_DATABASE, DEFAULT_SQL_DATABASE),
        SQL_USER: getenv(SQL_USER),
        SQL_PASSWORD: getenv(SQL_PASSWORD),
        SQL_CHARSET: getenv(SQL_CHARSET, DEFAULT_SQL_CHARSET),
    }
