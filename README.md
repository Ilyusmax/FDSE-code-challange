# FDSE Code Challenge – Full Data Stream Pipeline

This project implements a complete **end-to-end data streaming pipeline** as described in the [FDSE Code Challenge](https://github.com/quixio/FDSE-code-challange).

The pipeline simulates sensor data generation, ingestion, transformation, and storage in a time-series database — all orchestrated with Docker Compose.

---

## 🚀 Overview

### Architecture
```
Producer → MQTT (Mosquitto) → Ingester → Redis (raw_events)
          → Transformer → Redis (normalized_events) → Sink → InfluxDB → Notebook
```

Each stage is isolated in its own container, enabling independent scaling and monitoring.

| Component | Description | Technology |
|------------|-------------|-------------|
| **Producer** | Simulates sensor readings and publishes them to MQTT topics | Python, Paho-MQTT |
| **Ingester** | Subscribes to MQTT topics and pushes raw messages to Redis | Python, Redis |
| **Transformer** | Converts vertical sensor data into horizontal rows | Python, Redis |
| **Sink** | Writes normalized data from Redis into InfluxDB | Python, InfluxDB Client |
| **Notebook** | Provides an environment for data analysis and visualization | JupyterLab |
| **Mosquitto** | Message broker for the MQTT transport layer | Eclipse Mosquitto |
| **Redis** | Acts as a transient message queue between services | Redis |
| **InfluxDB** | Stores final, structured time-series data | InfluxDB 2.x |

---

## 🧠 Data Flow Example

### Raw message (vertical)
Published by the producer:
```json
{
  "timestamp": "2025-11-02T14:21:33.512Z",
  "value": 78.2
}
```
on topic:
```
rigs/RIG-42/measurements/temp_inlet
```

### Normalized message (horizontal)
Produced by the transformer and written to InfluxDB:
```json
{
  "rig_id": "RIG-42",
  "timestamp": "2025-11-02T14:21:33Z",
  "temp_inlet": 78.2,
  "temp_outlet": 79.1,
  "pressure": 31.4,
  "flow_rate": 14.8,
  "voltage": 220.3,
  "current": 5.2
}
```

---

## 🧱 Project Structure

```
.
├── producer/
│   ├── app.py
│   └── Dockerfile
│   └── requirements.txt
├── ingester/
│   ├── app.py
│   └── Dockerfile
│   └── requirements.txt
├── transformer/
│   ├── app.py
│   └── Dockerfile
│   └── requirements.txt
├── sink/
│   ├── app.py
│   └── Dockerfile
│   └── requirements.txt
├── notebooks/
│   ├── Dockerfile
│   └── Graphs.ipynb
│   └── requirements.txt
├── mosquitto/
│   └── config/mosquitto.conf
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Setup and Run

### Prerequisites
- Docker & Docker Compose
- At least 2 GB of RAM available
---

### Local Setup and Run

This section explains how to run the entire pipeline locally for development and testing.

#### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-folder>
```

#### 2. Build and start all services
```bash
docker compose up --build
```

This command will:
1. Pull and build all service images (`producer`, `ingester`, `transformer`, `sink`, `notebook`)  
2. Start Mosquitto MQTT broker, Redis, and InfluxDB  
3. Wire all containers into the same network

#### 3. Verify services
Open these URLs in your browser or CLI:

| Service | URL / Port | Notes |
|---------|------------|-------|
| **InfluxDB UI** | [http://localhost:8086](http://localhost:8086) | Login: `admin` / `admin123` |
| **Jupyter Notebook** | [http://localhost:8888](http://localhost:8888) | Token disabled for convenience |
| **MQTT Broker** | `localhost:1883` | Can test publishing/subscribing manually |
| **Redis** | `localhost:6379` | Inspect queues with `redis-cli` |

#### 4. Check data flow
1. Open **Jupyter Notebook** (`Graphs.ipynb`)
3. Query and visualize data in real-time as the `producer` publishes simulated sensor readings

#### 5. Stop the stack
```bash
docker compose down -v
```
This will stop all containers and remove the network, but volumes for InfluxDB will persist unless explicitly removed.

---

## 🧪 Environment Variables

| Variable | Default | Description |
|-----------|----------|-------------|
| `MQTT_HOST` | mosquitto | MQTT broker hostname |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `REDIS_HOST` | redis | Redis hostname |
| `REDIS_PORT` | 6379 | Redis port |
| `INFLUX_URL` | http://influxdb:8086 | InfluxDB connection URL |
| `INFLUX_TOKEN` | my-fixed-token-123 | InfluxDB access token |
| `INFLUX_ORG` | my-org | Influx organization |
| `INFLUX_BUCKET` | rigs | InfluxDB bucket name |

---

## 📊 Visualization

You can explore the stored data in two ways:

1. **InfluxDB UI**  
   - Navigate to *Data Explorer* → *rig_measurements* → select tags and fields.

2. **Jupyter Notebook**  
   - Open `Graphs.ipynb` from [http://localhost:8888](http://localhost:8888)  
   - Use Python libraries like `influxdb-client`, `polars`, or `pandas` to query and visualize data.

---

## 💡 Design Highlights

- Modular, containerized architecture (each service single-purpose).
- Horizontal data transformation based on rig ID and timestamp.
- Redis queues decouple services and provide buffering.
- InfluxDB 2.x for efficient time-series storage.
- Graceful error handling and retry logic.
- Easy to scale individual components.

---

## 🤖 AI.md

This project was partially developed with the assistance of **ChatGPT (GPT-5)**.  
AI support was used for:
- Designing the overall architecture and inter-service communication.
- Implementing robust Redis and MQTT clients.
- Drafting Docker and Compose configurations.
- Writing this documentation.

---

## 📚 License
MIT License © 2025 — Created for the FDSE Code Challenge
