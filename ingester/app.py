import os
import time
import json
import redis
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Any, Dict

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ---------------- Redis Abstraction ----------------
class RedisQueue:
    def __init__(self, host: str, port: int, queue_name: str = "raw_events") -> None:
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.redis = self._connect_redis()

    def _connect_redis(self) -> redis.Redis:
        for _ in range(5):
            try:
                r = redis.Redis(host=self.host, port=self.port, decode_responses=True)
                r.ping()
                logging.info("Connected to Redis at %s:%s", self.host, self.port)
                return r
            except redis.ConnectionError:
                logging.warning("Redis not available, retrying in 2s...")
                time.sleep(2)
        raise RuntimeError("Cannot connect to Redis")

    def push(self, payload: Dict[str, Any]) -> None:
        try:
            self.redis.rpush(self.queue_name, json.dumps(payload))
        except Exception as e:
            logging.exception(
                "Failed to push to Redis queue '%s': %s", self.queue_name, e
            )


# ---------------- MQTT Ingester ----------------
class MqttIngester:
    def __init__(
        self,
        mqtt_host: str,
        mqtt_port: int,
        redis_queue: RedisQueue,
        topic: str = "rigs/+/measurements/#",
    ) -> None:
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.redis_queue = redis_queue
        self.topic = topic

        self.client: mqtt.Client = mqtt.Client(protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)

    def on_connect(
        self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int
    ) -> None:
        if rc == 0:
            logging.info(
                "Connected to MQTT broker at %s:%s", self.mqtt_host, self.mqtt_port
            )
            client.subscribe(self.topic)
            logging.info("Subscribed to topic: %s", self.topic)
        else:
            logging.error("Failed to connect to MQTT broker (code %s)", rc)

    def on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            payload: Dict[str, Any] = json.loads(msg.payload.decode("utf-8"))
            payload["mqtt_topic"] = msg.topic
            payload["ingest_time"] = datetime.utcnow().isoformat()
            self.redis_queue.push(payload)
            logging.info("Ingested message from topic '%s'", msg.topic)
        except Exception as e:
            logging.exception("Error processing MQTT message: %s", e)

    def start(self) -> None:
        logging.info("Starting MQTT Ingester...")
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info("MQTT Ingester stopped gracefully.")


# ---------------- Main ----------------
if __name__ == "__main__":
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    mqtt_topic = os.getenv("MQTT_TOPIC", "rigs/+/measurements/#")

    redis_queue = RedisQueue(host=redis_host, port=redis_port)
    ingester = MqttIngester(mqtt_host, mqtt_port, redis_queue, topic=mqtt_topic)
    ingester.start()
