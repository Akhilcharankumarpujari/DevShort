const colorMap = {
  primary: { bg: "bg-primary/10", text: "text-primary", icon: "text-primary" },
  secondary: { bg: "bg-secondary/10", text: "text-secondary", icon: "text-secondary" },
  green: { bg: "bg-emerald-50", text: "text-emerald-600", icon: "text-emerald-500" },
  amber: { bg: "bg-amber-50", text: "text-amber-600", icon: "text-amber-500" },
};

export default function StatCard({ title, value, icon, color = "primary" }) {
  const colors = colorMap[color] || colorMap.primary;

  return (
    <div className="card flex items-center gap-4">
      {icon && (
        <div className={`w-12 h-12 rounded-xl ${colors.bg} ${colors.icon} flex items-center justify-center flex-shrink-0`}>
          {icon}
        </div>
      )}
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className={`text-2xl font-bold ${colors.text}`}>{value}</p>
      </div>
    </div>
  );
}
