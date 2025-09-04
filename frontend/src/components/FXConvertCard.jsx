import './FXConvertCard.css'

const FXConvertCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'fx_convert_card') return null

  const {
    amount_from,
    currency_from,
    amount_to,
    currency_to,
    rate
  } = cardData

  return (
    <div className="fx-card">
      <div className="fx-card-header">
        <div className="fx-card-icon" aria-hidden>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 10h12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
            <path d="M6 14h12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
          </svg>
        </div>
        <div className="fx-card-title">Döviz Dönüşümü</div>
      </div>
      <div className="fx-card-body">
        <div className="fx-row">
          <div className="fx-label">Tutar</div>
          <div className="fx-value">{amount_from} {currency_from}</div>
        </div>
        <div className="fx-row fx-equals">=</div>
        <div className="fx-row">
          <div className="fx-label">Dönüşen</div>
          <div className="fx-value strong">{amount_to} {currency_to}</div>
        </div>
        <div className="fx-divider" />
        <div className="fx-rate">Kur: {String(currency_from).toUpperCase()}/{String(currency_to).toUpperCase()} = {rate?.toFixed ? rate.toFixed(4) : rate}</div>
      </div>
    </div>
  )
}

export default FXConvertCard


