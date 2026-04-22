/**
 * SSE streaming client for the Deal agent.
 *
 * Calls POST /api/v1/chats/{chatId}/stream and yields parsed SSE events
 * via a callback interface so the caller can update the UI incrementally.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface StreamCallbacks {
  onSessionInfo: (data: { conversation_id: string; session_id: string }) => void;
  onStatus: (message: string) => void;
  onDelta: (token: string) => void;
  onDone: (metadata: Record<string, unknown>) => void;
  onError: (message: string) => void;
}

export interface StreamMessageParams {
  chatId: string;
  content: string;
  analyst_type: string;
  scenario_type: string;
  session_id?: string;
  session_title?: string;
}

/**
 * Opens an SSE stream to the Deal agent and dispatches events via callbacks.
 * Returns an AbortController so the caller can cancel the stream.
 */
export function streamMessage(
  params: StreamMessageParams,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  const url = `${API_BASE_URL}/chats/${params.chatId}/stream`;
  const body = JSON.stringify({
    content: params.content,
    analyst_type: params.analyst_type,
    scenario_type: params.scenario_type,
    session_id: params.session_id ?? null,
    session_title: params.session_title ?? null,
  });

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError(`Server error: ${response.status}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Split on newlines OR on consecutive "data: " boundaries
        const lines = buffer.split('\n');
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          // Handle case where multiple data: events are on the same line
          // e.g., 'data: {"type":"a"}data: {"type":"b"}'
          const dataSegments = line.split('data: ').filter(Boolean);
          for (const segment of dataSegments) {
            const jsonStr = segment.trim();
            if (!jsonStr) continue;
            try {
              const event = JSON.parse(jsonStr) as Record<string, unknown>;
            const type = event.type as string;
            switch (type) {
              case 'session_info':
                callbacks.onSessionInfo(event as { conversation_id: string; session_id: string });
                break;
              case 'status':
                callbacks.onStatus(event.content as string);
                break;
              case 'delta':
                callbacks.onDelta(event.content as string);
                break;
              case 'done':
                // Skip raw done — wait for done_enriched with doc names
                break;
              case 'done_enriched':
                callbacks.onDone(event.metadata as Record<string, unknown>);
                break;
              case 'error':
                callbacks.onError(event.content as string);
                break;
            }
          } catch {
              // skip malformed JSON
            }
          }
        }
      }
    })
    .catch((err: Error) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err.message);
      }
    });

  return controller;
}
