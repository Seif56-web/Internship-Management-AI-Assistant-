import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBadge from './StatusBadge'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../context/ThemeContext'
import { STATUT_STAGE, STATUT_DOSSIER, isSuspended, PROLONGATION_BADGE, PROLONGATION_BADGE_DARK } from '../constants/statuses'
import { ClipboardList, FileText, Plus, Download, Printer, Send, Loader2 } from 'lucide-react'
import api from '../services/api'

export default function StagiaireTable({ stagiaires, loading, error, onGenerate, onRowClick, selectedIds = [], onToggleSelect, onSelectAll, selectionMode = false }) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { theme } = useTheme()
  const prolongationBadge = theme === 'dark' ? PROLONGATION_BADGE_DARK : PROLONGATION_BADGE
  const [sendingId, setSendingId] = useState(null)
  const selectionEnabled = typeof onToggleSelect === 'function'
  const showSelection = selectionEnabled && selectionMode

  const handleRowClick = (e, s) => {
    if (selectionEnabled && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      e.stopPropagation()
      onToggleSelect(s.id)
      return
    }
    if (onRowClick) onRowClick(s)
    else navigate(`/stagiaires/${s.id}`)
  }

  const allSelected = stagiaires.length > 0 && stagiaires.every((s) => selectedIds.includes(s.id))

  const handleDownload = async (e, s) => {
    e.stopPropagation()
    try {
      const response = await api.get(`/attestations/download/${s.attestation_id}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `attestation_${s.attestation_numero || s.nom_complet}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Erreur lors du téléchargement')
    }
  }

  const handlePrint = async (e, attestationId) => {
    e.stopPropagation()
    try {
      const response = await api.get(`/attestations/download/${attestationId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const iframe = document.createElement('iframe')
      iframe.style.display = 'none'
      iframe.src = url
      document.body.appendChild(iframe)
      iframe.onload = () => {
        iframe.contentWindow.print()
        setTimeout(() => {
          document.body.removeChild(iframe)
          window.URL.revokeObjectURL(url)
        }, 1000)
      }
    } catch {
      alert('Erreur lors de l\'impression')
    }
  }

  const handleSend = async (e, s) => {
    e.stopPropagation()
    setSendingId(s.attestation_id)
    try {
      await api.post(`/attestations/send/${s.attestation_id}`)
      alert('Attestation envoyée avec succès')
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de l\'envoi')
    } finally {
      setSendingId(null)
    }
  }

  if (loading) {
    return (
      <div className="table-loading">
        <div className="loading-spinner" />
        <p>Chargement des stagiaires...</p>
      </div>
    )
  }

  if (error) {
    return <div className="table-error">{error}</div>
  }

  if (!stagiaires || stagiaires.length === 0) {
    return (
      <div className="table-empty">
        <ClipboardList size={48} className="empty-icon" />
        <h3>Aucun stagiaire trouvé</h3>
        <p>Commencez par ajouter un nouveau stagiaire.</p>
        {user?.role !== 'Encadrant' && (
          <button className="btn btn-primary" onClick={() => navigate('/stagiaires/ajouter')}>
            <Plus size={16} />
            Ajouter un stagiaire
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="table-container">
      <table className="stagiaire-table">
        <thead>
          <tr>
            {showSelection && (
              <th className="select-col">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={() => onSelectAll && onSelectAll(allSelected ? [] : stagiaires.map((s) => s.id))}
                  title="Tout sélectionner"
                />
              </th>
            )}
            <th>Nom et prénom</th>
            <th>Encadrant</th>
            <th>Début</th>
            <th>Fin</th>
            <th>Stage</th>
            <th>Dossier</th>
            {(user?.role === 'RH' || user?.role === 'Admin') && <th>Action</th>}
          </tr>
        </thead>
        <tbody>
          {stagiaires.map((s) => (
            <tr
              key={s.id}
              onClick={(e) => handleRowClick(e, s)}
              className={`clickable-row ${showSelection && selectedIds.includes(s.id) ? 'row-selected' : ''}`}
            >
              {showSelection && (
                <td className="select-col">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(s.id)}
                    onChange={(e) => { e.stopPropagation(); onToggleSelect(s.id) }}
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
              )}
              <td>{s.nom_complet}</td>
              <td>{s.encadrant_nom || '—'}</td>
              <td>{s.date_debut_stage ? new Date(s.date_debut_stage).toLocaleDateString('fr-FR') : '—'}</td>
              <td>{s.date_fin_stage ? new Date(s.date_fin_stage).toLocaleDateString('fr-FR') : '—'}</td>
              <td>
                <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexWrap: 'wrap' }}>
                  <StatusBadge statut={s.statut_stage} type="stage" />
                  {s.is_extended && <span className="status-badge" style={{ backgroundColor: prolongationBadge.bg, color: prolongationBadge.color, borderColor: prolongationBadge.color }}>{prolongationBadge.label}</span>}
                </div>
              </td>
              <td>
                {s.statut_dossier ? <StatusBadge statut={s.statut_dossier} type="dossier" /> : <StatusBadge statut={STATUT_DOSSIER.ATTESTATION_NON_GENEREE} type="dossier" />}
              </td>
              {(user?.role === 'RH' || user?.role === 'Admin') && (
                <td>
                  {s.attestation_id ? (
                    <div className="table-actions">
                      <button className="btn btn-sm btn-outline" onClick={(e) => handleDownload(e, s)} title="Télécharger">
                        <Download size={14} />
                      </button>
                      <button className="btn btn-sm btn-outline" onClick={(e) => handlePrint(e, s.attestation_id)} title="Imprimer">
                        <Printer size={14} />
                      </button>
                      <button className="btn btn-sm btn-primary" onClick={(e) => handleSend(e, s)} title="Envoyer" disabled={sendingId === s.attestation_id}>
                        {sendingId === s.attestation_id ? <Loader2 size={14} className="spin" /> : <Send size={14} />}
                      </button>
                    </div>
                  ) : (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={(e) => { e.stopPropagation(); onGenerate(s) }}
                      disabled={s.statut_stage === STATUT_STAGE.STAGE_NON_DEBUTE}
                      title={s.statut_stage === STATUT_STAGE.STAGE_NON_DEBUTE ? 'Stage non débuté' : 'Générer attestation'}
                    >
                      <FileText size={14} />
                      Générer
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
