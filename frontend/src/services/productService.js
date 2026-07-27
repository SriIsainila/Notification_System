import httpClient from '../api/httpClient.js'

export async function addTrackedProduct(payload) {
  const { data } = await httpClient.post('/products', payload)
  return data
}

export async function getTrackedProducts() {
  const { data } = await httpClient.get('/products')
  return data
}

export async function getPriceHistory(productId) {
  const { data } = await httpClient.get(`/products/${productId}/history`)
  return data
}

export async function deleteTrackedItem(productId) {
  const { data } = await httpClient.delete(`/products/${productId}`)
  return data
}

export async function updateTrackedProduct(productId, payload) {
  const { data } = await httpClient.patch(`/products/${productId}`, payload)
  return data
}

export async function enableTracking(productId) {
  const { data } = await httpClient.post(`/products/${productId}/enable`)
  return data
}

export async function disableTracking(productId) {
  const { data } = await httpClient.post(`/products/${productId}/disable`)
  return data
}
