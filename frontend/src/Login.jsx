import { useState, useEffect } from 'react'
import './Login.css'

function Login({ onLogin }) {
  const [customerNo, setCustomerNo] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isDarkTheme, setIsDarkTheme] = useState(false)

  // LocalStorage'dan tema tercihini yükle
  useEffect(() => {
    const savedTheme = localStorage.getItem('interChatTheme')
    if (savedTheme) {
      setIsDarkTheme(JSON.parse(savedTheme))
    }
  }, [])

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

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!customerNo.trim() || !password.trim()) {
      setError('Lütfen müşteri numaranızı ve şifrenizi girin.')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_no: customerNo, password })
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data?.detail || 'Giriş başarısız. Lütfen tekrar deneyin.')
        return
      }

      if (data?.success) {
        onLogin({
          customerNo,
          userId: data.customer_id,
          token: data.token
        })
      } else {
        setError(data?.message || 'Müşteri numarası veya şifre hatalı.')
      }
    } catch (err) {
      console.error("Login işlemi başarısız:", err)
      setError('Giriş işlemi başarısız. Lütfen tekrar deneyin.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`login-container ${isDarkTheme ? 'dark-theme' : ''}`}>
      {/* Theme Toggle - Top Right */}
      <div className="theme-toggle-wrapper">
        <button className="theme-toggle-switch" onClick={toggleTheme}>
          <div className={`toggle-slider ${isDarkTheme ? 'dark' : 'light'}`} style={isDarkTheme ? { '--slider-left': '35px' } : {}}>
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

      <div className="login-main">
        {/* Left Side - Logo Section */}
        <div className="logo-section">
          <div className="logo-content">
            <div className="bot-avatar">
              <img src="/logo.jpg" alt="InterChat Logo" className="avatar-logo" />
            </div>
            <div className="logo-info">
              <h1>InterChat</h1>
              <p>Akıllı Bankacılık Asistanı</p>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="form-section">
          <div className="login-form">
            <div className="form-header">
             <h2>Giriş Yap</h2>
           </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <div className="input-wrapper">
                  <div className="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  </div>
                  <input
                    type="text"
                    id="customerNo"
                    value={customerNo}
                    onChange={(e) => setCustomerNo(e.target.value)}
                    placeholder="Müşteri numaranızı girin"
                    className="form-input"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="form-group">
                <div className="input-wrapper">
                  <div className="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
                      <circle cx="12" cy="16" r="1" stroke="currentColor" strokeWidth="2"/>
                      <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Şifrenizi girin"
                    className="form-input"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="currentColor" strokeWidth="2"/>
                        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C7 20 2 12 2 12C2 12 4.5 7.5 8.5 4.5" stroke="currentColor" strokeWidth="2"/>
                        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4C17 4 22 12 22 12C22 12 21.5 13.5 20.5 14.5" stroke="currentColor" strokeWidth="2"/>
                        <path d="M14.12 14.12A3 3 0 1 1 9.88 9.88" stroke="currentColor" strokeWidth="2"/>
                        <path d="M1 1L23 23" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                    <path d="M15 9L9 15" stroke="currentColor" strokeWidth="2"/>
                    <path d="M9 9L15 15" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  {error}
                </div>
              )}

              <button
                type="submit"
                className={`login-button ${isLoading ? 'loading' : ''}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <div className="spinner"></div>
                    <span style={{animation: 'none', transform: 'none'}}>Giriş yapılıyor...</span>
                  </>
                ) : (
                  'Giriş'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
