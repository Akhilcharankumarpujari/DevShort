import { useState } from "react";
import toast from "react-hot-toast";
import client from "../api/client.js";
import { QRCodeSVG } from "qrcode.react";

export default function ShortenForm({ onUrlCreated }) {
  const [url, setUrl] = useState("");
  const [customAlias, setCustomAlias] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();

    if (!url.trim()) {
      toast.error("Please enter a URL");
      return;
    }

    // Basic URL validation
    if (!/^https?:\/\/.+/i.test(url.trim())) {
      toast.error("URL must start with http:// or https://");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = { url: url.trim() };
      if (customAlias.trim()) payload.customAlias = customAlias.trim();
      if (expiresAt) payload.expiresAt = new Date(expiresAt).toISOString();

      const response = await client.post("/api/urls", payload);
      setResult(response.data);
      toast.success("URL shortened successfully!");

      if (onUrlCreated) {
        onUrlCreated(response.data);
      }
    } catch (error) {
      toast.error(error.message || "Failed to shorten URL");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleCopy() {
    if (!result) return;
    navigator.clipboard.writeText(result.shortUrl).then(() => {
      toast.success("Copied to clipboard!");
    });
  }

  function handleReset() {
    setUrl("");
    setCustomAlias("");
    setExpiresAt("");
    setResult(null);
  }

  if (result) {
    return (
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-text">Your shortened URL</h3>
          <button
            onClick={handleReset}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Shorten another
          </button>
        </div>

        <div className="flex items-center gap-3 p-3 bg-background rounded-xl">
          <code className="flex-1 text-primary font-medium text-sm sm:text-base break-all">
            {result.shortUrl}
          </code>
          <button
            onClick={handleCopy}
            className="btn-primary text-sm px-4 py-2 whitespace-nowrap"
          >
            Copy
          </button>
        </div>

        <div className="flex justify-center pt-2">
          <QRCodeSVG
            value={result.shortUrl}
            size={128}
            bgColor="#FFFFFF"
            fgColor="#2563EB"
            level="M"
          />
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste your long URL here..."
          className="input-field text-base"
          required
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <input
            type="text"
            value={customAlias}
            onChange={(e) => setCustomAlias(e.target.value)}
            placeholder="Custom alias (optional)"
            className="input-field text-sm"
            maxLength={30}
            pattern="^[a-zA-Z0-9_-]{4,30}$"
            title="4-30 characters: letters, numbers, hyphens, underscores"
          />
        </div>
        <div className="flex-1">
          <input
            type="datetime-local"
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            className="input-field text-sm"
            min={new Date().toISOString().slice(0, 16)}
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="btn-primary whitespace-nowrap flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Shortening...
            </>
          ) : (
            "Shorten URL"
          )}
        </button>
      </div>
    </form>
  );
}
