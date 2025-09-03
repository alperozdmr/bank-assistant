import { useState } from 'react'
import './InterestCalculatorModal.css'

const InterestCalculatorModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    type: 'deposit',
    principal: '',
    term: '',
    term_unit: 'years',
    compounding: 'monthly',
    rate: '',
    currency: 'TRY'
  })

  const [errors, setErrors] = useState({})

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
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

    if (!formData.principal || parseFloat(formData.principal) <= 0) {
      newErrors.principal = 'Anapara 0\'dan büyük olmalıdır'
    }

    if (!formData.term || parseFloat(formData.term) <= 0) {
      newErrors.term = 'Vade 0\'dan büyük olmalıdır'
    }

    if (formData.type === 'loan' && formData.term_unit === 'years' && parseFloat(formData.term) > 30) {
      newErrors.term = 'Kredi vadesi 30 yıldan fazla olamaz'
    }

    if (formData.rate && (parseFloat(formData.rate) < 0 || parseFloat(formData.rate) > 100)) {
      newErrors.rate = 'Faiz oranı 0-100 arasında olmalıdır'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (validateForm()) {
      const submitData = {
        ...formData,
        principal: parseFloat(formData.principal),
        term: parseFloat(formData.term),
        rate: formData.rate ? parseFloat(formData.rate) : undefined
      }
      
      onSubmit(submitData)
      onClose()
    }
  }

  const handleClose = () => {
    setFormData({
      type: 'deposit',
      principal: '',
      term: '',
      term_unit: 'years',
      compounding: 'monthly',
      rate: '',
      currency: 'TRY'
    })
    setErrors({})
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content interest-calculator-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Faiz Hesaplama</h3>
          <button className="modal-close-button" onClick={handleClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-section">
            <h4>Hesaplama Türü</h4>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="type"
                  value="deposit"
                  checked={formData.type === 'deposit'}
                  onChange={handleInputChange}
                />
                <span className="radio-custom"></span>
                <span className="radio-label">Mevduat Getirisi</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="type"
                  value="loan"
                  checked={formData.type === 'loan'}
                  onChange={handleInputChange}
                />
                <span className="radio-custom"></span>
                <span className="radio-label">Kredi Taksiti</span>
              </label>
            </div>
          </div>

          <div className="form-section">
            <h4>Temel Bilgiler</h4>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="principal">Anapara</label>
                <div className="input-wrapper">
                  <input
                    type="number"
                    id="principal"
                    name="principal"
                    value={formData.principal}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    className={errors.principal ? 'error' : ''}
                  />
                  <span className="currency-symbol">{formData.currency}</span>
                </div>
                {errors.principal && <span className="error-message">{errors.principal}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="term">Vade</label>
                <div className="input-wrapper">
                  <input
                    type="number"
                    id="term"
                    name="term"
                    value={formData.term}
                    onChange={handleInputChange}
                    placeholder="0"
                    step="0.01"
                    min="0"
                    className={errors.term ? 'error' : ''}
                  />
                  <select
                    name="term_unit"
                    value={formData.term_unit}
                    onChange={handleInputChange}
                    className="term-unit-select"
                  >
                    <option value="years">Yıl</option>
                    <option value="months">Ay</option>
                  </select>
                </div>
                {errors.term && <span className="error-message">{errors.term}</span>}
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Faiz Oranı</h4>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="rate">Yıllık Faiz Oranı (%)</label>
                <div className="input-wrapper">
                  <input
                    type="number"
                    id="rate"
                    name="rate"
                    value={formData.rate}
                    onChange={handleInputChange}
                    placeholder="Otomatik (güncel oranlar)"
                    step="0.01"
                    min="0"
                    max="100"
                    className={errors.rate ? 'error' : ''}
                  />
                  <span className="input-suffix">%</span>
                </div>
                <span className="help-text">Boş bırakırsanız güncel banka oranları kullanılır</span>
                {errors.rate && <span className="error-message">{errors.rate}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="compounding">Bileşik Sıklığı</label>
                <select
                  id="compounding"
                  name="compounding"
                  value={formData.compounding}
                  onChange={handleInputChange}
                  className="form-select"
                >
                  <option value="annual">Yıllık</option>
                  <option value="semiannual">6 Aylık</option>
                  <option value="quarterly">3 Aylık</option>
                  <option value="monthly">Aylık</option>
                  <option value="weekly">Haftalık</option>
                  <option value="daily">Günlük</option>
                  <option value="continuous">Sürekli</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Para Birimi</h4>
            <div className="form-group">
              <label htmlFor="currency">Para Birimi</label>
              <select
                id="currency"
                name="currency"
                value={formData.currency}
                onChange={handleInputChange}
                className="form-select"
              >
                <option value="TRY">Türk Lirası (TRY)</option>
                <option value="USD">Amerikan Doları (USD)</option>
                <option value="EUR">Euro (EUR)</option>
                <option value="GBP">İngiliz Sterlini (GBP)</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="modal-cancel-button" onClick={handleClose}>
              İptal
            </button>
            <button type="submit" className="modal-confirm-button">
              Hesapla
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default InterestCalculatorModal
