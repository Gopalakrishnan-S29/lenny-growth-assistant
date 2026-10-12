
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || `Request failed with status ${response.status}`
    );
  }

  return data;
}

export async function sendChatMessage(message, sessionId = null) {
  return request("/api", {
    method: "POST",
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
    }),
  });
}

export async function getSessions() {
  return request("/api/sessions");
}

export async function getSession(sessionId) {
  return request(`/api/sessions/${sessionId}`);
}

export async function deleteSession(sessionId) {
  return request(`/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
