import { useState, useEffect } from 'react'
import './SmartNotification.css'

const SmartNotification = ({ notification, onClose, onAction }) => {
  const [isVisible, setIsVisible] = useState(false)
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    // Bildirimi göster
    setIsVisible(true)
    
    // Otomatik kapanma için progress bar
    if (notification.autoClose !== false) {
      const duration = notification.duration || 6000 // 5 saniye varsayılan
      const interval = 50 // 50ms'de bir güncelle
      const decrement = (interval / duration) * 100
      
      const timer = setInterval(() => {
        setProgress(prev => {
          if (prev <= 0) {
            clearInterval(timer)
            handleClose()
            return 0
          }
          return prev - decrement
        })
      }, interval)

      return () => clearInterval(timer)
    }
  }, [notification])

  const handleClose = () => {
    setIsVisible(false)
    setTimeout(() => {
      onClose(notification.id)
    }, 300) // CSS transition süresi
  }

  const handleAction = () => {
    if (notification.action && onAction) {
      onAction(notification.action)
    }
    handleClose()
  }

  if (!isVisible) return null

  return (
    <>
      {/* Overlay */}
      {isVisible && <div className="notification-overlay" onClick={handleClose} />}
      
      <div className={`smart-notification ${notification.type || 'info'} ${isVisible ? 'show' : ''}`}>
        <div className="notification-content">
        <div className="notification-icon">
          {notification.type === 'success' && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12L11 14L15 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
            </svg>
          )}
          {notification.type === 'warning' && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10.29 3.86L1.82 18C1.64 18.37 1.64 18.8 1.82 19.17C2 19.54 2.33 19.75 2.7 19.75H21.3C21.67 19.75 22 19.54 22.18 19.17C22.36 18.8 22.36 18.37 22.18 18L13.71 3.86C13.53 3.49 13.2 3.28 12.83 3.28C12.46 3.28 12.13 3.49 11.95 3.86H10.29Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 9V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
          {notification.type === 'error' && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M15 9L9 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M9 9L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
          {(!notification.type || notification.type === 'info') && (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 16V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 8H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </div>
        
        <div className="notification-text">
          <div className="notification-title">{notification.title}</div>
        </div>

        <button 
          className="notification-close-btn"
          onClick={handleClose}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
      
      {notification.action && (
        <div className="notification-action-container">
          <button 
            className="notification-action-btn"
            onClick={handleAction}
          >
            {notification.actionText || 'Görüntüle'}
          </button>
        </div>
      )}
      
      {notification.message && (
        <div className="notification-message-full">{notification.message}</div>
      )}
      
      {notification.autoClose !== false && (
        <div className="notification-progress">
          <div 
            className="notification-progress-bar"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      </div>
    </>
  )
}

export default SmartNotification
