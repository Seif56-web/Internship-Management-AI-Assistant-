import { useState, useEffect } from 'react'
import { getEncadrantsUsers } from '../services/users'

export default function EncadrantInput({ value, onChange, error }) {
  const [encadrants, setEncadrants] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadEncadrants()
  }, [])

  async function loadEncadrants() {
    try {
      const data = await getEncadrantsUsers()
      setEncadrants(data)
    } catch {
      setEncadrants([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="encadrant-input">
      <label className="form-label">Encadrant *</label>
      <select
        className={`form-select ${error ? 'input-error' : ''}`}
        value={value || ''}
        onChange={(e) => {
          const selectedId = e.target.value ? parseInt(e.target.value, 10) : null
          if (onChange) onChange(selectedId)
        }}
      >
        <option value="">— Sélectionner un encadrant —</option>
        {loading ? (
          <option disabled>Chargement...</option>
        ) : (
          encadrants.map((enc) => {
            const label = enc.email && !enc.email.includes('@placeholder.local')
              ? `${enc.prenom ? `${enc.prenom} ` : ''}${enc.nom} (${enc.email})`
              : `${enc.prenom ? `${enc.prenom} ` : ''}${enc.nom}`
            return <option key={enc.id} value={enc.id}>{label}</option>
          })
        )}
      </select>
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}
