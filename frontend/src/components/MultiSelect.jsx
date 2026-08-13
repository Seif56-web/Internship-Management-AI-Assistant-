import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'

export default function MultiSelect({ label, options, selected, onChange, placeholder, compact, searchable }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggle = (value) => {
    if (selected.includes(value)) {
      onChange(selected.filter(v => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  const hasSelection = selected.length > 0
  const q = query.trim().toLowerCase()
  const filteredOptions = searchable && q
    ? options.filter(opt => (opt.label || '').toLowerCase().includes(q))
    : options

  return (
    <div className="ms-wrapper" ref={ref}>
      {!compact && (
        <div className="ms-chips-row">
          <span className="ms-label">{label}</span>
          {selected.map(val => {
            const opt = options.find(o => o.value === val)
            return (
              <span key={val} className="ms-chip">
                <span className="ms-chip-text">{opt?.label || val}</span>
                <button className="ms-chip-remove" onClick={() => onChange(selected.filter(v => v !== val))}>
                  <span className="ms-x">×</span>
                </button>
              </span>
            )
          })}
        </div>
      )}

      <button
        className={`ms-trigger ${open ? 'open' : ''} ${hasSelection ? 'has-value' : ''}`}
        onClick={() => { setOpen(!open); setQuery('') }}
      >
        <span className="ms-trigger-text">
          {hasSelection ? `${selected.length} sélectionné${selected.length > 1 ? 's' : ''}` : placeholder}
        </span>
        <ChevronDown size={14} className={`ms-trigger-arrow ${open ? 'rotated' : ''}`} />
      </button>

      {open && (
        <div className="ms-dropdown">
          {searchable && (
            <div className="ms-search">
              <input
                type="text"
                className="ms-search-input"
                placeholder="Rechercher..."
                value={query}
                autoFocus
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          )}
          {filteredOptions.length === 0 ? (
            <div className="ms-empty">Aucun résultat</div>
          ) : (
            filteredOptions.map(opt => {
              const isSelected = selected.includes(opt.value)
              return (
                <div
                  key={opt.value}
                  className={`ms-option ${isSelected ? 'selected' : ''}`}
                  onClick={() => toggle(opt.value)}
                >
                  <span className={`ms-checkbox ${isSelected ? 'checked' : ''}`}>
                    {isSelected && <Check size={10} />}
                  </span>
                  <span className="ms-option-label">{opt.label}</span>
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
