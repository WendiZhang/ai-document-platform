import { useQuery } from "@tanstack/react-query";

import {
  getDocument,
  getDocumentChunks,
  getDocuments,
} from "../api/documents";
import type { Document } from "../types/document";


const ACTIVE_DOCUMENT_STATUSES = new Set([
  "queued",
  "processing",
  "chunking",
  "embedding",
]);


export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,

    refetchInterval: (query) => {
      const documents =
        query.state.data as Document[] | undefined;

      const hasActiveDocument =
        documents?.some((document) =>
          ACTIVE_DOCUMENT_STATUSES.has(
            document.status,
          ),
        ) ?? false;

      return hasActiveDocument
        ? 2000
        : false;
    },
  });
}


export function useDocument(
  documentId: string | undefined,
) {
  return useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId!),
    enabled: Boolean(documentId),

    refetchInterval: (query) => {
      const document =
        query.state.data as Document | undefined;

      if (
        document &&
        ACTIVE_DOCUMENT_STATUSES.has(
          document.status,
        )
      ) {
        return 2000;
      }

      return false;
    },
  });
}


export function useDocumentChunks(
  documentId: string | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey: [
      "document-chunks",
      documentId,
    ],
    queryFn: () =>
      getDocumentChunks(documentId!),
    enabled:
      Boolean(documentId) &&
      enabled,
  });
}