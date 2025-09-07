import { useState, useRef, useEffect, Fragment, useCallback } from 'react'
import './App.css'
import Login from './Login'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'react-chartjs-2'

// Chart.js'i register et
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

import BalanceCard from './components/BalanceCard'
import ExchangeRatesCard from './components/ExchangeRatesCard'
import FXConvertCard from './components/FXConvertCard'
import InterestRatesCard from './components/InterestRatesCard'
import FeesCard from './components/FeesCard'
import ATMCard from './components/ATMCard'
import CardInfoCard from './components/CardInfoCard'
import TransactionsCard from './components/TransactionsCard'
import UserProfileCard from './components/UserProfileCard'
import PortfoliosCard from './components/PortfoliosCard'
import InterestQuoteCard from './components/InterestQuoteCard'
import InterestCalculatorModal from './components/InterestCalculatorModal'
import AmortizationTableCard from './components/AmortizationTableCard'
import LoanAmortizationModal from './components/LoanAmortizationModal'
import ROISimulationCard from './components/ROISimulationCard'
import ROISimulationModal from './components/ROISimulationModal'
import PaymentConfirmationModal from './components/PaymentConfirmationModal'
import PaymentTransferModal from './components/PaymentTransferModal'
import PaymentReceiptCard from './components/PaymentReceiptCard'
import SmartNotification from './components/SmartNotification'
import UserGuide from './components/UserGuide'
import VoiceInputButton from './components/VoiceInputButton'

// PaymentConfirmationTrigger component - sonsuz render döngüsünü önlemek için
const PaymentConfirmationTrigger = ({ uiComponent, setPaymentConfirmationData, setShowPaymentConfirmation, isNewMessage = false }) => {
  useEffect(() => {
    // Sadece yeni mesajlar için modal açılsın, eski mesajlar için açılmasın
    if (uiComponent && uiComponent.data && isNewMessage) {
      const data = uiComponent.data
      setPaymentConfirmationData({
        from_account: data.from_account,
        to_account: data.to_account,
        amount: data.amount,
        currency: data.currency,
        fee: data.fee,
        note: data.note,
        limits: data.limits,
        customer_id: data.customer_id
      })
      setShowPaymentConfirmation(true)
    }
  }, [uiComponent, setPaymentConfirmationData, setShowPaymentConfirmation, isNewMessage])
  
  return null
}

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
  const [isLoadingChats, setIsLoadingChats] = useState(false)
  const [userProfile, setUserProfile] = useState(null)
  const [showProfile, setShowProfile] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [showSearchInput, setShowSearchInput] = useState(false)
  
  // Ses tanıma için state'ler
  const [isListening, setIsListening] = useState(false)
  
  // Ses tanıma fonksiyonları
  const [isTypingVoice, setIsTypingVoice] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  
  const handleVoiceTranscript = (transcript) => {
    setInputMessage(transcript);
    setVoiceText('');
  };

  const handleInterimTranscript = (transcript) => {
    setVoiceText(transcript);
    setIsTypingVoice(true);
  };

  const handleStartListening = () => {
    setIsListening(true);
    setIsTypingVoice(true);
    setVoiceText('');
  };

  const handleStopListening = () => {
    setIsListening(false);
    setIsTypingVoice(false);
    setVoiceText('');
  };

  // Kelime kelime yazma efekti
  const typeWordsEffect = (text) => {
    const words = text.split(' ');
    let currentText = '';
    let wordIndex = 0;

    const typeNextWord = () => {
      if (wordIndex < words.length) {
        currentText += (wordIndex > 0 ? ' ' : '') + words[wordIndex];
        setVoiceText(currentText);
        wordIndex++;
        setTimeout(typeNextWord, 200); // Her kelime arasında 200ms bekle
      }
    };

    typeNextWord();
  };
  const [showInterestCalculator, setShowInterestCalculator] = useState(false)
  const [showLoanAmortization, setShowLoanAmortization] = useState(false)
  const [showROISimulation, setShowROISimulation] = useState(false)
  const [showROIChart, setShowROIChart] = useState(false)
  const [roiChartData, setRoiChartData] = useState(null)
  const [showPaymentConfirmation, setShowPaymentConfirmation] = useState(false)
  const [paymentConfirmationData, setPaymentConfirmationData] = useState(null)
  const [showPaymentTransfer, setShowPaymentTransfer] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [showUserGuide, setShowUserGuide] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Para formatı
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  // Akıllı bildirim fonksiyonları
  const addNotification = (notification) => {
    const id = Date.now() + Math.random()
    const newNotification = {
      id,
      type: 'info',
      duration: 6000,
      autoClose: true,
      ...notification
    }
    setNotifications(prev => [...prev, newNotification])
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
  }

  const handleNotificationAction = (action) => {
    if (action === 'show_balance') {
      handleQuickAction('balance')
    } else if (action === 'show_transactions') {
      handleQuickAction('transactions')
    } else if (action === 'show_exchange') {
      handleQuickAction('exchange')
    } else if (action === 'show_interest') {
      handleQuickAction('interest')
    } else if (action === 'show_card') {
      handleQuickAction('card')
    } else if (action === 'show_atm') {
      handleQuickAction('atm')
    } else if (action === 'show_portfolios') {
      handleQuickAction('portfolios')
    } else if (action === 'roi_simulation') {
      setShowROISimulation(true)
    } else if (action === 'go_login') {
      // 401 sonrası giriş sayfasına yönlendir
      setIsLoggedIn(false)
      setUserInfo(null)
      setMessages([])
      setCurrentChatId(null)
      setChatList([])
      // Bildirimleri kapat
      setNotifications([])
    }
  }

  // Global 401 yakalayıcı: Tüm fetch çağrılarında 401 olursa uyarı göster
  useEffect(() => {
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args)
        if (response && response.status === 401) {
          addNotification({
            type: 'error',
            title: 'Oturumunuz sona erdi',
            message: 'Devam etmek için lütfen yeniden giriş yapın.',
            action: 'go_login',
            actionText: 'Giriş yap',
            autoClose: false
          })
        }
        return response
      } catch (e) {
        // Ağ hataları için varsayılan davranış
        throw e
      }
    }
    return () => {
      window.fetch = originalFetch
    }
  }, [])

  // Akıllı bildirim oluşturma fonksiyonları
  const createSmartNotifications = () => {
    const now = new Date()
    const hour = now.getHours()
    const day = now.getDay() // 0 = Pazar, 6 = Cumartesi

    // Sabah erken (06:00-08:00)
    if (hour >= 6 && hour < 8 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Günaydın! 🌅',
        message: 'Yeni güne başlarken döviz kurlarını kontrol etmek ister misiniz?',
        action: 'show_exchange',
        actionText: 'Döviz Kurları'
      })
    }

    // Sabah (08:00-10:00)
    if (hour >= 8 && hour < 10 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Mutlu Sabahlar! ☀️',
        message: 'Hesap bakiyenizi kontrol etmek için iyi bir zaman!',
        action: 'show_balance',
        actionText: 'Bakiyeyi Gör'
      })
    }

    // Öğle öncesi (10:00-12:00)
    if (hour >= 10 && hour < 12 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Öğleden Önce! 📈',
        message: 'Faiz oranlarını kontrol etmek ister misiniz?',
        action: 'show_interest',
        actionText: 'Faiz Oranları'
      })
    }

    // Öğle (12:00-14:00)
    if (hour >= 12 && hour < 14 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Öğle Arası! 📊',
        message: 'Günlük işlemlerinizi gözden geçirmek ister misiniz?',
        action: 'show_transactions',
        actionText: 'İşlem Geçmişi'
      })
    }

    // Öğle sonrası (14:00-16:00)
    if (hour >= 14 && hour < 16 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Öğleden Sonra! 💳',
        message: 'Kart bilgilerinizi kontrol etmek ister misiniz?',
        action: 'show_card',
        actionText: 'Kart Bilgileri'
      })
    }

    // İkindi (16:00-18:00)
    if (hour >= 16 && hour < 18 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'İkindi Vakti! 🏦',
        message: 'Yakınınızdaki ATM ve şubeleri bulmak ister misiniz?',
        action: 'show_atm',
        actionText: 'ATM/Şube'
      })
    }

    // Akşam (18:00-20:00)
    if (hour >= 18 && hour < 20 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Akşam Kontrolü! 🌆',
        message: 'Yatırım portföylerini değerlendirmek ister misiniz?',
        action: 'show_portfolios',
        actionText: 'Portföyler'
      })
    }

    // Gece (20:00-22:00)
    if (hour >= 20 && hour < 22 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Geceye Doğru! 🌙',
        message: 'ROI simülasyonu ile yatırım planlarınızı değerlendirin.',
        action: 'roi_simulation',
        actionText: 'ROI Simülasyonu'
      })
    }

    // Gece geç (22:00-24:00)
    if (hour >= 22 && hour < 24 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Uyku Vakti! 🕐',
        message: 'Uyumadan önce hesap hareketlerinizi incelemek ister misiniz?',
        action: 'show_transactions',
        actionText: 'İşlem Geçmişi'
      })
    }

    // Gece yarısı (00:00-04:00)
    if (hour >= 0 && hour < 4 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Gece Kuşu! 🌃',
        message: 'Yeni gün için finansal hedeflerinizi belirlemeye ne dersiniz?',
      })
    }

    // Sabah erken (04:00-06:00)
    if (hour >= 4 && hour < 6 && day !== 0 && day !== 1 && day !== 6) {
      addNotification({
        type: 'info',
        title: 'Gün Doğmadan! 🌄',
        message: 'Faiz oranlarını kontrol etmek ister misiniz?',
        action: 'show_interest',
        actionText: 'Faiz Oranları'
      })
    }

    // Hafta sonu özel bildirimi
    if (day === 0 || day === 6) {
      addNotification({
        type: 'info',
        title: 'Hafta Sonu! 💰',
        message: 'Hafta sonu yatırım fırsatlarını değerlendirmek için portföy simülasyonu yapabilirsiniz.',
        action: 'roi_simulation',
        actionText: 'ROI Simülasyonu'
      })
    }
  }

  // Kullanıcı profilini yükle
  const loadUserProfile = async () => {
    if (!userInfo?.userId) return
    
    setIsLoadingProfile(true)
    try {
      const response = await fetch(`http://127.0.0.1:8000/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })
      
      if (response.ok) {
        const profileData = await response.json()
        setUserProfile(profileData)
      } else {
        console.error('Profil yükleme hatası:', response.status)
      }
    } catch (error) {
      console.error('Profil yükleme hatası:', error)
    } finally {
      setIsLoadingProfile(false)
    }
  }

  // Backend'den chat sessions'ları yükle
  const loadChatSessions = async () => {
    if (!userInfo?.userId) return
    
    setIsLoadingChats(true)
    try {
      console.log('Chat sessions yükleniyor...', userInfo.userId)
      const response = await fetch(`http://127.0.0.1:8000/chat/sessions/${userInfo.userId}`, {
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })
      
      console.log('Chat sessions response status:', response.status)
      
      if (response.ok) {
        const sessions = await response.json()
        console.log('Chat sessions loaded:', sessions)
        
        const formattedSessions = sessions.map(session => ({
          id: session.chat_id,
          title: session.title,
          createdAt: new Date(session.created_at),
          updatedAt: new Date(session.updated_at),
          isNew: false
        }))
        
        setChatList(formattedSessions)
        console.log('Formatted sessions:', formattedSessions)
        
        // İlk session'ı seç
        if (formattedSessions.length > 0 && !currentChatId) {
          setCurrentChatId(formattedSessions[0].id)
        }
      } else {
        console.error('Chat sessions response not ok:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Chat sessions yükleme hatası:', error)
    } finally {
      setIsLoadingChats(false)
    }
  }

  // Backend'den chat mesajlarını yükle
  const loadChatMessages = async (chatId) => {
    if (!userInfo?.userId || !chatId) return
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/chat/messages/${userInfo.userId}/${chatId}`, {
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })
      
      if (response.ok) {
        const messages = await response.json()
        const formattedMessages = messages.map(msg => {
          let ui_component = null
          if (msg.ui_component) {
            try {
              ui_component = JSON.parse(msg.ui_component)
            } catch (e) {
              console.error('UI component parse hatası:', e)
            }
          }
          
          return {
            id: msg.message_id,
            text: msg.text,
            sender: msg.sender,
            timestamp: new Date(msg.timestamp),
            ui_component: ui_component
          }
        })
        
        setMessages(formattedMessages)
        setShowQuickActions(formattedMessages.length <= 1)
        
        // Chat history'yi güncelle
        setChatHistory(prev => ({
          ...prev,
          [chatId]: {
            id: chatId,
            messages: formattedMessages,
            isNew: false
          }
        }))
      }
    } catch (error) {
      console.error('Chat messages yükleme hatası:', error)
    }
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

    // Sadece state'e ekle, backend'e kaydetme (ilk mesaj gönderildiğinde kaydedilecek)
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

  // LocalStorage'dan sadece auth ve tema tercihini yükle
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

    const savedTheme = localStorage.getItem('interChatTheme')
    if (savedTheme) {
      setIsDarkTheme(JSON.parse(savedTheme))
    }
  }, [])

  // Kullanıcı giriş yaptığında chat sessions'ları ve profil bilgilerini yükle
  useEffect(() => {
    if (isLoggedIn && userInfo?.userId) {
      loadChatSessions()
      loadUserProfile()
    }
  }, [isLoggedIn, userInfo])

  // Mevcut sohbetin mesajlarını yükle
  useEffect(() => {
    if (currentChatId && userInfo?.userId) {
      // Eğer chat history'de yoksa backend'den yükle
      if (!chatHistory[currentChatId]) {
        loadChatMessages(currentChatId)
      } else if (!chatHistory[currentChatId].isNew) {
        // Eski sohbet ise mesajları yükle
        setMessages(chatHistory[currentChatId].messages || [])
        setShowQuickActions((chatHistory[currentChatId].messages || []).length <= 1)
      }
      // Yeni sohbet (isNew: true) ise hiçbir şey yapma, switchToChat zaten halletti
    }
  }, [currentChatId, userInfo])

  // Sadece tema tercihini localStorage'a kaydet
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

  // ROI Chart veri hesaplama
  const calculateROIData = (years, monthly_investment, target_outcomes) => {
    const labels = []
    const averageData = []
    const optimisticData = []
    const pessimisticData = []
    
    // Başlangıç değeri (0. yıl)
    labels.push('0. Yıl')
    averageData.push(0)
    optimisticData.push(0)
    pessimisticData.push(0)
    
    // Yıl bazında büyüme hesaplama
    for (let year = 1; year <= years; year++) {
      labels.push(`${year}. Yıl`)
      
      // Toplam yatırım
      const totalInvestment = monthly_investment * 12 * year
      
      // Her senaryo için büyüme hesaplama
      // Gerçek ROI simülasyon sonuçlarına göre interpolasyon
      const progress = year / years
      
      // Ortalama senaryo: Başlangıç 0, son nokta target_outcomes.average
      const averageGrowth = Math.round(totalInvestment + (target_outcomes.average - totalInvestment) * progress)
      averageData.push(averageGrowth)
      
      // İyimser senaryo: Başlangıç 0, son nokta target_outcomes.optimistic
      const optimisticGrowth = Math.round(totalInvestment + (target_outcomes.optimistic - totalInvestment) * progress)
      optimisticData.push(optimisticGrowth)
      
      // Kötümser senaryo: Başlangıç 0, son nokta target_outcomes.pessimistic
      const pessimisticGrowth = Math.round(totalInvestment + (target_outcomes.pessimistic - totalInvestment) * progress)
      pessimisticData.push(pessimisticGrowth)
    }
    
    return { labels, averageData, optimisticData, pessimisticData }
  }

  // Sohbet sil
  const deleteChat = async (chatId) => {
    if (chatList.length <= 1) return // Son sohbeti silmeyi engelle

    // Yeni sohbetleri silmeyi engelle
    const chatToDelete = chatHistory[chatId]
    if (chatToDelete && chatToDelete.isNew) {
      return
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/chat/session/${chatId}?user_id=${userInfo.userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })

      if (response.ok) {
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
    } catch (error) {
      console.error('Chat silme hatası:', error)
    }
  }

  // Sohbet değiştir
  const switchToChat = (chatId) => {
    setCurrentChatId(chatId)
    setShowSidebar(false)
    
    // Eğer bu sohbet history'de varsa mesajları hemen yükle
    if (chatHistory[chatId]) {
      if (chatHistory[chatId].isNew) {
        // Yeni sohbet ise karşılama mesajını göster
        setMessages(chatHistory[chatId].messages || [])
        setShowQuickActions(true)
      } else {
        // Eski sohbet ise mesajları yükle
        setMessages(chatHistory[chatId].messages || [])
        setShowQuickActions((chatHistory[chatId].messages || []).length <= 1)
      }
    } else {
      // History'de yoksa mesajları temizle
      setMessages([])
      setShowQuickActions(true)
    }
  }

  // Arama sonucuna tıklandığında o mesaja git
  const navigateToMessage = (chatId, messageId) => {
    setCurrentChatId(chatId)
    setShowSidebar(false)
    setSearchQuery('')
    setShowSearchInput(false)
    
    // Eğer messageId varsa o mesaja scroll yap
    if (messageId) {
      setTimeout(() => {
        const messageElement = document.getElementById(`message-${messageId}`)
        if (messageElement) {
          messageElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
          })
        }
      }, 500)
    }
  }

  // Sohbet başlığını güncelle
  const updateChatTitle = async (chatId, newTitle) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/chat/session/${chatId}/title?title=${encodeURIComponent(newTitle)}&user_id=${userInfo.userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })

      if (response.ok) {
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
    } catch (error) {
      console.error('Chat başlığı güncelleme hatası:', error)
    }
  }

  const toggleTheme = () => {
    setIsDarkTheme(!isDarkTheme)
  }

  const handleLogin = (credentials) => {
    setIsLoggedIn(true)
    setUserInfo(credentials)

    try {
      localStorage.setItem('interAuth', JSON.stringify(credentials))
    } catch (e) {
      console.error('Auth localStorage kaydı başarısız:', e)
    }

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

    // Yeni sohbeti state'e ekle
    setChatHistory({ [newChatId]: newChat })
    setChatList([newChat])
    setCurrentChatId(newChatId)
    setMessages([welcomeMessage])
    setShowQuickActions(true)

    // Akıllı bildirimleri göster (kısa bir gecikme ile)
    setTimeout(() => {
      createSmartNotifications()
    }, 1500)
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
      console.log('Mesaj gönderiliyor...', {
        message: inputMessage,
        user_id: userInfo.userId,
        chat_id: currentChatId
      })
      
      // FastAPI backend çağrısı - chat_id ile birlikte gönder
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${userInfo.token}`
        },
        body: JSON.stringify({
          message: inputMessage,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })

      console.log('Chat response status:', response.status)
      const data = await response.json()
      console.log('Chat response data:', data)

      // Check if this is a payment confirmation request
      let botMessageText = data.response
      let shouldShowPaymentModal = false
      let paymentData = null
      
      // Check ui_component first (new structure)
      if (data.ui_component && data.ui_component.type === 'payment_confirmation') {
        paymentData = data.ui_component.data
        shouldShowPaymentModal = true
        console.log('Payment confirmation detected via ui_component, showing modal.')
      }
      // Fallback to old tool_output structure
      else if (data.tool_output && data.tool_output.data && data.tool_output.data.value && data.tool_output.data.value[0] && data.tool_output.data.value[0].json) {
        const toolData = data.tool_output.data.value[0].json
        if (toolData.ok && toolData.confirm_required && toolData.preview) {
          paymentData = {
            ...toolData.preview,
            customer_id: parseInt(toolData.suggested_client_ref) || 1
          }
          shouldShowPaymentModal = true
          // Override bot message text to show the precheck message
          botMessageText = toolData.message || "Lütfen işlemi onaylayın."
          console.log('Payment confirmation detected via tool_output, showing modal. Bot message text:', botMessageText)
        }
      }

      const botMessage = {
        id: messages.length + 2,
        text: botMessageText, // Use the potentially overridden text
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component // UI component data'sı varsa ekle
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Bot mesajı eklendikten sonra 2 saniye bekleyip modal aç
      if (shouldShowPaymentModal && paymentData) {
        setPaymentConfirmationData(paymentData)
        setTimeout(() => {
          setShowPaymentConfirmation(true)
        }, 3000)
      }

      // Backend'den chat sessions'ları yeniden yükle (güncel liste için)
      if (data.chat_id) {
        console.log('Chat sessions yeniden yükleniyor...')
        loadChatSessions()
      }

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

  const handleInterestCalculatorSubmit = async (formData) => {
    // Bileşik sıklığı Türkçe'ye çevir
    const compoundingMap = {
      'annual': 'yıllık',
      'semiannual': '6 aylık',
      'quarterly': '3 aylık',
      'monthly': 'aylık',
      'weekly': 'haftalık',
      'daily': 'günlük',
      'continuous': 'sürekli'
    }
    
    // Form verilerini backend'e gönder
    const userMessage = {
      id: messages.length + 1,
      text: `Faiz hesaplaması yapmak istiyorum. ${formData.type === 'deposit' ? 'Mevduat' : 'Kredi'} hesaplaması: Anapara ${formData.principal} ${formData.currency}, Vade ${formData.term} ${formData.term_unit === 'years' ? 'yıl' : 'ay'}, Bileşik ${compoundingMap[formData.compounding]}${formData.rate ? `, Faiz oranı %${formData.rate}` : ''}`,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]

    // Hemen kullanıcı mesajını göster
    setMessages(updatedMessages)
    setShowQuickActions(false)

    // Sohbet başlığını güncelle
    if (messages.length === 1) {
      updateChatTitle(currentChatId, userMessage.text.length > 30 ? userMessage.text.substring(0, 30) + '...' : userMessage.text)

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

    // Sohbet geçmişini güncelle
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
          "Authorization": `Bearer ${userInfo.token}`
        },
        body: JSON.stringify({
          message: userMessage.text,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })

      const data = await response.json()

      // Check if this is a payment confirmation request
      let botMessageText = data.response
      let shouldShowPaymentModal = false
      let paymentData = null
      
      if (data.tool_output && data.tool_output.data && data.tool_output.data.value && data.tool_output.data.value[0] && data.tool_output.data.value[0].json) {
        const toolData = data.tool_output.data.value[0].json
        if (toolData.ok && toolData.confirm_required && toolData.preview) {
          paymentData = {
            ...toolData.preview,
            customer_id: parseInt(toolData.suggested_client_ref) || 1
          }
          shouldShowPaymentModal = true
          // Override bot message text to show the precheck message
          botMessageText = toolData.message || "Lütfen işlemi onaylayın."
          console.log('Payment confirmation detected via tool_output, showing modal. Bot message text:', botMessageText)
        }
      }

      const botMessage = {
        id: messages.length + 2,
        text: botMessageText, // Use the potentially overridden text
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Bot mesajı eklendikten sonra 2 saniye bekleyip modal aç
      if (shouldShowPaymentModal && paymentData) {
        setPaymentConfirmationData(paymentData)
        setTimeout(() => {
          setShowPaymentConfirmation(true)
        }, 3000)
      }

      // Backend'den chat sessions'ları yeniden yükle
      if (data.chat_id) {
        loadChatSessions()
      }

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

  const handleROISimulationSubmit = async ({ portfolio_name, monthly_investment, years }) => {
    const userMessage = {
      id: messages.length + 1,
      text: `ROI simülasyonu çalıştır: ${portfolio_name}, aylık ${monthly_investment} TL, ${years} yıl`,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setShowQuickActions(false)

    if (messages.length === 1) {
      updateChatTitle(currentChatId, userMessage.text.length > 30 ? userMessage.text.substring(0, 30) + '...' : userMessage.text)
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: { ...prev[currentChatId], isNew: false }
      }))
      setChatList(prev => prev.map(chat => (
        chat.id === currentChatId ? { ...chat, isNew: false } : chat
      )))
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: updatedMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))

    setIsTyping(true)
    let finalMessages = updatedMessages
    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${userInfo.token}` },
        body: JSON.stringify({
          message: userMessage.text,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })
      const data = await response.json()
      // Check if this is a payment confirmation request
      let botMessageText = data.response
      let shouldShowPaymentModal = false
      let paymentData = null
      
      if (data.tool_output && data.tool_output.data && data.tool_output.data.value && data.tool_output.data.value[0] && data.tool_output.data.value[0].json) {
        const toolData = data.tool_output.data.value[0].json
        if (toolData.ok && toolData.confirm_required && toolData.preview) {
          paymentData = {
            ...toolData.preview,
            customer_id: parseInt(toolData.suggested_client_ref) || 1
          }
          shouldShowPaymentModal = true
          // Override bot message text to show the precheck message
          botMessageText = toolData.message || "Lütfen işlemi onaylayın."
          console.log('Payment confirmation detected, showing modal. Bot message text:', botMessageText)
        }
      }

      const botMessage = {
        id: messages.length + 2,
        text: botMessageText, // Use the potentially overridden text
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Bot mesajı eklendikten sonra 2 saniye bekleyip modal aç
      if (shouldShowPaymentModal && paymentData) {
        setPaymentConfirmationData(paymentData)
        setTimeout(() => {
          setShowPaymentConfirmation(true)
        }, 3000)
      }
      
      if (data.chat_id) {
        loadChatSessions()
      }
    } catch (err) {
      finalMessages = [...updatedMessages, { id: messages.length + 2, text: '⚠️ Bot cevap veremedi.', sender: 'bot', timestamp: new Date() }]
      setMessages(finalMessages)
    } finally {
      setIsTyping(false)
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: finalMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
  }

  const handleROIChartShow = (data) => {
    setRoiChartData(data)
    setShowROIChart(true)
  }

  const handlePaymentConfirmation = async (paymentData) => {
    try {
      const noteText = paymentData.note ? `, note="${paymentData.note}"` : ''
      const userMessage = `Transferi onaylıyorum.`
      
      // Add user message to chat first
      const userMessageObj = {
        id: messages.length + 1,
        text: userMessage,
        sender: 'user',
        timestamp: new Date()
      }
      
      const messagesWithUser = [...messages, userMessageObj]
      setMessages(messagesWithUser)
      
      // Call the payment tool with confirm=true
      const apiMessage = `Transfer onayı: ${paymentData.from_account} numaralı hesabımdan ${paymentData.to_account} numaralı hesabıma ${paymentData.amount} ${paymentData.currency} gönder${noteText}. confirm=True, customer_id=${paymentData.customer_id}`
      
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${userInfo.token}` },
        body: JSON.stringify({
          message: apiMessage,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })
      
      const data = await response.json()
      
      // Add the bot's confirmation response to chat
      const confirmationMessage = {
        id: messagesWithUser.length + 1,
        text: data.response,
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component
      }
      
      const updatedMessages = [...messagesWithUser, confirmationMessage]
      setMessages(updatedMessages)
      
      // Update chat history
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: { ...prev[currentChatId], messages: updatedMessages, updatedAt: new Date() }
      }))
      setChatList(prev => prev.map(chat => (
        chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
      )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
      
      // Close the modal
      setShowPaymentConfirmation(false)
      setPaymentConfirmationData(null)
      
      // Show success notification
      addNotification({
        type: 'success',
        title: 'Transfer Başarılı',
        message: 'Transfer işleminiz başarıyla tamamlandı.',
        duration: 5000
      })
      
    } catch (error) {
      console.error('Payment confirmation error:', error)
      addNotification({
        type: 'error',
        title: 'Transfer Hatası',
        message: 'Transfer işlemi sırasında bir hata oluştu.',
        duration: 5000
      })
    }
  }

  const handleLoanAmortizationSubmit = async ({ principal, term, rate, currency }) => {
    const rateText = rate ? `, Faiz oranı %${rate}` : ''
    const userMessage = {
      id: messages.length + 1,
      text: `Kredi amortismanı hesapla: Anapara ${principal} ${currency}, Vade ${term} ay${rateText}`,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setShowQuickActions(false)

    if (messages.length === 1) {
      updateChatTitle(currentChatId, userMessage.text.length > 30 ? userMessage.text.substring(0, 30) + '...' : userMessage.text)
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: { ...prev[currentChatId], isNew: false }
      }))
      setChatList(prev => prev.map(chat => (
        chat.id === currentChatId ? { ...chat, isNew: false } : chat
      )))
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: updatedMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))

    setIsTyping(true)
    let finalMessages = updatedMessages
    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${userInfo.token}` },
        body: JSON.stringify({
          message: userMessage.text,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })
      const data = await response.json()
      // Check if this is a payment confirmation request
      let botMessageText = data.response
      let shouldShowPaymentModal = false
      let paymentData = null
      
      if (data.tool_output && data.tool_output.data && data.tool_output.data.value && data.tool_output.data.value[0] && data.tool_output.data.value[0].json) {
        const toolData = data.tool_output.data.value[0].json
        if (toolData.ok && toolData.confirm_required && toolData.preview) {
          paymentData = {
            ...toolData.preview,
            customer_id: parseInt(toolData.suggested_client_ref) || 1
          }
          shouldShowPaymentModal = true
          // Override bot message text to show the precheck message
          botMessageText = toolData.message || "Lütfen işlemi onaylayın."
          console.log('Payment confirmation detected, showing modal. Bot message text:', botMessageText)
        }
      }

      const botMessage = {
        id: messages.length + 2,
        text: botMessageText, // Use the potentially overridden text
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Bot mesajı eklendikten sonra 2 saniye bekleyip modal aç
      if (shouldShowPaymentModal && paymentData) {
        setPaymentConfirmationData(paymentData)
        setTimeout(() => {
          setShowPaymentConfirmation(true)
        }, 3000)
      }
      
      if (data.chat_id) {
        loadChatSessions()
      }
    } catch (err) {
      finalMessages = [...updatedMessages, { id: messages.length + 2, text: '⚠️ Bot cevap veremedi.', sender: 'bot', timestamp: new Date() }]
      setMessages(finalMessages)
    } finally {
      setIsTyping(false)
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: finalMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
  }

  const handlePaymentTransferSubmit = async ({ from_account, to_account, amount, currency, note, from_account_name, to_account_name }) => {
    const noteText = note ? `, Not: ${note}` : ''
    const userMessage = {
      id: messages.length + 1,
      text: `${from_account} numaralı hesabımdan ${to_account} numaralı hesabıma ${amount} ${currency} para göndermek istiyorum${noteText}`,
      sender: 'user',
      timestamp: new Date()
    }

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setShowQuickActions(false)

    if (messages.length === 1) {
      updateChatTitle(currentChatId, userMessage.text.length > 30 ? userMessage.text.substring(0, 30) + '...' : userMessage.text)
      setChatHistory(prev => ({
        ...prev,
        [currentChatId]: { ...prev[currentChatId], isNew: false }
      }))
      setChatList(prev => prev.map(chat => (
        chat.id === currentChatId ? { ...chat, isNew: false } : chat
      )))
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: updatedMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))

    setIsTyping(true)
    let finalMessages = updatedMessages
    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${userInfo.token}` },
        body: JSON.stringify({
          message: userMessage.text,
          user_id: userInfo.userId,
          chat_id: currentChatId
        })
      })
      const data = await response.json()
      console.log('Payment transfer response data:', data) // Debug için eklendi
      
      // Check if this is a payment confirmation request
      let botMessageText = data.response
      let shouldShowPaymentModal = false
      let paymentData = null
      
      // Check ui_component first (new structure)
      if (data.ui_component && data.ui_component.type === 'payment_confirmation') {
        paymentData = data.ui_component.data
        shouldShowPaymentModal = true
        console.log('Payment confirmation detected via ui_component, showing modal.')
      }
      // Fallback to old tool_output structure
      else if (data.tool_output && data.tool_output.data && data.tool_output.data.value && data.tool_output.data.value[0] && data.tool_output.data.value[0].json) {
        const toolData = data.tool_output.data.value[0].json
        if (toolData.ok && toolData.confirm_required && toolData.preview) {
          paymentData = {
            ...toolData.preview,
            customer_id: parseInt(toolData.suggested_client_ref) || 1
          }
          shouldShowPaymentModal = true
          // Override bot message text to show the precheck message
          botMessageText = toolData.message || "Lütfen işlemi onaylayın."
          console.log('Payment confirmation detected via tool_output, showing modal. Bot message text:', botMessageText)
        }
      }

      const botMessage = {
        id: messages.length + 2,
        text: botMessageText, // Use the potentially overridden text
        sender: 'bot',
        timestamp: new Date(data.timestamp),
        ui_component: data.ui_component
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Bot mesajı eklendikten sonra 2 saniye bekleyip modal aç
      if (shouldShowPaymentModal && paymentData) {
        setPaymentConfirmationData(paymentData)
        setTimeout(() => {
          setShowPaymentConfirmation(true)
        }, 3000)
      }
      
      if (data.chat_id) {
        loadChatSessions()
      }
    } catch (err) {
      finalMessages = [...updatedMessages, { id: messages.length + 2, text: '⚠️ Bot cevap veremedi.', sender: 'bot', timestamp: new Date() }]
      setMessages(finalMessages)
    } finally {
      setIsTyping(false)
    }

    setChatHistory(prev => ({
      ...prev,
      [currentChatId]: { ...prev[currentChatId], messages: finalMessages, updatedAt: new Date() }
    }))
    setChatList(prev => prev.map(chat => (
      chat.id === currentChatId ? { ...chat, updatedAt: new Date() } : chat
    )).sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)))
  }

  const handleQuickAction = async (actionKey) => {
    if (actionKey === 'interest_compute') {
      setShowInterestCalculator(true)
      setShowQuickActionsModal(false)
      return
    }
    if (actionKey === 'loan_amort') {
      setShowLoanAmortization(true)
      setShowQuickActionsModal(false)
      return
    }
    if (actionKey === 'roi_simulation') {
      setShowROISimulation(true)
      setShowQuickActionsModal(false)
      return
    }
    if (actionKey === 'payment_transfer') {
      setShowPaymentTransfer(true)
      setShowQuickActionsModal(false)
      return
    }

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
      },
      portfolios: {
        user: 'Yatırım portföylerini göster.'
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
          "Authorization": `Bearer ${userInfo.token}`
        },
        body: JSON.stringify({
          message: actions[actionKey].user,
          user_id: userInfo.userId,
          chat_id: currentChatId
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

      // Check if this is a payment confirmation request
      if (data.tool_output && data.tool_output.ok && data.tool_output.confirm_required && data.tool_output.preview) {
        setPaymentConfirmationData({
          ...data.tool_output.preview,
          client_ref: data.tool_output.suggested_client_ref
        })
        setShowPaymentConfirmation(true)
      }

      finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)

      // Backend'den chat sessions'ları yeniden yükle (güncel liste için)
      if (data.chat_id) {
        loadChatSessions()
      }

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

  // PDF indirme fonksiyonu
  const handleDownloadPDF = async (receipt, event) => {
    try {
      // jsPDF ve html2canvas import et
      const { default: jsPDF } = await import('jspdf')
      const { default: html2canvas } = await import('html2canvas')

      // Tıklanan butonun parent elementini bul (spesifik makbuz kartı)
      let paymentReceiptCard = null
      
      if (event) {
        const clickedButton = event.target?.closest('.download-pdf-button')
        if (clickedButton) {
          paymentReceiptCard = clickedButton.closest('.payment-receipt-card')
        }
      }
      
      // Eğer event ile bulunamazsa, receipt hash'ine göre bul
      if (!paymentReceiptCard && receipt?.hash) {
        const allReceiptCards = document.querySelectorAll('.payment-receipt-card')
        for (const card of allReceiptCards) {
          const hashElement = card.querySelector('.receipt-hash .value')
          if (hashElement && hashElement.textContent.includes(receipt.hash)) {
            paymentReceiptCard = card
            break
          }
        }
      }
      
      // Hala bulunamazsa ilk kartı al (fallback)
      if (!paymentReceiptCard) {
        paymentReceiptCard = document.querySelector('.payment-receipt-card')
      }
      
      if (!paymentReceiptCard) {
        console.error('Payment receipt card bulunamadı')
        return
      }

      // Koyu mod kontrolü
      const isDark = isDarkTheme
      const bgColor = isDark ? '#1a1a1a' : 'white'
      const textColor = isDark ? '#ffffff' : '#333333'
      const cardBgColor = isDark ? '#2d2d2d' : 'white'
      const borderColor = isDark ? '#404040' : '#e9ecef'
      const footerBgColor = isDark ? '#2d2d2d' : '#f8f9fa'
      const secondaryTextColor = isDark ? '#b0b0b0' : '#6c757d'
      const sectionTextColor = isDark ? '#e0e0e0' : '#495057'

      // Geçici bir div oluştur ve içeriği kopyala
      const tempDiv = document.createElement('div')
      tempDiv.style.position = 'absolute'
      tempDiv.style.left = '-9999px'
      tempDiv.style.top = '-9999px'
      tempDiv.style.width = '800px'
      tempDiv.style.backgroundColor = bgColor
      tempDiv.style.padding = '20px'
      tempDiv.style.fontFamily = 'Arial, sans-serif'
      
      // PDF için özel HTML template
      const pdfContent = `
        <div style="max-width: 800px; margin: 0 auto; background: ${bgColor}; padding: 20px; font-family: Arial, sans-serif; color: ${textColor};">
          <div style="background: linear-gradient(135deg, #1789dc 0%, #58167d 100%); color: white; padding: 30px; text-align: center; margin-bottom: 20px; border: 1px solid ${borderColor}; border-radius: 8px;">
            <div style="display: flex; align-items: center; justify-content: center;">
              <img src="/logo.jpg" alt="InterChat Logo" style="width: 60px; height: 60px; border-radius: 50%; margin-right: 15px; border: 3px solid white;" />
              <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: white;">InterChat</h1>
            </div>
          </div>
          
          <div style="padding: 20px; background: ${cardBgColor}; border: 1px solid ${borderColor}; border-radius: 8px;">
            ${paymentReceiptCard.innerHTML}
          </div>
          
          <div style="background: ${footerBgColor}; padding: 20px; text-align: center; border-top: 1px solid ${borderColor}; margin-top: 20px; border-radius: 8px;">
            <div style="font-family: 'Courier New', monospace; font-size: 12px; color: ${secondaryTextColor};">
              <span style="font-weight: 500;">Makbuz Hash: </span>
              <span style="font-weight: 600; color: ${sectionTextColor};">${receipt.hash || 'N/A'}</span>
            </div>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: ${secondaryTextColor};">
              Bu makbuz elektronik ortamda oluşturulmuştur ve imza gerektirmez.
            </p>
          </div>
        </div>
      `
      
      tempDiv.innerHTML = pdfContent
      document.body.appendChild(tempDiv)

      // Div'in boyutlarını al (kaldırmadan önce)
      const divWidth = tempDiv.offsetWidth
      const divHeight = tempDiv.offsetHeight

      // Canvas oluştur
      const canvas = await html2canvas(tempDiv, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        width: divWidth,
        height: divHeight
      })

      // Geçici div'i kaldır
      document.body.removeChild(tempDiv)

      // PDF oluştur - div boyutuna göre dinamik
      const imgData = canvas.toDataURL('image/png')
      
      // PDF boyutlarını div boyutuna göre hesapla (mm cinsinden)
      const pdfWidth = 210 // A4 genişliği sabit
      const pdfHeight = (divHeight * pdfWidth) / divWidth // Oranı koruyarak yükseklik hesapla
      
      // PDF oluştur - özel boyutlarla
      const pdf = new jsPDF({
        orientation: pdfHeight > pdfWidth ? 'portrait' : 'landscape',
        unit: 'mm',
        format: [pdfWidth, pdfHeight]
      })
      
      // Görüntüyü PDF'e ekle - tam boyutta
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)

      // PDF'i indir
      const fileName = `transfer_makbuzu_${receipt.hash || Date.now()}.pdf`
      pdf.save(fileName)

    } catch (error) {
      console.error('PDF indirme hatası:', error)
      alert('PDF indirme sırasında bir hata oluştu. Lütfen tekrar deneyin.')
    }
  }

  // Arama fonksiyonu
  const performSearch = async (query) => {
    if (!query.trim() || !userInfo?.userId) {
      setSearchResults([])
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    try {
      const response = await fetch(`http://127.0.0.1:8000/chat/search?user_id=${userInfo.userId}&query=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })

      if (response.ok) {
        const results = await response.json()
        setSearchResults(results)
      } else {
        console.error('Arama hatası:', response.status)
        setSearchResults([])
      }
    } catch (error) {
      console.error('Arama hatası:', error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Arama sorgusu değiştiğinde arama yap
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim()) {
        performSearch(searchQuery)
      } else {
        setSearchResults([])
      }
    }, 300) // 300ms gecikme ile arama

    return () => clearTimeout(timeoutId)
  }, [searchQuery, userInfo])

  // Arama sonuçlarında eşleşen kelimeleri highlight et
  const highlightSearchText = (text, searchQuery) => {
    if (!searchQuery.trim()) return text
    
    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} className="search-highlight">{part}</span>
      ) : part
    )
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
            <div className="sidebar-header-buttons">
              <button className={`search-toggle-button ${showSearchInput ? 'active' : ''}`} onClick={() => setShowSearchInput(!showSearchInput)}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
                  <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <button className="new-chat-button" onClick={createNewChat}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 5V19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
          
                    {/* Arama Kutusu */}
          {showSearchInput && (
            <div className="sidebar-search">
              <div className="search-input-wrapper">
                <div className="search-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
                    <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Mesajlarda ara..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                  autoFocus
                />
                {searchQuery && (
                  <button 
                    className="clear-search-button"
                    onClick={() => setSearchQuery('')}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                )}
              </div>
            </div>
          )}
          <div className="chat-list">
            {/* Arama Sonuçları */}
            {searchQuery && (
              <div className="search-results-section">
                <div className="search-results-header">
                  <h3>Arama Sonuçları</h3>
                  {isSearching && <div className="search-loading">Aranıyor...</div>}
                </div>
                {searchResults.length > 0 ? (
                  <div className="search-results">
                    {searchResults.map((result, index) => (
                      <div
                        key={`search-${index}`}
                        className="search-result-item"
                                               onClick={() => {
                         if (result.message_id) {
                           navigateToMessage(result.chat_id, result.message_id)
                         } else {
                           switchToChat(result.chat_id)
                           setSearchQuery('')
                         }
                       }}
                      >
                          <div className="search-result-content">
                           <div className="search-result-text">
                             {highlightSearchText(result.message_text, searchQuery)}
                           </div>
                           <div className="search-result-meta">
                             <span className="search-result-sender">
                               {result.sender === 'user' ? 'Siz' : 'Bot'}
                             </span>
                             <span className="search-result-time">
                               {new Date(result.timestamp).toLocaleDateString('tr-TR', {
                                 day: '2-digit',
                                 month: '2-digit',
                                 hour: '2-digit',
                                 minute: '2-digit'
                               })}
                             </span>
                           </div>
                         </div>
                        <div className="search-result-icon">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : !isSearching && searchQuery && (
                  <div className="no-search-results">
                    <p>Arama sonucu bulunamadı</p>
                  </div>
                )}
              </div>
            )}

            {/* Normal Sohbet Listesi */}
            {!searchQuery && (
              <>
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
              </>
            )}
          </div>
          
          {/* Profil Bölümü */}
          <div className="sidebar-profile-section">
            <button className="sidebar-profile-button" onClick={() => {
              setShowProfile(true)
              setShowSidebar(false)
            }}>
              <div className="profile-button-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div className="profile-button-text">
                <span className="profile-button-title">Profil Bilgileri</span>
                <span className="profile-button-subtitle">Kişisel - Hesap bilgileriniz</span>
              </div>
            </button>
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
            <div className="bot-avatar">
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
              <button className="user-guide-button" onClick={() => setShowUserGuide(true)} title="Kullanıcı Rehberi">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40913C11.0108 7.05016 11.7289 6.91894 12.4272 7.03871C13.1255 7.15849 13.7588 7.52152 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
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
                id={`message-${message.id}`}
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
              >
                <div className="message-content">
                  {/* Text varsa göster */}
                  {message.text && message.text.trim() && !(message.sender === 'bot' && message.ui_component && message.ui_component.type !== 'payment_confirmation') && (
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
                      {(message.ui_component.type === 'fees_card' || message.ui_component.type === 'fees_table') && (
                        <FeesCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'atm_card' && (
                        <ATMCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'fx_convert_card' && (
                        <FXConvertCard cardData={message.ui_component} />
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
                      {message.ui_component.type === 'portfolios_card' && (
                        <PortfoliosCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'interest_quote_card' && (
                        <InterestQuoteCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'amortization_table_card' && (
                        <AmortizationTableCard cardData={message.ui_component} />
                      )}
                      {message.ui_component.type === 'roi_simulation_card' && (
                        <ROISimulationCard cardData={message.ui_component} onShowChart={handleROIChartShow} />
                      )}
                      {message.ui_component.type === 'payment_receipt' && (
                        <PaymentReceiptCard 
                          cardData={message.ui_component} 
                          onDownloadPDF={handleDownloadPDF}
                        />
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
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Wallet Icon */}
                          <rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
                          <rect x="3" y="8" width="18" height="8" rx="1" fill="currentColor" opacity="0.1"/>
                          <rect x="17" y="10" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                          <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        </svg>
                      </div>
                      <span>Hesap Bakiyesi</span>
                    </button>
                                         <button className="quick-button" onClick={() => handleQuickAction('payment_transfer')}>
                       <div className="quick-icon">
                         <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                           {/* Money Transfer Icon - Left and Right Arrows */}
                           <path d="M3 12H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                           <path d="M8 7L3 12L8 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                           <path d="M16 7L21 12L16 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                         </svg>
                       </div>
                       <span>Para Transferi</span>
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
                    <button className="quick-button" onClick={() => handleQuickAction('portfolios')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Portfolio/Investment Icon */}
                          <path d="M3 3h18v18H3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M9 9h6v6H9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 3v18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M3 12h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>Yatırım Portföyleri</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('interest_compute')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Percentage/Interest Icon */}
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                          <path d="M8 16l8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                          <path d="M9 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M15 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>Faiz Hesaplama</span>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('loan_amort')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <div className="quick-text">
                        <span className="quick-title">Kredi Amortisman</span>
                      </div>
                    </button>
                    <button className="quick-button" onClick={() => handleQuickAction('roi_simulation')}>
                      <div className="quick-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          {/* Chart/Graph Icon */}
                          <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M18 17V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M13 17V5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8 17v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span>Yatırım Simülasyonu</span>
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
            <div className="input-with-voice">
              <textarea
                value={isTypingVoice ? voiceText : inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isListening ? "Dinleniyor..." : "Mesajınızı yazın..."}
                rows="1"
                className={`message-input ${isListening ? 'listening' : ''} ${isTypingVoice ? 'voice-typing' : ''}`}
                disabled={isListening}
              />
              {isListening && (
                <div className="voice-animation">
                  <div className="voice-wave">
                    <span></span>
                    <span></span>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
            </div>
            <VoiceInputButton
              onTranscript={handleVoiceTranscript}
              onInterimTranscript={handleInterimTranscript}
              isListening={isListening}
              onStartListening={handleStartListening}
              onStopListening={handleStopListening}
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
                      {/* Wallet Icon */}
                      <rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
                      <rect x="3" y="8" width="18" height="8" rx="1" fill="currentColor" opacity="0.1"/>
                      <rect x="17" y="10" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2" fill="none"/>
                      <path d="M3 10H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Hesap Bakiyesi</span>
                    <span className="modal-quick-desc">Güncel bakiye bilgilerinizi görün.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('payment_transfer')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Money Transfer Icon - Left and Right Arrows */}
                      <path d="M3 12H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 7L3 12L8 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M16 7L21 12L16 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Para Transferi</span>
                    <span className="modal-quick-desc">Hesaplarınız arasında para transferi yapın.</span>
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
                <button className="modal-quick-button" onClick={() => handleQuickAction('portfolios')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Portfolio/Investment Icon */}
                      <path d="M3 3h18v18H3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M9 9h6v6H9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M12 3v18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M3 12h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Yatırım Portföyleri</span>
                    <span className="modal-quick-desc">Yatırım portföylerini görüntüleyin.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('interest_compute')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Percentage/Interest Icon */}
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                      <path d="M8 16l8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M9 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M15 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Faiz Hesaplama</span>
                    <span className="modal-quick-desc">Mevduat ve kredi faiz hesaplamalarını yapın.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('loan_amort')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Kredi Amortisman</span>
                    <span className="modal-quick-desc">Aylık ödeme planını hesaplayın ve indirin.</span>
                  </div>
                </button>
                <button className="modal-quick-button" onClick={() => handleQuickAction('roi_simulation')}>
                  <div className="modal-quick-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      {/* Chart/Graph Icon */}
                      <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M18 17V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M13 17V5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 17v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="modal-quick-text">
                    <span className="modal-quick-title">Yatırım Simülasyonu</span>
                    <span className="modal-quick-desc">Yatırım getiri simülasyonu yapın.</span>
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

      {/* Profile Modal */}
      {showProfile && (
        <div className="modal-overlay" onClick={() => setShowProfile(false)}>
          <div className="modal-content profile-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Profil Bilgileri</h3>
              <button
                className="modal-close-button"
                onClick={() => setShowProfile(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="modal-body">
              {isLoadingProfile ? (
                <div className="profile-loading-modal">
                  <div className="loading-spinner"></div>
                  <p>Profil bilgileri yükleniyor...</p>
                </div>
              ) : (
                <UserProfileCard userData={userProfile} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Interest Calculator Modal */}
      <InterestCalculatorModal
        isOpen={showInterestCalculator}
        onClose={() => setShowInterestCalculator(false)}
        onSubmit={handleInterestCalculatorSubmit}
      />

      {/* Loan Amortization Modal */}
      <LoanAmortizationModal
        isOpen={showLoanAmortization}
        onClose={() => setShowLoanAmortization(false)}
        onSubmit={handleLoanAmortizationSubmit}
      />

      {/* ROI Simulation Modal */}
      <ROISimulationModal
        isOpen={showROISimulation}
        onClose={() => setShowROISimulation(false)}
        onSubmit={handleROISimulationSubmit}
      />

      {/* Payment Confirmation Modal */}
      <PaymentConfirmationModal
        isOpen={showPaymentConfirmation}
        onClose={() => {
          setShowPaymentConfirmation(false)
          setPaymentConfirmationData(null)
        }}
        onConfirm={handlePaymentConfirmation}
        paymentData={paymentConfirmationData}
      />

      {/* Payment Transfer Modal */}
      <PaymentTransferModal
        isOpen={showPaymentTransfer}
        onClose={() => setShowPaymentTransfer(false)}
        onSubmit={handlePaymentTransferSubmit}
        userInfo={userInfo}
      />

      {/* ROI Chart Modal */}
      {showROIChart && roiChartData && (
        <div className="modal-overlay" onClick={() => setShowROIChart(false)}>
          <div className="chart-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="chart-modal-header">
              <h3>ROI Büyüme Eğrisi</h3>
              <button 
                className="chart-modal-close-button"
                onClick={() => setShowROIChart(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="chart-modal-body">
              <div className="chart-container-large">
                                {roiChartData && (() => {
                  const chartData = calculateROIData(
                    roiChartData.years || 10,
                    roiChartData.monthly_investment || 1000,
                    {
                      average: roiChartData.average_outcome,
                      optimistic: roiChartData.good_scenario_outcome,
                      pessimistic: roiChartData.bad_scenario_outcome
                    }
                  )
                  
                  return (
                    <Line
                      data={{
                        labels: chartData.labels,
                        datasets: [
                          {
                            label: 'Kötümser Senaryo (25%)',
                            data: chartData.pessimisticData,
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                          },
                          {
                            label: 'Ortalama Senaryo',
                            data: chartData.averageData,
                            borderColor: '#1789dc',
                            backgroundColor: 'rgba(23, 137, 220, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                          },
                          {
                            label: 'İyimser Senaryo (75%)',
                            data: chartData.optimisticData,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                          }
                        ]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              usePointStyle: true,
                              padding: 20,
                              font: {
                                size: 12
                              }
                            }
                          },
                          tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                              label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y)
                              }
                            }
                          }
                        },
                        scales: {
                          x: {
                            title: {
                              display: true,
                              text: 'Yıl',
                              font: {
                                size: 14,
                                weight: 'bold'
                              }
                            },
                            grid: {
                              color: 'rgba(0,0,0,0.1)',
                              drawBorder: false
                            }
                          },
                          y: {
                            title: {
                              display: true,
                              text: 'Portföy Değeri (TL)',
                              font: {
                                size: 14,
                                weight: 'bold'
                              }
                            },
                            grid: {
                              color: 'rgba(0,0,0,0.1)',
                              drawBorder: false
                            },
                            ticks: {
                              callback: function(value) {
                                return formatCurrency(value)
                              }
                            }
                          }
                        },
                        interaction: {
                          mode: 'nearest',
                          axis: 'x',
                          intersect: false
                        }
                      }}
                      height={400}
                    />
                  )
                })()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Kullanıcı Rehberi */}
      <UserGuide 
        isOpen={showUserGuide} 
        onClose={() => setShowUserGuide(false)} 
      />

      {/* Akıllı Bildirimler */}
      {notifications.map((notification) => (
        <SmartNotification
          key={notification.id}
          notification={notification}
          onClose={removeNotification}
          onAction={handleNotificationAction}
        />
      ))}
    </div>
  )
}

export default App


