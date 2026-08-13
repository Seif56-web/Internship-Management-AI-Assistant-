import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getStagiaireById, deleteStagiaire } from '../services/stagiaires'
import { uploadRapport, deleteRapport, getRapports } from '../services/rapports'
import { getAttestations } from '../services/attestations'
import { getValidations } from '../services/validations'
import { getEvaluation, saveEvaluation } from '../services/evaluations'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../context/ThemeContext'
import StatusBadge from '../components/StatusBadge'
import { STATUT_STAGE, STATUT_DOSSIER, isSuspended, PROLONGATION_BADGE, PROLONGATION_BADGE_DARK } from '../constants/statuses'
import api from '../services/api'
import {
  ArrowLeft, FileText, Download, Trash2, Upload, Check, X,
  FileSignature, Printer, Send, Loader2, Star, Play, Pause,
} from 'lucide-react'

const CRITERES = [
  { key: 'qualite_travail', label: 'Qualité du travail' },
  { key: 'autonomie', label: 'Autonomie' },
  { key: 'ponctualite', label: 'Ponctualité' },
  { key: 'communication', label: 'Communication' },
  { key: 'esprit_equipe', label: "Esprit d'équipe" },
  { key: 'capacite_apprentissage', label: "Capacité d'apprentissage" },
  { key: 'initiative', label: 'Initiative' },
  { key: 'respect_consignes', label: 'Respect des consignes' },
]

function StarRating({ value, onChange, readOnly }) {
  const [hovered, setHovered] = useState(0)
  return (
    <div className="star-rating">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          className={`star ${n <= (readOnly ? value : (hovered || value || 0)) ? 'active' : ''} ${!readOnly && hovered && n <= hovered ? 'hovered' : ''}`}
          onClick={() => !readOnly && onChange?.(n === value ? 0 : n)}
          onMouseEnter={() => !readOnly && setHovered(n)}
          onMouseLeave={() => !readOnly && setHovered(0)}
          disabled={readOnly}
        >
          <Star size={18} fill={n <= (readOnly ? value : (hovered || value || 0)) ? '#f59e0b' : 'none'} />
        </button>
      ))}
    </div>
  )
}

export default function StagiaireDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { theme } = useTheme()
  const prolongationBadge = theme === 'dark' ? PROLONGATION_BADGE_DARK : PROLONGATION_BADGE
  const [stagiaire, setStagiaire] = useState(null)
  const [rapports, setRapports] = useState([])
  const [attestations, setAttestations] = useState([])
  const [validations, setValidations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [sendingId, setSendingId] = useState(null)
  const [attestationOutdated, setAttestationOutdated] = useState(false)
  const [previewAttestation, setPreviewAttestation] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [evalForm, setEvalForm] = useState({})
  const [savingEval, setSavingEval] = useState(false)
  const [changingStatut, setChangingStatut] = useState(false)

  useEffect(() => { loadData() }, [id])
  useEffect(() => {
    const onFocus = () => { if (document.visibilityState === 'visible') loadData(false) }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [id])

  async function loadData(showLoading = true) {
    if (showLoading) setLoading(true)
    try {
      const [s, r, a, v] = await Promise.all([
        getStagiaireById(id), getRapports(id), getAttestations(id), getValidations(id).catch(() => []),
      ])
      setStagiaire(s); setRapports(r); setAttestations(a); setValidations(v)
      const ev = await getEvaluation(id).catch(() => null)
      setEvaluation(ev)
      if (ev) {
        setEvalForm({
          qualite_travail: ev.qualite_travail || 0, autonomie: ev.autonomie || 0,
          ponctualite: ev.ponctualite || 0, communication: ev.communication || 0,
          esprit_equipe: ev.esprit_equipe || 0, capacite_apprentissage: ev.capacite_apprentissage || 0,
          initiative: ev.initiative || 0, respect_consignes: ev.respect_consignes || 0,
          recommandation_embauche: ev.recommandation_embauche || '', commentaire: ev.commentaire || '',
        })
      } else {
        setEvalForm({
          qualite_travail: 0, autonomie: 0, ponctualite: 0, communication: 0,
          esprit_equipe: 0, capacite_apprentissage: 0, initiative: 0, respect_consignes: 0,
          recommandation_embauche: '', commentaire: '',
        })
      }
      if (a.length > 0) {
        try { const resp = await api.get(`/attestations/${id}/outdated`); setAttestationOutdated(resp.data) }
        catch { setAttestationOutdated(false) }
      } else { setAttestationOutdated(false) }
    } catch (err) { setError(err.response?.data?.detail || 'Erreur de chargement') }
    finally { setLoading(false) }
  }

  const handleStatutChange = async (newStatut) => {
    setChangingStatut(true)
    try {
      const isStageValue = Object.values(STATUT_STAGE).includes(newStatut)
      if (isStageValue) {
        await api.post(`/stagiaires/${id}/statut-stage`, { statut: newStatut })
      } else {
        await api.post(`/stagiaires/${id}/statut-dossier`, { statut: newStatut })
      }
      loadData()
    } catch (err) { alert(err.response?.data?.detail || 'Erreur lors du changement de statut') }
    finally { setChangingStatut(false) }
  }

  const handleValiderStage = async () => {
    try {
      await api.post(`/stagiaires/${id}/statut-stage`, { statut: STATUT_STAGE.STAGE_VALIDE })
      alert('Stage validé')
      loadData()
    } catch (err) { alert(err.response?.data?.detail || 'Erreur') }
  }

  const handleRefuserStage = async () => {
    try {
      await api.post(`/stagiaires/${id}/statut-stage`, { statut: STATUT_STAGE.STAGE_REFUSE })
      alert('Stage refusé')
      loadData()
    } catch (err) { alert(err.response?.data?.detail || 'Erreur') }
  }

  const handleSuspendre = async () => {
    try {
      await api.post(`/stagiaires/${id}/statut-stage`, { statut: STATUT_STAGE.STAGE_SUSPENDU })
      loadData()
    } catch (err) { alert(err.response?.data?.detail || 'Erreur') }
  }

  const handleReprendre = async () => {
    try {
      await api.post(`/stagiaires/${id}/statut-stage`, { statut: STATUT_STAGE.STAGE_EN_COURS })
      loadData()
    } catch (err) { alert(err.response?.data?.detail || 'Erreur') }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) { alert('Seuls les fichiers PDF sont acceptés'); return }
    setUploading(true)
    try { await uploadRapport(id, file); alert('Rapport uploadé avec succès'); loadData() }
    catch (err) { alert(err.response?.data?.detail || "Erreur lors de l'upload") }
    finally { setUploading(false) }
  }

  const handleDeleteRapport = async (rapportId) => {
    if (!confirm('Supprimer ce rapport ?')) return
    try { await deleteRapport(rapportId); loadData() }
    catch { alert('Erreur lors de la suppression') }
  }

  const handleDownloadRapport = async (rapportId, fileName) => {
    try {
      const response = await api.get(`/rapports/download/${rapportId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a'); link.href = url; link.setAttribute('download', fileName)
      document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url)
    } catch { alert('Erreur lors du téléchargement') }
  }

  const handleDownloadAttestation = async (attestationId, numero) => {
    try {
      const response = await api.get(`/attestations/download/${attestationId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a'); link.href = url; link.setAttribute('download', `attestation_${numero}.pdf`)
      document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url)
    } catch { alert('Erreur lors du téléchargement') }
  }

  const handlePreviewAttestation = async (attestation) => {
    try {
      const response = await api.get(`/attestations/download/${attestation.id}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      setPreviewAttestation(attestation); setPreviewUrl(url)
    } catch { alert('Erreur lors du chargement de l\'aperçu') }
  }

  const handleClosePreview = () => {
    if (previewUrl) window.URL.revokeObjectURL(previewUrl)
    setPreviewAttestation(null); setPreviewUrl(null)
  }

  const handlePrintAttestation = async (attestationId) => {
    try {
      const response = await api.get(`/attestations/download/${attestationId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const iframe = document.createElement('iframe'); iframe.style.display = 'none'; iframe.src = url
      document.body.appendChild(iframe)
      iframe.onload = () => {
        iframe.contentWindow.print()
        setTimeout(() => { document.body.removeChild(iframe); window.URL.revokeObjectURL(url) }, 1000)
      }
    } catch { alert('Erreur lors de l\'impression') }
  }

  const handleDeleteAttestation = async (attestationId) => {
    if (!confirm("Supprimer cette attestation ?")) return
    try { await api.delete(`/attestations/${attestationId}`); loadData() }
    catch (err) { alert(err.response?.data?.detail || 'Erreur lors de la suppression') }
  }

  const handleSendAttestation = async (attestationId) => {
    setSendingId(attestationId)
    try { await api.post(`/attestations/send/${attestationId}`); alert('Attestation envoyée avec succès') }
    catch (err) { alert(err.response?.data?.detail || 'Erreur lors de l\'envoi') }
    finally { setSendingId(null) }
  }

  const handleDelete = async () => {
    if (!confirm(`Supprimer définitivement ${stagiaire?.nom_complet} ? Cette action est irréversible.`)) return
    try { await deleteStagiaire(id); navigate('/', { replace: true }) }
    catch (err) { alert(err.response?.data?.detail || 'Erreur lors de la suppression') }
  }

  const handleSaveEvaluation = async () => {
    setSavingEval(true)
    try {
      const data = {}
      for (const c of CRITERES) { if (evalForm[c.key] > 0) data[c.key] = evalForm[c.key] }
      if (evalForm.recommandation_embauche) data.recommandation_embauche = evalForm.recommandation_embauche
      if (evalForm.commentaire) data.commentaire = evalForm.commentaire
      await saveEvaluation(id, data); alert('Évaluation enregistrée avec succès'); loadData()
    } catch (err) { alert(err.response?.data?.detail || "Erreur lors de l'enregistrement") }
    finally { setSavingEval(false) }
  }

  if (loading) return <div className="page"><div className="loading-spinner" /><p>Chargement...</p></div>
  if (error || !stagiaire) return <div className="page"><div className="table-error">{error || 'Stagiaire introuvable'}</div></div>

  const statutStage = stagiaire.statut_stage
  const statutDossier = stagiaire.statut_dossier
  const suspended = isSuspended(statutStage)
  const isEnCours = statutStage === STATUT_STAGE.STAGE_EN_COURS
  const isNonDebute = statutStage === STATUT_STAGE.STAGE_NON_DEBUTE
  const isTermine = statutStage === STATUT_STAGE.STAGE_TERMINE
  const isValide = statutStage === STATUT_STAGE.STAGE_VALIDE
  const isRefuse = statutStage === STATUT_STAGE.STAGE_REFUSE

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link"><ArrowLeft size={14} /> Retour à la liste</Link>
          <h1 className="page-title">{stagiaire.civilite ? stagiaire.civilite + ' ' : ''}{stagiaire.nom_complet}</h1>
        </div>
        <div className="header-actions">
          <StatusBadge statut={statutStage} type="stage" />
          {stagiaire.is_extended && <span className="status-badge" style={{ backgroundColor: prolongationBadge.bg, color: prolongationBadge.color, borderColor: prolongationBadge.color }}>{prolongationBadge.label}</span>}
          {statutDossier ? <StatusBadge statut={statutDossier} type="dossier" /> : <StatusBadge statut={STATUT_DOSSIER.ATTESTATION_NON_GENEREE} type="dossier" />}
          {(user?.role === 'RH' || user?.role === 'Admin') && (
            <>
              <button className="btn btn-outline" onClick={() => navigate(`/stagiaires/${id}/modifier`)}><FileSignature size={14} /> Modifier</button>
              <button className="btn btn-danger" onClick={handleDelete}><Trash2 size={14} /> Supprimer</button>
            </>
          )}
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-card">
          <h3 className="card-title">Informations personnelles</h3>
          <div className="detail-fields">
            <div className="detail-field"><span>Nom et prénom</span><span>{stagiaire.nom_complet}</span></div>
            <div className="detail-field"><span>Civilité</span><span>{stagiaire.civilite || '—'}</span></div>
            <div className="detail-field"><span>Date de naissance</span><span>{stagiaire.date_naissance ? new Date(stagiaire.date_naissance).toLocaleDateString('fr-FR') : '—'}</span></div>
            <div className="detail-field"><span>CIN</span><span>{stagiaire.cin}</span></div>
            <div className="detail-field"><span>Téléphone</span><span>{stagiaire.country_code} {stagiaire.telephone}</span></div>
            <div className="detail-field"><span>Email</span><span>{stagiaire.email}</span></div>
            <div className="detail-field"><span>École</span><span>{stagiaire.ecole || '—'}</span></div>
            <div className="detail-field"><span>Lettre d'affectation</span><span>{stagiaire.lettre_affectation ? 'Oui' : 'Non'}</span></div>
          </div>
        </div>

        <div className="detail-card">
          <h3 className="card-title">Détails du stage</h3>
          <div className="detail-fields">
            <div className="detail-field"><span>Encadrant</span><span>{stagiaire.encadrant_nom || '—'}</span></div>
            <div className="detail-field"><span>Date début</span><span>{stagiaire.date_debut_stage ? new Date(stagiaire.date_debut_stage).toLocaleDateString('fr-FR') : '—'}</span></div>
            <div className="detail-field"><span>Date fin</span><span>{stagiaire.date_fin_stage ? new Date(stagiaire.date_fin_stage).toLocaleDateString('fr-FR') : '—'}</span></div>
            {stagiaire.is_extended && stagiaire.old_date_fin_stage && (
              <div className="detail-field"><span>Ancienne date fin</span><span style={{ textDecoration: 'line-through', color: '#9ca3af' }}>{new Date(stagiaire.old_date_fin_stage).toLocaleDateString('fr-FR')}</span></div>
            )}
            <div className="detail-field"><span>Période</span><span>{stagiaire.periode_stage || '—'}</span></div>
            <div className="detail-field"><span>Service</span><span>{stagiaire.service || '—'}</span></div>
            <div className="detail-field"><span>Taille</span><span>{stagiaire.taille || '—'}</span></div>
            <div className="detail-field"><span>Pointure</span><span>{stagiaire.pointure || '—'}</span></div>
          </div>
        </div>
      </div>

      {(user?.role === 'Encadrant' || user?.role === 'RH' || user?.role === 'Admin') && (
        <div className="detail-card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h3 className="card-title" style={{ margin: 0 }}>Stage</h3>
              <StatusBadge statut={statutStage} type="stage" />
              {stagiaire.is_extended && <span className="status-badge" style={{ backgroundColor: prolongationBadge.bg, color: prolongationBadge.color, borderColor: prolongationBadge.color }}>{prolongationBadge.label}</span>}
              <span style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 4px' }}>|</span>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Dossier :</span>
              {statutDossier ? (
                <StatusBadge statut={statutDossier} type="dossier" />
              ) : (
                <StatusBadge statut={STATUT_DOSSIER.ATTESTATION_NON_GENEREE} type="dossier" />
              )}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              {suspended && (
                <button className="btn btn-sm btn-primary" onClick={handleReprendre} disabled={changingStatut}>
                  <Play size={14} /> Reprendre
                </button>
              )}
              {(isEnCours && !suspended) || isTermine ? (
                <>
                  <button className="btn btn-sm btn-success" onClick={handleValiderStage} disabled={changingStatut}><Check size={14} /> Valider</button>
                  <button className="btn btn-sm btn-danger" onClick={handleRefuserStage} disabled={changingStatut}><X size={14} /> Refuser</button>
                  {isEnCours && !suspended && <button className="btn btn-sm btn-outline" onClick={handleSuspendre} disabled={changingStatut}><Pause size={14} /> Suspendre</button>}
                </>
              ) : null}
              {isTermine && (
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Stage terminé</span>
              )}
              {isValide && (
                <span style={{ fontSize: 13, color: '#16a34a', fontWeight: 500 }}>Stage validé</span>
              )}
              {isRefuse && (
                <span style={{ fontSize: 13, color: '#dc2626', fontWeight: 500 }}>Stage refusé</span>
              )}
            </div>
          </div>
          {(suspended || stagiaire.suspended_at) && (
            <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <div>Suspendu le : {stagiaire.suspended_at ? `${new Date(stagiaire.suspended_at).toLocaleDateString('fr-FR')} à ${new Date(stagiaire.suspended_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : 'Date inconnue'}</div>
              {stagiaire.resumed_at && (
                <div>Repris le : {new Date(stagiaire.resumed_at).toLocaleDateString('fr-FR')} à {new Date(stagiaire.resumed_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="detail-card">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 16 }}>
          <h3 className="card-title" style={{ margin: 0, paddingBottom: 0, borderBottom: 'none' }}>Rapport de stage</h3>
          <span style={{
            fontSize: 13,
            fontWeight: 500,
            color: rapports.length > 0 ? '#16a34a' : '#6b7280',
            lineHeight: '1.4',
          }}>
            {rapports.length > 0 ? 'Rapport déposé' : 'Rapport non déposé'}
          </span>
        </div>
        {rapports.length > 0 ? (
          <ul className="file-list">
            {rapports.map((r) => {
              const fileName = r.file_pdf ? r.file_pdf.split(/[/\\]/).pop() : 'rapport.pdf'
              return (
                <li key={r.id} className="file-item">
                  <FileText size={18} className="file-icon" />
                  <span className="file-name">{fileName}</span>
                  <small>{r.created_at ? new Date(r.created_at).toLocaleDateString('fr-FR') : ''}</small>
                  <button className="btn btn-sm btn-outline" onClick={() => handleDownloadRapport(r.id, fileName)}><Download size={14} /> Télécharger</button>
                  {(user?.role === 'RH' || user?.role === 'Admin') && (
                    <button className="btn btn-sm btn-danger" onClick={() => handleDeleteRapport(r.id)}><Trash2 size={14} /></button>
                  )}
                </li>
              )
            })}
          </ul>
        ) : <p className="text-muted">Aucun rapport uploadé</p>}
        <div className="rapport-actions">
          {((user?.role === 'Encadrant' && stagiaire.encadrant_id === user?.id) || user?.role === 'RH' || user?.role === 'Admin') && (
            <label className="btn btn-outline" style={{ cursor: 'pointer' }}>
              <Upload size={14} />
              {uploading ? 'Upload...' : 'Uploader un rapport PDF'}
              <input type="file" accept=".pdf" onChange={handleUpload} hidden disabled={uploading} />
            </label>
          )}
        </div>
      </div>

      <div className="detail-card">
        <h3 className="card-title">Attestations</h3>
        {attestations.length > 0 ? (
          <ul className="file-list">
            {attestations.map((a) => (
              <li key={a.id} className="file-item">
                <FileText size={18} className="file-icon" />
                <span className="attestation-link" onClick={() => handlePreviewAttestation(a)}>{a.numero_attestation}</span>
                <small>{a.created_at ? new Date(a.created_at).toLocaleDateString('fr-FR') : ''}</small>
                <button className="btn btn-sm btn-outline" onClick={() => handleDownloadAttestation(a.id, a.numero_attestation)}><Download size={14} /> Télécharger</button>
                <button className="btn btn-sm btn-outline" onClick={() => handlePrintAttestation(a.id)}><Printer size={14} /></button>
      {(user?.role === 'Encadrant' || user?.role === 'RH' || user?.role === 'Admin') && (
                  <>
                    <button className="btn btn-sm btn-primary" onClick={() => handleSendAttestation(a.id)} disabled={sendingId === a.id}>
                      {sendingId === a.id ? <Loader2 size={14} className="spin" /> : <Send size={14} />} Envoyer
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDeleteAttestation(a.id)}><Trash2 size={14} /></button>
                  </>
                )}
              </li>
            ))}
          </ul>
        ) : <p className="text-muted">Aucune attestation générée</p>}
        {(user?.role === 'RH' || user?.role === 'Admin') && !suspended && !isNonDebute && (
          <div style={{ marginTop: 16 }}>
            {(attestations.length === 0 || attestationOutdated) && (
              <button className="btn btn-primary" onClick={() => navigate(`/stagiaires/${id}/attestation`)}>
                <FileText size={14} />
                {attestationOutdated ? 'Régénérer' : "Générer l'attestation"}
              </button>
            )}
          </div>
        )}
      </div>

      {user?.role === 'Encadrant' && stagiaire.encadrant_id === user?.id && (
        <div className="evaluation-card">
          <h3 className="card-title"><Star size={18} fill="#f59e0b" color="#f59e0b" /> Évaluation du stagiaire</h3>
          <div className="criteria-grid">
            {CRITERES.map((c) => (
              <div key={c.key} className="criterion-item">
                <span className="criterion-label">{c.label}</span>
                <StarRating value={evalForm[c.key] || 0} onChange={(v) => setEvalForm((prev) => ({ ...prev, [c.key]: v }))} />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20 }}>
            <span className="criterion-label">Recommandation d'embauche</span>
            <div className="recommandation-group">
              {[{ value: 'oui', label: 'Oui' }, { value: 'non', label: 'Non' }, { value: 'a_considerer', label: 'À considérer' }].map((opt) => (
                <label key={opt.value}>
                  <input type="radio" name="recommandation" value={opt.value} checked={evalForm.recommandation_embauche === opt.value} onChange={(e) => setEvalForm((prev) => ({ ...prev, recommandation_embauche: e.target.value }))} />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>
          <div className="evaluation-comment">
            <label>Commentaire de l'encadrant</label>
            <textarea className="form-textarea" rows={4} maxLength={2000} placeholder="Excellent stagiaire, très autonome..." value={evalForm.commentaire || ''} onChange={(e) => setEvalForm((prev) => ({ ...prev, commentaire: e.target.value }))} />
          </div>
          <div className="evaluation-actions">
            <button className="btn btn-primary" onClick={handleSaveEvaluation} disabled={savingEval}>
              {savingEval ? <Loader2 size={14} className="spin" /> : null}
              {evaluation ? "Modifier l'évaluation" : "Enregistrer l'évaluation"}
            </button>
          </div>
        </div>
      )}

      {evaluation && !(user?.role === 'Encadrant' && stagiaire.encadrant_id === user?.id) && (
        <div className="evaluation-card evaluation-read-only">
          <h3 className="card-title"><Star size={18} fill="#f59e0b" color="#f59e0b" /> Évaluation du stagiaire</h3>
          <div className="evaluation-summary">
            {CRITERES.map((c) => {
              const val = evaluation[c.key]
              if (!val) return null
              return (
                <div key={c.key} className="summary-row">
                  <span className="summary-label">{c.label}</span>
                  <span className="summary-value">
                    <span className="summary-stars">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <Star key={n} size={14} className={n <= val ? 'star-icon' : 'star-icon star-empty'} fill={n <= val ? '#f59e0b' : 'none'} />
                      ))}
                    </span>
                    {val}/5
                  </span>
                </div>
              )
            })}
            {evaluation.recommandation_embauche && (
              <div className="summary-row">
                <span className="summary-label">Recommandation d'embauche</span>
                <span className="summary-value">
                  {evaluation.recommandation_embauche === 'oui' ? 'Oui' : evaluation.recommandation_embauche === 'non' ? 'Non' : 'À considérer'}
                </span>
              </div>
            )}
            {evaluation.commentaire && (
              <div style={{ marginTop: 12 }}>
                <span className="summary-label" style={{ fontSize: 14, fontWeight: 500 }}>Commentaire</span>
                <p style={{ marginTop: 4, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{evaluation.commentaire}</p>
              </div>
            )}
          </div>
          <div className="evaluation-meta">
            Évalué par {evaluation.encadrant_nom || '—'}
            {evaluation.date_modification && <> · Modifié le {new Date(evaluation.date_modification).toLocaleDateString('fr-FR')}</>}
          </div>
        </div>
      )}

      {previewAttestation && previewUrl && (
        <div className="modal-overlay" onClick={handleClosePreview}>
          <div className="modal-content attestation-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Aperçu - {previewAttestation.numero_attestation}</h3>
              <button className="btn btn-sm btn-outline" onClick={handleClosePreview}><X size={16} /></button>
            </div>
            <div className="attestation-pdf-container">
              <iframe src={previewUrl} className="attestation-pdf-iframe" title="Apercu attestation" />
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={() => handleDownloadAttestation(previewAttestation.id, previewAttestation.numero_attestation)}><Download size={16} /> Télécharger</button>
              <button className="btn btn-outline" onClick={() => handlePrintAttestation(previewAttestation.id)}><Printer size={16} /> Imprimer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
