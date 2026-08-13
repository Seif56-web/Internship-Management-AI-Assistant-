import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getStagiaireById } from '../services/stagiaires'
import { genererAttestation } from '../services/attestations'
import { STATUT_STAGE } from '../constants/statuses'
import api from '../services/api'
import { ArrowLeft, Download, Send, Loader2, CheckCircle } from 'lucide-react'

const generatingLocks = new Set()

export default function AttestationPreview() {
  const { id } = useParams()
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [attestationId, setAttestationId] = useState(null)
  const [pdfUrl, setPdfUrl] = useState(null)
  const [error, setError] = useState('')
  const [stagiaire, setStagiaire] = useState(null)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  useEffect(() => { loadAndGenerate() }, [id])
  useEffect(() => { return () => { if (pdfUrl) window.URL.revokeObjectURL(pdfUrl) } }, [pdfUrl])

  async function loadAndGenerate() {
    const lockKey = String(id)
    if (generatingLocks.has(lockKey)) return
    generatingLocks.add(lockKey)
    try {
      const data = await getStagiaireById(id)
      setStagiaire(data)
      const stageValid = [STATUT_STAGE.STAGE_VALIDE, STATUT_STAGE.STAGE_EN_COURS, STATUT_STAGE.STAGE_TERMINE].includes(data.statut_stage)
      const dossierInProgress = !data.statut_dossier
      const canGenerate = data.attestation_id || stageValid || dossierInProgress
      if (!canGenerate) {
        setError("Le stage doit être validé avant la génération de l'attestation.")
        setLoading(false)
        return
      }
      setGenerating(true)
      const att = await genererAttestation(id)
      setAttestationId(att.id)
      const response = await api.get(`/attestations/download/${att.id}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      setPdfUrl(url)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la generation')
    } finally {
      setLoading(false)
      setGenerating(false)
      generatingLocks.delete(lockKey)
    }
  }

  const handleSend = async () => {
    if (!attestationId) return
    setSending(true)
    try { await api.post(`/attestations/send/${attestationId}`); setSent(true) }
    catch (err) { alert(err.response?.data?.detail || 'Erreur lors de l\'envoi') }
    finally { setSending(false) }
  }

  const handleRegenerate = async () => {
    setGenerating(true); setError('')
    try {
      if (pdfUrl) window.URL.revokeObjectURL(pdfUrl)
      const att = await genererAttestation(id)
      setAttestationId(att.id); setSent(false)
      const response = await api.get(`/attestations/download/${att.id}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      setPdfUrl(url)
    } catch (err) { setError(err.response?.data?.detail || 'Erreur lors de la generation') }
    finally { setGenerating(false) }
  }

  const handleDownload = () => {
    if (!pdfUrl) return
    const link = document.createElement('a'); link.href = pdfUrl
    link.setAttribute('download', `attestation_${stagiaire?.nom_complet}.pdf`)
    document.body.appendChild(link); link.click(); link.remove()
  }

  if (loading) return <div className="page"><div className="loading-spinner" /><p>Chargement...</p></div>
  if (error && !stagiaire) return (
    <div className="page">
      <Link to="/" className="back-link"><ArrowLeft size={14} /> Retour</Link>
      <div className="table-error">{error}</div>
    </div>
  )

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to={`/stagiaires/${id}`} className="back-link"><ArrowLeft size={14} /> Retour au detail</Link>
          <h1 className="page-title">Attestation de stage</h1>
        </div>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="attestation-preview-card">
        {generating ? (
          <div className="attestation-generate-prompt">
            <Loader2 size={48} className="spin text-muted" />
            <p className="text-muted">Génération en cours...</p>
          </div>
        ) : pdfUrl ? (
          <>
            <div className="attestation-pdf-container">
              <iframe src={pdfUrl} className="attestation-pdf-iframe" title="Apercu PDF" />
            </div>
            <div className="attestation-actions">
              <button className="btn btn-primary btn-full" onClick={handleDownload}><Download size={16} /> Telecharger le PDF</button>
              <button className="btn btn-primary btn-full" onClick={handleSend} disabled={sending || sent}>
                {sending ? <Loader2 size={16} className="spin" /> : sent ? <CheckCircle size={16} /> : <Send size={16} />}
                {sending ? 'Envoi...' : sent ? 'Envoyée' : 'Envoyer au stagiaire'}
              </button>
              <button className="btn btn-outline btn-full" onClick={handleRegenerate} disabled={generating}>
                {generating ? <Loader2 size={16} className="spin" /> : null} Régénérer
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
