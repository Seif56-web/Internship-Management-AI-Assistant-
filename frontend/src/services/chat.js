import api from './api'

export async function sendMessage(message) {
  const response = await api.post('/chat', { message })
  return response.data
}