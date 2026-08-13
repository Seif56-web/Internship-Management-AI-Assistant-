import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../context/ThemeContext'
import InfoButton from './InfoButton'
import {
  Users,
  PlusCircle,
  Folder,
  UserCheck,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield,
  Sun,
  Moon,
} from 'lucide-react'

export default function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const isEncadrant = user?.role === 'Encadrant'
  const isAdmin = user?.role === 'Admin'

  const links = [
    { to: '/', label: 'Stagiaires', icon: Users, end: true },
    ...(isEncadrant ? [] : [{ to: '/stagiaires/ajouter', label: 'Ajouter un stagiaire', icon: PlusCircle }]),
    { to: '/rapports', label: 'Rapports', icon: Folder },
    ...(isEncadrant ? [] : [{ to: '/encadrants', label: 'Encadrants', icon: UserCheck }]),
    ...(isAdmin ? [{ to: '/comptes', label: 'Comptes', icon: Shield }] : []),
    { to: '/parametres', label: 'Paramètres', icon: Settings },
  ]

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <img src="/hutchinson_logo-remove.live.png" alt="Hutchinson" className="sidebar-logo" />
          {!collapsed && <span className="logo-text">Hut-Gestion de stagiaires</span>}
        </div>
        <button className="sidebar-toggle" onClick={onToggle}>
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-icon"><Icon size={18} /></span>
              {!collapsed && <span className="sidebar-label">{link.label}</span>}
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-footer">
          {!collapsed && (
            <div className="sidebar-user">
              <div className="sidebar-user-info">
                <span className="user-name">{user?.prenom ? `${user.prenom} ` : ''}{user?.nom}</span>
                <span className="user-role">{user?.role}</span>
              </div>
              <label className="switch" title={theme === 'light' ? 'Mode sombre' : 'Mode clair'}>
                <input type="checkbox" checked={theme === 'dark'} onChange={toggleTheme} />
                <span className="switch-slider">
                <Sun size={13} className="switch-icon switch-icon-sun" />
                  <Moon size={13} className="switch-icon switch-icon-moon" />
                </span>
              </label>
            </div>
          )}
          {collapsed && (
            <label className="switch" title={theme === 'light' ? 'Mode sombre' : 'Mode clair'}>
              <input type="checkbox" checked={theme === 'dark'} onChange={toggleTheme} />
              <span className="switch-slider">
                <Sun size={13} className="switch-icon switch-icon-sun" />
                  <Moon size={13} className="switch-icon switch-icon-moon" />
              </span>
            </label>
          )}
          <div className="sidebar-footer-row">
            <button className="sidebar-logout" onClick={logout}>
              <span className="sidebar-icon"><LogOut size={18} /></span>
              {!collapsed && <span>Déconnexion</span>}
            </button>
            <InfoButton text="Réalisé par Rania Mourali" />
          </div>
      </div>
    </aside>
  )
}
