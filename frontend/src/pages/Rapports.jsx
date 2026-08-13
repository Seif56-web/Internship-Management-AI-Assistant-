import { useState, useEffect, useRef } from 'react'
import { getStagiaires } from '../services/stagiaires'
import { getRapports } from '../services/rapports'
import StatusBadge from '../components/StatusBadge'
import { STATUT_STAGE, STATUT_DOSSIER } from '../constants/statuses'
import api from '../services/api'
import { FolderOpen, Eye, X } from 'lucide-react'

const PERIODE_OPTIONS = ['Été', 'Automne', 'Hiver', 'PFE']

const RAPPORT_VISIBLE_STAGES = [
  STATUT_STAGE.STAGE_TERMINE,
  STATUT_STAGE.STAGE_VALIDE,
  STATUT_STAGE.STAGE_REFUSE,
]

export default function Rapports() {
  const [stagiaires, setStagiaires] = useState([])
  const [rapportsMap, setRapportsMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [periodeFilter, setPeriodeFilter] = useState([])
  const [showPeriodeDropdown, setShowPeriodeDropdown] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowPeriodeDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const data = await getStagiaires()
      const filtered = data.filter((s) =>
        RAPPORT_VISIBLE_STAGES.includes(s.statut_stage)
      )
      setStagiaires(filtered)

      const map = {}
      await Promise.all(
        filtered.map(async (s) => {
          try {
            const r = await getRapports(s.id)
            map[s.id] = r.length > 0 ? r[0] : null
          } catch {
            map[s.id] = null
          }
        })
      )
      setRapportsMap(map)
    } catch {
      //
    } finally {
      setLoading(false)
    }
  }

  const handleViewRapport = async (rapport) => {
    try {
      const response = await api.get(`/rapports/download/${rapport.id}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      window.open(url, '_blank')
    } catch {
      alert('Erreur lors de l\'ouverture du rapport')
    }
  }

  if (loading) return <div className="page"><div className="loading-spinner" /></div>

  const displayed = periodeFilter.length > 0
    ? stagiaires.filter(s => periodeFilter.includes(s.periode_stage))
    : stagiaires

  const togglePeriode = (p) => {
    setPeriodeFilter(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Rapports de stage</h1>
      </div>

      <div className="rapports-filter">
        <div className="filter-advanced-toggle-wrapper" ref={dropdownRef}>
          <button
            className={`filter-advanced-toggle ${periodeFilter.length ? 'active' : ''}`}
            onClick={() => setShowPeriodeDropdown(!showPeriodeDropdown)}
          >
            Période
            {periodeFilter.length > 0 && <span className="filter-dot" />}
          </button>
          {showPeriodeDropdown && (
            <div className="ms-dropdown" style={{ display: 'block' }}>
              {PERIODE_OPTIONS.map(p => (
                <label key={p} className="ms-option">
                  <input
                    type="checkbox"
                    checked={periodeFilter.includes(p)}
                    onChange={() => togglePeriode(p)}
                  />
                  <span>{p}</span>
                </label>
              ))}
            </div>
          )}
        </div>
        {periodeFilter.length > 0 && (
          <div className="rapports-chips">
            {periodeFilter.map(p => (
              <span key={p} className="ms-chip">
                <span className="ms-chip-text">{p}</span>
                <button className="ms-chip-remove" onClick={() => togglePeriode(p)}>
                  <span className="ms-x">×</span>
                </button>
              </span>
            ))}
            <button className="filter-reset" onClick={() => setPeriodeFilter([])}>
              <X size={14} />
              Réinitialiser
            </button>
          </div>
        )}
      </div>

      {displayed.length === 0 ? (
        <div className="table-empty">
          <FolderOpen size={48} className="empty-icon" />
          <p>{stagiaires.length === 0 ? 'Aucun rapport disponible' : 'Aucun rapport pour cette période'}</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="stagiaire-table">
            <thead>
              <tr>
                <th>Stagiaire</th>
                <th>Période</th>
                <th>Stage</th>
                <th>Dossier</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map((s) => {
                const rapport = rapportsMap[s.id]
                return (
                  <tr key={s.id}>
                    <td>{s.nom_complet}</td>
                    <td>{s.periode_stage || '—'}</td>
                    <td><StatusBadge statut={s.statut_stage} type="stage" /></td>
                    <td>{s.statut_dossier ? <StatusBadge statut={s.statut_dossier} type="dossier" /> : <StatusBadge statut={STATUT_DOSSIER.ATTESTATION_NON_GENEREE} type="dossier" />}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        disabled={!rapport}
                        title={!rapport ? 'Aucun rapport uploadé' : ''}
                        onClick={() => rapport && handleViewRapport(rapport)}
                      >
                        <Eye size={14} />
                        Voir
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
