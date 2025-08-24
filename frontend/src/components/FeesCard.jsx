import './FeesCard.css'

const FeesCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'fees_card') return null

  const formatCurrency = (amount, currency = 'TRY') => {
    if (currency === 'TRY') {
      return `${parseFloat(amount).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.')} ${currency}`
    }
    return `${parseFloat(amount).toFixed(2)} ${currency}`
  }

  const renderPricing = (pricing) => {
    if (!pricing || typeof pricing !== 'object') {
      return <span className="fee-value">Bilgi yok</span>
    }

    const type = pricing.type?.toLowerCase()
    
    if (type === 'flat' && pricing.amount !== undefined) {
      return (
        <div className="fee-value-container">
          <span className="fee-value">{formatCurrency(pricing.amount, pricing.currency)}</span>
          <span className="fee-type">Sabit</span>
        </div>
      )
    }
    
    if (type === 'percent' && pricing.rate !== undefined) {
      const percentage = (parseFloat(pricing.rate) * 100).toFixed(2)
      return (
        <div className="fee-value-container">
          <span className="fee-value">%{percentage}</span>
          <span className="fee-type">Oransal</span>
          {(pricing.min || pricing.max) && (
            <div className="fee-limits">
              {pricing.min && <span>Min: {formatCurrency(pricing.min, pricing.currency)}</span>}
              {pricing.max && <span>Max: {formatCurrency(pricing.max, pricing.currency)}</span>}
            </div>
          )}
        </div>
      )
    }
    
    if (type === 'tiered' && pricing.tiers && Array.isArray(pricing.tiers)) {
      return (
        <div className="fee-tiers">
          {pricing.tiers.slice(0, 3).map((tier, index) => (
            <div key={index} className="fee-tier">
              <span className="tier-threshold">
                {tier.threshold ? `≤${parseInt(tier.threshold).toLocaleString('tr-TR')}` : 'Genel'}
              </span>
              <span className="tier-fee">{formatCurrency(tier.fee, 'TRY')}</span>
            </div>
          ))}
          {pricing.tiers.length > 3 && (
            <div className="fee-tier-more">+{pricing.tiers.length - 3} daha</div>
          )}
        </div>
      )
    }
    
    return <span className="fee-value">Detay yok</span>
  }

  return (
    <div className="fees-card">
      <div className="fees-card-header">
        <div className="fees-card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Receipt/Bill Icon */}
            <path d="M4 2v20l4-2 4 2 4-2 4 2V2l-4 2-4-2-4 2-4-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M8 7h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M8 11h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M8 15h5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div className="fees-card-title">Hizmet Ücreti</div>
      </div>
      <div className="fees-card-content">
        <div className="fee-service-info">
          <div className="service-code">{cardData.service_code}</div>
          <div className="service-description">{cardData.description}</div>
          {cardData.updated_at && (
            <div className="fee-updated">
              Son güncelleme: {new Date(cardData.updated_at).toLocaleString('tr-TR')}
            </div>
          )}
        </div>
        <div className="fee-pricing">
          {renderPricing(cardData.pricing)}
        </div>
      </div>
    </div>
  )
}

export default FeesCard

