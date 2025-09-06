import { useState, useEffect } from 'react'
import './PaymentTransferModal.css'

const PaymentTransferModal = ({ isOpen, onClose, onSubmit, userInfo }) => {
  const [formData, setFormData] = useState({
    from_account: '',
    to_account: '',
    amount: '',
    currency: 'TRY',
    note: ''
  })

  const [errors, setErrors] = useState({})
  const [accounts, setAccounts] = useState([])
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(false)

  // Hesapları yükle
  useEffect(() => {
    if (isOpen && userInfo?.token) {
      loadAccounts()
    }
  }, [isOpen, userInfo?.token])

  const loadAccounts = async () => {
    setIsLoadingAccounts(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/accounts', {
        headers: {
          'Authorization': `Bearer ${userInfo.token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // API'den gelen veriyi normalize et
        if (data.accounts) {
          // Birden fazla hesap varsa
          setAccounts(data.accounts.map(acc => ({
            number: acc.account_id.toString(),
            name: `${acc.account_type} Hesabı`,
            balance: acc.balance,
            currency: acc.currency,
            account_id: acc.account_id,
            account_type: acc.account_type,
            status: acc.status
          })))
        } else if (data.account_id) {
          // Tek hesap varsa
          setAccounts([{
            number: data.account_id.toString(),
            name: `${data.account_type} Hesabı`,
            balance: data.balance,
            currency: data.currency,
            account_id: data.account_id,
            account_type: data.account_type,
            status: data.status
          }])
        }
      } else {
        console.error('Hesaplar yüklenemedi:', response.status)
      }
    } catch (error) {
      console.error('Hesaplar yükleme hatası:', error)
    } finally {
      setIsLoadingAccounts(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Gönderen hesap değiştiğinde para birimini otomatik ayarla
    if (name === 'from_account' && value) {
      const selectedAccount = accounts.find(acc => acc.number === value)
      if (selectedAccount) {
        setFormData(prev => ({
          ...prev,
          [name]: value,
          currency: selectedAccount.currency
        }))
      }
    }
    
    // Hata mesajını temizle
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.from_account) {
      newErrors.from_account = 'Gönderen hesap seçilmelidir'
    }

    if (!formData.to_account) {
      newErrors.to_account = 'Alıcı hesap seçilmelidir'
    }

    if (formData.from_account === formData.to_account) {
      newErrors.to_account = 'Gönderen ve alıcı hesap aynı olamaz'
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Transfer tutarı 0\'dan büyük olmalıdır'
    }

    // Bakiye kontrolü
    const fromAccount = accounts.find(acc => acc.number === formData.from_account)
    if (fromAccount && parseFloat(formData.amount) > fromAccount.balance) {
      newErrors.amount = 'Yetersiz bakiye'
    }

    // Para birimi uyumsuzluğu kontrolü
    const toAccount = accounts.find(acc => acc.number === formData.to_account)
    if (fromAccount && toAccount && fromAccount.currency !== toAccount.currency) {
      newErrors.to_account = `Para birimi uyumsuzluğu: Gönderen hesap ${fromAccount.currency}, alıcı hesap ${toAccount.currency}`
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (validateForm()) {
      const fromAccount = accounts.find(acc => acc.number === formData.from_account)
      const toAccount = accounts.find(acc => acc.number === formData.to_account)
      
      const submitData = {
        ...formData,
        amount: parseFloat(formData.amount),
        from_account_name: fromAccount?.name || '',
        to_account_name: toAccount?.name || '',
        from_balance: fromAccount?.balance || 0,
        to_balance: toAccount?.balance || 0
      }
      
      onSubmit(submitData)
      onClose()
    }
  }

  const handleClose = () => {
    setFormData({
      from_account: '',
      to_account: '',
      amount: '',
      currency: 'TRY',
      note: ''
    })
    setErrors({})
    onClose()
  }

  const getAccountBalance = (accountNumber) => {
    const account = accounts.find(acc => acc.number === accountNumber)
    return account ? account.balance : 0
  }

  const formatCurrency = (amount, currency = 'TRY') => {
    if (amount === null || amount === undefined) return '-'
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content payment-transfer-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Para Transferi</h3>
          <button className="modal-close-button" onClick={handleClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body vertical-form">
          <div className="form-group">
            <label htmlFor="from_account">Gönderen Hesap</label>
            <select
              id="from_account"
              name="from_account"
              value={formData.from_account}
              onChange={handleInputChange}
              className={`form-select ${errors.from_account ? 'error' : ''}`}
              disabled={isLoadingAccounts}
            >
              <option value="">
                {isLoadingAccounts ? 'Hesaplar yükleniyor...' : 'Hesap seçiniz'}
              </option>
              {accounts.map(account => (
                <option key={account.number} value={account.number}>
                  {account.name} - {account.number} (Bakiye: {formatCurrency(account.balance, account.currency)})
                </option>
              ))}
            </select>
            {errors.from_account && <span className="error-message">{errors.from_account}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="to_account">Alıcı Hesap</label>
            <select
              id="to_account"
              name="to_account"
              value={formData.to_account}
              onChange={handleInputChange}
              className={`form-select ${errors.to_account ? 'error' : ''}`}
              disabled={isLoadingAccounts}
            >
              <option value="">
                {isLoadingAccounts ? 'Hesaplar yükleniyor...' : 'Hesap seçiniz'}
              </option>
              {accounts.map(account => (
                <option key={account.number} value={account.number}>
                  {account.name} - {account.number} (Bakiye: {formatCurrency(account.balance, account.currency)})
                </option>
              ))}
            </select>
            {errors.to_account && <span className="error-message">{errors.to_account}</span>}
          </div>

          <div className="form-row">
            <div className="form-group form-group--amount">
              <label htmlFor="amount">Transfer Tutarı</label>
              <input
                type="number"
                id="amount"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                placeholder="0.00"
                step="0.01"
                min="0"
                className={errors.amount ? 'error' : ''}
              />
              {errors.amount && <span className="error-message">{errors.amount}</span>}
            </div>
            <div className="form-group form-group--shrink">
              <label htmlFor="currency">Para Birimi</label>
              <select
                id="currency"
                name="currency"
                value={formData.currency}
                onChange={handleInputChange}
                className="form-select"
                disabled={!formData.from_account}
              >
                {formData.from_account ? (
                  <option value={formData.currency}>
                    {formData.currency === 'TRY' && 'Türk Lirası (TRY)'}
                    {formData.currency === 'USD' && 'ABD Doları (USD)'}
                    {formData.currency === 'EUR' && 'Euro (EUR)'}
                  </option>
                ) : (
                  <option value="">Önce gönderen hesap seçiniz</option>
                )}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="note">Açıklama (Opsiyonel)</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleInputChange}
              placeholder="Transfer açıklaması..."
              rows="3"
              maxLength="200"
              className="form-textarea"
            />
            <span className="help-text">Maksimum 200 karakter</span>
          </div>


          <div className="form-actions">
            <button type="button" className="modal-cancel-button" onClick={handleClose}>
              İptal
            </button>
            <button type="submit" className="modal-confirm-button">
              Transfer Et
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PaymentTransferModal
