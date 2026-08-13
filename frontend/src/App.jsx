import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import StagiaireList from './pages/StagiaireList'
import StagiaireDetail from './pages/StagiaireDetail'
import AddStagiaire from './pages/AddStagiaire'
import EditStagiaire from './pages/EditStagiaire'
import AttestationPreview from './pages/AttestationPreview'
import Rapports from './pages/Rapports'
import Encadrants from './pages/Encadrants'
import AddEncadrant from './pages/AddEncadrant'
import ActiverCompte from './pages/ActiverCompte'
import Comptes from './pages/Comptes'
import Settings from './pages/Settings'

export default function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Chargement...</p>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />
      <Route path="/activer-compte" element={<ActiverCompte />} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/" element={<StagiaireList />} />
        <Route path="/stagiaires/ajouter" element={<AddStagiaire />} />
        <Route path="/stagiaires/:id" element={<StagiaireDetail />} />
        <Route path="/stagiaires/:id/modifier" element={<EditStagiaire />} />
        <Route path="/stagiaires/:id/attestation" element={<AttestationPreview />} />
        <Route path="/rapports" element={<Rapports />} />
        <Route path="/encadrants" element={<Encadrants />} />
        <Route path="/encadrants/ajouter" element={<AddEncadrant />} />
        <Route path="/comptes" element={<Comptes />} />
        <Route path="/parametres" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
