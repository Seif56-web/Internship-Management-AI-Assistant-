import api from './api'

export async function getStagiaires(params = {}) {
  const response = await api.get('/stagiaires/', { params })
  return response.data
}

export async function getStagiaireById(id) {
  const response = await api.get(`/stagiaires/${id}`)
  return response.data
}

export async function createStagiaire(data) {
  const response = await api.post('/stagiaires/', data)
  return response.data
}

export async function updateStagiaire(id, data) {
  const response = await api.put(`/stagiaires/${id}`, data)
  return response.data
}

export async function deleteStagiaire(id) {
  const response = await api.delete(`/stagiaires/${id}`)
  return response.data
}

export async function deleteStagiaires(ids) {
  const response = await api.post('/stagiaires/batch-delete', { ids })
  return response.data
}

export async function importStagiaires(files) {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  const response = await api.post('/stagiaires/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return response.data
}
