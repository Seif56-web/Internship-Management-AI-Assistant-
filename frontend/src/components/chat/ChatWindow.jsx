import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { sendMessage } from '../../services/chat'
import ChatMessage from './ChatMessage'

const WELCOME_MESSAGE =
  "Bonjour ! Je suis l'assistant de gestion des stagiaires. Comment puis-je vous aider ?"

export default function ChatWindow({ onClose }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: WELCOME_MESSAGE },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setError(null)
    setLoading(true)

    try {
      const data = await sendMessage(text)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setError("Impossible de contacter l'assistant. Vérifiez votre connexion et réessayez.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-header-title">
          <span className="chat-header-dot" />
          Assistant
        </div>
        <button className="chat-header-close" onClick={onClose} aria-label="Fermer le chat">
          &times;
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-bubble chat-typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-footer">
        {error && <div className="chat-error">{error}</div>}
        <form className="chat-form" onSubmit={handleSend}>
          <input
            className="chat-input"
            type="text"
            placeholder="Écrire un message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button className="chat-send" type="submit" disabled={loading || !input.trim()} aria-label="Envoyer">
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  )
}