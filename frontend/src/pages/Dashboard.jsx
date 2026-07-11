import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import client from "../api/client.js";
import ShortenForm from "../components/ShortenForm.jsx";
import Pagination from "../components/Pagination.jsx";
import EditUrlModal from "../components/EditUrlModal.jsx";
import { copyToClipboard } from "../utils/clipboard.js";

export default function Dashboard() {
  const [urls, setUrls] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, limit: 10, total: 0, totalPages: 1 });
  const [totalClicks, setTotalClicks] = useState(0);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [editingUrl, setEditingUrl] = useState(null);

  const fetchUrls = useCallback(async (page = 1, searchTerm = "") => {
    setIsLoading(true);
    try {
      const response = await client.get("/api/dashboard", {
        params: { page, limit: 10, search: searchTerm, sortBy: "createdAt", sortOrder: "desc" },
      });
      setUrls(response.data.urls);
      setPagination(response.data.pagination);
      setTotalClicks(response.data.totalClicks);
    } catch (error) {
      toast.error(error.message || "Failed to load dashboard");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUrls(1, search);
  }, [fetchUrls, search]);

  function handleSearchChange(e) {
    setSearch(e.target.value);
  }

  function handlePageChange(page) {
    fetchUrls(page, search);
  }

  function handleUrlCreated() {
    fetchUrls(1, search);
  }

  async function handleDelete(urlId) {
    if (!window.confirm("Are you sure you want to delete this URL?")) return;

    try {
      await client.delete(`/api/urls/${urlId}`);
      toast.success("URL deleted");
      fetchUrls(pagination.page, search);
    } catch (error) {
      toast.error(error.message || "Failed to delete URL");
    }
  }

  function handleCopy(shortUrl) {
    copyToClipboard(shortUrl);
  }

  function handleEditSaved() {
    setEditingUrl(null);
    fetchUrls(pagination.page, search);
  }

  function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-text">Dashboard</h1>
        <p className="mt-1 text-gray-500">
          {totalClicks.toLocaleString()} total clicks across {pagination.total} URLs
        </p>
      </div>

      {/* Shortener */}
      <div className="mb-10">
        <ShortenForm onUrlCreated={handleUrlCreated} />
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          value={search}
          onChange={handleSearchChange}
          placeholder="Search URLs..."
          className="input-field max-w-md"
        />
      </div>

      {/* URL List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-100 rounded w-2/3 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/4" />
            </div>
          ))}
        </div>
      ) : urls.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-text mb-2">No URLs yet</h3>
          <p className="text-gray-500">
            {search ? "No URLs match your search" : "Shorten your first URL above to get started"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {urls.map((url) => (
            <div key={url.id} className="card flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <code className="text-sm font-semibold text-primary truncate">
                    {url.shortUrl}
                  </code>
                  <button
                    onClick={() => handleCopy(url.shortUrl)}
                    className="text-gray-400 hover:text-primary transition-colors flex-shrink-0"
                    title="Copy URL"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
                <p className="text-sm text-gray-500 truncate mb-2">{url.originalUrl}</p>
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>{url.clickCount} clicks</span>
                  <span>{formatDate(url.createdAt)}</span>
                  {url.expiresAt && (
                    <span className="text-amber-500">
                      Expires {formatDate(url.expiresAt)}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <a
                  href={url.shortUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 text-gray-400 hover:text-primary transition-colors"
                  title="Open URL"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
                <button
                  onClick={() => setEditingUrl(url)}
                  className="p-2 text-gray-400 hover:text-primary transition-colors"
                  title="Edit URL"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <Link
                  to={`/analytics/${url.id}`}
                  className="p-2 text-gray-400 hover:text-primary transition-colors"
                  title="View Analytics"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </Link>
                <button
                  onClick={() => handleDelete(url.id)}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  title="Delete URL"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}

          <Pagination
            page={pagination.page}
            totalPages={pagination.totalPages}
            onPageChange={handlePageChange}
          />
        </div>
      )}

      {/* Edit Modal */}
      {editingUrl && (
        <EditUrlModal
          url={editingUrl}
          onClose={() => setEditingUrl(null)}
          onSaved={handleEditSaved}
        />
      )}
    </div>
  );
}
