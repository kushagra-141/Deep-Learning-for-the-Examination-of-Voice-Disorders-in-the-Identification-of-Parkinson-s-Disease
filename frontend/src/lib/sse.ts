/**
 * SSE parser for `fetch`-based streams.
 *
 * The native `EventSource` is GET-only, so the chat client uses `fetch` with
 * a streaming body reader instead. This module turns the raw byte stream
 * into a sequence of parsed event objects, handling:
 *
 * - chunks that split mid-event (lines may arrive across multiple reads)
 * - heartbeat / comment lines (lines starting with `:`)
 * - explicit `event:` names and JSON `data:` payloads
 * - aborts via the standard `AbortController` (caller responsibility)
 */

export interface ParsedSseEvent<T> {
  /** SSE `event:` field; defaults to `"message"` when absent. */
  event: string;
  /** Parsed JSON payload from the `data:` field, or `null` if it failed to parse. */
  data: T | null;
  /** Raw `data:` text in case the caller wants the unparsed form. */
  raw: string;
}

/**
 * Async-iterate parsed SSE events from a `fetch` response body.
 *
 * Throws if `response.body` is null. Cancellation: pass a signal via the
 * underlying `fetch` and abort it; the iteration ends naturally.
 */
export async function* parseSseStream<T>(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<ParsedSseEvent<T>, void, unknown> {
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let currentEvent = "message";
  let dataBuffer = "";

  const flush = (): ParsedSseEvent<T> | null => {
    if (!dataBuffer && currentEvent === "message") return null;
    const raw = dataBuffer;
    let parsed: T | null = null;
    if (raw) {
      try {
        parsed = JSON.parse(raw) as T;
      } catch {
        parsed = null;
      }
    }
    const result: ParsedSseEvent<T> = { event: currentEvent, data: parsed, raw };
    currentEvent = "message";
    dataBuffer = "";
    return result;
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Events are delimited by a blank line (\n\n). Process whole events;
      // keep any trailing partial event in `buffer`.
      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1 || (sepIndex = buffer.indexOf("\r\n\r\n")) !== -1) {
        const block = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + (buffer[sepIndex + 1] === "\n" ? 2 : 4));

        const lines = block.split(/\r?\n/);
        for (const line of lines) {
          if (line.length === 0) continue;
          if (line.startsWith(":")) continue; // heartbeat / comment
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
            continue;
          }
          if (line.startsWith("data:")) {
            const piece = line.slice(5).replace(/^ /, "");
            dataBuffer = dataBuffer ? `${dataBuffer}\n${piece}` : piece;
            continue;
          }
          // id: / retry: are accepted-but-ignored per the spec.
        }
        const flushed = flush();
        if (flushed) yield flushed;
      }
    }

    // Flush trailing event without a blank-line terminator.
    if (buffer.trim().length > 0) {
      const lines = buffer.split(/\r?\n/);
      for (const line of lines) {
        if (line.startsWith("event:")) currentEvent = line.slice(6).trim();
        else if (line.startsWith("data:")) {
          const piece = line.slice(5).replace(/^ /, "");
          dataBuffer = dataBuffer ? `${dataBuffer}\n${piece}` : piece;
        }
      }
      const flushed = flush();
      if (flushed) yield flushed;
    }
  } finally {
    try {
      await reader.cancel();
    } catch {
      /* already closed */
    }
  }
}
