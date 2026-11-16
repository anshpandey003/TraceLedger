
const API_BASE_URL = "http://127.0.0.1:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`,
    );
  }

  return response.json() as Promise<T>;
}

export async function apiPost<T, B>(
  path: string,
  body: B,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      `API request failed: ${response.status} ${response.statusText}${
        message ? ` — ${message}` : ""
      }`,
    );
  }

  return response.json() as Promise<T>;
}
