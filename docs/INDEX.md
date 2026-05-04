# Documentation Index

This folder provides a concise, production-oriented overview of the project.

## Contents

- ARCHITECTURE.md: system flow and component roles
- API.md: REST endpoints for the optional FastAPI service

## Quick Start

- Install: `pip install -r requirements.txt`
- Run demo: `python -m multi_agent_moderation.examples.run_demo`
- Optional service: `uvicorn multi_agent_moderation.service.app:app --host 0.0.0.0 --port 8000`

## Configuration

Use `config.example.yaml` with `MAM_CONFIG_PATH` and `MAM_PROFILE`. See `.env.example` for environment variables.
