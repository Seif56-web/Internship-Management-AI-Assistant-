import { useState, useRef, useEffect } from 'react'

export default function InfoButton({ text }) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState(null)
  const btnRef = useRef(null)
  const hideTimer = useRef(null)

  const show = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current)
    const el = btnRef.current
    if (el) {
      const r = el.getBoundingClientRect()
      setPos({ left: r.left + r.width / 2, top: r.top - 8 })
    }
    setOpen(true)
  }

  const hide = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current)
    hideTimer.current = setTimeout(() => setOpen(false), 120)
  }

  useEffect(() => () => clearTimeout(hideTimer.current), [])

  return (
    <span className="info-button-wrapper">
      <button
        ref={btnRef}
        type="button"
        className="info-button"
        aria-label="Information"
        onClick={(e) => { e.stopPropagation(); open ? hide() : show() }}
        onMouseEnter={show}
        onMouseLeave={hide}
      >
        i
      </button>
      {open && pos && (
        <span className="info-tooltip" style={{ left: pos.left, top: pos.top }}>
          {text}
        </span>
      )}
    </span>
  )
}
