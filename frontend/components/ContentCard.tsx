import type { ContentItem } from "../lib/api";
import Link from "next/link";

interface Props {
  item: ContentItem;
}

const PLATFORM_BADGE: Record<string, string> = {
  youtube: "bg-red-100 text-red-700",
  instagram: "bg-purple-100 text-purple-700",
};

export function ContentCard({ item }: Props) {
  const { metadata, summary, source, content_id, score } = item;

  return (
    <Link href={`/content/${content_id}`} className="block group">
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow p-4 flex gap-4">
        {metadata.thumbnail_url && (
          <img
            src={metadata.thumbnail_url}
            alt={metadata.title}
            className="w-28 h-20 object-cover rounded-lg flex-shrink-0"
          />
        )}
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${
                PLATFORM_BADGE[source] ?? "bg-gray-100 text-gray-600"
              }`}
            >
              {source}
            </span>
            <span className="text-xs text-gray-400 capitalize">
              {summary.content_type}
            </span>
            {score !== undefined && (
              <span className="text-xs text-gray-400 ml-auto">
                {(score * 100).toFixed(0)}% match
              </span>
            )}
          </div>

          <h3 className="font-semibold text-gray-900 line-clamp-1 group-hover:text-blue-600 transition-colors">
            {metadata.title || "Untitled"}
          </h3>

          <p className="text-sm text-gray-500 line-clamp-2">{summary.one_liner}</p>

          <div className="flex gap-2 mt-1 flex-wrap">
            {summary.tags?.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Link>
  );
}
