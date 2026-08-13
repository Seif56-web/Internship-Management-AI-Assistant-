import api from './api'

export async function validerStage(stagiaireId, data) {
  const response = await api.post(`/validations/${stagiaireId}`, data)
  return response.data
}

export async function getValidations(stagiaireId) {
  const response = await api.get(`/validations/${stagiaireId}`)
  return response.data
}
