import { useState, useEffect } from 'react'
import api from '../services/api'
import StatusBadge from '../components/StatusBadge'
import { Users, Trash2, Edit3, X, Save } from 'lucide-react'

export default function Comptes() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ nom: '', prenom: '', email: '' })

  useEffect(() => {
    loadUsers()
  }, [])

  async function loadUsers() {
    try {
      const res = await api.get('/users/')
      setUsers(res.data)
    } catch {
      //
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (userId, userNom) => {
    if (!confirm(`Supprimer définitivement le compte de ${userNom} ? Cette action est irréversible.`)) return
    try {
      await api.delete(`/users/${userId}`)
      loadUsers()
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression')
    }
  }

  const startEdit = (u) => {
    setEditingId(u.id)
    setEditForm({ nom: u.nom, prenom: u.prenom, email: u.email })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditForm({ nom: '', prenom: '', email: '' })
  }

  const saveEdit = async (userId) => {
    try {
      await api.put(`/users/${userId}`, editForm)
      setEditingId(null)
      loadUsers()
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la modification')
    }
  }

  if (loading) return <div className="page"><div className="loading-spinner" /></div>

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Comptes</h1>
      </div>

      {users.length === 0 ? (
        <div className="table-empty">
          <Users size={48} className="empty-icon" />
          <p>Aucun compte trouvé</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="stagiaire-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Prénom</th>
                <th>Email</th>
                <th>Rôle</th>
                <th>Créé le</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  {editingId === u.id ? (
                    <>
                      <td>
                        <input className="form-input" value={editForm.nom} onChange={(e) => setEditForm({ ...editForm, nom: e.target.value })} />
                      </td>
                      <td>
                        <input className="form-input" value={editForm.prenom} onChange={(e) => setEditForm({ ...editForm, prenom: e.target.value })} />
                      </td>
                      <td>
                        <input className="form-input" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} />
                      </td>
                      <td><StatusBadge statut={u.role} /></td>
                      <td>{u.created_at ? new Date(u.created_at).toLocaleDateString('fr-FR') : '—'}</td>
                      <td>
                        <div className="header-actions" style={{ gap: 4 }}>
                          <button className="btn btn-sm btn-primary" onClick={() => saveEdit(u.id)}><Save size={14} /></button>
                          <button className="btn btn-sm btn-outline" onClick={cancelEdit}><X size={14} /></button>
                        </div>
                      </td>
                    </>
                  ) : (
                    <>
                      <td>{u.nom}</td>
                      <td>{u.prenom}</td>
                      <td>{u.email}</td>
                      <td><StatusBadge statut={u.role} /></td>
                      <td>{u.created_at ? new Date(u.created_at).toLocaleDateString('fr-FR') : '—'}</td>
                      <td>
                        <div className="header-actions" style={{ gap: 4 }}>
                          <button className="btn btn-sm btn-outline" onClick={() => startEdit(u)}><Edit3 size={14} /></button>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u.id, `${u.prenom} ${u.nom}`)}><Trash2 size={14} /></button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
