import './PortfoliosCard.css'

const PortfoliosCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'portfolios_card') return null

  const portfolios = cardData.portfolios || []

  if (portfolios.length === 0) {
    return (
      <div className="portfolios-card">
        <div className="portfolios-card-header">
          <div className="portfolios-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Portfolio/Investment Icon */}
              <path d="M3 3h18v18H3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M9 9h6v6H9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 3v18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 12h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="portfolios-card-title">Yatırım Portföyleri</div>
        </div>
        <div className="portfolios-card-content">
          <div className="no-portfolios">
            Henüz portföy bulunamadı.
          </div>
        </div>
      </div>
    )
  }

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'düşük':
      case 'low':
        return 'low-risk'
      case 'orta':
      case 'medium':
        return 'medium-risk'
      case 'yüksek':
      case 'high':
        return 'high-risk'
      default:
        return 'medium-risk'
    }
  }

  const getRiskLabel = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'düşük':
      case 'low':
        return 'Düşük Risk'
      case 'orta':
      case 'medium':
        return 'Orta Risk'
      case 'yüksek':
      case 'high':
        return 'Yüksek Risk'
      default:
        return riskLevel || 'Orta Risk'
    }
  }

  const formatAllocation = (allocationStr) => {
    if (!allocationStr) return 'Bilgi yok'
    
    // %30 Hisse Senedi, %40 Tahvil, %30 Altın formatını parse et
    const allocations = allocationStr.split(',').map(item => item.trim())
    return allocations.map(allocation => {
      const match = allocation.match(/%(\d+)\s*(.+)/)
      if (match) {
        const percentage = match[1]
        const asset = match[2]
        return (
          <div key={asset} className="allocation-item">
            <span className="allocation-percentage">{percentage}%</span>
            <span className="allocation-asset">{asset}</span>
          </div>
        )
      }
      return <div key={allocation} className="allocation-item">{allocation}</div>
    })
  }

  return (
    <div className="portfolios-card">
      <div className="portfolios-card-header">
                  <div className="portfolios-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Portfolio/Investment Icon */}
              <path d="M3 3h18v18H3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M9 9h6v6H9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 3v18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M3 12h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        <div className="portfolios-card-title">Yatırım Portföyleri</div>
      </div>
      <div className="portfolios-card-content">
        <div className="portfolios-list">
          {portfolios.map((portfolio, index) => (
            <div key={index} className="portfolio-item">
              <div className="portfolio-header">
                <div className="portfolio-name">{portfolio.portfoy_adi}</div>
                <div className={`risk-badge ${getRiskColor(portfolio.risk_seviyesi)}`}>
                  {getRiskLabel(portfolio.risk_seviyesi)}
                </div>
              </div>
              <div className="portfolio-allocation">
                <div className="allocation-title">Varlık Dağılımı:</div>
                <div className="allocation-items">
                  {formatAllocation(portfolio.varlik_dagilimi)}
                </div>
              </div>
            </div>
          ))}
        </div>
        {portfolios.length > 0 && (
          <div className="portfolios-summary">
            {portfolios.length} portföy gösteriliyor
          </div>
        )}
      </div>
    </div>
  )
}

export default PortfoliosCard
