import { useState, useRef, useEffect, Fragment } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Merhaba! Ben InterChat, bankacılık işlemleriniz için buradayım. Size nasıl yardımcı olabilirim?",
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)


  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])



  const handleLogoClick = () => {
    window.location.reload()
  }

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    // LLM API bağlantısı buraya gelecek
    setTimeout(() => {
      // TODO: LLM API çağrısı burada yapılacak
      // const response = await callLLMAPI(inputMessage);
      
      const botMessage = {
        id: messages.length + 2,
        text: "💬 [Bot cevabı buraya yüklenecek…]",
        sender: 'bot',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])
      setIsTyping(false)
    }, 1200)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }



  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('tr-TR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="app">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <div className="bot-avatar" onClick={handleLogoClick}>
              <img src="/logo.jpg" alt="InterChat Logo" className="avatar-logo" />
            </div>
            <div className="header-info">
              <h1>InterChat</h1>
              <p>Akıllı Bankacılık Asistanı</p>
            </div>

          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.map((message, idx) => (
            <Fragment key={`m-${message.id}`}>
              <div 
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
              >
                <div className="message-content">
                  <div className="message-text">{message.text}</div>
                  <div className="message-time">{formatTime(message.timestamp)}</div>
                </div>
                {message.sender === 'bot' && (
                  <div className="message-avatar">
                    <img src="/logo.jpg" alt="InterChat Logo" className="avatar-logo" />
                  </div>
                )}
              </div>


            </Fragment>
          ))}
          
          {isTyping && (
            <div className="message bot-message">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              <div className="message-avatar">
                <img src="/logo.jpg" alt="InterChat Logo" className="avatar-logo" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
      </div>

        {/* Input */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Mesajınızı yazın..."
              rows="1"
              className="message-input"
            />
            <button 
              onClick={handleSendMessage}
              disabled={inputMessage.trim() === ''}
              className="send-button"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
        </button>
          </div>
        </div>
      </div>


    </div>
  )
}

export default App
