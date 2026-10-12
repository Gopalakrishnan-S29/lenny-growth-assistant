
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  sendChatMessage,
  getSessions,
  getSession,
  deleteSession,
} from "./services/api";
import "./App.css";
import ArtifactViewer from "./components/ArtifactViewer";

const suggestions = [
  {
    title: "Find product-market fit",
    description: "Learn how startups validate demand.",
    prompt: "How can an early-stage startup find product-market fit?",
  },
  {
    title: "Build a growth strategy",
    description: "Identify practical growth opportunities.",
    prompt: "Create a practical growth strategy for a SaaS startup.",
  },
  {
    title: "Improve onboarding",
    description: "Help new users reach their first value.",
    prompt: "How can I improve activation and onboarding for a SaaS product?",
  },
];

function normalizeSessions(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.value)) return data.value;
  if (Array.isArray(data?.sessions)) return data.sessions;
  return [];
}

function getMessageSources(item) {
  const metadata = item.message_metadata ?? item.metadata ?? {};
  return Array.isArray(metadata.sources) ? metadata.sources : [];
}

export default function App() {
  const [activeView, setActiveView] = useState("chat");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [openingSession, setOpeningSession] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState(null);
  const [error, setError] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState({});

  const refreshSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(normalizeSessions(data));
    } catch (err) {
      setError(`Could not load conversation history: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function loadInitialSessions() {
      try {
        const data = await getSessions();
        if (active) setSessions(normalizeSessions(data));
      } catch (err) {
        if (active) {
          setError(`Could not load conversation history: ${err.message}`);
        }
      } finally {
        if (active) setLoadingHistory(false);
      }
    }

    loadInitialSessions();

    return () => {
      active = false;
    };
  }, []);

  async function handleSend(event, suppliedMessage) {
    event?.preventDefault();

    const text = (suppliedMessage ?? message).trim();
    if (!text || loading || openingSession) return;

    setError("");
    setMessage("");
    setLoading(true);

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);

    try {
      const result = await sendChatMessage(text, sessionId);

      setSessionId(result.session_id);

      setMessages((previous) => [
        ...previous,
        {
          id: result.assistant_message_id,
          role: "assistant",
          content: result.answer,
          sources: result.sources || [],
          grounded: result.grounded_in_transcripts,
          provider: result.provider,
          model: result.model,
        },
      ]);

      await refreshSessions();
    } catch (err) {
      setError(err.message || "Could not contact the assistant.");
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() {
    if (loading || openingSession) return;

    setMessages([]);
    setSessionId(null);
    setMessage("");
    setError("");
    setSourcesOpen({});
  }

  async function openConversation(id) {
    if (loading || openingSession || id === sessionId) return;

    setOpeningSession(true);
    setError("");

    try {
      const conversation = await getSession(id);

      const savedMessages = (conversation.messages || []).map((item) => ({
        id: item.id,
        role: item.role,
        content: item.content,
        sources: getMessageSources(item),
        model: item.message_metadata?.model ?? item.metadata?.model,
        grounded:
          item.message_metadata?.grounded_in_transcripts ??
          item.metadata?.grounded_in_transcripts,
      }));

      setSessionId(conversation.id);
      setMessages(savedMessages);
      setMessage("");
      setSourcesOpen({});
    } catch (err) {
      setError(err.message || "Could not open this conversation.");
    } finally {
      setOpeningSession(false);
    }
  }

  async function handleDeleteSession(event, session) {
    event.stopPropagation();

    if (loading || openingSession || deletingSessionId) return;

    const confirmed = window.confirm(
      `Delete "${session.title || "Untitled conversation"}"? This cannot be undone.`
    );

    if (!confirmed) return;

    setDeletingSessionId(session.id);
    setError("");

    try {
      await deleteSession(session.id);

      if (sessionId === session.id) {
        setSessionId(null);
        setMessages([]);
        setMessage("");
        setSourcesOpen({});
      }

      await refreshSessions();
    } catch (err) {
      setError(err.message || "Could not delete this conversation.");
    } finally {
      setDeletingSessionId(null);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">L</div>
          <div>
            <h1>Lenny AI</h1>
            <p>Growth Assistant</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewChat}
          disabled={loading || openingSession}
        >
          <span>＋</span> New conversation
        </button>

        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav">
          <button className={`nav-item ${activeView === "chat" ? "active" : ""}`} type="button" onClick={() => setActiveView("chat")}>
            ✳ &nbsp; AI Assistant
          </button>
          <button
            className="nav-item"
            type="button"
            onClick={() =>
              document.getElementById("conversation-history")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
              })
            }
          >
            ▤ &nbsp; Conversations
          </button>
          <button className="nav-item" type="button">
            ◈ &nbsp; Knowledge sources
          </button>
                    <button
            className={`nav-item ${activeView === "artifacts" ? "active" : ""}`}
            type="button"
            onClick={() => setActiveView("artifacts")}
          >
            ? &nbsp; Artifacts
          </button>
        </nav>

        <div className="history-section" id="conversation-history">
          <div className="history-heading">
            <span className="sidebar-label">RECENT CONVERSATIONS</span>
            <span className="history-count">{sessions.length}</span>
          </div>

          {loadingHistory ? (
            <p className="history-message">Loading conversations…</p>
          ) : sessions.length === 0 ? (
            <p className="history-message">No saved conversations yet.</p>
          ) : (
            <div className="session-list">
              {sessions.map((session) => (
                <div
                  className={`session-item ${
                    session.id === sessionId ? "selected" : ""
                  }`}
                  key={session.id}
                >
                  <button
                    className="session-open"
                    type="button"
                    onClick={() => openConversation(session.id)}
                    disabled={loading || openingSession}
                    title={session.title || "Untitled conversation"}
                  >
                    <span className="session-title">
                      {session.title || "Untitled conversation"}
                    </span>
                    <span className="session-date">
                      {session.updated_at
                        ? new Date(session.updated_at).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric" }
                          )
                        : ""}
                    </span>
                  </button>

                  <button
                    className="session-delete"
                    type="button"
                    title="Delete conversation"
                    aria-label={`Delete ${session.title || "conversation"}`}
                    disabled={
                      loading ||
                      openingSession ||
                      deletingSessionId === session.id
                    }
                    onClick={(event) =>
                      handleDeleteSession(event, session)
                    }
                  >
                    {deletingSessionId === session.id ? "…" : "×"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="model-status">
            <span className="status-dot" />
            <div>
              <strong>Local AI</strong>
              <small>Pi Agent · Ollama</small>
            </div>
          </div>
          <p className="sidebar-footer">Built for product people.</p>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>AI Assistant</strong>
          </div>
          <div className="topbar-badge">
            <span className="status-dot" />
            Local model
          </div>
        </header>

        {activeView === "artifacts" ? (
          <ArtifactViewer sessionId={sessionId} />
        ) : (
        <section
          className={`chat-content ${
            messages.length ? "has-messages" : ""
          }`}
        >
          {openingSession && (
            <div className="history-loading-banner">
              Opening conversation…
            </div>
          )}

          {messages.length === 0 ? (
            <section className="welcome-section">
              <div className="eyebrow">
                <span className="sparkle">✳</span>
                YOUR PRODUCT &amp; GROWTH PARTNER
              </div>

              <h2>
                Think better.
                <br />
                <span>Build what matters.</span>
              </h2>

              <p className="welcome-description">
                Explore product and growth lessons from Lenny&apos;s Podcast.
                Ask a question, discover insights, and turn ideas into action.
              </p>

              <div className="suggestion-grid">
                {suggestions.map((item) => (
                  <button
                    className="suggestion-card"
                    key={item.title}
                    onClick={() => handleSend(null, item.prompt)}
                    disabled={loading || openingSession}
                  >
                    <span className="suggestion-icon">↗</span>
                    <strong>{item.title}</strong>
                    <span>{item.description}</span>
                  </button>
                ))}
              </div>

              <div className="conversation-placeholder">
                <div className="placeholder-icon">✳</div>
                <div>
                  <strong>Your next breakthrough starts here.</strong>
                  <p>
                    Ask a question to explore podcast insights and practical
                    advice.
                  </p>
                </div>
              </div>
            </section>
          ) : (
            <section className="message-list" aria-live="polite">
              {messages.map((item, index) => (
                <article
                  className={`message-row ${item.role}`}
                  key={item.id || `${item.role}-${index}`}
                >
                  <div className="message-avatar">
                    {item.role === "user" ? "Y" : "L"}
                  </div>

                  <div className="message-body">
                    <div className="message-heading">
                      <strong>
                        {item.role === "user" ? "You" : "Lenny AI"}
                      </strong>
                      {item.role === "assistant" && item.model && (
                        <span className="message-model">{item.model}</span>
                      )}
                    </div>

                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {item.content}
                      </ReactMarkdown>
                    </div>

                    {item.role === "assistant" &&
                      item.sources?.length > 0 && (
                        <div className="sources-section">
                          <button
                            className="sources-toggle"
                            onClick={() =>
                              setSourcesOpen((previous) => ({
                                ...previous,
                                [item.id || index]: !previous[
                                  item.id || index
                                ],
                              }))
                            }
                          >
                            ◈ {item.sources.length} transcript sources
                            <span>
                              {sourcesOpen[item.id || index] ? "−" : "+"}
                            </span>
                          </button>

                          {sourcesOpen[item.id || index] && (
                            <div className="source-list">
                              {item.sources.map((source, sourceIndex) => (
                                <article
                                  className="source-card"
                                  key={
                                    source.source_id ||
                                    `${item.id || index}-${sourceIndex}`
                                  }
                                >
                                  <div className="source-card-heading">
                                    <span className="source-id">
                                      [{source.source_id || sourceIndex + 1}]
                                    </span>
                                    <span className="source-score">
                                      Score: {source.score ?? "N/A"}
                                    </span>
                                  </div>
                                  <strong>
                                    {source.episode_title || "Podcast source"}
                                  </strong>
                                  <p>
                                    {source.guest || "Guest unavailable"}
                                    {source.date ? ` · ${source.date}` : ""}
                                  </p>
                                  {source.excerpt && (
                                    <blockquote>{source.excerpt}</blockquote>
                                  )}
                                  {source.source_filename && (
                                    <small>{source.source_filename}</small>
                                  )}
                                </article>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                  </div>
                </article>
              ))}

              {loading && (
                <div className="loading-indicator">
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                  <span>Thinking and searching transcripts…</span>
                </div>
              )}

              <div className="chat-bottom-space" />
            </section>
          )}

          {error && (
            <div className="error-banner" role="alert">
              <strong>Notice.</strong> {error}
              <button type="button" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          )}

          <form className="composer" onSubmit={handleSend}>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  handleSend(event);
                }
              }}
              placeholder="Ask about product, growth, startups, or leadership..."
              rows={3}
              disabled={loading || openingSession}
              aria-label="Your message"
            />

            <div className="composer-bottom">
              <span>Enter to send · Shift + Enter for a new line</span>
              <button
                type="submit"
                disabled={!message.trim() || loading || openingSession}
              >
                {loading ? "Thinking…" : "Send message"} <span>↑</span>
              </button>
            </div>
          </form>

          <footer className="main-footer">
            AI can make mistakes. Verify important information against its
            sources.
          </footer>
        </section>
        )}
      </main>
    </div>
  );
}
