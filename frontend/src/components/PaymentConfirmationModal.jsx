import { useState } from 'react'
import './PaymentConfirmationModal.css'

const PaymentConfirmationModal = ({ isOpen, onClose, onConfirm, paymentData }) => {
  const [isProcessing, setIsProcessing] = useState(false)

  if (!isOpen || !paymentData) return null

  const handleConfirm = async () => {
    setIsProcessing(true)
    try {
      await onConfirm(paymentData)
    } finally {
      setIsProcessing(false)
    }
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

  const formatAccountNumber = (accountNumber) => {
    if (!accountNumber) return '-'
    return accountNumber.toString().replace(/(\d{4})(?=\d)/g, '$1 ')
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content payment-confirmation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Transfer Onayı</h3>
          <button className="modal-close-button" onClick={onClose} disabled={isProcessing}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        <div className="modal-body">
          <div className="payment-summary">
            <div className="summary-header">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 13H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 17H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M10 9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Transfer Detayları</span>
            </div>

            <div className="payment-details">
              <div className="detail-row">
                <span className="detail-label">Gönderen Hesap:</span>
                <span className="detail-value">{formatAccountNumber(paymentData.from_account)}</span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Alıcı Hesap:</span>
                <span className="detail-value">{formatAccountNumber(paymentData.to_account)}</span>
              </div>
              
              <div className="detail-row amount-row">
                <span className="detail-label">Transfer Tutarı:</span>
                <span className="detail-value amount">{formatCurrency(paymentData.amount, paymentData.currency)}</span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">Para Birimi:</span>
                <span className="detail-value">{paymentData.currency}</span>
              </div>
              
              {paymentData.fee > 0 && (
                <div className="detail-row">
                  <span className="detail-label">İşlem Ücreti:</span>
                  <span className="detail-value">{formatCurrency(paymentData.fee, paymentData.currency)}</span>
                </div>
              )}
              
              <div className="detail-row">
                <span className="detail-label">Açıklama:</span>
                <span className="detail-value">{paymentData.note}</span>
              </div>
            </div>
          </div>

          {paymentData.limits && (
            <div className="limits-info">
              <div className="info-header">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <path d="M12 16v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span>Limit Bilgileri</span>
              </div>
              <div className="info-content">
                <div className="limit-row">
                  <span>Tek İşlem Limiti:</span>
                  <span>{formatCurrency(paymentData.limits.per_txn, paymentData.currency)}</span>
                </div>
                <div className="limit-row">
                  <span>Günlük Limit:</span>
                  <span>{formatCurrency(paymentData.limits.daily, paymentData.currency)}</span>
                </div>
                <div className="limit-row">
                  <span>Bugün Kullanılan:</span>
                  <span>{formatCurrency(paymentData.limits.used_today, paymentData.currency)}</span>
                </div>
              </div>
            </div>
          )}

          <div className="confirmation-warning">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L22 20H2L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 9V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p>Bu işlemi onayladığınızda transfer gerçekleştirilecektir. Lütfen bilgileri kontrol ediniz.</p>
          </div>

          <div className="form-actions">
            <button 
              type="button" 
              className="modal-cancel-button" 
              onClick={onClose}
              disabled={isProcessing}
            >
              İptal
            </button>
            <button 
              type="button" 
              className="modal-confirm-button" 
              onClick={handleConfirm}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <svg className="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12A9 9 0 1 1 3 12A9 9 0 0 1 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="31.416" strokeDashoffset="31.416">
                      <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
                      <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
                    </path>
                  </svg>
                  İşleniyor...
                </>
              ) : (
                'Transferi Onayla'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaymentConfirmationModal


