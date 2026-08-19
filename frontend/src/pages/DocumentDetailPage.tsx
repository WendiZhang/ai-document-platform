import {
  ArrowLeft,
  FileText,
  Layers3,
  LoaderCircle,
  RefreshCw,
  Trash2,
  WandSparkles,
} from "lucide-react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router";
import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createDocumentChunks,
  deleteDocument,
  processDocument,
} from "../api/documents";
import DocumentStatusBadge from "../components/documents/DocumentStatusBadge";
import {
  useDocument,
  useDocumentChunks,
} from "../hooks/useDocuments";
import { formatFileSize } from "../utils/file";

export default function DocumentDetailPage() {
  const { documentId } = useParams();

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: document,
    isLoading,
    isError,
  } = useDocument(documentId);

  const shouldLoadChunks =
    document?.status === "chunked";

  const {
    data: chunks = [],
    isLoading: chunksLoading,
    isError: chunksError,
  } = useDocumentChunks(
    documentId,
    shouldLoadChunks,
  );

  const processMutation = useMutation({
    mutationFn: processDocument,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["document", documentId],
      });

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    },
  });

  const chunkMutation = useMutation({
    mutationFn: createDocumentChunks,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["document", documentId],
      });

      await queryClient.invalidateQueries({
        queryKey: ["document-chunks", documentId],
      });

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });

      navigate("/documents");
    },
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-2 text-slate-500">
          <LoaderCircle
            size={20}
            className="animate-spin"
          />

          Loading document...
        </div>
      </div>
    );
  }

  if (isError || !document) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-10">
        <Link
          to="/documents"
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600"
        >
          <ArrowLeft size={17} />
          Back to documents
        </Link>

        <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">
          The document could not be loaded.
        </div>
      </div>
    );
  }

  function handleDelete(
    documentId: string,
    originalFilename: string,
  ) {
    const confirmed = window.confirm(
      `Delete "${originalFilename}"?`,
    );

    if (!confirmed) {
      return;
    }

    deleteMutation.mutate(documentId);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <Link
        to="/documents"
        className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        <ArrowLeft size={17} />
        Back to documents
      </Link>

      <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
              <FileText size={24} />
            </div>

            <div className="min-w-0">
              <p className="text-sm font-medium text-blue-600">
                Document
              </p>

              <h1 className="mt-1 truncate text-3xl font-semibold tracking-tight text-slate-900">
                {document.original_filename}
              </h1>
            </div>
          </div>

          <div className="mt-4">
            <DocumentStatusBadge
              status={document.status}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          {document.status === "uploaded" && (
            <button
              type="button"
              onClick={() =>
                processMutation.mutate(document.id)
              }
              disabled={processMutation.isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 !text-white px-4 py-3 text-sm font-semibold shadow-sm shadow-blue-200 hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:opacity-50"
            >
              {processMutation.isPending ? (
                <LoaderCircle
                  size={17}
                  className="animate-spin"
                />
              ) : (
                <WandSparkles size={17} />
              )}

              Process document
            </button>
          )}

          {document.status === "processed" && (
            <button
              type="button"
              onClick={() =>
                chunkMutation.mutate(document.id)
              }
              disabled={chunkMutation.isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {chunkMutation.isPending ? (
                <LoaderCircle
                  size={17}
                  className="animate-spin"
                />
              ) : (
                <Layers3 size={17} />
              )}

              Create chunks
            </button>
          )}

          <button
            type="button"
            onClick={() =>
              handleDelete(
                document.id,
                document.original_filename,
              )
            }
            disabled={deleteMutation.isPending}
            className="inline-flex items-center gap-2 rounded-xl border border-red-200 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
          >
            <Trash2 size={17} />
            Delete
          </button>
        </div>
      </div>

      <section className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <InfoCard
          label="File type"
          value={document.content_type}
        />

        <InfoCard
          label="File size"
          value={formatFileSize(
            document.file_size,
          )}
        />

        <InfoCard
          label="Uploaded"
          value={new Date(
            document.created_at,
          ).toLocaleDateString()}
        />

        <InfoCard
          label="Status"
          value={document.status}
        />
      </section>

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 className="font-semibold text-slate-900">
              Document chunks
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Text segments prepared for semantic search.
            </p>
          </div>

          {document.status === "chunked" && (
            <button
              type="button"
              onClick={() =>
                queryClient.invalidateQueries({
                  queryKey: [
                    "document-chunks",
                    documentId,
                  ],
                })
              }
              className="rounded-lg border border-slate-300 p-2 text-slate-600 hover:bg-slate-50"
            >
              <RefreshCw size={17} />
            </button>
          )}
        </div>

        {document.status !== "chunked" && (
          <div className="px-6 py-14 text-center">
            <Layers3
              size={36}
              className="mx-auto text-slate-300"
            />

            <h3 className="mt-4 font-medium text-slate-900">
              No chunks yet
            </h3>

            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
              Process the document and create chunks
              before they can be viewed here.
            </p>
          </div>
        )}

        {document.status === "chunked" &&
          chunksLoading && (
            <div className="flex items-center justify-center gap-2 px-6 py-14 text-slate-500">
              <LoaderCircle
                size={20}
                className="animate-spin"
              />
              Loading chunks...
            </div>
          )}

        {document.status === "chunked" &&
          chunksError && (
            <div className="px-6 py-14 text-center text-red-600">
              The chunks could not be loaded.
            </div>
          )}

        {document.status === "chunked" &&
          !chunksLoading &&
          !chunksError &&
          chunks.length === 0 && (
            <div className="px-6 py-14 text-center text-slate-500">
              No chunks were found.
            </div>
          )}

        {document.status === "chunked" &&
          chunks.length > 0 && (
            <div className="space-y-4 p-6">
              {chunks.map((chunk) => (
                <article
                  key={chunk.id}
                  className="rounded-2xl border border-slate-200 p-5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="font-medium text-slate-900">
                      Chunk {chunk.chunk_index + 1}
                    </h3>

                    <span className="text-xs text-slate-500">
                      {chunk.character_count} characters
                    </span>
                  </div>

                  <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-600">
                    {chunk.content}
                  </p>

                  <div className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-400">
                    Characters{" "}
                    {chunk.start_character}–
                    {chunk.end_character}
                  </div>
                </article>
              ))}
            </div>
          )}
      </section>
    </div>
  );
}

type InfoCardProps = {
  label: string;
  value: string;
};

function InfoCard({
  label,
  value,
}: InfoCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-2 break-words font-medium capitalize text-slate-900">
        {value}
      </p>
    </div>
  );
}
