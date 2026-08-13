import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { KeyRound, Loader2, CheckCircle } from 'lucide-react'
import api from '../services/api'

export default function ActiverCompte() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Veuillez remplir tous les champs')
      return
    }
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas')
      return
    }

    setLoading(true)
    try {
      await api.post('/auth/activer', { email, password })
      setDone(true)
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'activation")
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="login-header">
            <CheckCircle size={48} className="text-success" />
            <h1 className="login-title">Compte activé</h1>
            <p className="login-subtitle">Vous pouvez maintenant vous connecter</p>
          </div>
          <button className="btn btn-primary btn-full" onClick={() => navigate('/login')}>
            Se connecter
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <KeyRound size={32} />
          <h1 className="login-title">Activer mon compte</h1>
          <p className="login-subtitle">Créez votre mot de passe pour activer votre compte encadrant</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          {error && <div className="login-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Email professionnel</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="votre@email.com"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mot de passe</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Votre mot de passe"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Confirmer le mot de passe</label>
            <input
              type="password"
              className="form-input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirmer le mot de passe"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? <Loader2 size={16} className="spin" /> : <KeyRound size={16} />}
            {loading ? 'Activation...' : 'Activer mon compte'}
          </button>
        </form>

        <div className="login-footer">
          <p className="login-hint">
            Déjà un compte ? <Link to="/login">Connectez-vous</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
