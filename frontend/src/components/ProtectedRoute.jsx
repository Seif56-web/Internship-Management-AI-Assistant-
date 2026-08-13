import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const DEV_BYPASS = false

export default function ProtectedRoute({ children, roles }) {
  if (DEV_BYPASS) {
    return children
  }

  const { user } = useAuth()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return children
}