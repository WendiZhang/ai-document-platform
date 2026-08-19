export type Document = {
  id: string;
  owner_id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  character_count: number;
  start_character: number;
  end_character: number;
  created_at: string;
};

export type DocumentDeleteResponse = {
  message: string;
  document_id: string;
};

export type DocumentProcessResponse = {
  message: string;
  document_id: string;
  status: string;
  character_count: number;
};

export type DocumentChunkingResponse = {
  message: string;
  document_id: string;
  status: string;
  chunk_count: number;
};

export type DocumentPrepareResponse = {
  message: string;
  document_id: string;
  status: string;
};