import { useState, useEffect } from 'react'
import './ROISimulationModal.css'

const ROISimulationModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    portfolio_name: '',
    monthly_investment: '',
    years: ''
  })

  const [errors, setErrors] = useState({})
  const [availablePortfolios, setAvailablePortfolios] = useState([])
  const [isLoadingPortfolios, setIsLoadingPortfolios] = useState(false)

  // Portföy listesini yükle
  useEffect(() => {
    if (isOpen) {
      loadPortfolios()
    }
  }, [isOpen])

  const loadPortfolios = async () => {
    setIsLoadingPortfolios(true)
    try {
      // Bu kısım backend'den portföy listesi çekecek
      // Şimdilik dummy data kullanıyoruz
      setAvailablePortfolios([
        { portfoy_adi: 'Dengeli Portföy', risk_seviyesi: 'Orta' },
        { portfoy_adi: 'Büyüme Portföyü', risk_seviyesi: 'Yüksek' },
        { portfoy_adi: 'Korumalı Portföy', risk_seviyesi: 'Düşük' },
      ])
    } catch (error) {
      console.error('Portföy listesi yüklenemedi:', error)
    } finally {
      setIsLoadingPortfolios(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }))
  }

  const validate = () => {
    const e = {}
    if (!formData.portfolio_name) e.portfolio_name = 'Portföy seçimi zorunludur'
    if (!formData.monthly_investment || parseFloat(formData.monthly_investment) <= 0) {
      e.monthly_investment = 'Aylık yatırım tutarı 0\'dan büyük olmalıdır'
    }
    if (!formData.years || parseInt(formData.years) < 1 || parseInt(formData.years) > 50) {
      e.years = 'Vade 1-50 yıl arasında olmalıdır'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    
    const payload = {
      portfolio_name: formData.portfolio_name,
      monthly_investment: parseFloat(formData.monthly_investment),
      years: parseInt(formData.years, 10)
    }
    onSubmit(payload)
    onClose()
  }

  const handleClose = () => {
    setFormData({ portfolio_name: '', monthly_investment: '', years: '' })
    setErrors({})
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content roi-simulation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>ROI Simülasyonu</h3>
          <button className="modal-close-button" onClick={handleClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body vertical-form">
          <div className="form-group">
            <label htmlFor="portfolio_name">Portföy Seçimi</label>
            <select
              id="portfolio_name"
              name="portfolio_name"
              value={formData.portfolio_name}
              onChange={handleInputChange}
              className={`form-select ${errors.portfolio_name ? 'error' : ''}`}
              disabled={isLoadingPortfolios}
            >
              <option value="">Portföy seçiniz</option>
              {availablePortfolios.map((portfolio, index) => (
                <option key={index} value={portfolio.portfoy_adi}>
                  {portfolio.portfoy_adi} ({portfolio.risk_seviyesi} Risk)
                </option>
              ))}
            </select>
            {isLoadingPortfolios && <span className="loading-text">Portföyler yükleniyor...</span>}
            {errors.portfolio_name && <span className="error-message">{errors.portfolio_name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="monthly_investment">Aylık Yatırım Tutarı (TL)</label>
            <input
              type="number"
              id="monthly_investment"
              name="monthly_investment"
              value={formData.monthly_investment}
              onChange={handleInputChange}
              placeholder="1000.00"
              step="100"
              min="100"
              className={errors.monthly_investment ? 'error' : ''}
            />
            <span className="help-text">Minimum 100 TL</span>
            {errors.monthly_investment && <span className="error-message">{errors.monthly_investment}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="years">Yatırım Vadesi (Yıl)</label>
            <input
              type="number"
              id="years"
              name="years"
              value={formData.years}
              onChange={handleInputChange}
              placeholder="5"
              step="1"
              min="1"
              max="50"
              className={errors.years ? 'error' : ''}
            />
            <span className="help-text">1-50 yıl arası</span>
            {errors.years && <span className="error-message">{errors.years}</span>}
          </div>

          <div className="simulation-info">
            <div className="info-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <path d="M12 16v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                <path d="M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              <span>Simülasyon Bilgileri</span>
            </div>
            <div className="info-content">
              <p>• Monte Carlo simülasyonu ile 1000 farklı senaryo hesaplanır</p>
              <p>• Geçmiş veriler kullanılarak risk ve getiri tahmini yapılır</p>
              <p>• Sonuçlar: Ortalama, İyimser (%75) ve Kötümser (%25) senaryolar</p>
              <p>• <strong>Uyarı:</strong> Geçmiş performans gelecekteki sonuçların garantisi değildir</p>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="modal-cancel-button" onClick={handleClose}>
              İptal
            </button>
            <button type="submit" className="modal-confirm-button">
              Simülasyonu Başlat
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ROISimulationModal
