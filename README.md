# The Lenny Growth Assistant

A full-stack AI assistant for exploring product management, startup, and growth lessons from Lenny's Podcast transcripts.

## Features

- React and Vite frontend
- FastAPI backend
- Local Ollama inference through Pi Coding Agent
- PostgreSQL conversation and message persistence
- Transcript retrieval and source references
- Conversation history and reopening
- Markdown and HTML artifact creation
- Sandboxed HTML preview and artifact download

## Technology Stack

- Frontend: React, Vite, JavaScript
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: PostgreSQL
- Local model: Ollama with `llama3.2:latest`
- Agent integration: Pi Coding Agent

## Local Setup

### Backend

Open PowerShell:

```powershell
cd F:\project\lenny-growth-assistant\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Frontend

Open a second PowerShell terminal:

```powershell
cd F:\project\lenny-growth-assistant\frontend
npm run dev
```

- Frontend: http://localhost:5173
- API documentation: http://127.0.0.1:8000/docs

Configure `backend/.env` with your actual database URL and model settings. Never commit credentials.

## Knowledge Data

The development database contains 3,842 transcript chunks. Follow the supplied dataset license and do not redistribute raw transcript files unless permitted.

## Verification

Verified locally:
- Chat responses and database persistence
- Conversation history after browser refresh
- Markdown artifact creation and preview
- HTML artifact creation and sandboxed preview

Cloud-provider integration and automated test results require separate verification.

## Security

Keep credentials outside source control. Verify generated claims against cited transcripts. HTML artifacts are displayed in a sandboxed iframe.