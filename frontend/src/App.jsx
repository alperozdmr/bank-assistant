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
  const [showQuickActions, setShowQuickActions] = useState(true)
  const [showQuickActionsModal, setShowQuickActionsModal] = useState(false)
  const [isDarkTheme, setIsDarkTheme] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Tema değişikliğini body'ye uygula
    if (isDarkTheme) {
      document.body.classList.add('dark-theme')
    } else {
      document.body.classList.remove('dark-theme')
    }
  }, [isDarkTheme])

  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme)
  }

  const handleLogoClick = () => {
    window.location.reload()
  }

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)
    setShowQuickActions(false)

    try {
      // FastAPI backend çağrısı
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: inputMessage,
          user_id: "user123" // istediğin kullanıcı ID
        })
      })

      const data = await response.json()

      // 1 saniye beklet (Bot yazıyor animasyonu için)
      await new Promise(resolve => setTimeout(resolve, 1000))

      const botMessage = {
        id: messages.length + 2,
        text: data.response, // FastAPI’den gelen cevap
        sender: 'bot',
        timestamp: new Date(data.timestamp)
      }

      setMessages(prev => [...prev, botMessage])
    } catch (err) {
      console.error("API çağrısı başarısız:", err)
      const botMessage = {
        id: messages.length + 2,
        text: "⚠️ Bot cevap veremedi.",
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleQuickAction = async (actionKey) => {
    const actions = {
      balance: {
        user: 'Hesap bakiyemi görmek istiyorum.'
      }
    }

    const userMessage = {
      id: messages.length + 1,
      text: actions[actionKey].user,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setShowQuickActions(false)
    setShowQuickActionsModal(false)
    setIsTyping(true)

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: actions[actionKey].user,
          user_id: "user123" // istediğin kullanıcı ID
        })
      })

      const data = await response.json()

      // 1 saniye beklet (Bot yazıyor animasyonu için)
      await new Promise(resolve => setTimeout(resolve, 1000))

      const botMessage = {
        id: messages.length + 2,
        text: data.response,
        sender: 'bot',
        timestamp: new Date(data.timestamp)
      }

      setMessages(prev => [...prev, botMessage])
    } catch (err) {
      console.error("API çağrısı başarısız:", err)
      const botMessage = {
        id: messages.length + 2,
        text: "⚠️ Bot cevap veremedi.",
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={`app ${isDarkTheme ? 'dark-theme' : ''}`}>
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
            <div className="header-actions">
              <button className="theme-toggle-switch" onClick={toggleTheme}>
                <div className={`toggle-slider ${isDarkTheme ? 'dark' : 'light'}`}>
                  <div className="toggle-icon moon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="toggle-icon sun">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2"/>
                      <path d="M12 1V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M12 21V23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M4.22 4.22L5.64 5.64" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M18.36 18.36L19.78 19.78" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M1 12H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M21 12H23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M4.22 19.78L5.64 18.36" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M18.36 5.64L19.78 4.22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>
                </div>
              </button>
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

              {idx === 0 && showQuickActions && (
                <div className="quick-actions">
                  <h3>Hızlı işlemler:</h3>
                  <div className="quick-buttons">
                    <button className="quick-button" onClick={() => handleQuickAction('balance')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <path d="M5 6H19C20.1046 6 21 6.89543 21 8V16C21 17.1046 20.1046 18 19 18H5C3.89543 18 3 17.1046 3 16V8C3 6.89543 3.89543 6 5 6Z" stroke="currentColor" strokeWidth="2"/>
                        </svg>
                      </div>
                      <span>Hesap Bakiyesi</span>
                    </button>
                  </div>
                </div>
              )}
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
            <button
              onClick={() => setShowQuickActionsModal(true)}
              className="quick-actions-button"
              title="Hızlı İşlemler"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <rect x="14" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <rect x="14" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <rect x="3" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
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

      {/* Quick Actions Modal */}
      {showQuickActionsModal && (
        <div className="modal-overlay" onClick={() => setShowQuickActionsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Hızlı İşlemler</h3>
              <button
                className="modal-close-button"
                onClick={() => setShowQuickActionsModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-quick-buttons">
                <button className="modal-quick-button" onClick={() => handleQuickAction('balance')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M5 6H19C20.1046 6 21 6.89543 21 8V16C21 17.1046 20.1046 18 19 18H5C3.89543 18 3 17.1046 3 16V8C3 6.89543 3.89543 6 5 6Z" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Hesap Bakiyesi</span>
                    <span className="modal-quick-desc">Güncel bakiye bilgilerinizi görün.</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
