import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import StagiaireForm from '../components/StagiaireForm'
import { getStagiaireById, updateStagiaire } from '../services/stagiaires'
import { ArrowLeft } from 'lucide-react'

export default function EditStagiaire() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [stagiaire, setStagiaire] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadStagiaire()
  }, [id])

  async function loadStagiaire() {
    try {
      const data = await getStagiaireById(id)
      setStagiaire(data)
    } catch (err) {
      setError('Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (data) => {
    setSaving(true)
    setError('')
    try {
      await updateStagiaire(id, data)
      navigate(`/stagiaires/${id}`, { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || d.message).join(', '))
      } else {
        setError(detail || 'Erreur lors de la modification')
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="page"><div className="loading-spinner" /><p>Chargement...</p></div>
  }

  if (error && !stagiaire) {
    return <div className="page"><div className="table-error">{error}</div></div>
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to={`/stagiaires/${id}`} className="back-link"><ArrowLeft size={14} /> Retour au détail</Link>
          <h1 className="page-title">Modifier le stagiaire</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-card">
        <StagiaireForm initialData={stagiaire} onSubmit={handleSubmit} loading={saving} />
      </div>
    </div>
  )
}
