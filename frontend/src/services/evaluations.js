import api from './api'

export async function getEvaluation(stagiaireId) {
  try {
    const response = await api.get(`/evaluations/${stagiaireId}`)
    return response.data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}

export async function saveEvaluation(stagiaireId, data) {
  const response = await api.post(`/evaluations/${stagiaireId}`, data)
  return response.data
}
