/**
 * Backend chat schemas, mirrored on the frontend.
 *
 * These are NOT auto-generated from OpenAPI because OpenAPI's SSE coverage is
 * weak. Keep this file in lockstep with `backend/app/schemas/chat.py`.
 */

export type ChatFeature = "explainer" | "help";

export interface ChatRequestBody {
  session_id?: string;
  prediction_id?: string;
  message: string;
  feature: ChatFeature;
}

export type ChatChunkType = "delta" | "tool" | "done" | "error";

export interface ChatChunkOut {
  type: ChatChunkType;
  delta_text?: string;
  tool_name?: string;
  tool_status?: "called" | "ok" | "error";
  tool_detail?: string | null;
  cached?: boolean;
  error?: string;
  session_id?: string;
  request_id?: string;
}

export interface ChatReadyEvent {
  session_id: string;
  request_id: string;
}

export type ChatRole = "user" | "assistant";

export interface ToolBadge {
  name: string;
  status: "called" | "ok" | "error";
  detail?: string | null;
}

export interface UiMessage {
  id: string;
  role: ChatRole;
  content: string;
  tools?: ToolBadge[];
  /** True while tokens are still streaming into this bubble. */
  streaming?: boolean;
}
