import { useState } from 'react'
import PhoneInput from './PhoneInput'
import EncadrantInput from './EncadrantInput'

const tailles = [34, 36, 38, 40, 42, 44, 46]
const periodes = ['Été', 'Automne', 'Hiver', 'PFE']

export default function StagiaireForm({ initialData, onSubmit, loading }) {
  const [form, setForm] = useState({
    civilite: initialData?.civilite || '',
    nom_complet: initialData?.nom_complet || '',
    lettre_affectation: initialData?.lettre_affectation || false,
    service: initialData?.service || '',
    date_naissance: initialData?.date_naissance || '',
    cin: initialData?.cin || '',
    country_code: initialData?.country_code || '+216',
    telephone: initialData?.telephone || '',
    email: initialData?.email || '',
    ecole: initialData?.ecole || '',
    taille: initialData?.taille || '',
    pointure: initialData?.pointure || '',
    date_debut_stage: initialData?.date_debut_stage || '',
    date_fin_stage: initialData?.date_fin_stage || '',
    periode_stage: initialData?.periode_stage || '',
    encadrant_nom: initialData?.encadrant_nom || '',
    encadrant_id: initialData?.encadrant_id || null,
  })
  const [errors, setErrors] = useState({})

  const validate = () => {
    const errs = {}
    if (form.date_debut_stage && form.date_fin_stage && new Date(form.date_fin_stage) <= new Date(form.date_debut_stage)) {
      errs.date_fin_stage = 'La date de fin doit être postérieure à la date de début'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const capitalizeFirst = (s) => s.charAt(0).toUpperCase() + s.slice(1)

  const handleChange = (field, value) => {
    let v = value
    if (['ecole', 'service'].includes(field)) {
      v = value ? capitalizeFirst(value) : value
    }
    setForm((prev) => ({ ...prev, [field]: v }))
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return

    const payload = {
      ...form,
      civilite: form.civilite || null,
      service: form.service || null,
      date_naissance: form.date_naissance || null,
      date_debut_stage: form.date_debut_stage || null,
      date_fin_stage: form.date_fin_stage || null,
      cin: form.cin || null,
      telephone: form.telephone || null,
      email: form.email || null,
      nom_complet: form.nom_complet || null,
      lettre_affectation: !!form.lettre_affectation,
      taille: form.taille ? parseInt(form.taille, 10) : null,
      pointure: form.pointure ? parseInt(form.pointure, 10) : null,
      encadrant_nom: undefined,
      encadrant_id: form.encadrant_id || null,
    }
    onSubmit(payload)
  }

  return (
    <form className="stagiaire-form" onSubmit={handleSubmit} noValidate>
      <div className="form-grid">
        <div className="form-row-3">
          <div className="form-group">
            <label className="form-label">Civilité</label>
            <select
              className="form-select"
              value={form.civilite}
              onChange={(e) => handleChange('civilite', e.target.value)}
            >
              <option value="">—</option>
              <option value="Mr">Mr</option>
              <option value="Mme">Mme</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Nom et prénom</label>
            <input
              type="text"
              className={`form-input ${errors.nom_complet ? 'input-error' : ''}`}
              value={form.nom_complet}
              onChange={(e) => handleChange('nom_complet', e.target.value)}
            />
            {errors.nom_complet && <span className="field-error">{errors.nom_complet}</span>}
          </div>
          <div className="form-group form-group-push-right">
            <label className="form-label">Lettre d'affectation</label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="lettre_affectation"
                  checked={!form.lettre_affectation}
                  onChange={() => handleChange('lettre_affectation', false)}
                />
                Non
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="lettre_affectation"
                  checked={!!form.lettre_affectation}
                  onChange={() => handleChange('lettre_affectation', true)}
                />
                Oui
              </label>
            </div>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Date de naissance</label>
          <input
            type="date"
            className={`form-input ${errors.date_naissance ? 'input-error' : ''}`}
            value={form.date_naissance}
            onChange={(e) => handleChange('date_naissance', e.target.value)}
          />
          {errors.date_naissance && <span className="field-error">{errors.date_naissance}</span>}
        </div>

        <div className="form-group">
          <label className="form-label">CIN (8 chiffres)</label>
          <input
            type="text"
            className={`form-input ${errors.cin ? 'input-error' : ''}`}
            value={form.cin}
            onChange={(e) => handleChange('cin', e.target.value.replace(/\D/g, '').slice(0, 8))}
            maxLength={8}
            placeholder="12345678"
          />
          {errors.cin && <span className="field-error">{errors.cin}</span>}
        </div>

        <div className="form-group">
          <label className="form-label">Téléphone</label>
          <PhoneInput
            value={form.telephone}
            code={form.country_code}
            onChange={(v) => handleChange('telephone', v)}
            onCodeChange={(v) => handleChange('country_code', v)}
            error={errors.telephone}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            className={`form-input ${errors.email ? 'input-error' : ''}`}
            value={form.email}
            onChange={(e) => handleChange('email', e.target.value)}
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label className="form-label">École</label>
          <input
            type="text"
            className="form-input"
            value={form.ecole}
            onChange={(e) => handleChange('ecole', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Service</label>
          <input
            type="text"
            className="form-input"
            value={form.service}
            onChange={(e) => handleChange('service', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Taille</label>
          <select
            className="form-select"
            value={form.taille}
            onChange={(e) => handleChange('taille', e.target.value)}
          >
            <option value="">— Sélectionner —</option>
            {tailles.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Pointure</label>
          <input
            type="number"
            className="form-input"
            value={form.pointure}
            onChange={(e) => handleChange('pointure', e.target.value)}
            placeholder="Ex: 42"
          />
        </div>

        <div className="form-row-3 form-row-dates">
          <div className="form-group">
            <label className="form-label">Date début stage</label>
            <input
              type="date"
              className={`form-input ${errors.date_debut_stage ? 'input-error' : ''}`}
              value={form.date_debut_stage}
              onChange={(e) => handleChange('date_debut_stage', e.target.value)}
            />
            {errors.date_debut_stage && <span className="field-error">{errors.date_debut_stage}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">Date fin stage</label>
            <input
              type="date"
              className={`form-input ${errors.date_fin_stage ? 'input-error' : ''}`}
              value={form.date_fin_stage}
              onChange={(e) => handleChange('date_fin_stage', e.target.value)}
            />
            {errors.date_fin_stage && <span className="field-error">{errors.date_fin_stage}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">Période de stage</label>
            <select
              className={`form-select ${errors.periode_stage ? 'input-error' : ''}`}
              value={form.periode_stage}
              onChange={(e) => handleChange('periode_stage', e.target.value)}
            >
              <option value="">— Sélectionner —</option>
              {periodes.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            {errors.periode_stage && <span className="field-error">{errors.periode_stage}</span>}
          </div>
        </div>

        <div className="form-group form-group-full">
          <EncadrantInput
            value={form.encadrant_id}
            onChange={(id) => handleChange('encadrant_id', id)}
            error={errors.encadrant_id}
          />
        </div>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Enregistrement...' : initialData ? 'Modifier le stagiaire' : 'Ajouter le stagiaire'}
        </button>
      </div>
    </form>
  )
}
