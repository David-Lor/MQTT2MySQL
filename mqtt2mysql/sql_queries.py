
SQL_CREATE_QUERIES = (
    # MQTT Topics table
    """CREATE TABLE IF NOT EXISTS `mqtt_topics` (
        `id` MEDIUMINT UNSIGNED PRIMARY KEY AUTO_INCREMENT
            COMMENT 'Auto-increment primary key (unsigned mediumint)',
        `topic` TEXT NOT NULL
            COMMENT 'MQTT topic (string)'
    )
    ROW_FORMAT=COMPRESSED
    KEY_BLOCK_SIZE=8
    ENGINE=InnoDB;""",
    # MQTT Messages table
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
    # Messages view
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
