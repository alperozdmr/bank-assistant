import './CardInfoCard.css'

const CardInfoCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'card_info_card') return null

  const formatCurrency = (amount) => {
    return `${parseFloat(amount).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TRY`
  }

  return (
    <div className="card-info-card">
      <div className="card-info-card-header">
        <div className="card-info-card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Credit Card Icon */}
            <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="2"/>
            <path d="M2 10H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="6" cy="15" r="1" fill="currentColor"/>
            <circle cx="9" cy="15" r="1" fill="currentColor"/>
          </svg>
        </div>
        <div className="card-info-card-title">Kredi Kartı Bilgileri</div>
      </div>
      <div className="card-info-card-content">
        <div className="card-info-grid">
          <div className="card-info-item">
            <div className="card-info-label">Kart No</div>
            <div className="card-info-value">#{cardData.card_id}</div>
          </div>
          <div className="card-info-item">
            <div className="card-info-label">Kredi Limiti</div>
            <div className="card-info-value limit">{formatCurrency(cardData.limit)}</div>
          </div>
          <div className="card-info-item">
            <div className="card-info-label">Güncel Borç</div>
            <div className="card-info-value debt">{formatCurrency(cardData.borc)}</div>
          </div>
          <div className="card-info-item">
            <div className="card-info-label">Kullanılabilir Limit</div>
            <div className="card-info-value available">
              {formatCurrency(cardData.limit - cardData.borc)}
            </div>
          </div>
          <div className="card-info-item">
            <div className="card-info-label">Kesim Tarihi</div>
            <div className="card-info-value">{cardData.kesim_tarihi}</div>
          </div>
          <div className="card-info-item">
            <div className="card-info-label">Son Ödeme Tarihi</div>
            <div className="card-info-value">{cardData.son_odeme_tarihi}</div>
          </div>
        </div>
        <div className="card-info-summary">
          <div className="card-usage-bar">
            <div className="usage-label">Limit Kullanımı</div>
            <div className="usage-bar">
              <div 
                className="usage-fill" 
                style={{ width: `${Math.min((cardData.borc / cardData.limit) * 100, 100)}%` }}
              ></div>
            </div>
            <div className="usage-percentage">
              %{Math.round((cardData.borc / cardData.limit) * 100)} kullanıldı
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CardInfoCard
