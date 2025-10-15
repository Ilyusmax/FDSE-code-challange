# Forward Deployed Software Engineer – Code Challenge

Welcome to the FDSE coding challenge! This challenge is designed to evaluate your ability to build data pipelines whiles leveraging AI tools effectively. This is not designed to be build without AI help, as time needed would greatly surpass reasonable time allocation for any code challenge for any job. 

## Goal

Build a small data pipeline that:

1. **Subscribes to an MQTT broker** streaming *test rig measurements*
2. **Normalizes** raw "vertical" messages into a **horizontal** (wide) schema by timestamp & rig
3. **Sinks** the normalized data into a **database of your choice** (e.g., InfluxDB, Postgres, DuckDB, SQLite)
4. **Visualizes** the result in a notebook (JupyterLab / Marimo / etc.)
5. **Runs in Docker** (bonus for `docker-compose` one-command bring-up)
6. **Uses AI** during development — your AI workflow will be part of the technical interview

---

## Deliverables

Your submission should include:

- A **Git repo** (fork this one or create your own **but don't make it public**) containing:
  - `README.md` – how to run locally & with Docker, assumptions, trade-offs
  - `docker-compose.yml` – orchestrates all services (MQTT broker, DB, producer, ingestion, transformation, sink, notebook)
  - `producer/` – service that publishes test rig data to MQTT
  - `ingestion/` – service that subscribes to MQTT and ingests messages
  - `transformation/` – service that transforms vertical → horizontal format
  - `sink/` – service that writes transformed data to the database
  - `notebooks/` – a notebook showing queries & at least one visualization
  - `AI.md` – a brief log of how AI tools were used (prompts, results, edits, mistakes)

---

## Data In/Out Specification

### MQTT Topics

- Measurements: `rigs/<rig_id>/measurements/<sensor_id>`

### Message Formats (JSON)
This is example schema but feel free to change it.

**Vertical measurement (raw)**
```json
{
  "timestamp": "2025-10-03T10:15:42.315Z",
  "value": 37.2
}
```

Multiple messages arrive for the same timestamp, each containing one parameter measurement.

### Horizontal Format (Target)

Your pipeline should transform these vertical messages into horizontal rows:

**Example horizontal row in database:**

| rig_id | timestamp                | temp_inlet | temp_outlet | pressure | flow_rate | voltage | current |
|--------|--------------------------|------------|-------------|----------|-----------|---------|---------|
| RIG-42 | 2025-10-03T10:15:42.315Z |       37.2 |        42.1 |      2.5 |      45.3 |   230.1 |     2.3 |

Each row represents all measurements for a given `(rig_id, timestamp)` combination.

---

## Architecture
This is example architecture but don't feel obliged to it. 

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌───────────────┐    ┌──────────┐
│  Producer   │───▶│ MQTT Broker  │───▶│  Ingestion  │───▶│Transformation │───▶│   Sink   │
│  Service    │    │              │    │   Service   │    │   Service     │    │ Service  │
└─────────────┘    └──────────────┘    └─────────────┘    └───────────────┘    └──────────┘
                                                                                       │
                                                                                       ▼
                                                                               ┌──────────────┐
                                                                               │   Database   │
                                                                               └──────────────┘
                                                                                       │
                                                                                       ▼
                                                                               ┌──────────────┐
                                                                               │   Notebook   │
                                                                               │   (viz)      │
                                                                               └──────────────┘
```

**Services:**
- **Producer**: Generates and publishes test rig measurements to MQTT topics
- **Ingestion**: Subscribes to MQTT topics and ingests raw vertical messages
- **Transformation**: Buffers messages and transforms vertical → horizontal format
- **Sink**: Writes horizontal data to database
- **Database**: Stores normalized horizontal data
- **Notebook**: Queries and visualizes the data

---

## Key Challenges

### 1. Vertical → Horizontal Transformation

Messages arrive one parameter at a time. You need to:
- Group messages by `(rig_id, timestamp)`
- Wait for "enough" parameters before writing a row
- Handle late-arriving data

**Considerations:**
- How long do you wait? (windowing strategy)
- What if some parameters never arrive?
- How do you handle missing or NULL values?

### 2. Production-Ready Patterns

Consider:
- Error handling and retries
- Graceful shutdown
- Monitoring/logging
- Testing strategy
- State handling

---

## Evaluation Criteria

Your submission will be evaluated on:

1. **Functionality** 
   - Does the pipeline work end-to-end?
   - Does it handle the vertical→horizontal transformation correctly?
   - Are edge cases handled (late data, missing parameters)?

2. **Code Quality** 
   - Clean, readable code
   - Proper error handling
   - Logical structure and separation of concerns

3. **Architecture & Design** 
   - Appropriate choice of tools/technologies
   - Clear explanation of trade-offs
   - Scalability considerations

4. **AI Usage** 
   - Effective use of AI tools
   - Honest reflection on what worked/didn't work
   - Evidence of iteration and learning

---

## Getting Started

### Run Local MQTT Broker

```bash
docker run -d -p 1883:1883 eclipse-mosquitto:2.0
```

### Create a Producer Service

Build a producer service that simulates realistic test rig data and publishes vertical messages to MQTT.

---

## Submission Instructions

1. Fork this repository (or create a new one but *don't make it public*)
2. Implement your solution
3. Document your AI usage in `AI.md`
4. Update this README with:
   - How to run your solution
   - Key design decisions
   - Trade-offs and limitations
5. Submit a zip with your repository

---

## Tips

- **Start simple**: Get a basic pipeline working first, then iterate
- **Use AI effectively**: Document your prompts, iterations, and learnings
- **Focus on trade-offs**: We care more about your reasoning than perfect solutions
- **Ask questions**: If requirements are unclear, use our community slack and ask (direct message to Tomas Neubauer)
- **Have fun**: This is your chance to showcase how you think and build!

---

## Suggested Tech Stack

Feel free to use any tools you're comfortable with. Here are some suggestions:

**MQTT Client:**
- Python: `paho-mqtt`

**Database:**
- InfluxDB (time-series optimized)
- PostgreSQL
- DuckDB (embedded, column-oriented)
- SQLite (simple, file-based)

**Visualization:**
- Jupyter Notebook
- Marimo


**Containerization:**
- Docker Compose (highly recommended)

---

## Time Expectation

This challenge should take approximately **3-4 hours** for a complete solution. We value quality over quantity—a well-reasoned minimal solution is better than an over-engineered complex one. 

---

## Questions?

If you have questions about the challenge, please reach out using our community slack (https://join.slack.com/t/stream-processing/shared_invite/zt-3fqoo39x1-BtFT_86sK3RRWgFUZkPFPg) and send direct message to Tomas Neubauer.

Good luck! 🚀
