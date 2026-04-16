import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api } from "../../lib/api";

export default function ContentDetail() {
  const router = useRouter();
  const { id } = router.query as { id: string };
  const [content, setContent] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .getContent(id)
      .then((data) => setContent(data as Record<string, unknown>))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-red-400">{error ?? "Content not found"}</p>
      </div>
    );
  }

  const meta = content.metadata as Record<string, unknown>;
  const summary = content.summary as Record<string, unknown>;
  const raw = content.raw as Record<string, unknown> | undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link href="/" className="text-blue-600 text-sm hover:underline">
            ← Back
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {meta?.thumbnail_url && (
          <img
            src={String(meta.thumbnail_url)}
            alt={String(meta.title ?? "")}
            className="w-full aspect-video object-cover rounded-2xl"
          />
        )}

        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-semibold bg-red-100 text-red-700 px-2 py-0.5 rounded-full capitalize">
              {String(content.source)}
            </span>
            <span className="text-xs text-gray-400 capitalize">
              {String(summary?.content_type ?? "")}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {String(meta?.title ?? "Untitled")}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {String(meta?.author ?? "")} &middot; {meta?.view_count?.toLocaleString()} views
          </p>
          <a
            href={String(content.url)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-500 hover:underline mt-1 block"
          >
            {String(content.url)}
          </a>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-900 mb-2">Summary</h2>
          <p className="text-gray-700 text-sm">{String(summary?.detailed_summary ?? "")}</p>

          {Array.isArray(summary?.key_topics) && summary.key_topics.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 mb-1">Key Topics</p>
              <div className="flex flex-wrap gap-2">
                {(summary.key_topics as string[]).map((t) => (
                  <span key={t} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(summary?.tags) && summary.tags.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold text-gray-500 mb-1">Tags</p>
              <div className="flex flex-wrap gap-2">
                {(summary.tags as string[]).map((tag) => (
                  <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {raw?.transcript && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-900 mb-2">Transcript</h2>
            <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
              {String(raw.transcript)}
            </p>
          </div>
        )}

        {Array.isArray(raw?.comments) && (raw.comments as unknown[]).length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-900 mb-3">Top Comments</h2>
            <div className="space-y-3">
              {(raw.comments as Record<string, unknown>[]).slice(0, 20).map((c, i) => (
                <div key={i} className="text-sm">
                  <span className="font-medium text-gray-800">{String(c.author)}</span>
                  <span className="text-gray-600 ml-2">{String(c.text)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
