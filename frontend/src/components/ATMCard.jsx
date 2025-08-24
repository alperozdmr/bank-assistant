import './ATMCard.css'

const ATMCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'atm_card') return null

  // Determine card width class based on result count
  const getWidthClass = (count) => {
    if (count === 1) return 'single-result'
    if (count === 2) return 'dual-result'
    return 'multi-result'
  }

  const widthClass = getWidthClass(cardData.count || cardData.items?.length || 0)

  return (
    <div className={`atm-card ${widthClass}`}>
      <div className="atm-card-header">
        <div className="atm-card-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Location Pin */}
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="atm-card-title">
          {cardData.query?.city} {cardData.query?.district ? `- ${cardData.query?.district}` : ''} 
          {cardData.query?.type === 'atm' ? ' ATM\'leri' : cardData.query?.type === 'branch' ? ' Şubeleri' : ' Lokasyonları'}
        </div>
      </div>
      <div className="atm-card-content">
        <div className="atm-list">
          {cardData.items.map((item, index) => (
            <div key={index} className="atm-item">
              <div className="atm-info">
                <div className="atm-name">{item.name}</div>
                <div className="atm-address">{item.address}</div>
                <div className="atm-meta">
                  <span className={`atm-type-badge ${item.type}`}>
                    {item.type === 'atm' ? 'ATM' : 'Şube'}
                  </span>
                  <span className="atm-location">
                    {item.city}{item.district ? `, ${item.district}` : ''}
                  </span>
                </div>
              </div>
              {(item.latitude && item.longitude) && (
                <div className="atm-actions">
                  <a 
                    href={`https://maps.google.com/?q=${item.latitude},${item.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="map-link"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M21 10C21 17 12 23 12 23S3 17 3 10C3 5.02944 7.02944 1 12 1C16.9706 1 21 5.02944 21 10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="10" r="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    Haritada Gör
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
        {cardData.count > 0 && (
          <div className="atm-summary">
            {cardData.count} sonuç bulundu
          </div>
        )}
      </div>
    </div>
  )
}

export default ATMCard
