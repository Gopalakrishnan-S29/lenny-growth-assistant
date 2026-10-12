# System Architecture

## 1. Overview

The system consists of a React/Vite frontend, FastAPI backend, PostgreSQL database, Pi Coding Agent integration, Ollama model runtime, and transcript retrieval component.

## 2. Chat Flow

1. The user submits a question in the browser.
2. The frontend sends a request to FastAPI.
3. The backend retrieves relevant transcript chunks.
4. The configured agent and model generate a response.
5. The frontend displays the response and available source references.
6. Sessions and messages are persisted in PostgreSQL.

## 3. Components

### Frontend

Responsible for chat, conversation history, source references, artifact creation, previews, and downloads.

### FastAPI Backend

Provides API endpoints for health, chat, sessions, and artifacts.

### Agent and Model

The Pi Coding Agent adapter invokes the configured agent. Ollama provides local model inference.

### Retrieval

Retrieves relevant transcript chunks and available episode metadata.

### PostgreSQL

Stores chat sessions, messages, artifacts, and transcript chunks.

## 4. Artifact API

- `POST /api/artifacts` — create an artifact.
- `GET /api/artifacts` — list artifacts.
- `GET /api/artifacts/{artifact_id}` — retrieve an artifact.

## 5. Database Entities

- `chat_sessions`: conversation identifiers and timestamps
- `messages`: user and assistant messages
- `artifacts`: saved Markdown or HTML content
- `transcript_chunks`: transcript passages and episode metadata

## 6. Security

Keep database credentials and API keys outside source control. Validate API inputs and use ORM operations. Render HTML artifacts in a sandboxed iframe. Add authentication and authorization before multi-user deployment.

## 7. Verification Status

Verified locally:
- Chat messages persist.
- Conversation history survives browser refresh.
- Transcript chunks are present in PostgreSQL.
- Markdown artifact creation and preview work.
- HTML artifact creation and sandboxed preview work.

Cloud-provider integration, automated test results, and production deployment require separate verification.