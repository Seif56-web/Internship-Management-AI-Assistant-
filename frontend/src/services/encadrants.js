import api from './api'

export async function getEncadrants() {
  const response = await api.get('/encadrants/')
  return response.data
}

export async function searchEncadrants(query) {
  const response = await api.get('/encadrants/search', { params: { q: query } })
  return response.data
}
