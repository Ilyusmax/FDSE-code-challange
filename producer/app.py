import json
import random
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List
from paho.mqtt import client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# ─────────────────────────────────────────────
# 🧱 Logging configuration
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 🧩 Abstract message broker
# ─────────────────────────────────────────────
class AbstractBroker(ABC):
    """Abstract interface for a message broker."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the broker."""
        pass

    @abstractmethod
    def publish(self, topic: str, payload: Dict) -> None:
        """Publish a message to the broker."""
        pass


# ─────────────────────────────────────────────
# 🛰️ Concrete implementation for MQTT
# ─────────────────────────────────────────────
class MqttBroker(AbstractBroker):
    """MQTT broker implementation using paho-mqtt."""

    def __init__(
        self, host: str = "mosquitto", port: int = 1883, client_id: str = "producer"
    ):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(
            client_id=client_id, callback_api_version=CallbackAPIVersion.VERSION2
        )
        self.connect()

    def connect(self) -> None:
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.host, self.port)
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def publish(self, topic: str, payload: Dict) -> None:
        """Publish a JSON message to an MQTT topic."""
        try:
            message = json.dumps(payload)
            self.client.publish(topic, message)
            logger.debug(f"Published to {topic}: {message}")
        except Exception as e:
            logger.warning(f"Failed to publish to {topic}: {e}")


# ─────────────────────────────────────────────
# ⚙️ Measurement data generation
# ─────────────────────────────────────────────
def generate_measurement(rig_id: str, sensor_id: str) -> Dict:
    """Generate a single measurement record."""
    timestamp = (
        time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}Z"
    )
    value = round(random.uniform(10, 100), 2)
    return {
        "rig_id": rig_id,
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "value": value,
    }


# ─────────────────────────────────────────────
# 🔁 Message publishing loop
# ─────────────────────────────────────────────
def publish_loop(
    broker: AbstractBroker, rigs: List[str], sensors: List[str], delay: float = 1.0
) -> None:
    """Continuously generate and publish measurements for all rigs and sensors."""
    logger.info("Starting producer publish loop")
    while True:
        rig = random.choice(rigs)
        for sensor in sensors:
            measurement = generate_measurement(rig, sensor)
            topic = f"rigs/{rig}/measurements/{sensor}"
            payload = {
                "timestamp": measurement["timestamp"],
                "value": measurement["value"],
            }
            broker.publish(topic, payload)
            time.sleep(0.05)
        time.sleep(delay)


# ─────────────────────────────────────────────
# 🚀 Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    RIGS = ["RIG-1", "RIG-42"]
    SENSORS = [
        "temp_inlet",
        "temp_outlet",
        "pressure",
        "flow_rate",
        "voltage",
        "current",
    ]

    broker = MqttBroker(host="mosquitto", port=1883)
    publish_loop(broker, RIGS, SENSORS)
