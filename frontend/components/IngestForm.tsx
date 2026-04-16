import { useState, useEffect } from "react";
import { api, type JobStatus } from "../lib/api";

interface Props {
  onComplete?: (contentId: string) => void;
}

export function IngestForm({ onComplete }: Props) {
  const [url, setUrl] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setStatus(null);
    try {
      const res = await api.ingest(url.trim());
      setJobId(res.job_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // Poll job status
  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(async () => {
      try {
        const s = await api.getJobStatus(jobId);
        setStatus(s);
        if (s.status === "complete") {
          clearInterval(interval);
          onComplete?.(s.content_id);
        } else if (s.status === "failed") {
          clearInterval(interval);
          setError(s.error ?? "Processing failed");
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Ingest Content</h2>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste a YouTube or Instagram URL..."
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
          disabled={loading || (status?.status === "processing")}
        />
        <button
          type="submit"
          disabled={loading || status?.status === "processing"}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Submitting..." : "Ingest"}
        </button>
      </form>

      {status && status.status !== "complete" && (
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span className="capitalize">{status.status}...</span>
            <span>{status.progress}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>
      )}

      {status?.status === "complete" && (
        <p className="mt-3 text-sm text-green-600 font-medium">
          Content processed successfully!
        </p>
      )}

      {error && (
        <p className="mt-3 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
