type DocumentStatusBadgeProps = {
  status: string;
};

export default function DocumentStatusBadge({
  status,
}: DocumentStatusBadgeProps) {
  const styles: Record<string, string> = {
    uploaded:
      "bg-blue-50 text-blue-700 ring-blue-600/20",

    queued:
      "bg-sky-50 text-sky-700 ring-sky-600/20",

    processing:
      "bg-amber-50 text-amber-700 ring-amber-600/20",

    processed:
      "bg-emerald-50 text-emerald-700 ring-emerald-600/20",

    chunked:
      "bg-violet-50 text-violet-700 ring-violet-600/20",

    failed:
      "bg-red-50 text-red-700 ring-red-600/20",

    chunking:
      "bg-violet-50 text-violet-700 ring-violet-600/20",

    embedding:
      "bg-indigo-50 text-indigo-700 ring-indigo-600/20",

    ready:
      "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  };

  const labels: Record<string, string> = {
    uploaded: "Uploaded",
    queued: "Queued",
    processing: "Processing",
    processed: "Processed",
    chunking: "Creating Chunks",
    chunked: "Chunked",
    embedding: "Generating Embeddings",
    ready: "Ready for AI",
    failed: "Failed",
  };

  const className =
    styles[status] ??
    "bg-slate-50 text-slate-700 ring-slate-600/20";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset ${className}`}
    >
      {labels[status] ?? status}
    </span>
  );
}