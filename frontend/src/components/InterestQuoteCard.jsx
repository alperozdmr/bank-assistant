import './InterestQuoteCard.css'

const InterestQuoteCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'interest_quote_card') return null

  const formatCurrency = (amount, currency = 'TRY') => {
    if (amount === undefined || amount === null || isNaN(parseFloat(amount))) return '—'
    if (currency === 'TRY') {
      return `${parseFloat(amount).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.')} ${currency}`
    }
    return `${parseFloat(amount).toFixed(2)} ${currency}`
  }

  const formatPercentage = (rate) => {
    if (rate === undefined || rate === null || isNaN(parseFloat(rate))) return '—'
    return `%${(parseFloat(rate) * 100).toFixed(2)}`
  }

  const getCompoundingLabel = (compounding) => {
    const labels = {
      'annual': 'Yıllık',
      'semiannual': '6 Aylık',
      'quarterly': '3 Aylık',
      'monthly': 'Aylık',
      'weekly': 'Haftalık',
      'daily': 'Günlük',
      'continuous': 'Sürekli'
    }
    return labels[compounding] || compounding
  }

  const getQuoteIcon = (quoteType) => {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Yüzde İşareti Icon */}
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
        <path d="M8 16l8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <path d="M9 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M15 12h.01" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  }

  const getQuoteTitle = (quoteType) => {
    return quoteType === 'deposit' ? 'Mevduat Getiri Hesaplama' : 'Kredi Taksit Hesaplama'
  }

  return (
    <div className="interest-quote-card">
      <div className="interest-quote-card-header">
        <div className="interest-quote-card-icon">
          {getQuoteIcon(cardData.quote_type)}
        </div>
        <div className="interest-quote-card-title">
          {getQuoteTitle(cardData.quote_type)}
        </div>
      </div>
      
      <div className="interest-quote-card-content">
        <div className="quote-summary">
          <div className="quote-row">
            <span className="quote-label">Anapara:</span>
            <span className="quote-value">{formatCurrency(cardData.principal, cardData.currency)}</span>
          </div>
          
          <div className="quote-row">
            <span className="quote-label">Yıllık Faiz Oranı:</span>
            <span className="quote-value rate-value">{formatPercentage(cardData.annual_rate)}</span>
          </div>
          
          {cardData.quote_type === 'deposit' && (
            <>
              <div className="quote-row">
                <span className="quote-label">Vade:</span>
                <span className="quote-value">{cardData.term_years} yıl</span>
              </div>
              
              <div className="quote-row">
                <span className="quote-label">Bileşik Sıklığı:</span>
                <span className="quote-value">{getCompoundingLabel(cardData.compounding)}</span>
              </div>
            </>
          )}
          
          {cardData.quote_type === 'loan' && cardData.periods && (
            <div className="quote-row">
              <span className="quote-label">Taksit Sayısı:</span>
              <span className="quote-value">{cardData.periods} taksit</span>
            </div>
          )}
        </div>

        {cardData.quote_type === 'deposit' ? (
          <div className="deposit-results">
            <div className="result-item main-result">
              <div className="result-label">Gelecek Değer</div>
              <div className="result-value future-value">
                {formatCurrency(cardData.future_value, cardData.currency)}
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Toplam Getiri</div>
              <div className="result-value interest-earned">
                {formatCurrency(cardData.total_interest, cardData.currency)}
              </div>
            </div>
          </div>
        ) : (
          <div className="loan-results">
            <div className="result-item main-result">
              <div className="result-label">Aylık Taksit</div>
              <div className="result-value installment">
                {formatCurrency(cardData.installment, cardData.currency)}
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Toplam Ödeme</div>
              <div className="result-value total-payment">
                {formatCurrency(cardData.total_payment, cardData.currency)}
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Toplam Faiz</div>
              <div className="result-value total-interest">
                {formatCurrency(cardData.total_interest, cardData.currency)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default InterestQuoteCard
