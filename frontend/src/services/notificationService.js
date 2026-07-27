import httpClient from '../api/httpClient.js'

export async function getNotifications(params) {
  const { data } = await httpClient.get('/notifications', { params })
  return data
}

export async function getUnreadNotifications(params) {
  const { data } = await httpClient.get('/notifications/unread', { params })
  return data
}

export async function markNotificationRead(notificationId) {
  const { data } = await httpClient.patch(`/notifications/${notificationId}/read`)
  return data
}

export async function markAllNotificationsRead() {
  const { data } = await httpClient.patch('/notifications/read-all')
  return data
}

export async function deleteNotification(notificationId) {
  const { data } = await httpClient.delete(`/notifications/${notificationId}`)
  return data
}
