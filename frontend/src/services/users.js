import api from './api'

export async function getEncadrantsUsers() {
  const response = await api.get('/users/encadrants')
  return response.data
}
