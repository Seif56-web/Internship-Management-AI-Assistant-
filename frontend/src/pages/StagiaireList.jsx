import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import FilterPanel from '../components/FilterPanel'
import StagiaireTable from '../components/StagiaireTable'
import ImportModal from '../components/ImportModal'
import { useStagiaires } from '../hooks/useStagiaires'
import { useAuth } from '../hooks/useAuth'
import { deleteStagiaires } from '../services/stagiaires'
import { getAttestations, getDownloadUrl } from '../services/attestations'
import api from '../services/api'
import { Upload, FileDown, X, Download, Printer, Trash2, Loader2 } from 'lucide-react'

const initialFilters = {
  search: '',
  statuts_stage: [],
  statuts_dossier: [],
  periodes: [],
  encadrant_ids: [],
  date_min: '',
  date_max: '',
}

export default function StagiaireList({ filter: initialFilter }) {
  const [filters, setFilters] = useState(() => {
    if (initialFilter) return { ...initialFilters, statuts_stage: [initialFilter] }
    return initialFilters
  })
  const [showImport, setShowImport] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewTitle, setPreviewTitle] = useState('')
  const [previewId, setPreviewId] = useState(null)
  const [selectedIds, setSelectedIds] = useState([])
  const [selectionMode, setSelectionMode] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [encadrantRefresh, setEncadrantRefresh] = useState(0)
  const { user } = useAuth()
  const navigate = useNavigate()
  const canManage = user?.role === 'RH' || user?.role === 'Admin'

  const rapportsFilters = filters.statuts_dossier.filter(s => s.startsWith('Rapport'))
  const dossierFilters = filters.statuts_dossier.filter(s => !s.startsWith('Rapport'))

  useEffect(() => {
    setSelectedIds([])
    setSelectionMode(false)
  }, [filters])
  const params = {}
  if (filters.search) params.search = filters.search
  if (filters.statuts_stage.length) params.statut = filters.statuts_stage.join(',')
  if (dossierFilters.length) params.statut_dossier = dossierFilters.join(',')
  if (rapportsFilters.length) params.statut_rapport = rapportsFilters.join(',')
  if (filters.periodes.length) params.periode = filters.periodes.join(',')
  if (filters.encadrant_ids.length) params.encadrant_id = filters.encadrant_ids.join(',')
  if (filters.date_min) params.date_min = filters.date_min
  if (filters.date_max) params.date_max = filters.date_max

  const { stagiaires, loading, error, refetch } = useStagiaires(params)

  const handleGenerate = useCallback((stagiaire) => {
    navigate(`/stagiaires/${stagiaire.id}/attestation`)
  }, [navigate])

  const handleImportComplete = () => {
    setShowImport(false)
    setEncadrantRefresh((n) => n + 1)
    refetch()
  }

  const handleToggleSelect = (id) => {
    setSelectionMode(true)
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const handleSelectAll = (ids) => {
    setSelectionMode(true)
    setSelectedIds(ids)
  }

  const handleCancelSelection = () => {
    setSelectedIds([])
    setSelectionMode(false)
  }

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) return
    if (!confirm(`Supprimer définitivement ${selectedIds.length} stagiaire(s) sélectionné(s) ? Cette action est irréversible.`)) return
    setDeleting(true)
    try {
      await deleteStagiaires(selectedIds)
      setSelectedIds([])
      setSelectionMode(false)
      setEncadrantRefresh((n) => n + 1)
      refetch()
      alert(`${selectedIds.length} stagiaire(s) supprimé(s) avec succès`)
    } catch (err) {
      alert(err.response?.data?.detail || 'Erreur lors de la suppression')
    } finally {
      setDeleting(false)
    }
  }

  const handleExport = async () => {
    const rapportsFilters = filters.statuts_dossier.filter(s => s.startsWith('Rapport'))
    const dossierFilters = filters.statuts_dossier.filter(s => !s.startsWith('Rapport'))
    const params = {}
    if (filters.search) params.search = filters.search
    if (filters.statuts_stage.length) params.statut = filters.statuts_stage.join(',')
    if (dossierFilters.length) params.statut_dossier = dossierFilters.join(',')
    if (rapportsFilters.length) params.statut_rapport = rapportsFilters.join(',')
    if (filters.periodes.length) params.periode = filters.periodes.join(',')
    if (filters.encadrant_ids.length) params.encadrant_id = filters.encadrant_ids.join(',')
    if (filters.date_min) params.date_min = filters.date_min
    if (filters.date_max) params.date_max = filters.date_max
    try {
      const response = await api.get('/stagiaires/export/excel', { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      const disposition = response.headers['content-disposition']
      const match = disposition && disposition.match(/filename=(.+)/)
      link.setAttribute('download', match ? match[1] : `Stagiaires_${new Date().toISOString().slice(0, 10)}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      alert("Erreur lors de l'export Excel")
    }
  }

  const hasAttestationFilter = dossierFilters.some(s =>
    s === 'Attestation générée' || s === 'Attestation envoyée'
  )

  const handleRowClick = useCallback(async (stagiaire) => {
    if (!hasAttestationFilter) {
      navigate(`/stagiaires/${stagiaire.id}`)
      return
    }
    try {
      const attests = await getAttestations(stagiaire.id)
      if (attests.length === 0) return
      const a = attests[0]
      setPreviewId(a.id)
      setPreviewTitle(a.numero_attestation || `Attestation - ${stagiaire.nom_complet}`)
      setPreviewUrl(getDownloadUrl(a.id))
    } catch { }
  }, [hasAttestationFilter, navigate])

  const handleClosePreview = () => {
    setPreviewUrl(null)
    setPreviewTitle('')
    setPreviewId(null)
  }

  const handlePrint = async () => {
    if (!previewId) return
    try {
      const response = await fetch(getDownloadUrl(previewId))
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const iframe = document.createElement('iframe')
      iframe.style.display = 'none'
      iframe.src = url
      document.body.appendChild(iframe)
      iframe.onload = () => {
        iframe.contentWindow.print()
        setTimeout(() => { document.body.removeChild(iframe); window.URL.revokeObjectURL(url) }, 1000)
      }
    } catch { alert("Erreur lors de l'impression") }
  }

  const pageTitle = hasAttestationFilter ? 'Attestations' : 'Stagiaires'

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{pageTitle}</h1>
        {canManage && !hasAttestationFilter && (
          <div style={{ display: 'flex', gap: 8 }}>
            {selectedIds.length > 0 && (
              <button className="btn btn-danger" onClick={handleBatchDelete} disabled={deleting}>
                {deleting ? <Loader2 size={16} className="spin" /> : <Trash2 size={16} />}
                Supprimer ({selectedIds.length})
              </button>
            )}
            {selectionMode && (
              <button className="btn btn-outline" onClick={handleCancelSelection}>
                <X size={16} /> Annuler la sélection
              </button>
            )}
            <button className="btn btn-primary" onClick={() => setShowImport(true)}>
              <Upload size={16} /> Importer des stagiaires
            </button>
            <button className="btn btn-outline" onClick={handleExport}>
              <FileDown size={16} /> Exporter en Excel
            </button>
          </div>
        )}
      </div>

      <FilterPanel filters={filters} onFiltersChange={setFilters} totalCount={stagiaires.length} encadrantRefresh={encadrantRefresh} />

      <StagiaireTable
        stagiaires={stagiaires}
        loading={loading}
        error={error}
        onGenerate={handleGenerate}
        onRowClick={handleRowClick}
        selectedIds={canManage && !hasAttestationFilter ? selectedIds : []}
        onToggleSelect={canManage && !hasAttestationFilter ? handleToggleSelect : undefined}
        onSelectAll={canManage && !hasAttestationFilter ? handleSelectAll : undefined}
        selectionMode={canManage && !hasAttestationFilter ? selectionMode : false}
      />

      {showImport && <ImportModal onClose={() => setShowImport(false)} onComplete={handleImportComplete} />}

      {previewUrl && (
        <div className="modal-overlay" onClick={handleClosePreview}>
          <div className="modal-content attestation-preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{previewTitle}</h3>
              <button className="btn btn-sm btn-outline" onClick={handleClosePreview}><X size={16} /></button>
            </div>
            <div className="attestation-pdf-container">
              <iframe src={previewUrl} className="attestation-pdf-iframe" title="Apercu attestation" />
            </div>
            <div className="modal-actions">
              <a href={previewUrl} download className="btn btn-primary"><Download size={16} /> Télécharger</a>
              <button className="btn btn-outline" onClick={handlePrint}><Printer size={16} /> Imprimer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
