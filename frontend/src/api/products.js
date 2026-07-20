const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

function authHeaders(token) {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

// Add a new product URL to track (backend scrapes it and saves to `products` +
// `tracked_items` tables per the ERD)
export async function addTrackedProduct({ url, targetPrice, notifyChannel }, token) {
  const res = await fetch(`${API_BASE}/products`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ url, targetPrice, notifyChannel }),
  })
  if (!res.ok) throw new Error('Could not add product. Check the URL and try again.')
  return res.json()
}

// Get all products the logged-in user is tracking
export async function getTrackedProducts(token) {
  const res = await fetch(`${API_BASE}/products`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error('Could not load tracked products.')
  return res.json()
}

// Get price history for one product (for the graph)
export async function getPriceHistory(productId, token) {
  const res = await fetch(`${API_BASE}/products/${productId}/history`, {
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error('Could not load price history.')
  return res.json()
}

export async function deleteTrackedItem(trackedItemId, token) {
  const res = await fetch(`${API_BASE}/products/${trackedItemId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error('Could not remove this product.')
  return res.json()
}
