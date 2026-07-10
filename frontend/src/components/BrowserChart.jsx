const COLORS = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"];

export default function BrowserChart({ data = [] }) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
        No browser data yet
      </div>
    );
  }

  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <div className="space-y-3">
      {data.map((item, index) => {
        const pct = total > 0 ? ((item.count / total) * 100).toFixed(1) : 0;
        return (
          <div key={item.browser} className="flex items-center gap-3">
            <span
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-sm text-gray-600 w-20 truncate">{item.browser}</span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${pct}%`,
                  backgroundColor: COLORS[index % COLORS.length],
                }}
              />
            </div>
            <span className="text-sm text-gray-400 w-16 text-right">
              {item.count} ({pct}%)
            </span>
          </div>
        );
      })}
    </div>
  );
}
