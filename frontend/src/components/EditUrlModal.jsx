import { useState } from "react";
import toast from "react-hot-toast";
import client from "../api/client.js";

export default function EditUrlModal({ url, onClose, onSaved }) {
  const [originalUrl, setOriginalUrl] = useState(url.originalUrl);
  const [customAlias, setCustomAlias] = useState(url.customAlias || "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();

    setIsSubmitting(true);
    try {
      const payload = {};
      if (originalUrl.trim() !== url.originalUrl) {
        payload.originalUrl = originalUrl.trim();
      }
      if (customAlias.trim() !== (url.customAlias || "")) {
        payload.customAlias = customAlias.trim() || null;
      }

      if (Object.keys(payload).length === 0) {
        onClose();
        return;
      }

      await client.patch(`/api/urls/${url.id}`, payload);
      toast.success("URL updated successfully");
      onSaved();
    } catch (error) {
      toast.error(error.message || "Failed to update URL");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-text">Edit URL</h3>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-text transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              Original URL
            </label>
            <input
              type="url"
              value={originalUrl}
              onChange={(e) => setOriginalUrl(e.target.value)}
              className="input-field"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              Custom Alias
            </label>
            <input
              type="text"
              value={customAlias}
              onChange={(e) => setCustomAlias(e.target.value)}
              className="input-field"
              placeholder="Leave empty for auto-generated"
              maxLength={30}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 px-4 rounded-xl border border-gray-200 text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 btn-primary text-sm py-2.5 disabled:opacity-50"
            >
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
