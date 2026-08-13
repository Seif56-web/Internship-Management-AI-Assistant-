import { useState, useRef } from 'react'
import { importStagiaires } from '../services/stagiaires'
import {
  Upload,
  X,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader,
} from 'lucide-react'

export default function ImportModal({ onClose, onComplete }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileRef = useRef(null)

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files)
    if (selected.length === 0) return
    const invalid = selected.find(f => !f.name.match(/\.xlsx?$/i))
    if (invalid) {
      setError(`"${invalid.name}" n'est pas un fichier Excel (.xlsx)`)
      return
    }
    setFiles(selected)
    setError('')
    setResult(null)
  }

  const handleImport = async () => {
    if (files.length === 0) return
    setLoading(true)
    setError('')
    try {
      const res = await importStagiaires(files)
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'import")
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (result && result.stagiaires_imported > 0) {
      onComplete()
    } else {
      onClose()
    }
  }

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx))
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            <Upload size={20} />
            Importer des stagiaires
          </h2>
          <button className="modal-close" onClick={handleClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {!result ? (
            <>
              <div className="import-info">
                <p>Sélectionnez un ou plusieurs fichiers Excel (.xlsx) à importer.</p>
                <p className="text-muted small">
                  Le système détecte automatiquement les colonnes (Nom et prénom, Date de naissance, CIN, Lettre d'affectation, etc.) même si les en-têtes varient.
                </p>
              </div>

              <div
                className={`import-dropzone ${files.length > 0 ? 'has-file' : ''}`}
                onClick={() => fileRef.current?.click()}
              >
                {files.length > 0 ? (
                  <div className="import-file-list">
                    {files.map((f, i) => (
                      <div key={i} className="import-file-info" style={{ position: 'relative' }}>
                        <FileSpreadsheet size={24} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <span className="import-filename">{f.name}</span>
                          <span className="text-muted small">
                            {(f.size / 1024).toFixed(1)} Ko
                          </span>
                        </div>
                        <button
                          className="btn btn-sm btn-outline"
                          style={{ padding: '2px 6px', lineHeight: 1, flexShrink: 0 }}
                          onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                    <span className="text-muted small" style={{ marginTop: 8, display: 'block' }}>
                      Cliquez pour ajouter d'autres fichiers
                    </span>
                  </div>
                ) : (
                  <div className="import-dropzone-text">
                    <Upload size={32} />
                    <span>Cliquez pour sélectionner des fichiers Excel</span>
                    <span className="text-muted small">.xlsx uniquement — plusieurs fichiers acceptés</span>
                  </div>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  hidden
                  multiple
                />
              </div>

              {error && (
                <div className="alert alert-error">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}
            </>
          ) : (
            <div className="import-result">
              <h3 className="import-result-title">
                {result.stagiaires_imported > 0 ? (
                  <>
                    <CheckCircle size={20} className="text-success" />
                    Import terminé
                  </>
                ) : (
                  <>
                    <XCircle size={20} className="text-danger" />
                    Aucun stagiaire importé
                  </>
                )}
              </h3>
              <div className="import-stats">
                <div className="import-stat success">
                  <CheckCircle size={20} />
                  <div>
                    <strong>{result.files_imported || 0}</strong>
                    <span>fichier(s) importé(s)</span>
                  </div>
                </div>
                <div className="import-stat success">
                  <CheckCircle size={20} />
                  <div>
                    <strong>{result.stagiaires_imported || 0}</strong>
                    <span>stagiaire(s) importé(s)</span>
                  </div>
                </div>
                {result.files_ignored > 0 && (
                  <div className="import-stat warning">
                    <AlertCircle size={20} />
                    <div>
                      <strong>{result.files_ignored}</strong>
                      <span>fichier(s) ignoré(s)</span>
                    </div>
                  </div>
                )}
                {result.errors_total > 0 && (
                  <div className="import-stat error">
                    <XCircle size={20} />
                    <div>
                      <strong>{result.errors_total}</strong>
                      <span>erreur(s)</span>
                    </div>
                  </div>
                )}
              </div>
              {result.errors && result.errors.length > 0 && (
                <div className="import-errors-list">
                  <h4>Détail des erreurs :</h4>
                  <ul>
                    {result.errors.map((e, i) => (
                      <li key={i} className="import-error-item">
                        <AlertCircle size={14} />
                        {e.file && <strong>{e.file} </strong>}
                        {e.row > 0 ? `Ligne ${e.row} : ` : ''}{e.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          {!result ? (
            <>
              <button className="btn btn-outline" onClick={handleClose}>
                Annuler
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={files.length === 0 || loading}
              >
                {loading ? (
                  <>
                    <Loader size={16} className="spin" />
                    Import en cours...
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    Importer ({files.length} fichier{files.length > 1 ? 's' : ''})
                  </>
                )}
              </button>
            </>
          ) : (
            <button className="btn btn-primary" onClick={handleClose}>
              Terminé
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
