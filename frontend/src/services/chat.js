import api from './api'

export async function sendMessage(message, conversationId) {
  const response = await api.post('/chat', {
    message,
    conversation_id: conversationId || null,
  })
  return response.data
}

export async function getConversations() {
  const response = await api.get('/chat/conversations')
  return response.data
}

export async function getMessages(conversationId) {
  const response = await api.get(`/chat/conversations/${conversationId}/messages`)
  return response.data
}

export async function deleteConversation(conversationId) {
  await api.delete(`/chat/conversations/${conversationId}`)
}