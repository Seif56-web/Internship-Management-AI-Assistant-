import { STAGE_COLORS, DOSSIER_COLORS, STAGE_COLORS_DARK, DOSSIER_COLORS_DARK, RAPPORT_NON_DEPOSE, RAPPORT_DEPOSE, RAPPORT_NON_DEPOSE_DARK, RAPPORT_DEPOSE_DARK } from '../constants/statuses'
import { useTheme } from '../context/ThemeContext'

export default function StatusBadge({ statut, type = 'stage' }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  let config
  if (type === 'rapport') {
    const map = statut === 'Rapport déposé'
      ? (isDark ? RAPPORT_DEPOSE_DARK : RAPPORT_DEPOSE)
      : (isDark ? RAPPORT_NON_DEPOSE_DARK : RAPPORT_NON_DEPOSE)
    config = map
  } else {
    const colors = type === 'dossier'
      ? (isDark ? DOSSIER_COLORS_DARK : DOSSIER_COLORS)
      : (isDark ? STAGE_COLORS_DARK : STAGE_COLORS)
    config = colors[statut] || (isDark
      ? { color: '#8b949e', bg: '#1c2128', label: statut }
      : { color: '#6b7280', bg: '#f3f4f6', label: statut })
  }

  return (
    <span
      className="status-badge"
      style={{
        backgroundColor: config.bg,
        color: config.color,
        borderColor: config.color,
      }}
    >
      {config.label}
    </span>
  )
}
