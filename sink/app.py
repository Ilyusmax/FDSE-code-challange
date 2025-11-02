import os
import json
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import redis
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dateutil import parser  # <-- добавлено

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------- Redis Abstraction ----------------
class RedisQueue:
    def __init__(self, host: str, port: int, decode_responses: bool = True) -> None:
        self.host = host
        self.port = port
        self.redis: redis.Redis = self._connect_redis(decode_responses)

    def _connect_redis(self, decode_responses: bool) -> redis.Redis:
        import time

        for _ in range(5):
            try:
                r = redis.Redis(
                    host=self.host, port=self.port, decode_responses=decode_responses
                )
                r.ping()
                logging.info("Connected to Redis at %s:%s", self.host, self.port)
                return r
            except redis.ConnectionError:
                logging.warning("Redis not available, retrying in 2s...")
                time.sleep(2)
        raise RuntimeError("Cannot connect to Redis")

    def blpop(self, queue_name: str, timeout: int = 0) -> Optional[Tuple[str, str]]:
        return self.redis.blpop(queue_name, timeout)  # type: ignore

    def rpush(self, queue_name: str, payload: Dict[str, Any]) -> None:
        try:
            self.redis.rpush(queue_name, json.dumps(payload))
        except Exception as e:
            logging.exception("Failed to push to Redis queue '%s': %s", queue_name, e)

# ---------------- InfluxDB Sink ----------------
class InfluxSink:
    def __init__(
        self,
        redis_queue: RedisQueue,
        normalized_queue: str = "normalized_events",
        bucket: str = "rigs",
        org: str = "my-org",
        url: str = "http://influxdb:8086",
        token: Optional[str] = None,
    ) -> None:
        if token is None:
            token = os.getenv("INFLUX_TOKEN")
        if not token:
            raise ValueError("INFLUX_TOKEN must be set in environment variables")

        self.redis_queue: RedisQueue = redis_queue
        self.normalized_queue: str = normalized_queue
        self.bucket: str = bucket
        self.org: str = org
        self.token: str = token
        self.url: str = url

        self.client: InfluxDBClient = InfluxDBClient(
            url=self.url, token=self.token, org=self.org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def run(self) -> None:
        logging.info("Starting InfluxDB sink...")
        while True:
            try:
                raw_event: Optional[Tuple[str, str]] = self.redis_queue.blpop(
                    self.normalized_queue, timeout=5
                )
                if not raw_event:
                    continue

                raw_json: str = raw_event[1]
                record: Dict[str, Any] = json.loads(raw_json)

                rig_id: Optional[str] = record.get("rig_id")
                timestamp: Optional[str] = record.get("timestamp")
                if not rig_id or not timestamp:
                    logging.warning(
                        "Skipping record with missing rig_id or timestamp: %s", record
                    )
                    continue

                # Парсим timestamp универсально
                dt: datetime = parser.isoparse(timestamp)

                # Усечение до секунд
                dt = dt.replace(microsecond=0)

                point: Point = (
                    Point("rig_measurements")
                    .tag("rig_id", rig_id)
                    .time(dt, WritePrecision.NS)
                )

                for key, value in record.items():
                    if key not in {"rig_id", "timestamp"} and value is not None and isinstance(value, (int, float)):
                        point.field(key, value)

                self.write_api.write(bucket=self.bucket, org=self.org, record=point)
                logging.info("Wrote record for rig %s at %s", rig_id, dt.isoformat())

            except Exception as e:
                logging.exception("Failed to write record: %s", e)

# ---------------- Main ----------------
if __name__ == "__main__":
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    normalized_queue: str = os.getenv("NORMALIZED_QUEUE", "normalized_events")

    redis_queue = RedisQueue(host=redis_host, port=redis_port)
    sink = InfluxSink(redis_queue=redis_queue, normalized_queue=normalized_queue)
    sink.run()
