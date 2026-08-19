import apiClient from "./client";

import type {
  Document,
  DocumentChunk,
  DocumentChunkingResponse,
  DocumentDeleteResponse,
  DocumentProcessResponse,
  DocumentPrepareResponse,
} from "../types/document";

export async function getDocuments(): Promise<Document[]> {
  const response = await apiClient.get<Document[]>(
    "/documents",
  );

  return response.data;
}

export async function getDocument(
  documentId: string,
): Promise<Document> {
  const response = await apiClient.get<Document>(
    `/documents/${documentId}`,
  );

  return response.data;
}

export async function getDocumentChunks(
  documentId: string,
): Promise<DocumentChunk[]> {
  const response = await apiClient.get<DocumentChunk[]>(
    `/documents/${documentId}/chunks`,
  );

  return response.data;
}

export async function uploadDocument(
  file: File,
): Promise<Document> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await apiClient.post<Document>(
    "/documents/upload",
    formData,
  );

  return response.data;
}

export async function deleteDocument(
  documentId: string,
): Promise<DocumentDeleteResponse> {
  const response =
    await apiClient.delete<DocumentDeleteResponse>(
      `/documents/${documentId}`,
    );

  return response.data;
}

export async function processDocument(
  documentId: string,
): Promise<DocumentProcessResponse> {
  const response =
    await apiClient.post<DocumentProcessResponse>(
      `/documents/${documentId}/process`,
    );

  return response.data;
}

export async function createDocumentChunks(
  documentId: string,
): Promise<DocumentChunkingResponse> {
  const response =
    await apiClient.post<DocumentChunkingResponse>(
      `/documents/${documentId}/chunks`,
    );

  return response.data;
}

export async function prepareDocument(
  documentId: string,
): Promise<DocumentPrepareResponse> {
  const response =
    await apiClient.post<DocumentPrepareResponse>(
      `/documents/${documentId}/prepare`,
    );

  return response.data;
}