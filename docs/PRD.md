# Product Requirements Document

## 1. Overview

The Lenny Growth Assistant helps users explore startup, product management, and growth lessons from podcast transcripts.

## 2. Goals

- Answer questions using transcript content.
- Provide available source references.
- Persist conversations and messages.
- Reopen previous conversations.
- Create, save, preview, and download Markdown and HTML artifacts.

## 3. Target Users

- Startup founders
- Product managers
- Growth practitioners
- Students and researchers

## 4. Functional Requirements

1. Users can submit questions and view assistant responses.
2. The backend retrieves relevant transcript chunks.
3. Available source metadata is displayed with responses.
4. Sessions and messages persist in PostgreSQL.
5. Users can reopen saved conversations.
6. Users can create artifacts linked to a conversation.
7. Markdown and HTML artifacts have in-app previews.
8. Artifacts can be downloaded.

## 5. Non-functional Requirements

- Clear separation between frontend and backend.
- Validated API inputs.
- Credentials kept outside source control.
- Sandboxed HTML previews.
- Documented local setup.

## 6. Acceptance Criteria

- Chat responds to user questions.
- Conversation history survives refresh.
- Transcript sources are available for inspection.
- Markdown and HTML artifacts can be saved and previewed.
- Setup and verification instructions are documented.

## 7. Risks and Limitations

AI answers may be inaccurate, retrieval may return imperfect matches, and transcript licensing may restrict redistribution. Cloud-provider integration and automated test coverage must be verified independently.