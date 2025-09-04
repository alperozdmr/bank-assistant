import { useState } from 'react'
import './InterestCalculatorModal.css'

const LoanAmortizationModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    principal: '',
    term: '', // months
    rate: '', // optional
    currency: 'TRY'
  })

  const [errors, setErrors] = useState({})

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }))
  }

  const validate = () => {
    const e = {}
    if (!formData.principal || parseFloat(formData.principal) <= 0) e.principal = 'Anapara 0’dan büyük olmalıdır'
    if (!formData.term || parseInt(formData.term) <= 0) e.term = 'Vade (ay) 0’dan büyük olmalıdır'
    if (formData.rate) {
      const r = parseFloat(formData.rate)
      if (r < 0 || r > 100) e.rate = 'Faiz oranı 0-100 arasında olmalıdır'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    const payload = {
      principal: parseFloat(formData.principal),
      term: parseInt(formData.term, 10),
      rate: formData.rate ? parseFloat(formData.rate) : undefined,
      currency: formData.currency
    }
    onSubmit(payload)
    onClose()
  }

  const handleClose = () => {
    setFormData({ principal: '', term: '', rate: '', currency: 'TRY' })
    setErrors({})
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content interest-calculator-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Kredi Amortisman Hesaplama</h3>
          <button className="modal-close-button" onClick={handleClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body vertical-form">
          <div className="form-row">
            <div className="form-group form-group--principal">
              <label htmlFor="principal">Anapara</label>
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
              {errors.principal && <span className="error-message">{errors.principal}</span>}
            </div>
            <div className="form-group form-group--shrink">
              <label htmlFor="currency">Para Birimi</label>
              <select
                id="currency"
                name="currency"
                value={formData.currency}
                onChange={handleInputChange}
                className="form-select"
              >
                <option value="TRY">Türk Lirası (TRY)</option>
                <option value="USD">ABD Doları (USD)</option>
                <option value="EUR">Euro (EUR)</option>
                <option value="GBP">İngiliz Sterlini (GBP)</option>
                <option value="JPY">Japon Yeni (JPY)</option>
                <option value="CHF">İsviçre Frangı (CHF)</option>
                <option value="CAD">Kanada Doları (CAD)</option>
                <option value="AUD">Avustralya Doları (AUD)</option>
                <option value="CNY">Çin Yuanı (CNY)</option>
                <option value="RUB">Rus Rublesi (RUB)</option>
                <option value="SAR">Suudi Arabistan Riyali (SAR)</option>
                <option value="AED">BAE Dirhemi (AED)</option>
                <option value="KWD">Kuveyt Dinarı (KWD)</option>
                <option value="NOK">Norveç Kronu (NOK)</option>
                <option value="SEK">İsveç Kronu (SEK)</option>
                <option value="DKK">Danimarka Kronu (DKK)</option>
                <option value="BGN">Bulgar Levası (BGN)</option>
                <option value="RON">Rumen Leyi (RON)</option>
                <option value="PKR">Pakistan Rupisi (PKR)</option>
                <option value="QAR">Katar Riyali (QAR)</option>
                <option value="KRW">Güney Kore Wonu (KRW)</option>
                <option value="AZN">Azerbaycan Manatı (AZN)</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="term">Vade (Ay)</label>
              <input
                type="number"
                id="term"
                name="term"
                value={formData.term}
                onChange={handleInputChange}
                placeholder="0"
                step="1"
                min="1"
                className={errors.term ? 'error' : ''}
              />
              {errors.term && <span className="error-message">{errors.term}</span>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="rate">Yıllık Faiz Oranı (%)</label>
            <input
              type="number"
              id="rate"
              name="rate"
              value={formData.rate}
              onChange={handleInputChange}
              placeholder="Otomatik (güncel oran)"
              step="0.01"
              min="0"
              max="100"
              className={errors.rate ? 'error' : ''}
            />
            <span className="help-text">Boş bırakırsanız güncel banka oranları kullanılır</span>
            {errors.rate && <span className="error-message">{errors.rate}</span>}
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

export default LoanAmortizationModal
