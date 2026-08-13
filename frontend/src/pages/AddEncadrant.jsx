import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserCheck, Loader2, ArrowLeft, ExternalLink } from 'lucide-react'
import api from '../services/api'

export default function AddEncadrant() {
  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!nom) {
      setError('Le nom est requis')
      return
    }
    setLoading(true)
    try {
      const response = await api.post('/encadrants/create', { nom, prenom, email: email || null })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de la création")
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Encadrant créé avec succès</h1>
        </div>
        <div className="detail-card">
          <div className="detail-fields">
            <div className="detail-field"><span>Code</span><span className="badge-bg">{result.code_encadrant}</span></div>
            <div className="detail-field"><span>Nom</span><span>{result.nom}</span></div>
            <div className="detail-field"><span>Email</span><span>{result.email || '—'}</span></div>
          </div>
          {result.email && (
            <div className="alert alert-info" style={{ marginTop: 16 }}>
              <strong>Prochaine étape :</strong> l'encadrant doit activer son compte sur
              {' '}<Link to="/activer-compte">/activer-compte</Link> avec son email pour choisir son mot de passe.
            </div>
          )}
          <div className="form-actions" style={{ marginTop: 20 }}>
            <button className="btn btn-primary" onClick={() => navigate('/encadrants')}>
              Retour aux encadrants
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/encadrants" className="back-link"><ArrowLeft size={14} /> Retour aux encadrants</Link>
          <h1 className="page-title">Ajouter un encadrant</h1>
        </div>
      </div>

      <form className="detail-card" onSubmit={handleSubmit}>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Nom *</label>
            <input type="text" className="form-input" value={nom} onChange={(e) => setNom(e.target.value)} autoFocus />
          </div>
          <div className="form-group">
            <label className="form-label">Prénom</label>
            <input type="text" className="form-input" value={prenom} onChange={(e) => setPrenom(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="encadrant@hutchinson.com" />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <Loader2 size={16} className="spin" /> : <UserCheck size={16} />}
            {loading ? 'Création...' : "Créer l'encadrant"}
          </button>
        </div>
      </form>
    </div>
  )
}
