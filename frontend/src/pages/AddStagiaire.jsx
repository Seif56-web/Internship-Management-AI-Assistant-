import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import StagiaireForm from '../components/StagiaireForm'
import { createStagiaire } from '../services/stagiaires'
import { ArrowLeft } from 'lucide-react'

export default function AddStagiaire() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (data) => {
    setLoading(true)
    setError('')
    try {
      const result = await createStagiaire(data)
      navigate(`/stagiaires/${result.id}`, { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || d.message).join(', '))
      } else {
        setError(detail || 'Erreur lors de la création')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link"><ArrowLeft size={14} /> Retour à la liste</Link>
          <h1 className="page-title">Ajouter un stagiaire</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-card">
        <StagiaireForm onSubmit={handleSubmit} loading={loading} />
      </div>
    </div>
  )
}
