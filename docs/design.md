# Design Document

## 1. Design Principles

- Focus the main experience on chat and growth learning.
- Keep conversation history accessible in the sidebar.
- Use a dark interface with purple accents.
- Maintain readable text and control contrast.
- Separate source references from assistant responses.
- Provide a dedicated artifact workspace.

## 2. Main Screens

### AI Assistant

Displays user messages, assistant responses, available transcript references, and the message composer.

### Conversations

Lists saved sessions and supports reopening or deleting conversations.

### Knowledge Sources

A sidebar navigation entry for the transcript collection. A standalone source-browsing screen requires separate verification.

### Artifacts

Includes a title field, format selector, content editor, save action, saved-artifact list, preview, and download action.

## 3. Artifact Interaction

- Markdown content renders as formatted text.
- HTML content renders in a sandboxed iframe.
- Users can select saved artifacts.
- Users can download artifact content.

## 4. Visual Style

- Dark backgrounds and panel surfaces
- Purple accent color for active navigation and primary actions
- High-contrast controls
- Scrollable content areas
- Source references displayed separately from the main answer

## 5. Limitations

The artifact form currently uses inline styling. Comprehensive accessibility and responsive-device testing require further review.