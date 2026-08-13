import { useState, useEffect } from 'react'
import { Search, X, SlidersHorizontal } from 'lucide-react'
import { STATUT_STAGE, STATUT_DOSSIER } from '../constants/statuses'
import { getEncadrants } from '../services/encadrants'
import MultiSelect from './MultiSelect'

const STATUT_STAGE_OPTIONS = [
  { value: STATUT_STAGE.STAGE_NON_DEBUTE, label: 'Stage non débuté' },
  { value: STATUT_STAGE.STAGE_EN_COURS, label: 'Stage en cours' },
  { value: STATUT_STAGE.STAGE_SUSPENDU, label: 'Stage suspendu' },
  { value: STATUT_STAGE.STAGE_TERMINE, label: 'Stage terminé' },
  { value: STATUT_STAGE.STAGE_VALIDE, label: 'Stage validé' },
  { value: STATUT_STAGE.STAGE_REFUSE, label: 'Stage refusé' },
]

const STATUT_DOSSIER_OPTIONS = [
  { value: 'Rapport déposé', label: 'Rapport déposé' },
  { value: 'Rapport non déposé', label: 'Rapport non déposé' },
  { value: STATUT_DOSSIER.ATTESTATION_GENEREE, label: 'Attestation générée' },
  { value: STATUT_DOSSIER.ATTESTATION_ENVOYEE, label: 'Attestation envoyée' },
]

const PERIODE_OPTIONS = [
  { value: 'Été', label: 'Été' },
  { value: 'Automne', label: 'Automne' },
  { value: 'Hiver', label: 'Hiver' },
  { value: 'PFE', label: 'PFE' },
]

const initialFilters = {
  search: '',
  statuts_stage: [],
  statuts_dossier: [],
  periodes: [],
  encadrant_ids: [],
  date_min: '',
  date_max: '',
}

const formatDate = (iso) => {
  if (!iso) return ''
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function FilterPanel({ filters, onFiltersChange, totalCount, encadrantRefresh = 0 }) {
  const [encadrants, setEncadrants] = useState([])
  const [showDates, setShowDates] = useState(false)

  useEffect(() => {
    getEncadrants().then(setEncadrants).catch(() => {})
  }, [encadrantRefresh])

  useEffect(() => {
    if (filters.date_min || filters.date_max) setShowDates(true)
  }, [filters.date_min, filters.date_max])

  const encadrantOptions = encadrants.map(enc => ({
    value: enc.user_id,
    label: [enc.prenom, enc.nom].filter(Boolean).join(' '),
  }))

  const update = (key, value) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const handleReset = () => {
    onFiltersChange(initialFilters)
    setShowDates(false)
  }

  const hasAnyFilter = filters.search || filters.statuts_stage.length || filters.statuts_dossier.length ||
    filters.periodes.length || filters.encadrant_ids.length || filters.date_min || filters.date_max

  const hasDateFilters = filters.date_min || filters.date_max

  return (
    <div className="filter-panel">
      <div className="filter-panel-header">
        <div className="filter-panel-title">
          <SlidersHorizontal size={16} />
          <span>Filtres</span>
        </div>
        <span className="filter-count">{totalCount} stagiaire{totalCount !== 1 ? 's' : ''} trouvé{totalCount !== 1 ? 's' : ''}</span>
      </div>

      <div className="filter-row">
        <div className="search-container">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Rechercher par nom et prénom, ou email..."
            value={filters.search}
            onChange={(e) => update('search', e.target.value)}
          />
        </div>

        <MultiSelect
          label="Statut stage"
          placeholder="Statut stage"
          options={STATUT_STAGE_OPTIONS}
          selected={filters.statuts_stage}
          onChange={(val) => update('statuts_stage', val)}
          compact
        />

        <MultiSelect
          label="Statut dossier"
          placeholder="Statut dossier"
          options={STATUT_DOSSIER_OPTIONS}
          selected={filters.statuts_dossier}
          onChange={(val) => update('statuts_dossier', val)}
          compact
        />

        <MultiSelect
          label="Période"
          placeholder="Période"
          options={PERIODE_OPTIONS}
          selected={filters.periodes}
          onChange={(val) => update('periodes', val)}
          compact
        />

        <MultiSelect
          label="Encadrant"
          placeholder="Encadrant"
          options={encadrantOptions}
          selected={filters.encadrant_ids}
          onChange={(val) => update('encadrant_ids', val)}
          compact
          searchable
        />

        <button
          className={`filter-advanced-toggle ${showDates || hasDateFilters ? 'active' : ''}`}
          onClick={() => setShowDates(!showDates)}
        >
          Dates
          {hasDateFilters && <span className="filter-dot" />}
        </button>
      </div>

      {showDates && (
        <div className="filter-row filter-advanced">
          <div className="filter-date-group">
            <div className="filter-date-range">
              <div>
                <label className="filter-date-label">Du</label>
                <input type="date" className="filter-date-input" value={filters.date_min} onChange={(e) => update('date_min', e.target.value)} />
              </div>
              <div>
                <label className="filter-date-label">Au</label>
                <input type="date" className="filter-date-input" value={filters.date_max} onChange={(e) => update('date_max', e.target.value)} />
              </div>
            </div>
          </div>
        </div>
      )}

      {hasAnyFilter && (
        <div className="filter-active-row">
          <div className="filter-active-chips">
            {filters.statuts_stage.map(val => {
              const opt = STATUT_STAGE_OPTIONS.find(o => o.value === val)
              return (
                <span key={`ss-${val}`} className="ms-chip">
                  <span className="ms-chip-text">{opt?.label || val}</span>
                  <button className="ms-chip-remove" onClick={() => update('statuts_stage', filters.statuts_stage.filter(v => v !== val))}>
                    <span className="ms-x">×</span>
                  </button>
                </span>
              )
            })}
            {filters.statuts_dossier.map(val => {
              const opt = STATUT_DOSSIER_OPTIONS.find(o => o.value === val)
              return (
                <span key={`sd-${val}`} className="ms-chip">
                  <span className="ms-chip-text">{opt?.label || val}</span>
                  <button className="ms-chip-remove" onClick={() => update('statuts_dossier', filters.statuts_dossier.filter(v => v !== val))}>
                    <span className="ms-x">×</span>
                  </button>
                </span>
              )
            })}
            {filters.periodes.map(val => {
              const opt = PERIODE_OPTIONS.find(o => o.value === val)
              return (
                <span key={`p-${val}`} className="ms-chip">
                  <span className="ms-chip-text">{opt?.label || val}</span>
                  <button className="ms-chip-remove" onClick={() => update('periodes', filters.periodes.filter(v => v !== val))}>
                    <span className="ms-x">×</span>
                  </button>
                </span>
              )
            })}
            {filters.encadrant_ids.map(val => {
              const opt = encadrantOptions.find(o => o.value === val)
              return (
                <span key={`e-${val}`} className="ms-chip">
                  <span className="ms-chip-text">{opt?.label || val}</span>
                  <button className="ms-chip-remove" onClick={() => update('encadrant_ids', filters.encadrant_ids.filter(v => v !== val))}>
                    <span className="ms-x">×</span>
                  </button>
                </span>
              )
            })}
            {filters.date_min && (
              <span className="ms-chip">
                <span className="ms-chip-text">Après {formatDate(filters.date_min)}</span>
                <button className="ms-chip-remove" onClick={() => update('date_min', '')}><span className="ms-x">×</span></button>
              </span>
            )}
            {filters.date_max && (
              <span className="ms-chip">
                <span className="ms-chip-text">Avant {formatDate(filters.date_max)}</span>
                <button className="ms-chip-remove" onClick={() => update('date_max', '')}><span className="ms-x">×</span></button>
              </span>
            )}
          </div>
          <button className="filter-reset" onClick={handleReset}>
            <X size={14} />
            Réinitialiser les filtres
          </button>
        </div>
      )}
    </div>
  )
}
