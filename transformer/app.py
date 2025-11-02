import os
import json
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any, Dict, Tuple
import time

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

    def blpop(self, queue_name: str, timeout: int = 0) -> Tuple[str, str]:
        return self.redis.blpop(queue_name, timeout)  # type: ignore

    def rpush(self, queue_name: str, payload: Dict[str, Any]) -> None:
        try:
            self.redis.rpush(queue_name, json.dumps(payload))
        except Exception as e:
            logging.exception("Failed to push to Redis queue '%s': %s", queue_name, e)


# ---------------- Transformer ----------------
class Transformer:
    def __init__(
        self,
        redis_queue: RedisQueue,
        raw_queue: str = "raw_events",
        normalized_queue: str = "normalized_events",
        flush_interval: int = 5,
    ) -> None:
        self.redis_queue: RedisQueue = redis_queue
        self.raw_queue: str = raw_queue
        self.normalized_queue: str = normalized_queue
        self.buffer: defaultdict[Tuple[str, str], Dict[str, Any]] = defaultdict(dict)
        self.flush_interval: timedelta = timedelta(seconds=flush_interval)
        self.last_flush: datetime = datetime.utcnow()

    def transform_loop(self) -> None:
        logging.info("Starting transformer loop...")
        while True:
            _, raw = self.redis_queue.blpop(self.raw_queue)
            event: Dict[str, Any] = json.loads(raw)
            self._process_event(event)
            self._maybe_flush()

    def _process_event(self, event: Dict[str, Any]) -> None:
        topic_parts = event["mqtt_topic"].split("/")
        rig_id: str = topic_parts[1]
        sensor_id: str = topic_parts[-1]
        timestamp_str: str = event.get("timestamp", datetime.utcnow().isoformat())
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        ts_rounded = ts.replace(microsecond=0)
        key = (rig_id, ts_rounded)
        self.buffer[key][sensor_id] = event.get("value")

    def _maybe_flush(self) -> None:
        now: datetime = datetime.utcnow()
        if now - self.last_flush >= self.flush_interval:
            self._flush_ready()
            self.last_flush = now

    def _flush_ready(self) -> None:
        if not self.buffer:
            return
        for (rig_id, ts), sensors in list(self.buffer.items()):
            timestamp_str = ts.isoformat()
            row: Dict[str, Any] = {
                "rig_id": rig_id,
                "timestamp": timestamp_str,
                **sensors,
            }
            self.redis_queue.rpush(self.normalized_queue, row)
            logging.info(f"Flushed normalized row for {rig_id}@{timestamp_str}: {row}")
            del self.buffer[(rig_id, ts)]


# ---------------- Main ----------------
if __name__ == "__main__":
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    raw_queue: str = os.getenv("RAW_QUEUE", "raw_events")
    normalized_queue: str = os.getenv("NORMALIZED_QUEUE", "normalized_events")
    flush_interval: int = int(os.getenv("FLUSH_INTERVAL", "5"))

    redis_queue = RedisQueue(host=redis_host, port=redis_port)
    transformer = Transformer(
        redis_queue=redis_queue,
        raw_queue=raw_queue,
        normalized_queue=normalized_queue,
        flush_interval=flush_interval,
    )
    transformer.transform_loop()
