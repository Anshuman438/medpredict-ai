import { useState, useEffect, useRef } from 'react'
import MainLayout from '../layouts/MainLayout'
import api from '../services/api'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    fetchChat()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchChat = async () => {
    const { data } = await api.get('/chat')
    setMessages(data.messages || [])
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const { data } = await api.post('/chat', { text: input })
    setMessages(data.messages)
    setInput('')
  }

  return (
    <MainLayout>

      <div className="chat-container">

        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          <div ref={bottomRef}></div>
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button className="primary-btn" onClick={sendMessage}>
            Send
          </button>
        </div>

      </div>

    </MainLayout>
  )
}

export default Chat