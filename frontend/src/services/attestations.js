import api from './api'

export async function genererAttestation(stagiaireId) {
  const response = await api.post(`/attestations/generate/${stagiaireId}`)
  return response.data
}

export async function getAttestations(stagiaireId) {
  const response = await api.get(`/attestations/${stagiaireId}`)
  return response.data
}

export function getDownloadUrl(attestationId) {
  return `/api/attestations/download/${attestationId}`
}
