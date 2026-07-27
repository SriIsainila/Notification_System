import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { formatChartDate, formatPrice } from '../utils/formatters.js'

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
    date: formatChartDate(h.checked_at),
    price: Number(h.price),
    currency: h.currency || 'LKR',
  }))

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#173A241A" vertical={false} />
          <XAxis dataKey="date" stroke="#65806D" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#65806D" fontSize={12} tickLine={false} axisLine={false} width={60} />
          <Tooltip
            contentStyle={{
              background: '#FFFFFF',
              border: '1px solid #173A2426',
              color: '#173A24',
              borderRadius: 8,
              fontSize: 13,
            }}
            labelStyle={{ color: '#65806D' }}
            formatter={(value, _name, item) => [formatPrice(value, item.payload.currency), 'Price']}
          />
          <Line type="monotone" dataKey="price" stroke="#36A85A" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
