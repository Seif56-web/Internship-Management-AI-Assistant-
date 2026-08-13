export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'}`}>
      <div className="chat-bubble">{message.content}</div>
    </div>
  )
}