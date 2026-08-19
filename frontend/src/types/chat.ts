export type ChatSession = {
  id: string;
  owner_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatSource = {
  document_id: string;
  document_name: string;
  chunk_id: string;
  chunk_index: number;
  content: string;
  score: number;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[] | null;
  created_at: string;
};

export type ChatRequest = {
  question: string;
  document_id?: string | null;
};

export type ChatResponse = {
  session_id: string;
  answer: string;
  sources: ChatSource[];
};