import { useState, useRef, useEffect, Fragment } from 'react'
import './App.css'
import Login from './Login'
import BalanceCard from './components/BalanceCard'
import ExchangeRatesCard from './components/ExchangeRatesCard'
import InterestRatesCard from './components/InterestRatesCard'
import FeesCard from './components/FeesCard'
import ATMCard from './components/ATMCard'
import CardInfoCard from './components/CardInfoCard'
import TransactionsCard from './components/TransactionsCard'

function App() {
  // Login state
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userInfo, setUserInfo] = useState(null)

  // Sohbet geçmişi için state yapısı
  const [chatHistory, setChatHistory] = useState({})
  const [currentChatId, setCurrentChatId] = useState(null)
  const [chatList, setChatList] = useState([])
  const [showSidebar, setShowSidebar] = useState(false)

  // Mevcut sohbet mesajları
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showQuickActions, setShowQuickActions] = useState(true)
  const [showQuickActionsModal, setShowQuickActionsModal] = useState(false)
  const [showLogoutModal, setShowLogoutModal] = useState(false)
  const [isDarkTheme, setIsDarkTheme] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Yeni sohbet oluştur
  const createNewChat = () => {
    // Eğer zaten yeni bir sohbet varsa ve hiç mesaj yazılmamışsa, o sohbete geç
    const existingNewChat = chatList.find(chat => chat.isNew && chat.messages.length <= 1)
    if (existingNewChat) {
      setCurrentChatId(existingNewChat.id)
      setMessages(existingNewChat.messages)
      setShowQuickActions(true)
      setShowSidebar(false)
      return
    }

    const newChatId = `chat-${Date.now()}`
    const welcomeMessage = {
      id: 1,
      text: "Merhaba! Ben InterChat, bankacılık işlemleriniz için buradayım. Size nasıl yardımcı olabilirim?",
      sender: 'bot',
      timestamp: new Date()
    }

    const newChat = {
      id: newChatId,
      title: 'Yeni Sohbet',
      messages: [welcomeMessage],
      createdAt: new Date(),
      updatedAt: new Date(),
      isNew: true // Yeni sohbet olduğunu belirtmek için flag ekle
    }

    // Sadece state'e ekle, localStorage'a kaydetme
    setChatHistory(prev => ({
      ...prev,
      [newChatId]: newChat
    }))

    setChatList(prev => [newChat, ...prev])
    setCurrentChatId(newChatId)
    setMessages([welcomeMessage])
    setShowQuickActions(true)
    setShowSidebar(false)
  }

  // LocalStorage'dan auth ve sohbet geçmişini yükle
  useEffect(() => {
    // Oturumu geri yükle
    try {
      const savedAuth = localStorage.getItem('interAuth')
      if (savedAuth) {
        const parsed = JSON.parse(savedAuth)
        if (parsed?.token && parsed?.userId) {
          setIsLoggedIn(true)
          setUserInfo(parsed)
        }
      }
    } catch (e) {
      console.error('Auth localStorage okuma hatası:', e)
    }

    const savedChatHistory = localStorage.getItem('interChatHistory')
    const savedChatList = localStorage.getItem('interChatList')
    const savedCurrentChatId = localStorage.getItem('interCurrentChatId')
    const savedTheme = localStorage.getItem('interChatTheme')

    if (savedChatHistory) {
      const parsedHistory = JSON.parse(savedChatHistory)
      // Timestamp'leri Date objelerine dönüştür
      Object.keys(parsedHistory).forEach(chatId => {
        const chat = parsedHistory[chatId]
        chat.createdAt = new Date(chat.createdAt)
        chat.updatedAt = new Date(chat.updatedAt)
        chat.isNew = false // Kaydedilmiş sohbetler için isNew = false
        if (chat.messages) {
          chat.messages.forEach(message => {
            message.timestamp = new Date(message.timestamp)
          })
        }
      })
      setChatHistory(parsedHistory)
    }

    if (savedChatList) {
      const parsedList = JSON.parse(savedChatList)
      // Timestamp'leri Date objelerine dönüştür
      parsedList.forEach(chat => {
        chat.createdAt = new Date(chat.createdAt)
        chat.updatedAt = new Date(chat.updatedAt)
        chat.isNew = false // Kaydedilmiş sohbetler için isNew = false
      })
      setChatList(parsedList)
    }

    if (savedCurrentChatId) {
      setCurrentChatId(savedCurrentChatId)
    }
    if (savedTheme) {
      setIsDarkTheme(JSON.parse(savedTheme))
    }

    // Eğer hiç sohbet yoksa, yeni bir sohbet başlat
    if (!savedChatList || JSON.parse(savedChatList).length === 0) {
      const newChatId = `chat-${Date.now()}`
      const welcomeMessage = {
        id: 1,
        text: "Merhaba! Ben InterChat, bankacılık işlemleriniz için buradayım. Size nasıl yardımcı olabilirim?",
        sender: 'bot',
        timestamp: new Date()
      }

      const newChat = {
        id: newChatId,
        title: 'Yeni Sohbet',
        messages: [welcomeMessage],
        createdAt: new Date(),
        updatedAt: new Date(),
        isNew: true // Yeni sohbet olduğunu belirtmek için flag ekle
      }

      setChatHistory({ [newChatId]: newChat })
      setChatList([newChat])
      setCurrentChatId(newChatId)
      setMessages([welcomeMessage])
      setShowQuickActions(true)
    }
  }, [])

  // Mevcut sohbetin mesajlarını yükle
  useEffect(() => {
    if (currentChatId && chatHistory[currentChatId]) {
      setMessages(chatHistory[currentChatId].messages || [])
      setShowQuickActions(chatHistory[currentChatId].messages?.length <= 1)
    }
  }, [currentChatId, chatHistory])

  // Sohbet geçmişini localStorage'a kaydet
  useEffect(() => {
    if (Object.keys(chatHistory).length > 0) {
      try {
        localStorage.setItem('interChatHistory', JSON.stringify(chatHistory))
      } catch (e) {
        console.error('ChatHistory localStorage kaydı başarısız:', e)
      }
    }
  }, [chatHistory])

  useEffect(() => {
    if (chatList.length > 0) {
      try {
        localStorage.setItem('interChatList', JSON.stringify(chatList))
      } catch (e) {
        console.error('ChatList localStorage kaydı başarısız:', e)
      }
    }
  }, [chatList])

  useEffect(() => {
    if (currentChatId) {
      localStorage.setItem('interCurrentChatId', currentChatId)
    }
  }, [currentChatId])

  useEffect(() => {
    localStorage.setItem('interChatTheme', JSON.stringify(isDarkTheme))
  }, [isDarkTheme])

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

  // Sohbet sil
  const deleteChat = (chatId) => {
    if (chatList.length <= 1) return // Son sohbeti silmeyi engelle

    // Yeni sohbetleri silmeyi engelle
    const chatToDelete = chatHistory[chatId]
    if (chatToDelete && chatToDelete.isNew) {
      return
    }

    setChatHistory(prev => {
      const newHistory = { ...prev }
      delete newHistory[chatId]
      return newHistory
    })

    setChatList(prev => prev.filter(chat => chat.id !== chatId))

    if (currentChatId === chatId) {
      const remainingChats = chatList.filter(chat => chat.id !== chatId)
      if (remainingChats.length > 0) {
        switchToChat(remainingChats[0].id)
      }
    }
  }

  // Sohbet değiştir
  const switchToChat = (chatId) => {
    setCurrentChatId(chatId)
    setShowSidebar(false)
  }

  // Sohbet başlığını güncelle
  const updateChatTitle = (chatId, newTitle) => {
    setChatHistory(prev => ({
      ...prev,
      [chatId]: {
        ...prev[chatId],
        title: newTitle,
        updatedAt: new Date()
      }
    }))

    setChatList(prev => prev.map(chat =>
      chat.id === chatId
        ? { ...chat, title: newTitle, updatedAt: new Date() }
        : chat
    ))
  }

  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme)
  }

  const handleLogoClick = () => {
    window.location.reload()
  }

  const handleLogin = (credentials) => {
    setIsLoggedIn(true)
    setUserInfo(credentials)

    try {
      localStorage.setItem('interAuth', JSON.stringify(credentials))
    } catch (e) {
      console.error('Auth localStorage kaydı başarısız:', e)
    }

    // LocalStorage'dan mevcut sohbet geçmişini al
    const savedChatHistory = localStorage.getItem('interChatHistory')
    const savedChatList = localStorage.getItem('interChatList')

    // Yeni sohbet oluştur
    const newChatId = `chat-${Date.now()}`
    const welcomeMessage = {
      id: 1,
      text: "Merhaba! Ben InterChat, bankacılık işlemleriniz için buradayım. Size nasıl yardımcı olabilirim?",
      sender: 'bot',
      timestamp: new Date()
    }

    const newChat = {
      id: newChatId,
      title: 'Yeni Sohbet',
      messages: [welcomeMessage],
      createdAt: new Date(),
      updatedAt: new Date(),
      isNew: true // Yeni sohbet olduğunu belirtmek için flag ekle
    }

    // Mevcut sohbet geçmişini yükle ve yeni sohbeti ekle
    if (savedChatHistory && savedChatList) {
      const parsedHistory = JSON.parse(savedChatHistory)
      const parsedList = JSON.parse(savedChatList)

      // Timestamp'leri Date objelerine dönüştür
      Object.keys(parsedHistory).forEach(chatId => {
        const chat = parsedHistory[chatId]
        chat.createdAt = new Date(chat.createdAt)
        chat.updatedAt = new Date(chat.updatedAt)
        chat.isNew = false // Kaydedilmiş sohbetler için isNew = false
        if (chat.messages) {
          chat.messages.forEach(message => {
            message.timestamp = new Date(message.timestamp)
          })
        }
      })

      parsedList.forEach(chat => {
        chat.createdAt = new Date(chat.createdAt)
        chat.updatedAt = new Date(chat.updatedAt)
        chat.isNew = false // Kaydedilmiş sohbetler için isNew = false
      })

      // Yeni sohbeti mevcut geçmişe ekle
      const updatedHistory = { ...parsedHistory, [newChatId]: newChat }
      const updatedList = [newChat, ...parsedList]

      setChatHistory(updatedHistory)
      setChatList(updatedList)
      setCurrentChatId(newChatId)
      setMessages([welcomeMessage])
      setShowQuickActions(true)
    } else {
      // İlk giriş - sadece yeni sohbet
      setChatHistory({ [newChatId]: newChat })
      setChatList([newChat])
      setCurrentChatId(newChatId)
      setMessages([welcomeMessage])
      setShowQuickActions(true)
    }
  }

  const handleLogout = () => {
    setShowLogoutModal(true)
  }

  const confirmLogout = async () => {
    try {
      if (userInfo?.token) {
        await fetch('http://127.0.0.1:8000/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${userInfo.token}` }
        })
      }
    } catch (e) {
      console.error('Logout hatası:', e)
    } finally {
      try {
        localStorage.removeItem('interAuth')
      } catch (e) {
        console.error('Auth localStorage silme hatası:', e)
      }
      setIsLoggedIn(false)
      setUserInfo(null)
      // Sadece state'i temizle, localStorage'ı silme
      setChatHistory({})
      setChatList([])
      setCurrentChatId(null)
      setMessages([])
      setShowLogoutModal(false)
    }
  }

  const cancelLogout = () => {
    setShowLogoutModal(false)
  }

  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]
    const messageText = inputMessage

    // Hemen kullanıcı mesajını göster
    setMessages(updatedMessages)
    setInputMessage('')
    setShowQuickActions(false)

    // Sohbet başlığını ilk mesajdan otomatik oluştur
    if (messages.length === 1) { // İlk kullanıcı mesajı
      const title = messageText.length > 30
        ? messageText.substring(0, 30) + '...'
        : messageText
      updateChatTitle(currentChatId, title)

      // İlk kullanıcı mesajı gönderildiğinde isNew flag'ini false yap
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: {
          ...prev[currentChatId],
          isNew: false
        }
      }))

      setChatList(prev => prev.map(chat =>
        chat.id === currentChatId
          ? { ...chat, isNew: false }
          : chat
      ))
    }

    // Sohbet geçmişini kullanıcı mesajıyla güncelle
    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        messages: updatedMessages,
        updatedAt: new Date()
      }
    }))

    // Sohbet listesini güncelle
    setChatList(prev => prev.map(chat =>
      chat.id === currentChatId
        ? { ...chat, updatedAt: new Date() }
        : chat
    ).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))

    setIsTyping(true)
    let finalMessages = updatedMessages

    try {
      // FastAPI backend çağrısı
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userInfo.token}` // Authorization başlığı eklendi
        },
        body: JSON.stringify({
          message: inputMessage,
          user_id: userInfo.userId // userInfo.userId kullanıldı
        })
      })

      const data = await response.json()

      const botMessage = {
        id: messages.length + 2,
        text: data.response, // FastAPI'den gelen cevap
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component // UI component data'sı varsa ekle
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)

    } catch (err) {
      console.error("API çağrısı başarısız:", err)
      const botMessage = {
        id: messages.length + 2,
        text: "⚠️ Bot cevap veremedi.",
        sender: 'bot',
        timestamp: new Date()
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)

    } finally {
      setIsTyping(false)
    }

    // Sohbet geçmişini bot mesajıyla güncelle
    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        messages: finalMessages,
        updatedAt: new Date()
      }
    }))

    // Sohbet listesini güncelle
    setChatList(prev => prev.map(chat =>
      chat.id === currentChatId
        ? { ...chat, updatedAt: new Date() }
        : chat
    ).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
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
      },
      atm: {
        user: 'En yakın ATM/Şube nerede?'
      },
      exchange: {
        user: 'Güncel döviz kurlarını göster.'
      },
      interest: {
        user: 'Faiz oranlarını göster.'
      },
      fees: {
        user: 'Hizmet ücretlerini öğrenmek istiyorum.'
      },
      card: {
        user: 'Kart bilgilerimi göster.'
      },
      transactions: {
        user: 'İşlem geçmişimi göster.'
      }
    }

    const userMessage = {
      id: messages.length + 1,
      text: actions[actionKey].user,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]

    // Hemen kullanıcı mesajını göster
    setMessages(updatedMessages)
    setShowQuickActions(false)
    setShowQuickActionsModal(false)

    // Sohbet başlığını hızlı eylemden güncelle
    if (messages.length === 1) {
      updateChatTitle(currentChatId, userMessage.text.length > 30 ? userMessage.text.substring(0, 30) + '...' : userMessage.text)

      // İlk kullanıcı mesajı gönderildiğinde isNew flag'ini false yap
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: {
          ...prev[currentChatId],
          isNew: false
        }
      }))

      setChatList(prev => prev.map(chat =>
        chat.id === currentChatId
          ? { ...chat, isNew: false }
          : chat
      ))
    }

    // Sohbet geçmişini kullanıcı mesajıyla güncelle
    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        messages: updatedMessages,
        updatedAt: new Date()
      }
    }))

    // Sohbet listesini güncelle
    setChatList(prev => prev.map(chat =>
      chat.id === currentChatId
        ? { ...chat, updatedAt: new Date() }
        : chat
    ).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))

    setIsTyping(true)
    let finalMessages = updatedMessages

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userInfo.token}` // Authorization başlığı eklendi
        },
        body: JSON.stringify({
          message: actions[actionKey].user,
          user_id: userInfo.userId // userInfo.userId kullanıldı
        })
      })

      const data = await response.json()

      const botMessage = {
        id: messages.length + 2,
        text: data.response,
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component // UI component data'sı varsa ekle
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)

    } catch (err) {
      console.error("API çağrısı başarısız:", err)
      const botMessage = {
        id: messages.length + 2,
        text: "⚠️ Bot cevap veremedi.",
        sender: 'bot',
        timestamp: new Date()
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)

    } finally {
      setIsTyping(false)
    }

    // Sohbet geçmişini bot mesajıyla güncelle
    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        messages: finalMessages,
        updatedAt: new Date()
      }
    }))

    // Sohbet listesini güncelle
    setChatList(prev => prev.map(chat =>
      chat.id === currentChatId
        ? { ...chat, updatedAt: new Date() }
        : chat
    ).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
  }

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Login sayfasını göster
  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className={`app ${isDarkTheme ? 'dark-theme' : ''}`}>
      <div className="chat-container">
        {/* Sidebar */}
        <div className={`sidebar ${showSidebar ? 'show' : ''}`}>
          <div className="sidebar-header">
            <h2>Sohbetler</h2>
            <button className="new-chat-button" onClick={createNewChat}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 5V19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
          <div className="chat-list">
            {chatList.map((chat) => (
              <div
                key={chat.id}
                className={`chat-item ${currentChatId === chat.id ? 'active' : ''}`}
                onClick={() => switchToChat(chat.id)}
              >
                <div className="chat-info">
                  <div className="chat-title">{chat.title}</div>
                  <div className="chat-time">
                    {(chat.updatedAt instanceof Date ? chat.updatedAt : new Date(chat.updatedAt)).toLocaleDateString('tr-TR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
                {chatList.length > 1 && !chat.isNew && (
                  <button
                    className="delete-chat-button"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteChat(chat.id)
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 6H5H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar Overlay */}
        {showSidebar && (
          <div className="sidebar-overlay" onClick={() => setShowSidebar(false)}></div>
        )}

        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <button className="sidebar-toggle" onClick={() => setShowSidebar(!showSidebar)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 12H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M3 6H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
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
              <button className="logout-button" onClick={handleLogout} title="Çıkış Yap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16 17L21 12L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
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
                  {/* Text varsa göster */}
                  {message.text && message.text.trim() && !(message.sender === 'bot' && message.ui_component) && (
                    <div className="message-text">{message.text}</div>
                  )}
                  {/* UI component varsa göster */}
                  {message.sender === 'bot' && message.ui_component && (
                    <div className="message-ui-component">
                      {message.ui_component.type === 'balance_card' && (
                        <BalanceCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'exchange_rates_card' && (
                        <ExchangeRatesCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'interest_rates_card' && (
                        <InterestRatesCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'fees_card' && (
                        <FeesCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'atm_card' && (
                        <ATMCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'card_info_card' && (
                        <CardInfoCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'transactions_list' && (
                        (() => {
                          const ui = message.ui_component
                          const mapped = {
                            account_id: ui.account_id,
                            customer_id: ui.customer_id,
                            transactions: (ui.items || []).map((it, idx) => ({
                              transaction_id: it.id ?? idx,
                              transaction_date: it.datetime || it.date,
                              amount: it.amount,
                              amount_formatted: it.amount_formatted,
                              currency: it.currency || 'TRY',
                              type: it.type,
                              description: it.description,
                              balance_after: it.balance_after,
                              account_id: it.account_id || ui.account_id,
                            }))
                          }
                          return <TransactionsCard data={mapped} />
                        })()
                      )}
                    </div>
                  )}
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
                          {/* Account/User Icon */}
                          <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>Hesap Bakiyesi</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('atm')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Location Pin */}
                          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>ATM/Şube</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('exchange')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Dollar Sign with Exchange Arrows */}
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                          {/* Dollar Sign */}
                          <path d="M12 6v12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <path d="M9 9a3 3 0 0 1 6 0c0 2-3 3-3 3s-3-1-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M9 15a3 3 0 0 0 6 0c0-2-3-3-3-3s-3 1-3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          {/* Exchange Arrows */}
                          <path d="M6 8l-2 2 2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M18 16l2-2-2-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>Döviz Kurları</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('interest')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Chart/Line Graph Icon */}
                          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                          {/* Chart Line */}
                          <path d="M7 14l3-3 2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          {/* Data Points */}
                          <circle cx="7" cy="14" r="1.5" fill="currentColor"/>
                          <circle cx="10" cy="11" r="1.5" fill="currentColor"/>
                          <circle cx="12" cy="13" r="1.5" fill="currentColor"/>
                          <circle cx="16" cy="9" r="1.5" fill="currentColor"/>
                        </svg>
                      </div>
                      <span>Faiz Oranları</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('fees')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Receipt/Bill Icon */}
                          <path d="M4 2v20l4-2 4 2 4-2 4 2V2l-4 2-4-2-4 2-4-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8 7h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <path d="M8 11h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <path d="M8 15h5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        </svg>
                      </div>
                      <span>Ücretler</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('transactions')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Transactions/List Icon */}
                          <path d="M8 6h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8 12h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8 18h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M3 6h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M3 12h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M3 18h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>İşlem Geçmişi</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('card')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Credit Card Icon */}
                          <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="2"/>
                          <path d="M2 10H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <circle cx="6" cy="15" r="1" fill="currentColor"/>
                          <circle cx="9" cy="15" r="1" fill="currentColor"/>
                        </svg>
                      </div>
                      <span>Kart Bilgileri</span>
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
                      {/* Account/User Icon */}
                      <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Hesap Bakiyesi</span>
                    <span className="modal-quick-desc">Güncel bakiye bilgilerinizi görün.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('atm')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Location Pin */}
                      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">ATM/Şube</span>
                    <span className="modal-quick-desc">Yakınınızdaki ATM ve şubeleri bulun.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('exchange')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Dollar Sign with Exchange Arrows */}
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                      {/* Dollar Sign */}
                      <path d="M12 6v12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M9 9a3 3 0 0 1 6 0c0 2-3 3-3 3s-3-1-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M9 15a3 3 0 0 0 6 0c0-2-3-3-3-3s-3 1-3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      {/* Exchange Arrows */}
                      <path d="M6 8l-2 2 2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M18 16l2-2-2-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Döviz Kurları</span>
                    <span className="modal-quick-desc">Güncel döviz kurlarını görün.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('interest')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Chart/Line Graph Icon */}
                      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                      {/* Chart Line */}
                      <path d="M7 14l3-3 2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      {/* Data Points */}
                      <circle cx="7" cy="14" r="1.5" fill="currentColor"/>
                      <circle cx="10" cy="11" r="1.5" fill="currentColor"/>
                      <circle cx="12" cy="13" r="1.5" fill="currentColor"/>
                      <circle cx="16" cy="9" r="1.5" fill="currentColor"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Faiz Oranları</span>
                    <span className="modal-quick-desc">Güncel faiz oranlarını görün.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('fees')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Receipt/Bill Icon */}
                      <path d="M4 2v20l4-2 4 2 4-2 4 2V2l-4 2-4-2-4 2-4-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 7h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M8 11h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M8 15h5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Ücretler</span>
                    <span className="modal-quick-desc">Bankacılık işlem ücretlerini görün.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('transactions')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Transactions/List Icon */}
                      <path d="M8 6h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 12h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 18h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M3 6h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M3 12h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M3 18h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">İşlem Geçmişi</span>
                    <span className="modal-quick-desc">Son işlemlerinizi hızlıca görüntüleyin.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('card')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Credit Card Icon */}
                      <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="2"/>
                      <path d="M2 10H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <circle cx="6" cy="15" r="1" fill="currentColor"/>
                      <circle cx="9" cy="15" r="1" fill="currentColor"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Kart Bilgileri</span>
                    <span className="modal-quick-desc">Kredi kartı limit ve borç bilgilerinizi görün.</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="modal-overlay" onClick={cancelLogout}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Çıkış Yap</h3>
              <button
                className="modal-close-button"
                onClick={cancelLogout}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="modal-body">
              <p>Çıkış yapmak istediğinizden emin misiniz?</p>
              <div className="modal-actions">
                <button className="modal-confirm-button" onClick={confirmLogout}>
                  Evet
                </button>
                <button className="modal-cancel-button" onClick={cancelLogout}>
                  İptal
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
