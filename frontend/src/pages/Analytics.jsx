import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import client from "../api/client.js";
import StatCard from "../components/StatCard.jsx";
import ClickChart from "../components/ClickChart.jsx";
import BrowserChart from "../components/BrowserChart.jsx";
import DeviceChart from "../components/DeviceChart.jsx";
import TopUrlsTable from "../components/TopUrlsTable.jsx";

export default function Analytics() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const response = await client.get("/api/analytics/overview");
        setData(response.data);
      } catch (error) {
        toast.error(error.message || "Failed to load analytics");
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnalytics();
  }, []);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card h-32 bg-gray-100" />
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
        <p className="text-gray-500">Create some URLs to see analytics</p>
      </div>
    );
  }

  const { overview, topUrls, dailyClicks, browserStats, deviceStats } = data;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-text mb-8">Analytics Overview</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <StatCard
          title="Total URLs"
          value={overview.totalUrls.toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          }
          color="primary"
        />
        <StatCard
          title="Total Clicks"
          value={overview.totalClicks.toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
          }
          color="secondary"
        />
        <StatCard
          title="Active Links"
          value={overview.activeLinks.toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="green"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
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
      </div>

      {/* Top URLs */}
      <div className="card">
        <h3 className="text-lg font-semibold text-text mb-4">Top Performing URLs</h3>
        <TopUrlsTable urls={topUrls} />
      </div>
    </div>
  );
}
