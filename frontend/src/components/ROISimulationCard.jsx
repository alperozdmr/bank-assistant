import './ROISimulationCard.css'

const ROISimulationCard = ({ cardData, onShowChart }) => {
  
  if (!cardData || cardData.type !== 'roi_simulation_card') return null

  const {
    portfolio_name,
    years,
    monthly_investment,
    average_outcome,
    good_scenario_outcome,
    bad_scenario_outcome,
    num_simulations_run
  } = cardData



  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (value) => {
    return `${value.toFixed(2)}%`
  }

  const calculateROI = (finalValue) => {
    const totalInvestment = monthly_investment * years * 12
    return ((finalValue - totalInvestment) / totalInvestment) * 100
  }

  return (
    <div className="roi-simulation-card">
              <div className="roi-simulation-card-header">
          <div className="roi-simulation-card-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* Chart/Graph Icon */}
              <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M18 17V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M13 17V5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 17v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="roi-simulation-card-title">ROI Simülasyonu</div>
          <div className="header-actions">
            <button 
              className="chart-button"
              onClick={() => onShowChart(cardData)}
              aria-label="ROI Grafiğini Aç"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M18 17V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M13 17V5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M8 17v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="chart-button-text">Yatırım Getirisi Grafiğini Aç</span>
            </button>
          </div>
        </div>

      <div className="roi-simulation-card-content">
        {/* Portföy Bilgileri */}
        <div className="portfolio-info">
          <div className="portfolio-name">{portfolio_name}</div>
          <div className="simulation-details">
            <span className="detail-item">
              <span className="label">Aylık Yatırım:</span>
              <span className="value">{formatCurrency(monthly_investment)}</span>
            </span>
            <span className="detail-item">
              <span className="label">Vade:</span>
              <span className="value">{years} yıl</span>
            </span>
            <span className="detail-item">
              <span className="label">Simülasyon:</span>
              <span className="value">{num_simulations_run.toLocaleString()} adet</span>
            </span>
          </div>
        </div>

        {/* Sonuç Özeti */}
        <div className="results-summary">
          <div className="result-card pessimistic">
            <div className="result-label">Kötümser Senaryo (25%)</div>
            <div className="result-amount">{formatCurrency(bad_scenario_outcome)}</div>
            <div className="result-roi">
              ROI: {formatPercentage(calculateROI(bad_scenario_outcome))}
            </div>
          </div>
          
          <div className="result-card average">
            <div className="result-label">Ortalama Senaryo</div>
            <div className="result-amount">{formatCurrency(average_outcome)}</div>
            <div className="result-roi">
              ROI: {formatPercentage(calculateROI(average_outcome))}
            </div>
          </div>
          
          <div className="result-card optimistic">
            <div className="result-label">İyimser Senaryo (75%)</div>
            <div className="result-amount">{formatCurrency(good_scenario_outcome)}</div>
            <div className="result-roi">
              ROI: {formatPercentage(calculateROI(good_scenario_outcome))}
            </div>
          </div>
        </div>



        {/* Detay Bilgileri */}
        <div className="detailed-analysis">
          <div className="analysis-item">
            <span className="analysis-label">Toplam Yatırım:</span>
            <span className="analysis-value">
              {formatCurrency(monthly_investment * years * 12)}
            </span>
          </div>
          <div className="analysis-item">
            <span className="analysis-label">Ortalama Yıllık Getiri:</span>
            <span className="analysis-value">
              {formatPercentage(calculateROI(average_outcome) / years)}
            </span>
          </div>
          <div className="analysis-item">
            <span className="analysis-label">Risk Aralığı:</span>
            <span className="analysis-value">
              {formatCurrency(bad_scenario_outcome)} - {formatCurrency(good_scenario_outcome)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ROISimulationCard
