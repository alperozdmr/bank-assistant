import React from 'react'
import './PaymentReceiptCard.css'

const PaymentReceiptCard = ({ cardData, onDownloadPDF }) => {
  if (!cardData || !cardData.data) return null

  const { txn, receipt } = cardData.data

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatAmount = (amount, currency = 'TRY') => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: currency
    }).format(amount)
  }

  return (
    <div className="payment-receipt-card">
      <div className="payment-receipt-header">
        <div className="payment-receipt-left">
          <div className="payment-receipt-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3 className="payment-receipt-title">Transfer Makbuzu</h3>
        </div>
        <div className="payment-receipt-status">
          <button 
            className="download-pdf-button"
            onClick={(e) => onDownloadPDF && onDownloadPDF(receipt, e)}
            title="PDF olarak indir"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 13H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 17H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M10 9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            PDF
          </button>
        </div>
      </div>

      <div className="payment-receipt-content">
        <div className="receipt-section">
          <h4>İşlem Bilgileri</h4>
          <div className="receipt-row">
            <span className="label">İşlem ID:</span>
            <span className="value">{txn.payment_id || '-'}</span>
          </div>
          <div className="receipt-row">
            <span className="label">Tarih:</span>
            <span className="value">{formatDate(txn.posted_at || txn.created_at)}</span>
          </div>
          <div className="receipt-row">
            <span className="label">Durum:</span>
            <span className="value status-success">Tamamlandı</span>
          </div>
        </div>

        <div className="receipt-sections-grid">
          <div className="receipt-section">
            <h4>Transfer Detayları</h4>
            <div className="receipt-row">
              <span className="label">Gönderen Hesap:</span>
              <span className="value">#{txn.from_account}</span>
            </div>
            <div className="receipt-row">
              <span className="label">Alıcı Hesap:</span>
              <span className="value">#{txn.to_account}</span>
            </div>
            <div className="receipt-row">
              <span className="label">Tutar:</span>
              <span className="value amount">{formatAmount(txn.amount, txn.currency)}</span>
            </div>
            {txn.fee > 0 && (
              <div className="receipt-row">
                <span className="label">İşlem Ücreti:</span>
                <span className="value fee">-{formatAmount(txn.fee, txn.currency)}</span>
              </div>
            )}
          </div>

          <div className="receipt-section">
            <h4>Açıklama</h4>
            <div className="receipt-note">
              {txn.note || 'Açıklama yok'}
            </div>
          </div>

          <div className="receipt-section">
            <h4>Bakiye Bilgileri</h4>
            {txn.from_balance_after !== undefined && (
              <div className="receipt-row">
                <span className="label">Gönderen Hesap Yeni Bakiye:</span>
                <span className="value">{formatAmount(txn.from_balance_after, txn.currency)}</span>
              </div>
            )}
            {txn.to_balance_after !== undefined && (
              <div className="receipt-row">
                <span className="label">Alıcı Hesap Yeni Bakiye:</span>
                <span className="value">{formatAmount(txn.to_balance_after, txn.currency)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaymentReceiptCard
