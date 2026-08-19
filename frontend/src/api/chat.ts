import apiClient from "./client";

import type {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSource,
} from "../types/chat";

export async function createChatSession(): Promise<ChatSession> {
  const response = await apiClient.post<ChatSession>(
    "/chat/sessions",
    {
      title: null,
    },
  );

  return response.data;
}

export async function getChatSessions(): Promise<ChatSession[]> {
  const response = await apiClient.get<ChatSession[]>(
    "/chat/sessions",
  );

  return response.data;
}

export async function getChatMessages(
  sessionId: string,
): Promise<ChatMessage[]> {
  const response = await apiClient.get<ChatMessage[]>(
    `/chat/sessions/${sessionId}/messages`,
  );

  return response.data;
}

export async function askDocuments(
  sessionId: string,
  data: ChatRequest,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    `/chat/sessions/${sessionId}/messages`,
    data,
  );

  return response.data;
}

export async function deleteChatSession(
  sessionId: string,
): Promise<void> {
  await apiClient.delete(
    `/chat/sessions/${sessionId}`,
  );
}

export type StreamEvent =
  | {
      type: "delta";
      content: string;
    }
  | {
      type: "sources";
      sources: ChatSource[];
    }
  | {
      type: "done";
    }
  | {
      type: "error";
      message: string;
    };


export async function streamChat(
  sessionId: string,
  data: ChatRequest,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const token =
    localStorage.getItem("access_token");

  if (!token) {
    throw new Error(
      "You are not authenticated.",
    );
  }

  const baseUrl =
    import.meta.env.VITE_API_BASE_URL;

  const response = await fetch(
    `${baseUrl}/chat/sessions/${sessionId}/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorData?.detail ??
        "The AI request failed.",
    );
  }

  if (!response.body) {
    throw new Error(
      "Streaming is not supported.",
    );
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let buffer = "";

  function processLine(line: string) {
    if (!line.trim()) {
      return;
    }

    const event =
      JSON.parse(line) as StreamEvent;

    onEvent(event);

    if (event.type === "error") {
      throw new Error(event.message);
    }
  }

  while (true) {
    const {
      value,
      done,
    } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(
      value,
      {
        stream: true,
      },
    );

    const lines =
      buffer.split("\n");

    buffer =
      lines.pop() ?? "";

    for (const line of lines) {
      processLine(line);
    }
  }

  buffer += decoder.decode();

  if (buffer.trim()) {
    processLine(buffer);
  }
}