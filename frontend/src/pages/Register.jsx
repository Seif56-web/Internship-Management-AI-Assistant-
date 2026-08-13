import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../services/auth'
import { UserPlus, Loader2 } from 'lucide-react'

export default function Register() {
  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('RH')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!nom || !prenom || !email || !password) {
      setError('Tous les champs sont requis')
      return
    }
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas')
      return
    }

    setLoading(true)
    try {
      await register({ nom, prenom, email, password, role })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'inscription")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <img src="/hutchinson_logo-remove.live.png" alt="Hutchinson" className="login-logo-img" />
          <h1 className="login-title">Hut-Gestion de stagiaires</h1>
          <p className="login-subtitle">Créez votre compte</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {error && <div className="login-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Nom</label>
            <input type="text" className="form-input" value={nom} onChange={(e) => setNom(e.target.value)} placeholder="Votre nom" autoFocus />
          </div>

          <div className="form-group">
            <label className="form-label">Prénom</label>
            <input type="text" className="form-input" value={prenom} onChange={(e) => setPrenom(e.target.value)} placeholder="Votre prénom" />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@exemple.com" />
          </div>

          <div className="form-group">
            <label className="form-label">Mot de passe</label>
            <input type="password" className="form-input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>

          <div className="form-group">
            <label className="form-label">Confirmer le mot de passe</label>
            <input type="password" className="form-input" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" />
          </div>

          <div className="form-group">
            <label className="form-label">Rôle</label>
            <select className="form-input" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="RH">RH</option>
              <option value="Encadrant">Encadrant</option>
              <option value="Admin">Admin</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? <Loader2 size={16} className="spin" /> : <UserPlus size={16} />}
            {loading ? 'Inscription...' : "S'inscrire"}
          </button>
        </form>

        <div className="login-footer">
          <p className="login-hint">
            Déjà inscrit ? <Link to="/login">Connectez-vous</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
