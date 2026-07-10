import { Link } from "react-router-dom";

export default function TopUrlsTable({ urls = [] }) {
  if (urls.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400 text-sm">
        No URLs yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-3 px-4 text-gray-500 font-medium">Original URL</th>
            <th className="text-right py-3 px-4 text-gray-500 font-medium">Clicks</th>
            <th className="text-right py-3 px-4 text-gray-500 font-medium">Created</th>
            <th className="text-right py-3 px-4 text-gray-500 font-medium">Details</th>
          </tr>
        </thead>
        <tbody>
          {urls.map((url, index) => (
            <tr
              key={url.id}
              className={`border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                index === 0 ? "bg-amber-50/50" : ""
              }`}
            >
              <td className="py-3 px-4">
                <div className="max-w-xs truncate text-gray-700">{url.originalUrl}</div>
              </td>
              <td className="py-3 px-4 text-right">
                <span className="font-semibold text-primary">{url.clickCount}</span>
              </td>
              <td className="py-3 px-4 text-right text-gray-400">
                {new Date(url.createdAt).toLocaleDateString()}
              </td>
              <td className="py-3 px-4 text-right">
                <Link
                  to={`/analytics/${url.id}`}
                  className="text-primary hover:text-primary-700 text-xs font-medium"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
