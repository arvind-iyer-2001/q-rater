import { useEffect, useState } from "react";
import { api, type ContentItem } from "../lib/api";
import { ContentCard } from "../components/ContentCard";
import Link from "next/link";

const USER_ID = "guest";

export default function Recommendations() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [interests, setInterests] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.getRecommendations(USER_ID, 15);
      setItems(res.items);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSaveInterests = async () => {
    const list = interests
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!list.length) return;
    setSaving(true);
    try {
      await api.updateInterests(USER_ID, list);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      await load();
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/" className="text-blue-600 text-sm hover:underline">
            ← Back
          </Link>
          <h1 className="text-xl font-bold text-gray-900">For You</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-900 mb-2">Your Interests</h2>
          <p className="text-xs text-gray-500 mb-3">
            Enter comma-separated interests to personalize your feed.
          </p>
          <div className="flex gap-3">
            <input
              type="text"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              placeholder="e.g. machine learning, cooking, travel"
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSaveInterests}
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {saving ? "Saving..." : saved ? "Saved!" : "Save"}
            </button>
          </div>
        </div>

        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recommended For You
          </h2>
          {loading ? (
            <p className="text-gray-400 text-sm">Loading recommendations...</p>
          ) : items.length === 0 ? (
            <p className="text-gray-400 text-sm">
              No recommendations yet. Ingest some content and set your interests.
            </p>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <ContentCard key={item.content_id} item={item} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
