import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function ArtifactViewer({ sessionId }) {
  const [artifacts, setArtifacts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [title, setTitle] = useState("Growth Strategy");
  const [type, setType] = useState("markdown");
  const [content, setContent] = useState(
    "# Growth Strategy\n\n## Goal\nFind and focus on a high-value customer segment.\n\n## Actions\n- Interview target customers.\n- Identify their most painful problem.\n- Test a focused solution.\n- Measure activation and retention.\n\n## Success metric\nTrack the percentage of users who reach the product's core value."
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadArtifacts() {
    try {
      const response = await fetch(`${API}/api/artifacts`);
      if (!response.ok) throw new Error(`Load failed (${response.status})`);
      const data = await response.json();
      setArtifacts(data);
      if (selected) {
        setSelected(data.find((item) => item.id === selected.id) || null);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadArtifacts();
  }, []);

  async function createArtifact(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (!sessionId) {
        throw new Error("Start or open a conversation before saving an artifact.");
      }

      const response = await fetch(`${API}/api/artifacts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          title,
          artifact_type: type,
          content,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Save failed (${response.status})`);

      setSelected(data);
      await loadArtifacts();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={{ padding: 28, color: "var(--text-primary, #eef2ff)", maxWidth: 1100, margin: "0 auto" }}>
      <h2>Artifacts</h2>
      <p>Create and save Markdown documents or standalone HTML previews.</p>

      {error && <p role="alert" style={{ color: "#ff9292" }}>{error}</p>}

      <form onSubmit={createArtifact} style={{ display: "grid", gap: 12, marginBottom: 28 }}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Artifact title"
          required
          maxLength={200}
          style={{ padding: 12, borderRadius: 8, background: "#1b1b27", color: "#f5f5ff", border: "1px solid #514565" }}
        />

        <select value={type} onChange={(e) => setType(e.target.value)} style={{ padding: 12, borderRadius: 8, background: "#1b1b27", color: "#f5f5ff", border: "1px solid #514565" }}>
          <option style={{ background: "#1b1b27", color: "#ffffff" }} value="markdown">Markdown document</option>
          <option style={{ background: "#1b1b27", color: "#ffffff" }} value="html">HTML page</option>
        </select>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
          rows={10}
          placeholder="Write your artifact content..."
          style={{ padding: 12, borderRadius: 8, fontFamily: "monospace", background: "#1b1b27", color: "#f5f5ff", border: "1px solid #514565" }}
        />

        <button disabled={busy || !sessionId} type="submit" style={{ padding: 12, borderRadius: 8, cursor: "pointer", background: "#7c3aed", color: "#ffffff", border: "none", fontWeight: 600 }}>
          {busy ? "Saving..." : "Save artifact"}
        </button>
        {!sessionId && <small>Open an existing conversation or start a chat before saving.</small>}
      </form>

      <h3>Saved artifacts ({artifacts.length})</h3>
      {artifacts.length === 0 && <p>No saved artifacts yet.</p>}

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
        {artifacts.map((item) => (
          <button key={item.id} onClick={() => setSelected(item)} style={{ padding: 10, borderRadius: 8, background: "#342342", color: "#ffffff", border: "1px solid #7850a0", cursor: "pointer" }}>
            {item.title}
          </button>
        ))}
      </div>

      {selected && (
        <section>
          <h3>{selected.title}</h3>
          <button onClick={() => setSelected(null)} style={{ marginBottom: 12, padding: 10, background: "#342342", color: "#ffffff", border: "1px solid #7850a0", borderRadius: 8, cursor: "pointer" }}>Close preview</button>
          {selected.artifact_type === "html" ? (
            <iframe
              title={selected.title}
              sandbox=""
              srcDoc={selected.content}
              style={{ width: "100%", height: 500, background: "white", border: "1px solid #444", borderRadius: 8 }}
            />
          ) : (
            <article style={{ background: "#111827", padding: 24, borderRadius: 8, overflowWrap: "anywhere" }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{selected.content}</ReactMarkdown>
            </article>
          )}
          <button
            onClick={() => {
              const blob = new Blob([selected.content], {
                type: selected.artifact_type === "html" ? "text/html" : "text/markdown",
              });
              const url = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = url;
              link.download = `${selected.title.replace(/[^a-z0-9-_]/gi, "_")}.${selected.artifact_type === "html" ? "html" : "md"}`;
              link.click();
              URL.revokeObjectURL(url);
            }}
            style={{ marginTop: 12, padding: 10, borderRadius: 8, background: "#342342", color: "#ffffff", border: "1px solid #7850a0", cursor: "pointer" }}
          >
            Download artifact
          </button>
        </section>
      )}
    </section>
  );
}
