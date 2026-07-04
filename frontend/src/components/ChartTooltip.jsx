import React from 'react';

/**
 * Shared dark-theme tooltip for Recharts. Renders every series in the payload,
 * so it works for single-series radars and multi-candidate comparisons alike.
 */
export default function ChartTooltip({ active, payload, label, suffix = '/100' }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-black/90 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-xl">
      <p className="text-gray-400 text-xs font-semibold">{payload[0]?.payload?.subject ?? label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-sm font-bold mt-1" style={{ color: entry.stroke || entry.color || '#4DFFA4' }}>
          {entry.name}: {entry.value}
          {suffix}
        </p>
      ))}
    </div>
  );
}
