import './ExchangeRatesCard.css'

const ExchangeRatesCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'exchange_rates_card') return null

  const isSingleRate = cardData.rates && cardData.rates.length === 1

  return (
    <div className={`exchange-rates-card ${isSingleRate ? 'single-rate' : ''}`}>
      <div className="exchange-rates-card-header">
        <div className="exchange-rates-card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
        <div className="exchange-rates-card-title">
          {isSingleRate ? `${cardData.rates[0].code} Kuru` : 'Güncel Döviz Kurları'}
        </div>
      </div>
      <div className="exchange-rates-card-content">
        <div className={`rates-list ${isSingleRate ? 'single-rate-list' : ''}`}>
          {cardData.rates && cardData.rates.map((rate, index) => (
            <div key={index} className={`rate-item ${isSingleRate ? 'single-rate-item' : ''}`}>
              <div className="rate-info">
                <div className="currency-pair">{rate.code}</div>
                <div className="rate-updated">
                  {rate.updated_at && new Date(rate.updated_at).toLocaleString('tr-TR')}
                </div>
              </div>
              <div className="rate-prices">
                <div className="rate-price buy">
                  <span className="rate-label">Alış</span>
                  <span className="rate-value">{rate.buy ? parseFloat(rate.buy).toFixed(4) : 'N/A'}</span>
                </div>
                <div className="rate-price sell">
                  <span className="rate-label">Satış</span>
                  <span className="rate-value">{rate.sell ? parseFloat(rate.sell).toFixed(4) : 'N/A'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        {cardData.rates && cardData.rates.length > 0 && !isSingleRate && (
          <div className="rates-summary">
            {cardData.rates.length} döviz kuru gösteriliyor
          </div>
        )}
      </div>
    </div>
  )
}

export default ExchangeRatesCard
