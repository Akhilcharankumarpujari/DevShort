export default function ClickChart({ data = [] }) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        No click data yet
      </div>
    );
  }

  // Show last 14 data points for readability
  const displayData = data.slice(-14);
  const maxClicks = Math.max(...displayData.map((d) => d.clicks), 1);

  return (
    <div className="w-full">
      <div className="flex items-end gap-1 h-40">
        {displayData.map((item) => {
          const heightPct = (item.clicks / maxClicks) * 100;
          return (
            <div
              key={item.date}
              className="flex-1 flex flex-col items-center gap-1 min-w-0"
            >
              <span className="text-[10px] text-gray-400 font-medium">
                {item.clicks}
              </span>
              <div
                className="w-full bg-primary rounded-t-md transition-all duration-300 hover:bg-primary-600 min-h-[2px]"
                style={{ height: `${Math.max(heightPct, 2)}%` }}
                title={`${item.date}: ${item.clicks} clicks`}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-1 mt-2">
        {displayData.map((item) => (
          <div key={item.date} className="flex-1 min-w-0">
            <span className="text-[10px] text-gray-400 block text-center truncate">
              {item.date.slice(5)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
