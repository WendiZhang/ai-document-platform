import {
  FileCheck2,
  Files,
  Layers3,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router";

import { useDocuments } from "../hooks/useDocuments";
import DocumentStatusBadge from "../components/documents/DocumentStatusBadge";

export default function DashboardPage() {
  const {
    data: documents = [],
    isLoading,
  } = useDocuments();

  const processedCount =
    documents.filter(
      (document) =>
        document.status === "processed" ||
        document.status === "chunked"||
        document.status === "embedded" ||
        document.status === "ready",
    ).length;

  const readyCount =
    documents.filter(
      (document) =>
        document.status === "ready" ||
        document.status === "embedded",
    ).length;

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">
            Overview
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
            Dashboard
          </h1>

          <p className="mt-2 text-slate-600">
            Monitor your document processing pipeline.
          </p>
        </div>

        <Link
          to="/documents"
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 !text-white px-4 py-2.5 text-sm font-semibold shadow-sm shadow-blue-200 transition hover:-translate-y-0.5 hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100"
        >
          Manage documents
          <ArrowRight size={16} />
        </Link>
      </div>

      <section className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <DashboardCard
          label="Total documents"
          value={
            isLoading ? "..." : documents.length
          }
          icon={<Files size={22} />}
        />

        <DashboardCard
          label="Processed"
          value={
            isLoading ? "..." : processedCount
          }
          icon={<FileCheck2 size={22} />}
        />

        <DashboardCard
          label="Ready for AI"
          value={
            isLoading ? "..." : readyCount
          }
          icon={<Layers3 size={22} />}
        />
      </section>

      <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
          <div>
            <h2 className="font-semibold text-slate-900">
              Recent documents
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Your latest uploads and processing status.
            </p>
          </div>
          <Link to="/documents" className="text-sm font-semibold text-blue-600 hover:text-blue-700">
            View all
          </Link>
        </div>

        {documents.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <Files size={30} className="mx-auto text-slate-300" />
            <p className="mt-3 text-sm font-medium text-slate-700">
              No documents uploaded yet.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {documents
              .slice(0, 5)
              .map((document) => (
                <div
                  key={document.id}
                  className="flex items-center justify-between gap-4 px-6 py-4 transition hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <Link to={`/documents/${document.id}`} className="block truncate font-medium text-slate-900 hover:text-blue-600">
                      {
                        document.original_filename
                      }
                    </Link>

                    <p className="mt-1 text-xs text-slate-500">
                      {new Date(
                        document.created_at,
                      ).toLocaleDateString()}
                    </p>
                  </div>

                  <DocumentStatusBadge status={document.status} />
                </div>
              ))}
          </div>
        )}
      </section>
    </div>
  );
}

type DashboardCardProps = {
  label: string;
  value: number | string;
  icon: React.ReactNode;
};

function DashboardCard({
  label,
  value,
  icon,
}: DashboardCardProps) {
  return (
    <div className="group rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-200/60">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-indigo-100 text-blue-600 transition group-hover:scale-105">
        {icon}
      </div>

      <p className="mt-6 text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-3xl font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}
