import './AmortizationTableCard.css'

const AmortizationTableCard = ({ cardData }) => {
  if (!cardData || cardData.type !== 'amortization_table_card') return null

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

  const buildScheduleFromSummary = (summary) => {
    try {
      const principal = Number(summary.principal)
      const annualRate = Number(summary.annual_rate)
      const n = Number(summary.term_months)
      const currency = summary.currency || 'TRY'
      if (!(principal > 0) || !(n > 0) || annualRate === undefined || annualRate === null) return []
      const i = annualRate / 12
      const installment = annualRate === 0 ? principal / n : principal * i / (1 - Math.pow(1 + i, -n))
      let remaining = principal
      const rows = []
      for (let month = 1; month <= n; month++) {
        const interest = remaining * i
        let principalPart = installment - interest
        let pay = installment
        if (month === n) {
          principalPart = remaining
          pay = principalPart + interest
        }
        remaining = Math.max(0, remaining - principalPart)
        rows.push({
          month,
          installment: Number(pay.toFixed(2)),
          interest: Number(interest.toFixed(2)),
          principal: Number(principalPart.toFixed(2)),
          remaining: Number(remaining.toFixed(2)),
          currency,
        })
      }
      return rows
    } catch (e) {
      return []
    }
  }

  const handleCSVDownload = () => {
    const schedule = Array.isArray(cardData.schedule) && cardData.schedule.length > 0
      ? cardData.schedule
      : buildScheduleFromSummary(cardData.summary)

    if (!schedule || schedule.length === 0) return

    const delimiter = ';' // TR Excel için daha uyumlu
    const headers = ['Ay', 'Taksit', 'Faiz', 'Kalan Anapara (Ödenecek)']

    const formatNumberForCSV = (val) => {
      // Türkçe format (virgül) + başına TAB ekleyerek Excel'in otomatik tarih/numara algısını engelle
      const num = Number(val)
      if (isNaN(num)) return String(val)
      const tr = num.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      return `\t${tr}`
    }

    const rows = schedule.map(row => [
      row.month,
      formatNumberForCSV(row.installment),
      formatNumberForCSV(row.interest),
      formatNumberForCSV(row.remaining)
    ])

    const escapeCell = (val) => `"${String(val).replace(/"/g, '""')}"`
    const csvString = [
      headers.map(escapeCell).join(delimiter),
      ...rows.map(r => r.map(escapeCell).join(delimiter))
    ].join('\r\n')

    const bom = '\ufeff' // Excel için UTF-8 BOM
    const blob = new Blob([bom + csvString], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `kredi_odeme_plani_${cardData.summary.principal}_${cardData.summary.term_months}ay.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const getAmortizationIcon = () => {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )
  }

  return (
    <div className="amortization-table-card">
      <div className="amortization-card-header">
        <div className="amortization-card-left">
          <div className="amortization-card-icon">
            {getAmortizationIcon()}
          </div>
          <div className="amortization-card-title">Kredi Ödeme Planı</div>
        </div>
        <button 
          className="csv-export-button"
          onClick={handleCSVDownload}
          title="Taksit tablosunu CSV olarak indir"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="csv-export-button-text">Taksit Tablosu İndir</span>
        </button>
      </div>
      
      <div className="amortization-card-content">
        <div className="amortization-summary">
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-label">Anapara</span>
              <span className="summary-value">{formatCurrency(cardData.summary.principal, cardData.summary.currency)}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Aylık Faiz</span>
              <span className="summary-value rate-value">{formatPercentage(cardData.summary.monthly_rate)}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Vade</span>
              <span className="summary-value">{cardData.summary.term_months} ay</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Aylık Taksit</span>
              <span className="summary-value installment-value">{formatCurrency(cardData.summary.installment, cardData.summary.currency)}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Toplam Faiz</span>
              <span className="summary-value">{formatCurrency(cardData.summary.total_interest, cardData.summary.currency)}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Toplam Ödeme</span>
              <span className="summary-value total-value">{formatCurrency(cardData.summary.total_payment, cardData.summary.currency)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AmortizationTableCard
