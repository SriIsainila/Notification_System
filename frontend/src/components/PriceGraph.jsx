import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

// Expects history: [{ checked_at: '2026-01-01', price: 4500 }, ...]
export default function PriceGraph({ history = [] }) {
  if (!history.length) {
    return (
      <p className="text-sm text-muted py-8 text-center">
        No price history yet — check back after the first scheduled check.
      </p>
    )
  }

  const data = history.map((h) => ({
    date: new Date(h.checked_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    price: Number(h.price),
  }))

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff14" vertical={false} />
          <XAxis dataKey="date" stroke="#9C9AC0" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#9C9AC0" fontSize={12} tickLine={false} axisLine={false} width={60} />
          <Tooltip
            contentStyle={{
              background: '#1E1D42',
              border: '1px solid #ffffff1a',
              borderRadius: 8,
              fontSize: 13,
            }}
            labelStyle={{ color: '#9C9AC0' }}
            formatter={(value) => [`Rs. ${value.toLocaleString()}`, 'Price']}
          />
          <Line type="monotone" dataKey="price" stroke="#F2A93B" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
