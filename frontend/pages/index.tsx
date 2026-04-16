import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { IngestForm } from "../components/IngestForm";
import { SearchBar } from "../components/SearchBar";
import { ContentCard } from "../components/ContentCard";
import { api, type ContentItem } from "../lib/api";

const GUEST_USER_ID = "guest";

export default function Home() {
  const router = useRouter();
  const [tab, setTab] = useState<"feed" | "search">("feed");
  const [feed, setFeed] = useState<ContentItem[]>([]);
  const [feedLoading, setFeedLoading] = useState(true);

  const loadFeed = async () => {
    setFeedLoading(true);
    try {
      const items = await api.listContent({ limit: 20 });
      setFeed(items);
    } catch {
      // ignore
    } finally {
      setFeedLoading(false);
    }
  };

  useEffect(() => {
    loadFeed();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Q-Rater</h1>
          <nav className="flex gap-1">
            {(["feed", "search"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize ${
                  tab === t
                    ? "bg-gray-900 text-white"
                    : "text-gray-500 hover:text-gray-900"
                }`}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <IngestForm onComplete={() => loadFeed()} />

        {tab === "search" && (
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Search &amp; Ask
            </h2>
            <SearchBar userId={GUEST_USER_ID} />
          </section>
        )}

        {tab === "feed" && (
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Content Library
            </h2>
            {feedLoading ? (
              <p className="text-gray-400 text-sm">Loading...</p>
            ) : feed.length === 0 ? (
              <p className="text-gray-400 text-sm">
                No content yet. Ingest a YouTube or Instagram URL above.
              </p>
            ) : (
              <div className="space-y-3">
                {feed.map((item) => (
                  <ContentCard key={item.content_id} item={item} />
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
