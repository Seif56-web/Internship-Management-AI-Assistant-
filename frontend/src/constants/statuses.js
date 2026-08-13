export const STATUT_STAGE = {
  STAGE_NON_DEBUTE: 'Stage non débuté',
  STAGE_EN_COURS: 'Stage en cours',
  STAGE_SUSPENDU: 'Stage suspendu',
  STAGE_TERMINE: 'Stage terminé',
  STAGE_VALIDE: 'Stage validé',
  STAGE_REFUSE: 'Stage refusé',
}

export const STATUT_DOSSIER = {
  ATTESTATION_NON_GENEREE: 'Attestation non générée',
  ATTESTATION_GENEREE: 'Attestation générée',
  ATTESTATION_ENVOYEE: 'Attestation envoyée',
}

export const STAGE_COLORS = {
  [STATUT_STAGE.STAGE_NON_DEBUTE]: { color: '#6b7280', bg: '#f3f4f6', label: 'Stage non débuté' },
  [STATUT_STAGE.STAGE_EN_COURS]: { color: '#2563eb', bg: '#dbeafe', label: 'Stage en cours' },
  [STATUT_STAGE.STAGE_SUSPENDU]: { color: '#ea580c', bg: '#fff7ed', label: 'Stage suspendu' },
  [STATUT_STAGE.STAGE_TERMINE]: { color: '#7c3aed', bg: '#ede9fe', label: 'Stage terminé' },
  [STATUT_STAGE.STAGE_VALIDE]: { color: '#16a34a', bg: '#dcfce7', label: 'Stage validé' },
  [STATUT_STAGE.STAGE_REFUSE]: { color: '#dc2626', bg: '#fee2e2', label: 'Stage refusé' },
}

export const STAGE_COLORS_DARK = {
  [STATUT_STAGE.STAGE_NON_DEBUTE]: { color: '#8b949e', bg: '#1c2128', label: 'Stage non débuté' },
  [STATUT_STAGE.STAGE_EN_COURS]: { color: '#58a6ff', bg: '#0d2a4a', label: 'Stage en cours' },
  [STATUT_STAGE.STAGE_SUSPENDU]: { color: '#ffa657', bg: '#2d1a00', label: 'Stage suspendu' },
  [STATUT_STAGE.STAGE_TERMINE]: { color: '#d2a8ff', bg: '#1a1a3e', label: 'Stage terminé' },
  [STATUT_STAGE.STAGE_VALIDE]: { color: '#3fb950', bg: '#0d2a1a', label: 'Stage validé' },
  [STATUT_STAGE.STAGE_REFUSE]: { color: '#f85149', bg: '#2d0d0d', label: 'Stage refusé' },
}

export const DOSSIER_COLORS = {
  [STATUT_DOSSIER.ATTESTATION_NON_GENEREE]: { color: '#6b7280', bg: '#f3f4f6', label: 'Attestation non générée' },
  [STATUT_DOSSIER.ATTESTATION_GENEREE]: { color: '#2563eb', bg: '#dbeafe', label: 'Attestation générée' },
  [STATUT_DOSSIER.ATTESTATION_ENVOYEE]: { color: '#15803d', bg: '#dcfce7', label: 'Attestation envoyée' },
}

export const DOSSIER_COLORS_DARK = {
  [STATUT_DOSSIER.ATTESTATION_NON_GENEREE]: { color: '#8b949e', bg: '#1c2128', label: 'Attestation non générée' },
  [STATUT_DOSSIER.ATTESTATION_GENEREE]: { color: '#58a6ff', bg: '#0d2a4a', label: 'Attestation générée' },
  [STATUT_DOSSIER.ATTESTATION_ENVOYEE]: { color: '#3fb950', bg: '#0d2a1a', label: 'Attestation envoyée' },
}

export const STAGE_TRANSITIONS = {
  [STATUT_STAGE.STAGE_NON_DEBUTE]: [STATUT_STAGE.STAGE_EN_COURS],
  [STATUT_STAGE.STAGE_EN_COURS]: [STATUT_STAGE.STAGE_SUSPENDU, STATUT_STAGE.STAGE_TERMINE, STATUT_STAGE.STAGE_VALIDE, STATUT_STAGE.STAGE_REFUSE],
  [STATUT_STAGE.STAGE_SUSPENDU]: [STATUT_STAGE.STAGE_EN_COURS],
  [STATUT_STAGE.STAGE_TERMINE]: [STATUT_STAGE.STAGE_EN_COURS, STATUT_STAGE.STAGE_VALIDE, STATUT_STAGE.STAGE_REFUSE],
  [STATUT_STAGE.STAGE_VALIDE]: [],
  [STATUT_STAGE.STAGE_REFUSE]: [],
}

export function canTransitionStage(current, target) {
  return STAGE_TRANSITIONS[current]?.includes(target) || false
}

export function getAllowedStageTransitions(current) {
  return STAGE_TRANSITIONS[current] || []
}

export function isSuspended(statutStage) {
  return statutStage === STATUT_STAGE.STAGE_SUSPENDU
}

export function canGenerateAttestation(statutStage, statutDossier) {
  if (statutDossier && statutDossier !== STATUT_DOSSIER.ATTESTATION_GENEREE) {
    return false
  }
  return true
}

export const STATUT_STAGE_FILTERS = [
  { value: '', label: 'Tous' },
  { value: STATUT_STAGE.STAGE_NON_DEBUTE, label: 'Non débuté' },
  { value: STATUT_STAGE.STAGE_EN_COURS, label: 'En cours' },
  { value: STATUT_STAGE.STAGE_SUSPENDU, label: 'Suspendu' },
  { value: STATUT_STAGE.STAGE_TERMINE, label: 'Terminé' },
  { value: STATUT_STAGE.STAGE_VALIDE, label: 'Validé' },
  { value: STATUT_STAGE.STAGE_REFUSE, label: 'Refusé' },
]

export const STATUT_DOSSIER_FILTERS = [
  { value: '', label: 'Tous' },
  { value: STATUT_DOSSIER.ATTESTATION_GENEREE, label: 'Attestation générée' },
  { value: STATUT_DOSSIER.ATTESTATION_ENVOYEE, label: 'Attestation envoyée' },
]

export const STAGE_FILTERS = STATUT_STAGE_FILTERS

export const PROLONGATION_BADGE = { color: '#92400e', bg: '#fef3c7', label: 'Prolongation' }
export const PROLONGATION_BADGE_DARK = { color: '#ffa657', bg: '#2d1a00', label: 'Prolongation' }

export const RAPPORT_NON_DEPOSE = { color: '#6b7280', bg: '#f3f4f6', label: 'Rapport non déposé' }
export const RAPPORT_DEPOSE = { color: '#16a34a', bg: '#dcfce7', label: 'Rapport déposé' }
export const RAPPORT_NON_DEPOSE_DARK = { color: '#8b949e', bg: '#1c2128', label: 'Rapport non déposé' }
export const RAPPORT_DEPOSE_DARK = { color: '#3fb950', bg: '#0d2a1a', label: 'Rapport déposé' }
