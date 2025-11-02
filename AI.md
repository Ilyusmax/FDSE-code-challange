# AI.md – AI Assistance Log

This file briefly documents the use of AI tools (ChatGPT GPT-5) in the FDSE Code Challenge project.

## Prompts and Guidance
- Asked AI to review project code structure (producer, ingester, transformer, sink, Docker Compose).  
- Requested recommendations on data flow architecture and modular design.  
- Requested help generating `README.md` with setup instructions, architecture diagram, and local run instructions.  
- Requested assistance in creating a working `docker-compose.yml` for all services (producer, ingester, transformer, sink, InfluxDB).

## Results from AI
- Produced structured README content including architecture, project structure, environment variables, and local setup instructions.  
- Suggested timestamp handling improvements for InfluxDB sink.  
- Recommended Docker Compose networking and service dependencies.  
- Suggested examples for raw and normalized data messages.  
- Helped create a complete `docker-compose.yml` setup for local development and testing.

## Edits and Adjustments
- Manual edits applied to timestamp formatting in the sink.  
- Adjusted README sections to include Local Setup and Run instructions.  
- Corrected minor wording and formatting for Markdown readability.  
- Minor adjustments applied to Docker Compose service names, ports, and environment variables to match actual project setup.

## Mistakes / Limitations
- Initial AI suggestions lacked detailed local run instructions — user manually added step-by-step instructions.  
- Minor adjustments required for consistency with actual Docker service names and environment variables.

---

This log is for transparency and acknowledgment of AI-assisted development.
