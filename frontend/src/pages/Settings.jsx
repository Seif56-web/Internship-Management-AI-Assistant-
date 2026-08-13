import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Settings as SettingsIcon, Save, Loader2 } from 'lucide-react'
import api from '../services/api'

export default function Settings() {
  const { user, login } = useAuth()
  const [nom, setNom] = useState(user?.nom || '')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  const handleSave = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })

    if (newPassword && newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'Les nouveaux mots de passe ne correspondent pas' })
      return
    }

    setSaving(true)
    try {
      const body = {}
      if (nom !== user.nom) body.nom = nom
      if (email !== user.email) body.email = email
      if (newPassword) {
        if (!currentPassword) {
          setMessage({ type: 'error', text: 'Mot de passe actuel requis' })
          setSaving(false)
          return
        }
        body.current_password = currentPassword
        body.new_password = newPassword
      }
      const response = await api.put('/auth/account', body)
      localStorage.setItem('user', JSON.stringify(response.data))
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setMessage({ type: 'success', text: 'Paramètres mis à jour avec succès' })
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erreur lors de la mise à jour' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Paramètres du compte</h1>
      </div>

      <form className="detail-card" onSubmit={handleSave}>
        <h3 className="card-title">Informations personnelles</h3>

        {message.text && (
          <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
            {message.text}
          </div>
        )}

        <div className="form-group">
          <label className="form-label">Nom</label>
          <input
            type="text"
            className="form-input"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Rôle</label>
          <input
            type="text"
            className="form-input"
            value={user?.role || ''}
            disabled
          />
        </div>

        <h3 className="card-title" style={{ marginTop: 32 }}>Changer le mot de passe</h3>
        <p className="text-muted" style={{ marginBottom: 16 }}>Laissez vide pour ne pas changer</p>

        <div className="form-group">
          <label className="form-label">Mot de passe actuel</label>
          <input
            type="password"
            className="form-input"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Votre mot de passe actuel"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Nouveau mot de passe</label>
          <input
            type="password"
            className="form-input"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Nouveau mot de passe"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Confirmer le nouveau mot de passe</label>
          <input
            type="password"
            className="form-input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirmer le nouveau mot de passe"
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={saving} style={{ marginTop: 16 }}>
          {saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
          {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
        </button>
      </form>
    </div>
  )
}
