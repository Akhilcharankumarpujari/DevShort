import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { QRCodeSVG } from "qrcode.react";
import client from "../api/client.js";
import StatCard from "../components/StatCard.jsx";
import ClickChart from "../components/ClickChart.jsx";
import BrowserChart from "../components/BrowserChart.jsx";
import DeviceChart from "../components/DeviceChart.jsx";

export default function UrlAnalytics() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const response = await client.get(`/api/urls/${id}/analytics`);
        setData(response.data);
      } catch (error) {
        toast.error(error.message || "Failed to load analytics");
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnalytics();
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-4 bg-gray-100 rounded w-96" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="card h-64 bg-gray-100" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center">
        <h2 className="text-xl font-semibold text-text mb-2">No data available</h2>
        <Link to="/dashboard" className="text-primary hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const { url, totalEvents, browserStats, deviceStats, osStats, countryStats, referrerStats, dailyClicks } = data;
  const shortUrl = `${window.location.protocol}//${window.location.hostname}:4000/${url.shortCode}`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to="/dashboard" className="hover:text-primary transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-gray-600">Analytics</span>
      </div>

      {/* URL Info */}
      <div className="card mb-8">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-text mb-2 break-all">
              {url.originalUrl}
            </h1>
            <code className="text-primary font-medium">{shortUrl}</code>
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
              <span>Created {new Date(url.createdAt).toLocaleDateString()}</span>
              <span>{url.clickCount} total clicks</span>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(shortUrl);
                  toast.success("Copied!");
                }}
                className="btn-primary text-sm px-4 py-2"
              >
                Copy URL
              </button>
              <a
                href={shortUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-sm px-4 py-2"
              >
                Open
              </a>
            </div>
          </div>
          <div className="flex-shrink-0 flex items-center justify-center">
            <QRCodeSVG
              value={shortUrl}
              size={120}
              bgColor="#FFFFFF"
              fgColor="#2563EB"
              level="M"
            />
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Events" value={totalEvents.toLocaleString()} color="primary" />
        <StatCard title="Browsers" value={browserStats.length} color="secondary" />
        <StatCard title="Countries" value={countryStats.length} color="green" />
        <StatCard title="Referrers" value={referrerStats.length} color="amber" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Daily Clicks (30 days)</h3>
          <ClickChart data={dailyClicks} />
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Browser Distribution</h3>
          <BrowserChart data={browserStats} />
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Device Distribution</h3>
          <DeviceChart data={deviceStats} />
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Operating Systems</h3>
          <div className="space-y-3">
            {osStats.length === 0 ? (
              <p className="text-gray-400 text-sm">No data yet</p>
            ) : (
              osStats.map((item) => (
                <div key={item.os} className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 w-24 truncate">{item.os}</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{
                        width: `${totalEvents > 0 ? (item.count / totalEvents) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-gray-400 w-12 text-right">{item.count}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Referrers & Countries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Top Referrers</h3>
          {referrerStats.length === 0 ? (
            <p className="text-gray-400 text-sm">No referrer data yet</p>
          ) : (
            <div className="space-y-2">
              {referrerStats.map((item) => (
                <div key={item.referrer} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 truncate max-w-[200px]">
                    {item.referrer === "Direct" ? "Direct / None" : item.referrer}
                  </span>
                  <span className="text-gray-400 font-medium">{item.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold text-text mb-4">Top Countries</h3>
          {countryStats.length === 0 ? (
            <p className="text-gray-400 text-sm">No country data yet</p>
          ) : (
            <div className="space-y-2">
              {countryStats.map((item) => (
                <div key={item.country} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{item.country || "Unknown"}</span>
                  <span className="text-gray-400 font-medium">{item.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
