import api from './api'

export async function uploadRapport(stagiaireId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post(`/rapports/upload/${stagiaireId}`, formData)
  return response.data
}

export async function getRapports(stagiaireId) {
  const response = await api.get(`/rapports/${stagiaireId}`)
  return response.data
}

export async function deleteRapport(rapportId) {
  const response = await api.delete(`/rapports/${rapportId}`)
  return response.data
}
