export function formatPrice(value, currency = 'LKR') {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return 'Price unavailable'

  const formatted = amount.toLocaleString('en-LK', { maximumFractionDigits: 2 })
  return currency === 'LKR' ? `Rs. ${formatted}` : `${currency} ${formatted}`
}

export function formatChartDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}
