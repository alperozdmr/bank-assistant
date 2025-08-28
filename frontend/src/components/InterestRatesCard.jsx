import './InterestRatesCard.css'

const InterestRatesCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'interest_rates_card') return null

  const normalize = (s) => (s || '').toString().trim().toLocaleLowerCase('tr-TR')

  const allowedMap = new Map([
    ['mevduat', 'Mevduat'],
    ['ihtiyaç kredisi', 'İhtiyaç Kredisi'],
    ['ihtiyac kredisi', 'İhtiyaç Kredisi'],
    ['kredi kartı', 'Kredi Kartı'],
    ['kredi karti', 'Kredi Kartı'],
  ])

  const filteredRates = (cardData.rates || []).filter(r => allowedMap.has(normalize(r.product)))

  const productDisplayName = (product) => allowedMap.get(normalize(product)) || product

  return (
    <div className="interest-rates-card">
      <div className="interest-rates-card-header">
        <div className="interest-rates-card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Chart/Line Graph Icon */}
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
            {/* Chart Line */}
            <path d="M7 14l3-3 2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            {/* Data Points */}
            <circle cx="7" cy="14" r="1.5" fill="currentColor"/>
            <circle cx="10" cy="11" r="1.5" fill="currentColor"/>
            <circle cx="12" cy="13" r="1.5" fill="currentColor"/>
            <circle cx="16" cy="9" r="1.5" fill="currentColor"/>
          </svg>
        </div>
        <div className="interest-rates-card-title">Güncel Faiz Oranları</div>
      </div>
      <div className="interest-rates-card-content">
        <div className="interest-rates-list">
          {filteredRates && filteredRates.map((rate, index) => (
            <div key={index} className="interest-rate-item">
              <div className="interest-rate-info">
                <div className="product-name">
                  {productDisplayName(rate.product)}
                </div>
                <div className="rate-updated">
                  {rate.updated_at && new Date(rate.updated_at).toLocaleString('tr-TR')}
                </div>
              </div>
              <div className="interest-rate-value">
                <span className="rate-percentage">
                  %{rate.rate_apy ? parseFloat(rate.rate_apy).toFixed(2) : 'N/A'}
                </span>
                <span className="rate-type">Yıllık</span>
              </div>
            </div>
          ))}
        </div>
        {filteredRates && filteredRates.length > 0 && (
          <div className="interest-rates-summary">
            {filteredRates.length} faiz oranı gösteriliyor
          </div>
        )}
      </div>
    </div>
  )
}

export default InterestRatesCard
