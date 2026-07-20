const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

export async function getNotifications(token) {
  const res = await fetch(`${API_BASE}/notifications`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Could not load notifications.')
  return res.json()
}
