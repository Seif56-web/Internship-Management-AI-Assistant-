import { Search } from 'lucide-react'
import { STAGE_FILTERS } from '../constants/statuses'

export default function TopBar({ search, onSearchChange, filter, onFilterChange }) {
  return (
    <div className="topbar">
      <div className="search-container">
        <Search size={16} className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Rechercher un stagiaire..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <div className="filter-container">
        {STAGE_FILTERS.map((f) => (
          <button
            key={f.value}
            className={`filter-btn ${filter === f.value ? 'active' : ''}`}
            onClick={() => onFilterChange(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  )
}
