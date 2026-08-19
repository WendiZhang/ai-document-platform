import { useRef, useState } from "react";
import { Link } from "react-router";
import {
  FileText,
  LoaderCircle,
  Trash2,
  Upload,
  WandSparkles,
} from "lucide-react";
import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  deleteDocument,
  uploadDocument,
  prepareDocument,
} from "../api/documents";
import DocumentStatusBadge from "../components/documents/DocumentStatusBadge";
import { useDocuments } from "../hooks/useDocuments";
import { formatFileSize } from "../utils/file";
import { getApiErrorMessage } from "../utils/apiError";

export default function DocumentsPage() {
  const queryClient = useQueryClient();

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const {
    data: documents = [],
    isLoading,
    isError,
  } = useDocuments();

  const uploadMutation = useMutation({
    mutationFn: uploadDocument,

    onSuccess: async () => {
      setSuccessMessage(
        "Document uploaded successfully.",
      );

      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

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
    },
  });

  const prepareMutation = useMutation({
    mutationFn: prepareDocument,

    onSuccess: async () => {
      setSuccessMessage(
        "Document preparation started.",
      );

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    },
  });

  const activeStatuses = [
    "queued",
    "processing",
    "chunking",
    "embedding",
  ];

  const [successMessage, setSuccessMessage] =
  useState("");

  function handleUpload() {
    if (!selectedFile) {
      return;
    }

    uploadMutation.mutate(selectedFile);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-600">
            Document Library
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            Documents
          </h1>

          <p className="mt-2 text-slate-600">
            Upload PDF or DOCX files, process their text,
            and prepare them for AI search.
          </p>
        </div>
      </div>

      <section className="mt-8 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
            <Upload size={22} />
          </div>

          <div>
            <h2 className="font-semibold text-slate-900">
              Upload document
            </h2>

            <p className="text-sm text-slate-500">
              PDF and DOCX files are supported.
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-4 md:flex-row">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={(event) =>
              setSelectedFile(
                event.target.files?.[0] ?? null,
              )
            }
            className="block w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition hover:border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
          />

          <button
            type="button"
            onClick={handleUpload}
            disabled={
              !selectedFile ||
              uploadMutation.isPending
            }
            className="inline-flex min-w-36 items-center justify-center gap-2 rounded-xl bg-blue-600 !text-white px-5 py-3 font-semibold shadow-sm shadow-blue-200 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploadMutation.isPending ? (
              <>
                <LoaderCircle
                  size={18}
                  className="animate-spin"
                />
                Uploading
              </>
            ) : (
              <>
                <Upload size={18} />
                Upload
              </>
            )}
          </button>
        </div>

        {selectedFile && (
          <p className="mt-3 text-sm text-slate-500">
            Selected:{" "}
            <span className="font-medium text-slate-700">
              {selectedFile.name}
            </span>
          </p>
        )}

        {successMessage && (
          <div className="mt-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {successMessage}
          </div>
        )}


        {uploadMutation.isError && (
          <p className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
            {getApiErrorMessage(
              uploadMutation.error,
              "The document could not be uploaded.",
            )}
          </p>
        )}
      </section>

      <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5">
          <h2 className="font-semibold text-slate-900">
            Your documents
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {documents.length} document
            {documents.length === 1 ? "" : "s"}
          </p>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center gap-2 px-6 py-16 text-slate-500">
            <LoaderCircle
              size={20}
              className="animate-spin"
            />
            Loading documents...
          </div>
        )}

        {isError && (
          <div className="px-6 py-16 text-center text-red-600">
            Documents could not be loaded.
          </div>
        )}

        {!isLoading &&
          !isError &&
          documents.length === 0 && (
            <div className="px-6 py-16 text-center">
              <FileText
                size={36}
                className="mx-auto text-slate-300"
              />

              <h3 className="mt-4 font-medium text-slate-900">
                No documents yet
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Upload your first PDF or DOCX above.
              </p>
            </div>
          )}

        {!isLoading &&
          !isError &&
          documents.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[850px]">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-6 py-4 font-medium">
                      Document
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Size
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Status
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Uploaded
                    </th>

                    <th className="px-6 py-4 text-right font-medium">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200">
                  {documents.map((document) => {
                  const isPreparing =
                    activeStatuses.includes(
                      document.status,
                    );

                  return (
                    <tr
                      key={document.id}
                      className="transition hover:bg-blue-50/30"
                    >
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-3">
                          <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
                            <FileText size={18} />
                          </div>

                          <div>
                            <Link
                              to={`/documents/${document.id}`}
                              className="block max-w-xs truncate font-medium text-slate-900 hover:text-blue-600"
                            >
                              {document.original_filename}
                            </Link>

                            <p className="mt-1 text-xs text-slate-500">
                              {document.content_type}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-5 text-sm text-slate-600">
                        {formatFileSize(
                          document.file_size,
                        )}
                      </td>

                      <td className="px-6 py-5">
                        <DocumentStatusBadge
                          status={document.status}
                        />
                      </td>

                      <td className="px-6 py-5 text-sm text-slate-600">
                        {new Date(
                          document.created_at,
                        ).toLocaleDateString()}
                      </td>

                      <td className="px-6 py-5">
                        <div className="flex justify-end gap-2">
                          
                          {document.status === "uploaded" && (
                            <button
                              type="button"
                              onClick={() =>
                                prepareMutation.mutate(document.id)
                              }
                              disabled={prepareMutation.isPending}
                              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 !text-white px-3 py-2 text-sm font-semibold shadow-sm shadow-blue-100 hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100 disabled:opacity-50"
                            >
                              {prepareMutation.isPending ? (
                                <LoaderCircle
                                  size={16}
                                  className="animate-spin"
                                />
                              ) : (
                                <WandSparkles size={16} />
                              )}

                              Prepare
                            </button>
                          )}

                          {isPreparing && (
                            <div className="inline-flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium capitalize text-blue-700">
                              <LoaderCircle
                                size={16}
                                className="animate-spin"
                              />
                              {document.status}
                            </div>
                          )}

                          {document.status === "failed" && (
                            <button
                              type="button"
                              onClick={() =>
                                prepareMutation.mutate(document.id)
                              }
                              disabled={prepareMutation.isPending}
                              className="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100 disabled:opacity-50"
                            >
                              <WandSparkles size={16} />
                              Retry
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => {
                              const confirmed =
                                window.confirm(
                                  `Delete "${document.original_filename}"?`,
                                );

                              if (confirmed) {
                                deleteMutation.mutate(
                                  document.id,
                                );
                              }
                            }}
                            disabled={
                              deleteMutation.isPending
                            }
                            className="rounded-lg border border-red-200 p-2 text-red-600 hover:bg-red-50 disabled:opacity-50"
                          >
                            <Trash2 size={17} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          )}
      </section>
    </div>
  );
}
