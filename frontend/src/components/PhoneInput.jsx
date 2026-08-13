import { useState } from 'react'

const countries = [
  { code: '+216', country: 'Tunisie' },
  { code: '+33', country: 'France' },
  { code: '+212', country: 'Maroc' },
]

const lengthMap = {
  '+216': 8,
  '+33': 9,
  '+212': 9,
}

export default function PhoneInput({ value, code, onChange, onCodeChange, error }) {
  const [localError, setLocalError] = useState('')

  const handleCodeChange = (e) => {
    onCodeChange(e.target.value)
    setLocalError('')
  }

  const handleNumberChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '')
    const maxLen = lengthMap[code] || 8

    if (raw.length > maxLen) return

    onChange(raw)

    if (raw.length > 0 && raw.length < maxLen) {
      setLocalError(`Le numéro doit contenir ${maxLen} chiffres`)
    } else {
      setLocalError('')
    }
  }

  return (
    <div className="phone-input">
      <div className="phone-code">
        <select value={code} onChange={handleCodeChange} className="form-select">
          {countries.map((c) => (
            <option key={c.code} value={c.code}>
              {c.code}
            </option>
          ))}
        </select>
      </div>
      <div className="phone-number">
        <input
          type="text"
          className={`form-input ${error || localError ? 'input-error' : ''}`}
          value={value}
          onChange={handleNumberChange}
          placeholder={`${lengthMap[code]} chiffres`}
          inputMode="numeric"
        />
        {(error || localError) && (
          <span className="field-error">{error || localError}</span>
        )}
      </div>
    </div>
  )
}
