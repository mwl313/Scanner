export async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  let data = null;
  let rawText = '';

  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    rawText = await response.text();
  }

  if (!response.ok) {
    const fallback = rawText
      ? rawText.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
      : '';
    const message =
      data?.error?.message ||
      fallback ||
      `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}
