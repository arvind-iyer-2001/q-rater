import { useState } from "react";
import { api, type SearchResponse } from "../lib/api";
import { ContentCard } from "./ContentCard";

interface Props {
  userId?: string;
}

export function SearchBar({ userId }: Props) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.search(query.trim(), userId);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about your content library..."
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-gray-900 hover:bg-gray-700 disabled:bg-gray-400 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      {result && (
        <div className="space-y-6">
          {result.answer && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
              <p className="text-sm font-semibold text-blue-700 mb-2">AI Answer</p>
              <p className="text-gray-800 text-sm whitespace-pre-wrap">{result.answer}</p>
            </div>
          )}
          {result.sources.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-gray-500 mb-3">
                {result.sources.length} source{result.sources.length !== 1 ? "s" : ""}
              </p>
              <div className="space-y-3">
                {result.sources.map((item) => (
                  <ContentCard key={item.content_id} item={item} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
