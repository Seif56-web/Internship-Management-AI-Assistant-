import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getEncadrants } from '../services/encadrants'
import { useAuth } from '../hooks/useAuth'
import { UserCheck, PlusCircle, Search } from 'lucide-react'

export default function Encadrants() {
  const [encadrants, setEncadrants] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const data = await getEncadrants()
      setEncadrants(data)
    } catch {
      //
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="page"><div className="loading-spinner" /></div>

  const canCreate = user?.role === 'RH' || user?.role === 'Admin'

  const q = search.trim().toLowerCase()
  const filtered = q
    ? encadrants.filter((e) => [e.nom, e.prenom, e.email].filter(Boolean).join(' ').toLowerCase().includes(q))
    : encadrants

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Encadrants</h1>
        {canCreate && (
          <button className="btn btn-primary" onClick={() => navigate('/encadrants/ajouter')}>
            <PlusCircle size={14} />
            Ajouter un encadrant
          </button>
        )}
      </div>

      <div className="search-container" style={{ marginBottom: 16 }}>
        <Search size={16} className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Rechercher un encadrant par nom, prénom ou email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <div className="table-empty">
          <UserCheck size={48} className="empty-icon" />
          <p>{q ? 'Aucun encadrant ne correspond à la recherche' : 'Aucun encadrant trouvé'}</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="stagiaire-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id}>
                  <td>{e.nom}</td>
                  <td>{e.prenom}</td>
                  <td>{e.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
