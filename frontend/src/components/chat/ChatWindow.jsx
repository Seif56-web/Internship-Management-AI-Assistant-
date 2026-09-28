import { useCallback, useEffect, useRef, useState } from 'react'
import { Send, Plus, Trash2 } from 'lucide-react'
import {
  sendMessage,
  getConversations,
  getMessages,
  deleteConversation,
} from '../../services/chat'
import ChatMessage from './ChatMessage'

const WELCOME_MESSAGE =
  "Bonjour ! Je suis l'assistant de gestion des stagiaires. Comment puis-je vous aider ?"

export default function ChatWindow({ onClose }) {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: WELCOME_MESSAGE },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  const startNew = useCallback(() => {
    setActiveId(null)
    setMessages([{ role: 'assistant', content: WELCOME_MESSAGE }])
    setError(null)
  }, [])

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await getConversations())
    } catch {
      // Liste non critique : le chat reste utilisable
    }
  }, [])

  useEffect(() => {
    refreshConversations()
  }, [refreshConversations])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const openConversation = async (conversationId) => {
    setError(null)
    setActiveId(conversationId)
    setMessages([{ role: 'assistant', content: WELCOME_MESSAGE }])
    try {
      const history = await getMessages(conversationId)
      if (history.length > 0) {
        setMessages(history.map((m) => ({ role: m.role, content: m.content })))
      }
    } catch {
      setError("Impossible de charger l'historique de cette conversation.")
    }
  }

  const handleDelete = async (conversationId) => {
    try {
      await deleteConversation(conversationId)
      setConversations((prev) => prev.filter((c) => c.id !== conversationId))
      if (activeId === conversationId) startNew()
    } catch {
      setError("Impossible de supprimer cette conversation.")
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setError(null)
    setLoading(true)

    try {
      const data = await sendMessage(text, activeId)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
      if (!activeId) {
        setActiveId(data.conversation_id)
        refreshConversations()
      }
    } catch (err) {
      if (err.response?.status === 429) {
        setError("Trop de messages envoyés. Veuillez patienter un instant.")
      } else {
        setError("Impossible de contacter l'assistant. Vérifiez votre connexion et réessayez.")
      }
    } finally {
      setLoading(false)
    }
  }

  const activeTitle =
    conversations.find((c) => c.id === activeId)?.title || 'Nouvelle conversation'

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-header-title">
          <span className="chat-header-dot" />
          Assistant
        </div>
        <div className="chat-header-actions">
          {conversations.length > 0 && (
            <select
              className="chat-history-select"
              value={activeId ?? ''}
              onChange={(e) =>
                e.target.value ? openConversation(Number(e.target.value)) : startNew()
              }
              aria-label="Conversations"
            >
              <option value="">Nouvelle conversation</option>
              {conversations.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title || `Conversation ${c.id}`}
                </option>
              ))}
            </select>
          )}
          <button
            className="chat-header-action"
            onClick={startNew}
            title="Nouvelle conversation"
            aria-label="Nouvelle conversation"
          >
            <Plus size={16} />
          </button>
          {activeId && (
            <button
              className="chat-header-action"
              onClick={() => handleDelete(activeId)}
              title="Supprimer la conversation"
              aria-label="Supprimer la conversation"
            >
              <Trash2 size={16} />
            </button>
          )}
          <button className="chat-header-close" onClick={onClose} aria-label="Fermer le chat">
            &times;
          </button>
        </div>
      </div>

      <div className="chat-context">{activeTitle}</div>

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